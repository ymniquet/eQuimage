# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2023.11.27

"""Add Unistellar frame from an other image."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .tools import BaseToolWindow

class AddUnistellarFrame(BaseToolWindow):
  """Add Unistellar frame tool class."""

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Add frame"): return
    wbox = Gtk.VBox(spacing = 16)
    self.window.add(wbox)
    self.window.show_all()
    self.start_polling()

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
