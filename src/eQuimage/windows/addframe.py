# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2023.11.27

"""Add Unistellar frame from an other image."""

import os
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .gtk.utils import flush_gtk_events
from .gtk.filechoosers import ImageChooserDialog
from .base import ErrorDialog
from .tools import BaseToolWindow
from ..imageprocessing.Unistellar import UnistellarImage as Image

class AddUnistellarFrame(BaseToolWindow):
  """Add Unistellar frame tool class."""

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Add frame"): return False
    filename = ImageChooserDialog(self.app.mainmenu.window, Gtk.FileChooserAction.OPEN, path = self.app.get_filename(), preview = True, title = "Open framed image")
    if filename is None:
      self.destroy()
      return False
    image = Image()
    image.load(filename, description = "Framed image")
    hasframe = image.check_frame()
    if not hasframe:
      ErrorDialog(self.window, "This image has no frame.")
      self.destroy()
      return False
    print(f"Image has a frame type '{image.get_frame_type()}'.")
    frame = image.get_frame()
    self.toolparams = os.path.basename(filename)
    wbox = Gtk.VBox(spacing = 16)
    self.window.add(wbox)
    wbox.pack_start(self.tool_control_buttons(model = "onthefly"), False, False, 0)
    self.window.show_all()
    return True

  def run(self, params):
    """Run tool for parameters 'params'."""
    return None, False

  def apply(self, *args, **kwargs):
    """Apply tool."""
    print("Adding Unistellar frame...")
    super().apply()

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    return f"AddUnistellarFrame('{params}')"

