# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 2023.09

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .base import BaseWindow, Container

"""Settings window."""

class SettingsWindow(BaseWindow):
  """Settings window class."""

  def open(self):
    """Open tool window with title 'title' for image 'image'."""
    if self.opened: return
    self.opened = True
    self.window = Gtk.Window(title = "Settings",
                             transient_for = self.app.mainmenu.window,
                             border_width = 16,
                             modal = True)
    self.window.connect("delete-event", self.close)
    self.widgets = Container()
    vbox = Gtk.VBox(spacing = 16)
    self.window.add(vbox)
    self.widgets.ontheflybutton = Gtk.CheckButton(label = "Apply transformations on the fly")
    self.widgets.ontheflybutton.set_active(self.app.onthefly)
    vbox.pack_start(self.widgets.ontheflybutton, False, False, 0)
    hbox = Gtk.HButtonBox(homogeneous = True, spacing = 16, halign = Gtk.Align.START)
    vbox.pack_start(hbox, False, False, 0)
    self.widgets.applybutton = Gtk.Button(label = "OK")
    self.widgets.applybutton.connect("clicked", self.apply)
    hbox.pack_start(self.widgets.applybutton, False, False, 0)
    self.widgets.cancelbutton = Gtk.Button(label = "Cancel")
    self.widgets.cancelbutton.connect("clicked", self.close)
    hbox.pack_start(self.widgets.cancelbutton, False, False, 0)
    self.window.show_all()

  def apply(self, *args, **kwargs):
    """Apply settings."""
    if not self.opened: return
    self.app.onthefly = self.widgets.ontheflybutton.get_active()
    self.close()

  def close(self, *args, **kwargs):
    """Close settings window."""
    if not self.opened: return
    self.window.destroy()
    self.opened = False
    del self.widgets
