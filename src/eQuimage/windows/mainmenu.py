# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.1.0 / 2023.10.06

"""Main menu."""

import os
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .base import BaseWindow, ErrorDialog
from .settings import SettingsWindow
from .hotpixels import RemoveHotPixelsTool
from .colorbalance import ColorBalanceTool
from .stretch import StretchTool

class MainMenu(BaseWindow):
  """Main menu class."""

  def open(self):
    """Open main menu window."""
    if self.opened: return
    self.opened = True
    self.window = Gtk.ApplicationWindow(application = self.app, title = "eQuimage", border_width = 8)
    self.window.connect("delete-event", self.close)
    wbox = Gtk.VBox(spacing = 8)
    self.window.add(wbox)
    frame = Gtk.Frame(label = " File & App management ")
    frame.set_label_align(0.025, 0.5)
    wbox.pack_start(frame, False, False, 0)
    vbox = Gtk.VBox(homogeneous = True, margin = 8)
    frame.add(vbox)
    self.buttons = {}
    self.buttons["Open"] = Gtk.Button(label = "Open")
    self.buttons["Open"].context = {"noimage": True, "nooperations": True, "activetool": False, "noframe": True}
    self.buttons["Open"].connect("clicked", self.load_file)
    vbox.pack_start(self.buttons["Open"], False, False, 0)
    self.buttons["Save"] = Gtk.Button(label = "Save")
    self.buttons["Save"].context = {"noimage": False, "nooperations": False, "activetool": False, "noframe": True}
    self.buttons["Save"].connect("clicked", self.save_file)
    vbox.pack_start(self.buttons["Save"], False, False, 0)
    self.buttons["Close"] = Gtk.Button(label = "Close")
    self.buttons["Close"].context = {"noimage": False, "nooperations": True, "activetool": True, "noframe": True}
    self.buttons["Close"].connect("clicked", lambda button: self.app.clear())
    vbox.pack_start(self.buttons["Close"], False, False, 0)
    self.buttons["Quit"] = Gtk.Button(label = "Quit")
    self.buttons["Quit"].context = {"noimage": True, "nooperations": True, "activetool": True, "noframe": True}
    self.buttons["Quit"].connect("clicked", self.close)
    vbox.pack_start(self.buttons["Quit"], False, False, 0)
    self.buttons["Settings"] = Gtk.Button(label = "Settings")
    self.buttons["Settings"].context = {"noimage": True, "nooperations": True, "activetool": False, "noframe": True}
    self.buttons["Settings"].connect("clicked", lambda button: SettingsWindow(self.app).open())
    vbox.pack_start(self.buttons["Settings"], False, False, 0)
    frame = Gtk.Frame(label = " Image transformations ")
    frame.set_label_align(0.025, 0.5)
    wbox.pack_start(frame, False, False, 0)
    vbox = Gtk.VBox(homogeneous = True, margin = 8)
    frame.add(vbox)
    self.buttons["Hotpixels"] = Gtk.Button(label = "Remove hot pixels")
    self.buttons["Hotpixels"].context = {"noimage": False, "nooperations": True, "activetool": False, "noframe": True}
    self.buttons["Hotpixels"].connect("clicked", lambda button: self.app.run_tool(RemoveHotPixelsTool, self.app.hotpixlotf))
    vbox.pack_start(self.buttons["Hotpixels"], False, False, 0)
    self.buttons["Sharpen"] = Gtk.Button(label = "Sharpen")
    self.buttons["Sharpen"].context = {"noimage": False, "nooperations": True, "activetool": False, "noframe": True}
    self.buttons["Sharpen"].connect("clicked", lambda button: self.app.sharpen())
    vbox.pack_start(self.buttons["Sharpen"], False, False, 0)
    self.buttons["Colors"] = Gtk.Button(label = "Balance colors")
    self.buttons["Colors"].context = {"noimage": False, "nooperations": True, "activetool": False, "noframe": True}
    self.buttons["Colors"].connect("clicked", lambda button: self.app.run_tool(ColorBalanceTool, self.app.colorblotf))
    vbox.pack_start(self.buttons["Colors"], False, False, 0)
    self.buttons["Stretch"] = Gtk.Button(label = "Stretch (Shadow/Midtone/Highlight)")
    self.buttons["Stretch"].context = {"noimage": False, "nooperations": True, "activetool": False, "noframe": True}
    self.buttons["Stretch"].connect("clicked", lambda button: self.app.run_tool(StretchTool, self.app.stretchotf))
    vbox.pack_start(self.buttons["Stretch"], False, False, 0)
    self.buttons["Grayscale"] = Gtk.Button(label = "Convert to gray scale")
    self.buttons["Grayscale"].context = {"noimage": False, "nooperations": True, "activetool": False, "noframe": True}
    self.buttons["Grayscale"].connect("clicked", lambda button: self.app.gray_scale())
    vbox.pack_start(self.buttons["Grayscale"], False, False, 0)
    self.buttons["Cancel"] = Gtk.Button(label = "Cancel last operation")
    self.buttons["Cancel"].context = {"noimage": False, "nooperations": False, "activetool": False, "noframe": True}
    self.buttons["Cancel"].connect("clicked", lambda button: self.app.cancel_last_operation())
    vbox.pack_start(self.buttons["Cancel"], False, False, 0)
    self.buttons["Logs"] = Gtk.Button(label = "View logs")
    self.buttons["Logs"].context = {"noimage": False, "nooperations": True, "activetool": True, "noframe": True}
    self.buttons["Logs"].connect("clicked", lambda button: self.app.logwindow.open())
    vbox.pack_start(self.buttons["Logs"], False, False, 0)
    frame = Gtk.Frame(label = " Unistellar frame ")
    frame.set_label_align(0.025, 0.5)
    wbox.pack_start(frame, False, False, 0)
    hbbox = Gtk.HBox(margin = 8, spacing = 8, homogeneous = True)
    frame.add(hbbox)
    self.buttons["Removeframe"] = Gtk.Button(label = "Remove frame")
    self.buttons["Removeframe"].context = {"noimage": False, "nooperations": True, "activetool": False, "noframe": False}
    self.buttons["Removeframe"].connect("clicked", lambda button: self.app.remove_unistellar_frame())
    hbbox.pack_start(self.buttons["Removeframe"], True, True, 0)
    self.buttons["Restoreframe"] = Gtk.Button(label = "Restore frame")
    self.buttons["Restoreframe"].context = {"noimage": False, "nooperations": True, "activetool": False, "noframe": False}
    self.buttons["Restoreframe"].connect("clicked", lambda button: self.app.restore_unistellar_frame())
    hbbox.pack_start(self.buttons["Restoreframe"], True, True, 0)
    self.window.show_all()
    self.update()

  def close(self, *args, **kwargs):
    """Close main menu window (force if kwargs["force"] = True)."""
    if not self.opened: return None
    force = kwargs["force"] if "force" in kwargs.keys() else False
    if not force:
      dialog = Gtk.MessageDialog(transient_for = self.window,
                                 message_type = Gtk.MessageType.QUESTION,
                                 buttons = Gtk.ButtonsType.OK_CANCEL,
                                 modal = True)
      dialog.set_markup("Are you sure you want to quit ?")
      response = dialog.run()
      dialog.destroy()
      if response != Gtk.ResponseType.OK: return True
    print("Exiting eQuimage...")
    self.app.quit()

  def update(self, present = True):
    """Update main menu window (and present if 'present' is True)."""
    if not self.opened: return
    context = self.app.get_context()
    for button in self.buttons.values():
      if not context["image"]:
        sensitive = button.context["noimage"]
      elif context["activetool"]:
        sensitive = button.context["activetool"]
      else:
        sensitive = True
      if not context["frame"]:
        sensitive = sensitive and button.context["noframe"]
      if not context["operations"]:
        sensitive = sensitive and button.context["nooperations"]
      button.set_sensitive(sensitive)
    if present: self.window.present()

  def load_file(self, *args, **kwargs):
    """Open file dialog and load image file."""
    if not self.opened: return
    dialog = Gtk.FileChooserDialog(title = "Open",
                                   transient_for = self.window,
                                   action = Gtk.FileChooserAction.OPEN)
    dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                       Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
    response = dialog.run()
    filename = dialog.get_filename()
    dialog.destroy()
    if response != Gtk.ResponseType.OK: return
    try:
      self.app.load_file(filename)
    except Exception as err:
      ErrorDialog(self.window, str(err))
      self.app.clear()

  def save_file(self, *args, **kwargs):
    """Open file dialog and save image file."""
    if not self.opened: return
    if not self.app.get_context("image"): return
    dialog = Gtk.FileChooserDialog(title = "Save as",
                                   transient_for = self.window,
                                   action = Gtk.FileChooserAction.SAVE)
    dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                       Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
    filename = self.app.get_savename()
    dialog.set_filename(filename)
    dialog.set_current_name(os.path.basename(filename))
    response = dialog.run()
    filename = dialog.get_filename()
    dialog.destroy()
    if response != Gtk.ResponseType.OK: return
    try:
      self.app.save_file(filename)
    except Exception as err:
      ErrorDialog(self.window, str(err))
