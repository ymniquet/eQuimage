# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2024.01.14

"""Splash window."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

class SplashWindow:
  """Splash window class."""

  def __init__(self, backgroundfile, version):
    """Init splash window with background image 'backgroundfile' for version 'version'."""
    self.backgroundfile = backgroundfile
    self.version = version
    self.opened = False

  def open(self):
    """Open splash window."""
    if self.opened: return
    self.opened = True
    self.window = Gtk.Window(title = f"eQuimage v{self.version}", border_width = 0)
    self.window.set_position(Gtk.WindowPosition.CENTER)
    self.window.connect("delete-event", self.close)
    try:
      background = Gtk.Image.new_from_file(self.backgroundfile)
      self.window.add(background)
      self.window.show_all()
    except:
      self.close()

  def close(self, *args, **kwargs):
    """Close splash window."""
    if not self.opened: return
    self.window.destroy()
    self.opened = False
