# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.0.0 / 2023.10.06

"""Log window."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
from .base import BaseWindow

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
    vbox = Gtk.VBox(spacing = 8)
    self.window.add(vbox)
    textview = Gtk.TextView()
    textview.set_editable(False)
    textview.set_cursor_visible(False)
    textview.set_wrap_mode(True)
    textview.set_justification(Gtk.Justification.LEFT)
    vbox.pack_start(textview, True, True, 0)
    self.textbuffer = textview.get_buffer()
    hbox = Gtk.HButtonBox(homogeneous = True, spacing = 16, halign = Gtk.Align.START)
    vbox.pack_start(hbox, False, False, 0)
    copybutton = Gtk.Button(label = "Copy")
    copybutton.connect("clicked", self.copy_to_clipboard)
    hbox.pack_start(copybutton, False, False, 0)
    closebutton = Gtk.Button(label = "Close")
    closebutton.connect("clicked", self.close)
    hbox.pack_start(closebutton, False, False, 0)
    self.update()
    self.window.show_all()

  def close(self, *args, **kwargs):
    """Close log window."""
    if not self.opened: return
    self.window.destroy()
    self.opened = False
    del self.textbuffer

  def update(self):
    """Update log window."""
    if not self.opened: return
    self.textbuffer.set_text(self.app.logs())

  def copy_to_clipboard(self, *args, **kwargs):
    """Copy the content of the log window to the clipboard."""
    if not self.opened: return
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    clipboard.set_text(self.textbuffer.get_text(self.textbuffer.get_start_iter(), self.textbuffer.get_end_iter(), False), -1)
