# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2024.01.14

"""Base tool window class."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject
from .base import BaseWindow, Container
from .gtk.customwidgets import Button
import threading
from collections import OrderedDict as OD

class BaseToolWindow(BaseWindow):
  """Base tool window class."""

  __action__ = None # Message printed when the tool is applied.

  def __init__(self, app, polltime = -1):
    """Bind window with application 'app'.
       If polltime > 0, run the tool on the fly by polling for
       tool parameters change every 'polltime' ms.
       If polltime <= 0, run the tool on demand when the
       user clicks the "Apply" button."""
    super().__init__(app)
    self.polltime = polltime
    self.onthefly = (polltime > 0)

  def open(self, image, title):
    """Open tool window with title 'title' for image 'image'.
       Return True if successful, False otherwise."""
    if self.opened: return False
    if self.__action__ is not None: print(self.__action__)
    self.opened = True
    self.image = image.clone(meta = {"tag": "Image", "params": None, "description": None, "deletable": False})
    self.image.stats = None # Image statistics.
    self.reference = image.clone(meta = {"tag": "Reference", "deletable": False})
    self.reference.stats = None # Reference image statistics.
    self.app.mainwindow.set_images(OD(Image = self.image, Reference = self.reference), reference = "Reference")
    self.app.mainwindow.set_copy_paste_callbacks(self.copy, self.paste)
    self.window = Gtk.Window(title = title, border_width = 16)
    self.window.connect("delete-event", self.quit)
    self.widgets = Container()
    self.polltimer = None # Polling/update threads data.
    self.updatelock = threading.Lock()
    self.updatethread = threading.Thread(target = None)
    self.toolparams = None # Tool parameters of the last transformation.
    self.transformed = False # True if the image has been transformed.
    self.defaultparams = None # Default tool parameters.
    self.defaultparams_identity = True # True if default tool parameters are the identity operation.
    self.frame = None # New frame if modified by the tool.
    return True

  # Start tool.

  def start(self, identity = True):
    """Start tool.
       Set the present tool parameters (drawn from self.get_params()) as default parameters, show the tool window and start polling
       for tool parameters change.
       If 'identity' is True, the default parameters are the identity operation (no image transformation)."""
    self.defaultparams = self.get_params()
    self.toolparams = self.get_params()
    self.defaultparams_identity = identity
    if not identity:
      if self.onthefly: self.apply(cancellable = False)
    self.window.show_all()
    self.start_polling()

  # Finalize tool.

  def finalize(self, image, operation, frame = None):
    """Finalize tool.
       Close window and return image 'image' (if not None), operation 'operation', and frame 'frame' to the application."""
    self.app.mainwindow.set_copy_paste_callbacks(None, None) # Disconnect Ctrl-C/Ctrl-V callbacks.
    self.app.mainwindow.set_rgb_luminance_callback(None) # Disconnect RGB luminance callback (if any).
    self.app.mainwindow.set_guide_lines(None) # Remove guide lines.
    self.window.destroy()
    self.opened = False
    if image is not None: self.app.finalize_tool(image.set_meta({"tag": "Image"}), operation, frame)
    del self.widgets
    del self.image
    del self.reference
    self.cleanup()

  def destroy(self):
    """Destroy tool (without returning any image and operation to the application)."""
    if not self.opened: return
    self.stop_polling(wait = True) # Stop polling.
    self.finalize(None, None)

  def quit(self, *args, **kwargs):
    """Quit tool (return reference image and operation = None to the application)."""
    if not self.opened: return
    self.stop_polling(wait = True) # Stop polling.
    self.finalize(self.reference, None)

  def close(self, *args, **kwargs):
    """Close tool (return current image, operation and frame to the application)."""
    if not self.opened: return
    if self.stop_polling(wait = True): # Stop polling.
      params = self.get_params()
      if params != self.toolparams: # Make sure that the last changes have been applied.
        toolparams, self.transformed = self.run(params)
        self.image.meta["params"] = toolparams
        self.image.meta["description"] = self.operation(toolparams)
    self.finalize(self.image, self.image.meta["description"] if self.transformed else None, self.frame)

  def cleanup(self):
    """Free memory on exit.
       Must be defined (if needed) in each subclass."""
    return

  # Tool control buttons.

  def tool_control_buttons(self, model = None, reset = True):
    """Return a Gtk HButtonBox with tool control buttons.
       If None, 'model' is set to "ondemand" if self.onthefly is False, and to "onthefly" if self.onthefly is True.
       If 'model' is "ondemand", the transformations are applied on demand and the control buttons are
         Apply, Cancel, Reset and Close
       connected to the self.apply, self.cancel, self.reset and self.close methods.
       If 'model' is "onthefly", the transformations are applied on the fly and the control buttons are
         OK, Reset, and Cancel
       connected to the self.close, self.cancel and self.quit methods.
       The Reset button is not displayed if 'reset' is False."""
    if model is None:
      model = "onthefly" if self.onthefly else "ondemand"
    hbox = Gtk.HButtonBox(homogeneous = True, spacing = 16, halign = Gtk.Align.START)
    if model == "ondemand":
      self.widgets.applybutton = Button(label = "Apply") # Apply transformation on demand.
      self.widgets.applybutton.connect("clicked", self.apply)
      hbox.pack_start(self.widgets.applybutton, False, False, 0)
      self.widgets.cancelbutton = Button(label = "Cancel") # Cancel all transformations (restore the reference image).
      self.widgets.cancelbutton.connect("clicked", self.cancel)
      self.widgets.cancelbutton.set_sensitive(False)
      hbox.pack_start(self.widgets.cancelbutton, False, False, 0)
      self.widgets.resetbutton = Button(label = "Reset") # Cancel last transformation.
      self.widgets.resetbutton.connect("clicked", self.reset)
      if reset: hbox.pack_start(self.widgets.resetbutton, False, False, 0)
      self.widgets.closebutton = Button(label = "Close") # Close tool and return the transformed image to the application.
      self.widgets.closebutton.connect("clicked", self.close)
      hbox.pack_start(self.widgets.closebutton, False, False, 0)
    elif model == "onthefly":
      self.widgets.closebutton = Button(label = "OK") # Close tool and return the transformed image to the application.
      self.widgets.closebutton.connect("clicked", self.close)
      hbox.pack_start(self.widgets.closebutton, False, False, 0)
      self.widgets.cancelbutton = Button(label = "Reset") # Cancel all transformations (restore the reference image).
      self.widgets.cancelbutton.connect("clicked", self.cancel)
      self.widgets.cancelbutton.set_sensitive(False)
      if reset: hbox.pack_start(self.widgets.cancelbutton, False, False, 0)
      self.widgets.quitbutton = Button(label = "Cancel") # Cancel all transformations and close tool (return the reference image to the application).
      self.widgets.quitbutton.connect("clicked", self.quit)
      hbox.pack_start(self.widgets.quitbutton, False, False, 0)
    else:
      raise ValueError("Model must be 'onthefly' or 'ondemand'.")
    return hbox

  # Apply tool.

  def get_params(self):
    """Return tool parameters.
       Must be defined in each subclass."""
    return None

  def set_params(self, params):
    """Set tool parameters 'params'.
       Must be defined in each subclass."""
    return

  def run(self, params):
    """Run tool for parameters 'params'.
       Return (toolparams, transformed), where toolparams are the tool parameters
       actually applied (that might differ from params if the latter are, e.g., out
       of range), and transformed is True if self.image has indeed been transformed
       (with respect to self.reference), False otherwise.
       Must be defined in each subclass."""
    print("Doing nothing !...")
    return None, False

  def update_gui(self):
    """Update main window."""
    if not self.opened: return
    self.app.mainwindow.update_image("Image", self.image)
    self.app.mainwindow.unlock_rgb_luminance()

  def apply(self, *args, **kwargs):
    """Run tool and update main window.
       If the keyword argument 'cancellable' is False (default True), this run can not be cancelled,
       so that the "Cancel" button is not made sensitive."""
    self.app.mainwindow.lock_rgb_luminance()
    params = self.get_params()
    toolparams, self.transformed = self.run(params) # Must be defined in each subclass.
    self.image.meta["params"] = toolparams
    self.image.meta["description"] = self.operation(toolparams)
    self.toolparams = toolparams    
    self.update_gui()
    if self.toolparams != params: self.set_params(self.toolparams)
    cancellable = kwargs["cancellable"] if "cancellable" in kwargs.keys() else True
    if cancellable: self.widgets.cancelbutton.set_sensitive(True)

  def apply_async(self):
    """Attempt to run tool and update main window in a separate thread in order to keep the GUI responsive.
       Give up if an update thread is already running. Return True if thread successfully started, False otherwise."""

    def update(params):
      """Update tool wrapper."""

      def update_gui(completed):
        """Update GUI wrapper."""
        self.update_gui()
        completed.set()
        return False

      with self.updatelock: # Make sure no other thread is running concurrently.
        toolparams, self.transformed = self.run(params) # Must be defined in each subclass.
        self.image.meta["params"] = toolparams
        self.image.meta["description"] = self.operation(toolparams)        
        self.toolparams = params
        completed = threading.Event()
        GObject.idle_add(update_gui, completed, priority = GObject.PRIORITY_DEFAULT) # Thread-safe.
        #completed.wait()

    if not self.updatethread.is_alive():
      #print("Updating asynchronously...")
      self.app.mainwindow.lock_rgb_luminance()
      self.app.mainwindow.set_busy()
      self.updatethread = threading.Thread(target = update, args = (self.get_params(),), daemon = True)
      self.updatethread.start()
      self.widgets.cancelbutton.set_sensitive(True)
      return True
    else:
      #print("Update thread already running...")
      return False

  # Reset/Cancel tool.

  def reset(self, *args, **kwargs):
    """Reset tool parameters."""
    self.set_params(self.toolparams)

  def cancel(self, *args, **kwargs):
    """Cancel tool."""
    self.stop_polling(wait = True) # Stop polling while restoring reference image.
    self.set_params(self.defaultparams)
    if self.onthefly and not self.defaultparams_identity:
      self.apply(cancellable = False)
    else:
      self.image.copy_rgb_from(self.reference)
      self.image.meta["params"] = None
      self.image.meta["description"] = None
      self.toolparams = self.get_params()
      self.transformed = False
      self.update_gui()
    self.widgets.cancelbutton.set_sensitive(False)
    self.resume_polling() # Resume polling.

  # Polling for tool parameter changes.

  def start_polling(self, lastparams = None):
    """Start polling for tool parameter changes every self.polltime ms.
       At each poll, get the tool parameters from self.get_params(); then
       call self.apply_async() if the tool parameters are the same *twice* in a row,
       but are different from the self.toolparams registered at the last update.
       'lastparams' is the assumptive outcome of the last poll (defaults to self.toolparams if None);
       set to self.get_params() to attempt calling self.apply_async() as soon as the first poll.
       Return true if successfully polling, False otherwise (self.polltime < 0)."""
    if self.polltime <= 0: return False # No poll time defined.
    self.pollparams = self.toolparams if lastparams is None else lastparams
    self.polltimer = GObject.timeout_add(self.polltime, self.poll)
    return True

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
       If 'wait' is True, wait for the current update thread (if any) to finish.
       Return True if polling was actually enabled, False otherwise."""
    ispolling = self.polltimer is not None
    if ispolling:
      GObject.source_remove(self.polltimer)
      self.polltimer = None
    if wait and self.updatethread.is_alive(): self.updatethread.join() # Wait for the current update thread to finish.
    return ispolling

  def resume_polling(self):
    """Resume polling for tool parameter changes.
       Return true if successfully polling, False otherwise (self.polltime < 0)."""
    if self.polltimer is not None: return True # Already polling.
    return self.start_polling()

  def reset_polling(self, lastparams = None):
    """Reset polling for tool parameter changes (call stop_polling/start_polling in a row).
       Return true if successfully polling, False otherwise (self.polltime < 0)."""
    if self.polltimer is None: return False
    self.stop_polling()
    return self.start_polling(lastparams)

  def connect_update_request(self, widget, signames):
    """Connect signals 'signames' of widget 'widget' to self.reset_polling(self.get_params()) in
       order to request tool update on next poll. This enhances responsivity to tool parameters changes."""
    widget.connect(signames, lambda *args: self.reset_polling(self.get_params()))

  # Ctrl-C/Ctrl-V callbacks.

  def copy(self, key, image):
    """Copy image 'image' with key 'key' in a new tab."""
    if key != "Image": return # Can only copy the transformed image.
    if image.meta["params"] is None: return
    ncopies = self.app.mainwindow.get_nbr_images()-1
    if ncopies > 10: return # Allow 10 copies max.
    clone = image.clone()
    clone.meta["tag"] = f"#{ncopies}"
    clone.meta["deletable"] = True
    self.app.mainwindow.append_image(f"Copy #{ncopies}", clone)

  def paste(self, key, image):
    """Paste the parameters of the image 'image' with key 'key' to the tool."""
    if key[0:4] != "Copy": return # Can only paste the parameters from the copies.
    params = image.meta["params"]
    self.stop_polling(wait = True) # Stop polling while restoring parameters.
    self.set_params(params)
    self.start_polling(params) # Resume polling.
