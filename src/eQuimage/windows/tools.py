# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 2023.09

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject
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
    self.polltime = -1
    self.polltimer = None

  def close(self, *args, **kwargs):
    """Close tool window."""
    if not self.opened: return
    self.stop_polling_and_update() # Make sure the last changes have been applied.
    self.window.destroy()
    self.opened = False
    self.app.mainwindow.set_rgb_luminance_callback(None)
    self.app.finalize_tool(self.image, self.operation())
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

  # Polling for tool parameter changes.

  def start_polling(self, time, lastparams = None):
    """Start polling for tool parameter changes every 'time' ms.
       At each poll, get the tool parameters from self.get_params().
       Call self.update() if the tool parameters are the same *twice* in a row,
       but are different from the self.toolparams registered at the last update.
       lastparams is the original outcome of the last poll (default self.toolparams).
       Set to self.get_params() to tentatively call self.update() as soon as the first poll."""
    self.polltime = time
    self.pollparams = self.toolparams if lastparams is None else lastparams
    self.polltimer = GObject.timeout_add(self.polltime, self.poll)

  def poll(self, *args, **kwargs):
    """Poll for tool parameter changes, and call self.update() if the tool
       parameters are the same twice in a row, but are different from the
       self.toolparams registered at the last update."""
    params = self.get_params()
    #if params == self.pollparams and params != self.toolparams: self.update()
    if params != self.toolparams:
      if params == self.pollparams:
        print("Updating...")
        self.update()
      else:
        print("Deferring update...")
    self.pollparams = params
    return True

  def stop_polling(self):
    """Stop polling for tool parameter changes."""
    if self.polltimer is None: return
    GObject.source_remove(self.polltimer)
    self.polltimer = None

  def stop_polling_and_update(self):
    """Stop polling for tool parameter changes and update tool if needed."""
    if self.polltimer is None: return
    self.stop_polling()
    if self.get_params() != self.toolparams: self.update()

  def restart_polling(self):
    """Restart polling for tool parameter changes."""
    if self.polltimer is not None: return # Already polling.
    if self.polltime <= 0: return # No poll time defined.
    self.start_polling(self.polltime)

  def reset_polling(self, lastparams = None):
    """Reset polling for tool parameter changes."""
    if self.polltimer is None: return
    self.stop_polling()
    self.start_polling(self.polltime, lastparams)

  def connect_reset_polling(self, widget, signames):
    """Connect signals 'signames' of widget 'widget' to self.reset_poll(self.get_params()).
       This enhances responsivity to tool parameters changes."""
    widget.connect(signames, lambda *args: self.reset_polling(self.get_params()))
