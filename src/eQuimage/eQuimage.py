#!/usr/bin/python

# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.4.0 / 2024.02.26

"""eQuimage is a python tool to postprocess astronomical images from Unistellar telescopes."""

__version__ = "1.4.0"

import os
os.environ["LANGUAGE"] = "en"
import sys
import ast
import inspect
packagepath = os.path.dirname(inspect.getabsfile(inspect.currentframe()))
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Gio
import matplotlib.pyplot as plt
plt.style.use(os.path.join(packagepath, "config", "eQuimage.mplstyle"))
from .gui.base import ErrorDialog
from .gui.mainmenu import MainMenu
from .gui.mainwindow import MainWindow
from .gui.toolmanager import BaseToolWindow
from .gui.logs import LogWindow
from .imageprocessing import imageprocessing
from .imageprocessing.Unistellar import UnistellarImage

class eQuimageApp(Gtk.Application):
  """The eQuimage application."""

  #######################
  # Gtk initialization. #
  #######################

  def __init__(self, *args, **kwargs):
    """Initialize the eQuimage application."""
    super().__init__(*args, flags = Gio.ApplicationFlags.HANDLES_OPEN, **kwargs)
    self.initialize()

  def do_startup(self):
    """Load CSS and prepare main menu on startup."""
    Gtk.Application.do_startup(self)
    # Load CSS.
    screen = Gdk.Screen.get_default()
    provider = Gtk.CssProvider()
    provider.load_from_path(os.path.join(self.packagepath, "config", "eQuimage.css"))
    stylecontext = Gtk.StyleContext()
    stylecontext.add_provider_for_screen(screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    # Prepare main menu.
    self.mainmenu = MainMenu(self)

  def do_activate(self):
    """Open the main window on activation."""
    self.mainwindow.open()
    try: # Download freeimage plugin for imageio...
      import imageio
      imageio.plugins.freeimage.download()
    except:
      ErrorDialog(self.mainwindow.window, "Failed to download and install the freeimage plugin for imageio.")
      self.quit()

  def do_open(self, files, nfiles, hint):
    """Open command line file."""
    if nfiles > 1:
      print("Syntax : eQuimage [image_file] where [image_file] is the image to open.")
      self.quit()
    self.activate()
    try:
      self.load_file(files[0].get_path())
    except Exception as err:
      ErrorDialog(self.mainwindow.window, str(err))

  ###############################
  # Application data & methods. #
  ###############################
  
  ImageClass = UnistellarImage # The base class used for images.

  # Initialization.

  def initialize(self):
    """Initialize the eQuimage object."""
    self.version = __version__
    self.packagepath = packagepath
    self.mainwindow = MainWindow(self)
    self.toolwindow = BaseToolWindow(self)
    self.logwindow  = LogWindow(self)
    self.default_settings()
    if self.load_settings() > 0: self.save_settings() # Overwrite invalid or incomplete configuration file.
    self.reset()

  def reset(self):
    """Reset the eQuimage object data."""
    self.filename = None
    self.pathname = None
    self.basename = None
    self.savename = None
    self.frame = None
    self.images = []
    self.operations = []
    self.cancelled = []
    self.width = 0
    self.height = 0
    self.colordepth = 8
    self.meta = {}

  def clear(self, mainwindow = True):
    """Clear the eQuimage object data and windows.
       Don't clear the main window if mainwindow is False."""
    if self.filename is not None: print(f"Closing {self.filename}...")
    self.reset()
    self.logwindow.close()
    self.toolwindow.destroy()
    if mainwindow: self.mainwindow.reset_images()
    self.mainmenu.update()

  # Application context.

  def get_context(self, key = None):
    """Return the application context:
         - get_context("image") = True if an image is loaded.
         - get_context("activetool") = True if a tool is active.
         - get_context("cancelled") = True if there are cancelled operations available for redo.
         - get_context() returns all above keys as a dictionnary."""
    context = {"image": len(self.images) > 0, "activetool": self.toolwindow.opened, "cancelled": len(self.cancelled) > 0}
    return context[key] if key is not None else context

  def get_image_size(self):
    """Return width and height of the *original* image."""
    return self.width, self.height

  def get_color_depth(self):
    """Return color depth (bits per channel)."""
    return self.colordepth

  # File management.

  def get_packagepath(self):
    """Return package path."""
    return self.packagepath

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
    image = self.ImageClass()
    meta = image.load(filename)
    if not image.is_valid(): return
    self.clear(mainwindow = False)
    self.meta = meta
    self.filename = filename
    self.pathname = os.path.dirname(filename)
    self.basename = os.path.basename(filename)
    root, ext = os.path.splitext(filename)
    self.savename = root+"-post"+ext
    self.width, self.height = image.size() # *Original* image size.
    self.colordepth = self.meta["colordepth"] # Bits per channel.
    framed = image.check_frame()
    if framed:
      print(f"""Image has a frame type '{framed["type"]}'.""")
      self.frame = image.get_frame()
    else:
      self.frame = None
    image.meta["description"] = "Original image"
    self.push_operation(f"Load('{self.basename}')", image, self.frame)
    self.mainwindow.reset_images()
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
      if self.images[-1].rgb.dtype != imageprocessing.IMGTYPE:
        print(f"Warning: The last image pushed on the stack is not of type {str(imageprocessing.IMGTYPE)}.")
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

  def push_operation(self, operation, image, frame = None):
    """Push operation 'operation' on image 'image' on top of the operations and images stacks.
       If not None, 'frame' is the new image frame."""
    if frame is not None:
      self.frame = self.push_image(frame, clone = True)
    else:
      self.push_image(self.frame) # Just push a reference; do not duplicate the current frame.
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
    text = f"eQuimage v{self.version}\n"
    n = 0
    for operation, *images in self.operations:
      n += 1
      text += f"#{n} | {operation}\n"
    return text

  # Tools management.

  def run_tool(self, ToolClass, onthefly = True):
    """Run tool 'ToolClass'.
       Apply tool and update the main window on the fly if 'onthefly' is True."""
    if self.toolwindow.opened: return
    self.toolwindow = ToolClass(self, self.polltime if onthefly else -1)
    if not self.toolwindow.open(self.images[-1]): return
    self.mainmenu.update()
    self.toolwindow.window.present()

  def finalize_tool(self, image, operation, frame = None):
    """Finalize tool: push ('operation', 'image', 'frame') on the operations and images stacks (if operation is not None)
       and refresh main menu, main window, and log window.
       If 'frame' is None, the current self.frame is used as image frame from now on."""
    if operation is not None:
      image.meta["description"] = operation
      self.push_operation(operation, image, frame)
      self.cancelled = []
    self.mainwindow.reset_images()
    self.logwindow.update()
    self.mainmenu.update()

  def undo(self):
    """Cancel last operation."""
    if self.toolwindow.opened: return
    if not self.operations: return
    print("Cancelling last operation...")
    self.cancelled.append(self.pop_operation())
    if self.images: self.frame = self.images[-2] # Update current frame.
    self.mainwindow.reset_images()
    self.logwindow.update()
    self.mainmenu.update()

  def redo(self):
    """Redo last operation."""
    if self.toolwindow.opened: return
    if not self.cancelled: return
    print("Redoing last operation...")
    self.push_operation(*self.cancelled.pop())
    self.mainwindow.reset_images()
    self.logwindow.update()
    self.mainmenu.update()

  # Simple tools.

  def sharpen(self):
    """Sharpen image."""
    if self.toolwindow.opened: return
    print("Sharpening image (with Laplacian kernel)...")
    self.finalize_tool(self.images[-1].sharpen(inplace = False), f"Sharpen()")

  def negative(self):
    """Make a negative of the image."""
    if self.toolwindow.opened: return
    print("Converting to negative...")
    self.finalize_tool(self.images[-1].negative(inplace = False), f"Negative()")

  def remove_unistellar_frame(self):
    """Remove Unistellar frame."""
    if self.toolwindow.opened: return
    frame = self.images[-1].get_frame()
    if frame is None:
      ErrorDialog(self.mainwindow.window, "This image has no frame.")
      return
    print("Removing Unistellar frame...")
    self.finalize_tool(self.images[-1].remove_frame(frame, inplace = False), "RemoveUnistellarFrame()")

  def restore_unistellar_frame(self):
    """Restore Unistellar frame."""
    if self.toolwindow.opened: return
    if self.frame is None:
      ErrorDialog(self.mainwindow.window, "This is no registered frame.")
      return
    print("Restoring Unistellar frame...")
    try:
      image = self.images[-1].add_frame(self.frame, inplace = False)
    except:
      ErrorDialog(self.mainwindow.window, "Operation failed.")
      return
    self.finalize_tool(image, "RestoreUnistellarFrame()")

  # Settings.

  def settings_from_dict(self, settings):
    """Set settings from dictionnary 'settings'.
       Return zero if successful, non-zero otherwise."""
    error = 0
    try: # Apply remove hot pixels tool on the fly ?
      self.hotpixelsotf = bool(settings["remove_hot_pixels_on_the_fly"])
    except:
      print("remove_hot_pixels_on_the_fly keyword not found in configuration file.")
      error = 1
    try: # Apply stretch tools on the fly ?
      self.stretchotf = bool(settings["stretch_on_the_fly"])
    except:
      print("stretch_on_the_fly keyword not found in configuration file.")
      error = 2
    try: # Apply color tools on the fly ?
      self.colorotf = bool(settings["colors_on_the_fly"])
    except:
      print("colors_on_the_fly keyword not found in configuration file.")
      error = 3
    try: # Apply blend tool on the fly ?
      self.blendotf = bool(settings["blend_on_the_fly"])
    except:
      print("blend_on_the_fly keyword not found in configuration file.")
      error = 4
    try: # Poll for new operations every self.polltime ms.
      self.polltime = int(settings["poll_time"])
    except:
      print("poll_time keyword not found in configuration file.")
      error = 5
    return error

  def get_default_settings(self):
    """Return default settings as a dictionnary."""
    return {"remove_hot_pixels_on_the_fly": True, "stretch_on_the_fly": True, "colors_on_the_fly": True, "blend_on_the_fly": True, "poll_time": 333}

  def default_settings(self):
    """Apply default settings."""
    self.settings_from_dict(self.get_default_settings())

  def load_settings(self):
    """Read settings in (system wide) file packagepath/eQuimagerc.
       Return zero if successful, non-zero otherwise."""
    filename = os.path.join(self.packagepath, "config", "eQuimagerc")
    try:
      with open(filename, "r") as f:
        string = f.readline()
      settings = ast.literal_eval(string)
      if not isinstance(settings, dict): raise TypeError
    except:
      print(f"Failed to read configuration file {filename}.")
      return -1
    return self.settings_from_dict(settings)

  def save_settings(self):
    """Save settings in (system wide) file packagepath/eQuimagerc.
       Return zero if successful, non-zero otherwise."""
    error = 0
    settings = {"remove_hot_pixels_on_the_fly": self.hotpixelsotf, "stretch_on_the_fly": self.stretchotf, "colors_on_the_fly": self.colorotf, "blend_on_the_fly": self.blendotf, "poll_time": self.polltime}
    filename = os.path.join(self.packagepath, "config", "eQuimagerc")
    try:
      with open(filename, "w") as f:
        f.write(repr(settings))
    except:
      print(f"Failed to write configuration file {filename}.")
      error = -1
    return error

#

def run():
  """Run eQuimage."""
  application = eQuimageApp()
  application.run(sys.argv)

#

if __name__ == "__main__": run()
