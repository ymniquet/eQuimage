# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.4.0 / 2024.02.26
# GUI updated.

"""Pixel math tool."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject
from ..gtk.customwidgets import Label, HBox, VBox, FramedVBox, ScrolledBox, Entry, TextView
from ..toolmanager import BaseToolWindow
from ..misc.imagechooser import ImageChooser
from ...imageprocessing.utils import is_valid_image
from ...imageprocessing.pixelmath import PixelMath
import numpy as np

class PixelMathTool(BaseToolWindow):
  """Pixel math window class."""

  __action__ = "Doing pixel math..."

  __onthefly__ = False # This transformation can not be applied on the fly.

  __help__ = """<b>Instructions</b>:
Use python syntax. Reference image #i of the above list as 'IMGi'. Module numpy is imported as np.
<b>Commands</b>:
  \u2022 value(IMG1, midtone = 0.5): HSV value of image 'IMG1', with midtone correction 'midtone'.
  \u2022 luma(IMG1, midtone = 0.5): luma of image 'IMG1', with midtone correction 'midtone'.
  \u2022 luminance(IMG1, midtone = 0.5): luminance of image 'IMG1', with midtone correction 'midtone'.
  \u2022 blend(IMG1, IMG2, mix): Returns (1-mix)*IMG1+mix*IMG2. 'mix' can be an image or a scalar.
<b>Example</b>:
  \u2022 blend(IMG3, blend(IMG2, IMG1, luminance(IMG1)), luminance(IMG3)):
        HDR composition between "short" exposure image 'IMG1', "medium" exposure image 'IMG2', and "long" exposure image 'IMG3'.

<b>Log</b>:
"""

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Pixel math"): return False
    wbox = VBox()
    self.window.add(wbox)
    wbox.pack("List of available images:")
    self.widgets.chooser = ImageChooser(self.app, self.window, wbox, last = True)
    frame, vbox = FramedVBox()
    wbox.pack(frame, expand = True, fill = True)
    self.widgets.scrolled = ScrolledBox(800, 200)
    vbox.pack(self.widgets.scrolled, expand = True, fill = True)
    self.widgets.textview = TextView(wrap = False)
    self.widgets.textview.append_markup(self.__help__)
    self.widgets.scrolled.add(self.widgets.textview)
    self.widgets.commandentry = Entry()
    self.widgets.commandentry.connect("activate", lambda entry: self.apply())
    wbox.pack(self.widgets.commandentry.hbox(prepend = "IMG = "))
    wbox.pack(self.tool_control_buttons())
    self.start(identity = True)
    return True

  def get_params(self):
    """Return tool parameters."""
    return self.widgets.commandentry.get_text()

  def set_params(self, params):
    """Set tool parameters 'params'."""
    command = params
    self.widgets.commandentry.set_text(command)

  def run(self, params):
    """Run tool for parameters 'params'."""
    command = params
    if command == "": return params, False
    try:
      pm = PixelMath(self.widgets.chooser.get_images_list())
      output = pm.run(command)
    except Exception as err:
      GObject.idle_add(self.append_message, str(err), "red")
      return "", False
    if not is_valid_image(output):
      GObject.idle_add(self.append_message, "The command did not return a valid image", "red")
      return "", False
    self.image.set_image(output)
    GObject.idle_add(self.append_message, "Done", "green")
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    command = params
    if command == "": return None
    files = ""
    separator = ""
    for image in self.widgets.chooser.get_images_list():
      filename = image.meta.get("imchooser.file", None)
      if filename:
        row = image.meta.get("imchooser.row")
        files += f"{separator}#{row}: '{filename}'"
        separator = ", "
    if files: files = ", {"+files+"}"
    return f"PixelMath('{command}'{files})"

  # Log messages.

  def append_message(self, message, color = "black"):
    """Append message 'message' with color 'color' to self.widgets.textview."""
    self.widgets.textview.append_markup(f"<span foreground='{color}'>{message}</span>\n")
    vadj = self.widgets.scrolled.get_vadjustment() # Display the end of the text buffer.
    vadj.set_value(vadj.get_upper()-vadj.get_page_size())
