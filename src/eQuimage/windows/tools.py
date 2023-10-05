# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 2023.10 *

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject
from .base import BaseWindow, Container
from .gtk.customwidgets import Button
from collections import OrderedDict as OD
import threading

"""Base tool window class."""

class BaseToolWindow(BaseWindow):
  """Base tool window class."""

  def __init__(self, app, polltime = -1):
    """Bind window with app 'app'.
       If polltime > 0, run the tool and update the main window on the fly by polling for
       tool parameter changes every 'polltime' ms. If polltime <= 0, the user must click
       an 'Apply' button to run the tool and update the main window."""
    super().__init__(app)
    self.polltime = polltime
    self.onthefly = (polltime > 0)
    self.transformed = False

  def open(self, image, title):
    """Open tool window with title 'title' for image 'image'.
       Return True if successful, False otherwise."""
    if self.opened: return False
    if not self.app.mainwindow.opened: return False
    self.opened = True
    self.image = image.clone(description = "Image")
    self.image.stats = None # Image statistics.
    self.reference = image.clone(description = "Reference")
    self.reference.stats = None # Reference image statistics.
    self.transformed = False
    self.app.mainwindow.set_images(OD(Image = self.image, Reference = self.reference), reference = "Reference")
    self.window = Gtk.Window(title = title,
                             transient_for = self.app.mainmenu.window,
                             border_width = 16)
    self.window.connect("delete-event", self.close)
    self.widgets = Container()
    self.polltimer = None
    self.updatethread = threading.Thread(target = self.apply_async)
    self.toolparams = None
    return True

  def close(self, *args, **kwargs):
    """Close tool window."""
    if not self.opened: return
    self.stop_polling(wait = True) # Stop polling.
    if self.get_params() != self.toolparams: self.toolparams = self.run() # Make sure that the last changes have been applied.
    self.app.mainwindow.set_rgb_luminance_callback(None) # Disconnect RGB luminance callback (if any).
    self.window.destroy()
    self.opened = False
    self.app.finalize_tool(self.image, self.operation())
    del self.widgets
    del self.image
    del self.reference

  def apply_cancel_reset_close_buttons(self):
    """Return a Gtk.HButtonBox with Apply/Cancel/Reset/Close buttons
       connected to self.apply, self.cancel, self.reset and self.close methods.
       If self.onethefly is True, the transformations are applied 'on the fly', thus
       the Apply and Reset buttons are not shown."""
    hbox = Gtk.HButtonBox(homogeneous = True, spacing = 16, halign = Gtk.Align.START)
    if not self.onthefly:
      self.widgets.applybutton = Button(label = "Apply")
      self.widgets.applybutton.connect("clicked", self.apply)
      hbox.pack_start(self.widgets.applybutton, False, False, 0)
    self.widgets.cancelbutton = Button(label = "Cancel")
    self.widgets.cancelbutton.connect("clicked", self.cancel)
    self.widgets.cancelbutton.set_sensitive(False)
    hbox.pack_start(self.widgets.cancelbutton, False, False, 0)
    if not self.onthefly:
      self.widgets.resetbutton = Button(label = "Reset")
      self.widgets.resetbutton.connect("clicked", self.reset)
      hbox.pack_start(self.widgets.resetbutton, False, False, 0)
    self.widgets.closebutton = Button(label = "Close")
    self.widgets.closebutton.connect("clicked", self.close)
    hbox.pack_start(self.widgets.closebutton, False, False, 0)
    return hbox

  # Polling for tool parameter changes.

  def start_polling(self, lastparams = None):
    """Start polling for tool parameter changes every self.polltime ms.
       At each poll, get the tool parameters from self.get_params(); then
       call self.apply_async() if the tool parameters are the same *twice* in a
       row, but are different from the self.toolparams registered at the last update.
       lastparams is the assumptive outcome of the last poll (default self.toolparams);
       set to self.get_params() to attempt calling self.apply_async() on the first poll."""
    if self.polltime <= 0: return # No poll time defined.
    self.pollparams = self.toolparams if lastparams is None else lastparams
    self.polltimer = GObject.timeout_add(self.polltime, self.poll)

  def poll(self, *args, **kwargs):
    """Poll for tool parameter changes, and call self.apply_async()
       if the tool parameters are the same *twice* in a row, but are
       different from the self.toolparams registered at the last update."""
    params = self.get_params()
    if params != self.toolparams and params == self.pollparams: self.apply_async()
    self.pollparams = params
    return True

  def stop_polling(self, wait = False):
    """Stop polling for tool parameter changes.
       If 'wait' is True, wait for the current update thread (if any) to finish."""
    if self.polltimer is not None:
      GObject.source_remove(self.polltimer)
      self.polltimer = None
    if wait and self.updatethread.is_alive(): self.updatethread.join() # Wait for the current update thread to finish.

  def resume_polling(self):
    """Resume polling for tool parameter changes."""
    if self.polltimer is not None: return # Already polling.
    self.start_polling()

  def reset_polling(self, lastparams = None):
    """Reset polling for tool parameter changes."""
    if self.polltimer is None: return
    self.stop_polling()
    self.start_polling(lastparams)

  def connect_reset_polling(self, widget, signames):
    """Connect signals 'signames' of widget 'widget' to self.reset_polling(self.get_params()) in
       order to force tool update on next poll. This enhances responsivity to tool parameters changes."""
    widget.connect(signames, lambda *args: self.reset_polling(self.get_params()))

  # Apply/Update tool.

  def run(self):
    """Run tool and return tool parameters.
       Must be defined in each subclass."""
    raise RuntimeError("The run method is not defined in the BaseToolWindow class.")

  def apply(self):
    """Run tool and update main window."""
    self.toolparams = self.run() # Must be defined in each subclass.
    self.transformed = True
    self.app.mainwindow.update_image("Image", self.image)
    self.widgets.cancelbutton.set_sensitive(True)

  def update_gui():
    """Update GUI after asynchronous tool run."""
    self.app.mainwindow.update_image("Image", self.image)
    completed.set()
    return False

  def apply_async(self):
    """Attempt to run tool and update main window in a separate thread in order to keep the GUI responsive.
       Give up if an update thread is already running. Return True if thread successfully started, False otherwise."""

    def update():
      """Tool update wrapper."""
      self.toolparams = self.run() # Must be defined in each subclass.
      self.transformed = True
      completed = threading.Event()
      GObject.idle_add(self.update_gui, priority = GObject.PRIORITY_DEFAULT) # Thread-safe.
      completed.wait()

    if not self.updatethread.is_alive():
      #print("Updating asynchronously...")
      self.app.mainwindow.set_busy()
      self.updatethread = threading.Thread(target = update)
      self.updatethread.setDaemon(True)
      self.updatethread.start()
      self.widgets.cancelbutton.set_sensitive(True)
      return True
    else:
      #print("Update thread already running...")
      return False

  # Cancel tool.

  def cancel(self):
    """Cancel tool."""
    self.stop_polling(wait = True) # Stop polling while restoring original image.
    if not self.transformed: return # Nothing done, actually.
    self.image.copy_from(self.reference)
    self.transformed = False
    self.app.mainwindow.update_image("Image", self.image)
    self.widgets.cancelbutton.set_sensitive(False)
