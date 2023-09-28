#!/usr/bin/python

# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 2023.09 *

# TO DO:
#  - Remove hot pixels on super-resolution images ?

import os
os.environ["LANGUAGE"] = "en"
import sys
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
from .imageprocessing import imageprocessing
from .imageprocessing.Unistellar import UnistellarImage as Image

"""eQuimage is a python tool to postprocess astronomical images from Unistellar telescopes."""

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

  def initialize(self):
    """Initialize the eQuimage object."""
    self.mainmenu = MainMenu(self)
    self.mainwindow = MainWindow(self)
    self.toolwindow = BaseToolWindow(self)
    self.logwindow = LogWindow(self)
    self.filename = None
    self.hasframe = False
    self.onthefly = False
    self.clear()

  def clear(self):
    """Close file (if any) and clear the eQuimage object data."""
    if self.filename is not None: print(f"Closing {self.filename}...")
    self.mainwindow.close(force = True, clear = False)
    self.logwindow.close()
    self.toolwindow.close()
    if self.hasframe: del self.frame
    self.hasframe = False
    self.filename = None
    self.pathname = None
    self.basename = None
    self.savename = None
    self.images = []
    self.operations = []
    self.width = 0
    self.height = 0
    self.exif = None
    self.mainmenu.update()

  def get_context(self, key = None):
    """Return the application context:
         - get_context("image") = True if an image is loaded.
         - get_context("operations") = True if operations have been performed on the image.
         - get_context("activetool") = True if a tool is active.
         - get_context("frame") = True if the image has a frame.
         - get_context() returns all above keys as a dictionnary."""
    context = {"image": len(self.images) > 0, "operations": len(self.operations) > 0, "activetool": self.toolwindow.opened, "frame": self.hasframe}
    return context[key] if key is not None else context

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

  def get_image_size(self):
    """Return width and height of the images."""
    return self.width, self.height

  def push_image(self, image):
    """Push a clone of image 'image' on top of the images stack."""
    self.images.append(image.clone())

  def pop_image(self):
    """Pop and return image from the top of the images stack."""
    return self.images.pop()

  def get_nbr_images(self):
    """Return the number of images in the images stack."""
    return len(self.images)

  def get_image(self, index):
    """Return image with index 'index' from the images stack."""
    return self.images[index]

  def load_file(self, filename):
    """Load image file 'filename'."""
    print(f"Loading file {filename}...")
    image = Image()
    self.exif = image.load(filename, description = "Original")
    self.clear()
    self.filename = filename
    self.pathname = os.path.dirname(filename)
    self.basename = os.path.basename(filename)
    root, ext = os.path.splitext(filename)
    self.savename = root+"-post"+ext
    self.width, self.height = image.size()
    self.hasframe = image.check_frame()
    if self.hasframe:
      print(f"Image has a frame type '{image.get_frame_type()}'.")
      self.frame = image.get_frame()
    self.push_image(image)
    self.mainwindow.open()
    self.mainmenu.update()

  def save_file(self, filename = None):
    """Save image file 'filename' (defaults to self.savename if None)."""
    if not self.images: return
    if filename is None: filename = self.savename
    if self.images[-1].is_gray_scale():
      print(f"Saving file {filename} as gray scale...")
      self.images[-1].save_gray_scale(filename, exif = self.exif)
    else:
      print(f"Saving file {filename} as RGBA...")
      self.images[-1].save(filename, exif = self.exif)
    root, ext = os.path.splitext(filename)
    with open(root+".log", "w") as f: f.write(self.logs())
    self.savename = filename

  def push_operation(self, image, operation = "Unknown"):
    """Push operation 'operation' on image 'image' on top of the operations and images stacks."""
    self.push_image(image)
    self.operations.append((operation, self.images[-1]))

  def pop_operation(self):
    """Pop and return last (operation, image) from the top of the operations stack.
       The images stack is truncated accordingly."""
    operation, image = self.operations.pop()
    index = self.images.index(image)
    self.images = self.images[:index]
    return operation, image

  def get_nbr_operations(self):
    """Return the number of operations in the operations stack."""
    return len(self.operations)

  def logs(self):
    """Return logs from the operations stack."""
    text = ""
    for operation, image in self.operations:
      text += operation+"\n"
    return text

  def run_tool(self, ToolClass):
    """Run tool 'ToolClass'."""
    if not self.mainwindow.opened: return
    if self.toolwindow.opened: return
    self.toolwindow = ToolClass(self)
    self.toolwindow.open(self.images[-1])
    self.mainmenu.update(present = False)
    self.toolwindow.window.present()

  def finalize_tool(self, image, operation):
    """Finalize tool: push ('image', 'operation') on the operations and images stacks (if operation is not None)
       and refresh main menu, main window, and log window."""
    if operation is not None:
      image.set_description("Image")
      self.push_operation(image, operation)
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
    red, green, blue = imageprocessing.get_rgb_luminance()
    self.finalize_tool(self.images[-1].gray_scale(inplace = False), f"GrayScale({red:.2f}, {green:.2f}, {blue:.2f})")

  def remove_unistellar_frame(self):
    """Remove Unistellar frame."""
    if not self.mainwindow.opened: return
    if self.toolwindow.opened: return
    if not self.hasframe: return
    print("Removing Unistellar frame...")
    self.finalize_tool(self.images[-1].remove_frame(self.frame, inplace = False), "RemoveUnistellarFrame()")

  def restore_unistellar_frame(self):
    """Restore Unistellar frame."""
    if not self.mainwindow.opened: return
    if self.toolwindow.opened: return
    if not self.hasframe: return
    print("Restoring Unistellar frame...")
    self.finalize_tool(self.images[-1].add_frame(self.frame, inplace = False), "RestoreUnistellarFrame()")

#

def run():
  """Run eQuimage."""
  application = eQuimageApp()
  application.run(sys.argv)

#

if __name__ == "__main__": run()
