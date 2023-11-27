# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2023.11.27

"""Add Unistellar frame from an other image."""

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
    frame = image.get_frame()
    wbox = Gtk.VBox(spacing = 16)
    self.window.add(wbox)
    wbox.pack_start(self.apply_cancel_reset_close_buttons(), False, False, 0)
    self.window.show_all()
    return True

  def get_params(self):
    """Return tool parameters."""
    return None

  def reset(self, *args, **kwargs):
    """Reset tool parameters."""
    return

  def run(self, *args, **kwargs):
    """Run tool."""
    return None

  def apply(self, *args, **kwargs):
    """Apply tool."""
    print("Adding Unistellar frame...")
    super().apply()

  def operation(self):
    """Return tool operation string."""
    if not self.transformed: return None
    return f"Add Unistellar Frame()"

  def cancel(self, *args, **kwargs):
    """Cancel tool."""
    super().cancel()
    self.resume_polling() # Resume polling.
