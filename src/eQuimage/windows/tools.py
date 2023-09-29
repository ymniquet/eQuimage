# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 2023.09

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from matplotlib.backends.backend_gtk3 import NavigationToolbar2GTK3 as NavigationToolbar
from .base import BaseWindow, Container

"""Base tool window class."""

class BaseToolWindow(BaseWindow):
  """Base tool window class."""

  def __init__(self, app):
    """Bind window with app 'app'."""
    super().__init__(app)
    self.transformed = False

  def open(self, image, title):
    """Open tool window with title 'title' for image 'image'."""
    self.opened = True
    self.image = image.clone(description = "Image")
    self.image.stats = None
    self.reference = image.clone(description = "Reference")
    self.reference.stats = None
    self.transformed = False
    self.window = Gtk.Window(title = title,
                             transient_for = self.app.mainmenu.window,
                             border_width = 16)
    self.window.connect("delete-event", self.close)
    self.widgets = Container()
    self.signals = []

  def close(self, *args, **kwargs):
    """Close tool window."""
    if not self.opened: return
    self.window.destroy()
    self.opened = False
    self.app.mainwindow.set_rgb_luminance_callback(None)
    self.app.finalize_tool(self.image, self.operation())
    del self.signals
    del self.widgets
    del self.image
    del self.reference

  def apply_cancel_reset_close_buttons(self, onthefly = False):
    """Return a Gtk.HButtonBox with Apply/Cancel/Reset/Close buttons
       connected to self.apply, self.cancel, self.reset and self.close methods.
       If onethefly is True, the transformations are applied 'on the fly', thus
       the Apply and Reset buttons are not shown."""
    hbox = Gtk.HButtonBox(homogeneous = True, spacing = 16, halign = Gtk.Align.START)
    if not onthefly:
      self.widgets.applybutton = Gtk.Button(label = "Apply")
      self.widgets.applybutton.connect("clicked", self.apply)
      hbox.pack_start(self.widgets.applybutton, False, False, 0)
    self.widgets.cancelbutton = Gtk.Button(label = "Cancel")
    self.widgets.cancelbutton.connect("clicked", self.cancel)
    self.widgets.cancelbutton.set_sensitive(False)
    hbox.pack_start(self.widgets.cancelbutton, False, False, 0)
    if not onthefly:
      self.widgets.resetbutton = Gtk.Button(label = "Reset")
      self.widgets.resetbutton.connect("clicked", self.reset)
      hbox.pack_start(self.widgets.resetbutton, False, False, 0)
    self.widgets.closebutton = Gtk.Button(label = "Close")
    self.widgets.closebutton.connect("clicked", self.close)
    hbox.pack_start(self.widgets.closebutton, False, False, 0)
    return hbox

  def block_all_signals(self):
    """Block all signals."""
    for widget, signal in self.signals:
      widget.handler_block(signal)

  def unblock_all_signals(self):
    """Unblock all signals."""
    for widget, signal in self.signals:
      widget.handler_unblock(signal)
