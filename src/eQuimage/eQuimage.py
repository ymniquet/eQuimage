#!/usr/bin/python

# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2023.11.27

"""eQuimage is a python tool to postprocess astronomical images from Unistellar telescopes."""

__version__ = "1.2.0"

import os
os.environ["LANGUAGE"] = "en"
import sys
import ast
import inspect
packagepath = os.path.dirname(inspect.getabsfile(inspect.currentframe()))
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio
import matplotlib.pyplot as plt
plt.style.use(packagepath+"/eQuimage.mplstyle")
from .windows.mainmenu import MainMenu
from .windows.mainwindow import MainWindow
from .windows.tools import BaseToolWindow
from .windows.logs import LogWindow
from .windows.splash import SplashWindow
from .imageprocessing import imageprocessing
from .imageprocessing.Unistellar import UnistellarImage as Image

class eQuimageApp(Gtk.Application):
  """The eQuimage application."""

  #######################
  # Gtk initialization. #
  #######################

  def __init__(self, *args, **kwargs):
    """Initialize the eQuimage application."""
    super().__init__(*args, flags = Gio.ApplicationFlags.HANDLES_OPEN, **kwargs)
    self.initialize()

  def do_activate(self):
    """Open the main menu on activation."""
    self.splashwindow.open()
    self.mainmenu.open()

  def do_open(self, files, nfiles, hint):
    """Open command line file on startup."""
    if nfiles > 1:
      print("Syntax : eQuimage [image_file] where [image_file] is the image to open.")
      self.quit()
    self.activate()
    self.load_file(files[0].get_path())

  ###############################
  # Application data & methods. #
  ###############################

  # Initialization.

  def initialize(self):
    """Initialize the eQuimage object."""
    self.version = __version__
    self.splashwindow = SplashWindow(packagepath+"/images/splash.png", self.version)
    self.mainmenu = MainMenu(self)
    self.mainwindow = MainWindow(self)
    self.toolwindow = BaseToolWindow(self)
    self.logwindow = LogWindow(self)
    self.filename = None
    self.frame = None
    self.default_settings()
    if self.load_settings() > 0: self.save_settings() # Overwrite invalid or incomplete configuration file.
    self.clear()

  def clear(self):
    """Close file (if any) and clear the eQuimage object data."""
    if self.filename is not None: print(f"Closing {self.filename}...")
    self.logwindow.close()
    self.toolwindow.destroy()
    self.mainwindow.destroy()
    self.filename = None
    self.pathname = None
    self.basename = None
    self.savename = None
    self.frame = None
    self.images = []
    self.operations = []
    self.width = 0
    self.height = 0
    self.meta = {}
    self.mainmenu.update()

  # Application context.

  def get_context(self, key = None):
    """Return the application context:
         - get_context("image") = True if an image is loaded.
         - get_context("operations") = True if operations have been performed on the image.
         - get_context("activetool") = True if a tool is active.
         - get_context("frame") = True if the image has a frame.
         - get_context() returns all above keys as a dictionnary."""
    context = {"image": len(self.images) > 0, "operations": len(self.operations) > 0, "activetool": self.toolwindow.opened, "frame": self.frame is not None}
    return context[key] if key is not None else context

  def get_image_size(self):
    """Return width and height of the *original* images."""
    return self.width, self.height

  # File management.

  def get_filename(self):
    """Return image file name."""
    return self.filename

  def get_basename(self):
    """Return image base name."""
    return self.basename

  def get_pathname(self):
    """Return image path name."""
    return self.pathname

  def get_savename(self):
    """Return image save name."""
    return self.savename

  def load_file(self, filename):
    """Load image file 'filename'."""
    image = Image()
    meta = image.load(filename, description = "Original")
    if not image.is_valid(): return
    self.clear()
    self.meta = meta
    self.filename = filename
    self.pathname = os.path.dirname(filename)
    self.basename = os.path.basename(filename)
    root, ext = os.path.splitext(filename)
    self.savename = root+"-post"+ext
    self.width, self.height = image.size() # *Original* image size.
    self.push_image(image, clone = True) # Push the original (reference) image at the bottom of the stack.
    if image.check_frame(): # Push (original frame, original image) on the stack as a starting point ("cancel last operation" won't pop images beyond that point).
      print(f"Image has a frame type '{image.get_frame_type()}'.")
      self.frame = self.push_image(image.get_frame(), clone = True)
    else:
      self.frame = self.push_image(None)
    self.push_image(self.images[-2]) # Just push a pointer; do not duplicate original image.
    self.splashwindow.close()
    self.mainwindow.open()
    self.mainmenu.update()

  def save_file(self, filename = None, depth = 8):
    """Save image in file 'filename' (defaults to self.savename if None) with color depth 'depth' (bits/channel)."""
    if not self.images: return
    if filename is None: filename = self.savename
    self.images[-1].save(filename, depth = depth)
    root, ext = os.path.splitext(filename)
    with open(root+".log", "w") as f: f.write(self.logs())
    self.savename = filename

  # Images stack.

  def push_image(self, image, clone = False):
    """Push (or clone) image 'image' on top of the images stack."""
    self.images.append(image.clone() if clone else image)
    if self.images[-1] is not None:
      if self.images[-1].image.dtype != imageprocessing.imgtype:
        print(f"Warning: The last image pushed on the stack is not {str(imageprocessing.imgtype)}.")
    return self.images[-1]

  def pop_image(self):
    """Pop and return image from the top of the images stack."""
    return self.images.pop()

  def get_nbr_images(self):
    """Return the number of images in the images stack."""
    return len(self.images)

  def get_image(self, index):
    """Return image with index 'index' from the images stack."""
    return self.images[index]

  # Operations stack.

  def push_operation(self, image, operation = "Unknown", frame = None):
    """Push operation 'operation' on image 'image' on top of the operations and images stacks.
       If not None, 'frame' is the new image frame."""
    if frame is not None:
      self.frame = self.push_image(frame, clone = True)
    else:
      self.push_image(self.frame) # Just push a pointer; do not duplicate current frame.
    self.push_image(image, clone = True)
    self.operations.append((operation, self.images[-1], self.images[-2]))

  def pop_operation(self):
    """Pop and return last (operation, image, frame) from the top of the operations stack.
       The images stack is truncated accordingly."""
    operation, image, frame = self.operations.pop()
    index = self.images.index(image)
    self.images = self.images[:index-1] # Include frame.
    return operation, image, frame

  def get_nbr_operations(self):
    """Return the number of operations in the operations stack."""
    return len(self.operations)

  def logs(self):
    """Return logs from the operations stack."""
    text = "eQuimage v"+self.version+"\n"
    for operation, *images in self.operations:
      text += operation+"\n"
    return text

  # Tools management.

  def run_tool(self, ToolClass, onthefly = True):
    """Run tool 'ToolClass'.
       Apply tool and update the main window on the fly if 'onthefly' is True."""
    if not self.mainwindow.opened: return
    if self.toolwindow.opened: return
    self.toolwindow = ToolClass(self, self.polltime if onthefly else -1)
    if not self.toolwindow.open(self.images[-1]): return
    self.mainmenu.update(present = False)
    self.toolwindow.window.present()

  def finalize_tool(self, image, operation, frame = None):
    """Finalize tool: push ('image', 'operation', 'frame') on the operations and images stacks (if operation is not None)
       and refresh main menu, main window, and log window.
       If 'frame' is None, the current self.frame is used as image frame."""
    if operation is not None:
      image.set_description("Image")
      self.push_operation(image, operation, frame)
    self.mainwindow.reset_images()
    self.logwindow.update()
    self.mainmenu.update()

  def cancel_last_operation(self):
    """Cancel last operation."""
    if not self.mainwindow.opened: return
    if self.toolwindow.opened: return
    if not self.operations: return
    print("Cancelling last operation...")
    self.pop_operation()
    self.frame = self.images[-2] # Update current frame.
    self.mainwindow.reset_images()
    self.logwindow.update()
    self.mainmenu.update()

  def sharpen(self):
    """Sharpen image."""
    if not self.mainwindow.opened: return
    if self.toolwindow.opened: return
    print("Sharpening image...")
    self.finalize_tool(self.images[-1].sharpen(inplace = False), f"Sharpen()")

  def gray_scale(self):
    """Convert image to gray scale."""
    if not self.mainwindow.opened: return
    if self.toolwindow.opened: return
    print("Converting to gray scale...")
    self.mainwindow.lock_rgb_luminance()
    red, green, blue = imageprocessing.get_rgb_luminance()
    self.finalize_tool(self.images[-1].gray_scale(inplace = False), f"GrayScale({red:.2f}, {green:.2f}, {blue:.2f})")
    self.mainwindow.unlock_rgb_luminance()

  def remove_unistellar_frame(self):
    """Remove Unistellar frame."""
    if not self.mainwindow.opened: return
    if self.toolwindow.opened: return
    if self.frame is None: return
    print("Removing Unistellar frame...")
    self.finalize_tool(self.images[-1].remove_frame(self.frame, inplace = False), "RemoveUnistellarFrame()")

  def restore_unistellar_frame(self):
    """Restore Unistellar frame."""
    if not self.mainwindow.opened: return
    if self.toolwindow.opened: return
    if self.frame is None: return
    print("Restoring Unistellar frame...")
    self.finalize_tool(self.images[-1].add_frame(self.frame, inplace = False), "RestoreUnistellarFrame()")

  # Settings.

  def settings_from_dict(self, settings):
    """Set settings from dictionnary 'settings'.
       Return zero if successful, non-zero otherwise."""
    error = 0
    try: # Apply remove hot pixels tool on the fly ?
      self.hotpixlotf = bool(settings["remove_hot_pixels_on_the_fly"])
    except:
      print("remove_hot_pixels_on_the_fly keyword not found in configuration file.")
      error = 1
    try: # Apply balance colors tool on the fly ?
      self.colorblotf = bool(settings["balance_colors_on_the_fly"])
    except:
      print("balance_colors_on_the_fly keyword not found in configuration file.")
      error = 2
    try: # Apply stretch tool on the fly ?
      self.stretchotf = bool(settings["stretch_on_the_fly"])
    except:
      print("stretch_on_the_fly keyword not found in configuration file.")
      error = 3
    try: # Poll for new operations every self.polltime ms.
      self.polltime = int(settings["poll_time"])
    except:
      print("poll_time keyword not found in configuration file.")
      error = 4
    return error

  def get_default_settings(self):
    """Return default settings as a dictionnary."""
    return {"remove_hot_pixels_on_the_fly": True, "balance_colors_on_the_fly": True, "stretch_on_the_fly": True, "poll_time": 333}

  def default_settings(self):
    """Apply default settings."""
    self.settings_from_dict(self.get_default_settings())

  def save_settings(self):
    """Save settings in (system wide) file packagepath/eQuimagerc.
       Return zero if successful, non-zero otherwise."""
    error = 0
    settings = {"remove_hot_pixels_on_the_fly": self.hotpixlotf, "balance_colors_on_the_fly": self.colorblotf, "stretch_on_the_fly": self.stretchotf, "poll_time": self.polltime}
    try:
      with open(packagepath+"/eQuimagerc", "w") as f:
        f.write(repr(settings))
    except:
      print("Failed to write configuration file "+packagepath+"/eQuimagerc.")
      error = -1
    return error

  def load_settings(self):
    """Read settings in (system wide) file packagepath/eQuimagerc.
       Return zero if successful, non-zero otherwise."""
    try:
      with open(packagepath+"/eQuimagerc", "r") as f:
        string = f.readline()
      settings = ast.literal_eval(string)
      if not isinstance(settings, dict): raise TypeError
    except:
      print("Failed to read configuration file "+packagepath+"/eQuimagerc.")
      return -1
    return self.settings_from_dict(settings)

#

def run():
  """Run eQuimage."""
  application = eQuimageApp()
  application.run(sys.argv)

#

if __name__ == "__main__": run()
