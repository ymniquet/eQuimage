# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 3.0.0 / 2026.01.15
# Doc OK.

"""External image editors."""

import os
import tempfile
import subprocess
import numpy as np

from . import image_io as io

#####################################
# For inclusion in the Image class. #
#####################################

class MixinImage:
  """To be included in the Image class."""

  def edit_with(self, command, export = "tiff", depth = 16, script = None, editor = "<Editor>", interactive = True, cwd = None):
    """Edit the image with an external tool.

    The image is saved on disk; the editor is then run on this file, which is finally reloaded in
    eQuimageLab and returned.

    The user/editor must simply overwrite the edited file on exit.

    Args:
      command (str): The editor command to be run (e.g., "gimp -n $FILE$").
        Any "$FILE$" is replaced by the name of the image file to be opened by the editor.
        Any "$SCRIPT$" is replaced by the name of the script file to be run by the editor.
      export (str, optional): The format used to export the image. Can be:

        - "png": PNG file with depth = 8 or 16 bits integer per channel.
        - "tiff" (default): TIFF file with depth = 8, 16 or 32 bits integer per channel.
        - "fits": FITS file width depth = 32 bits float per channel.

      depth (int, optional): The color depth (bits per channel) used to export the image
        (see above; default 16).
      script (str, optional): A string containing a script to be executed by the editor
        (default None). Any "$FILE$" is replaced by the name of the image file.
      editor (str, optional): The name of the editor (for pretty print; default "<Editor>").
      interactive (bool, optional): If True (default), the editor is interactive (awaits commands
        from the user); if False, the editor processes the image autonomously and does not require
        inputs from the user.
      cwd (str, optional): If not None (default), change to this working directory before running
        the editor.

    Returns:
      Image: The edited image.
    """
    self.check_color_model("RGB", "gray")
    if export not in ["png", "tiff", "fits"]:
      raise ValueError(f"Error, unknown export format '{export}'.")
    if depth not in [8, 16, 32]:
      raise ValueError("Error, depth must be 8, 16 or 32 bpc.")
    # Edit image.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors = True) as tmpdir:
      filename = "eQuimageLab."+export # Set image tmp file name.
      filepath = os.path.join(tmpdir, filename)
      filefound = False
      # Process script.
      if script is not None:
        scriptname = "eQuimageLab.script" # Set script tmp file name.
        scriptpath = os.path.join(tmpdir, scriptname)
        scriptfound = False
        filefound = "$FILE$" in script
        if filefound: script = script.replace("$FILE$", filepath)
      # Process command.
      splitcmd = []
      for item in command.strip().split(" "):
        if item == "$FILE$":
          filefound = True
          splitcmd.append(filepath)
        elif item == "$SCRIPT$":
          if script is None:
            raise ValueError("Error, there is a place holder for a script file ($SCRIPT$) in the command but no script provided.")
          scriptfound = True
          splitcmd.append(scriptpath)
        else:
          splitcmd.append(item)
      # Check script & command consistency.
      if script is None:
        if not filefound:
          raise ValueError("Error, no place holder for the image file ($FILE$) found in the command.")
      else:
        if not filefound:
          raise ValueError("Error, no place holder for the image file ($FILE$) found in the command and in the script.")
        if not scriptfound:
          raise ValueError("Error, no place holder for the script file ($SCRIPT$) found in the command.")
      # Save script.
      if script is not None:
        print(f"Writing file {scriptpath}...")
        with open(scriptpath, "w") as f: f.write(script)
      # Save image.
      print(f"Writing file {filepath} with depth = {depth} bpc...")
      self.save(filepath, depth = depth, compress = 0, verbose = False) # Don't compress image to ensure compatibility with the editor.
      ctime = os.path.getmtime(filepath)
      # Run editor.
      print(f"Running {editor}...")
      if interactive: print(f"Overwrite file {filepath} when leaving {editor}.")
      subprocess.run(splitcmd, cwd = cwd)
      # Load and return edited image.
      mtime = os.path.getmtime(filepath)
      if mtime == ctime:
        if interactive:
          print(f"The image has not been modified by {editor}; Returning the original...")
          return self.copy()
        else:
          raise ValueError(f"Error, the image has not been modified by {editor}...")
      print(f"Reading file {filepath}...")
      image, meta = io.load_image_as_array(filepath, verbose = False)
      return self.newImage(image)

  def edit_with_gimp(self, export = "tiff", depth = 16):
    """Edit the image with Gimp.

    The image is saved on disk; Gimp is then run on this file, which is finally reloaded in
    eQuimageLab and returned.

    The user must simply overwrite the edited file when leaving Gimp.

    Warning:
      The command "gimp" must be in the PATH.

    Args:
      export (str, optional): The format used to export the image. Can be:

        - "png": PNG file with depth = 8 or 16 bits integer per channel.
        - "tiff" (default): TIFF file with depth = 8, 16 or 32 bits integer per channel.
        - "fits": FITS file width depth = 32 bits float per channel.

      depth (int, optional): The color depth (bits per channel) used to export the image
        (see above; default 16).

    Returns:
      Image: The edited image.
    """
    return self.edit_with("gimp -n $FILE$", export = export, depth = depth, editor = "Gimp", interactive = True)

  def edit_with_siril(self):
    """Edit the image with Siril.

    The image is saved as a FITS file (32 bits float per channel); Siril is then run on this file,
    which is finally reloaded in eQuimageLab and returned.

    The user must simply overwrite the edited file when leaving Siril.

    Warning:
      The command "siril" must be in the PATH.

    Returns:
      Image: The edited image.
    """
    return self.edit_with("siril $FILE$", export = "fits", depth = 32, editor = "Siril", interactive = True)
