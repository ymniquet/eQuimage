# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.7.0 / 2025.05.11
# GUI updated (+).

"""Log window."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .gtk.customwidgets import VBox, ScrolledBox, HButtonBox, Button, TextView
from .base import BaseWindow, Container

class LogWindow(BaseWindow):
  """Log window class."""

  def open(self):
    """Open log window."""
    if self.opened: return
    if self.app.get_basename() is None: return
    self.opened = True
    self.window = Gtk.Window(title = f"Logs for {self.app.get_basename()}", border_width = 16)
    self.window.connect("delete-event", self.close)
    self.window.set_size_request(480, 360)
    self.widgets = Container()
    wbox = VBox()
    self.window.add(wbox)
    self.widgets.scrolled = ScrolledBox(-1, -1)
    wbox.pack(self.widgets.scrolled, expand = True, fill = True)
    self.widgets.textview = TextView()
    self.widgets.scrolled.add(self.widgets.textview)
    hbox = HButtonBox()
    wbox.pack(hbox)
    self.widgets.copybutton = Button(label = "Copy")
    self.widgets.copybutton.connect("clicked", self.widgets.textview.copy_to_clipboard)
    hbox.pack(self.widgets.copybutton)
    self.widgets.closebutton = Button(label = "Close")
    self.widgets.closebutton.connect("clicked", self.close)
    hbox.pack(self.widgets.closebutton)
    self.update()
    self.window.show_all()

  def close(self, *args, **kwargs):
    """Close log window."""
    if not self.opened: return
    self.window.destroy()
    self.opened = False
    del self.widgets

  def update(self):
    """Update log window."""
    if not self.opened: return
    self.widgets.textview.set_text(self.app.logs())
