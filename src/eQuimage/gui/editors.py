# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.6.1 / 2024.09.01
# GUI updated.

"""Edition with external tools."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject
from .gtk.customwidgets import Label, VBox, HButtonBox, Button, RadioButtons, Entry
from .base import BaseWindow, Container, InfoDialog, ErrorDialog
import os
import tempfile
import threading
import subprocess

class EditTool(BaseWindow):
  """External editor class."""

  def __init__(self, app, command = None, filename = "eQuimage.tiff", depth = 32):
    """Initialize external editor for app 'app'.
        - 'command' is the command to be run (e.g., "gimp -n $"). "$" is replaced by the name of the image file to be opened by the editor.
        - 'filename' is the name of the image file to be opened by the editor, created in a temporary directory.
        - 'depth' is the default color depth of this file."""
    super().__init__(app)
    self.set_command(command)
    self.set_filename(filename, depth)

  def set_command(self, command):
    """(Re)Set editor command 'command'."""
    self.command = command

  def set_filename(self, filename, depth = 32):
    """(Re)Set image file name 'filename' and color depth 'depth'."""
    self.filename = filename
    self.set_depth(depth)

  def set_depth(self, depth):
    """(Re)Set image file color depth 'depth'."""
    self.depth = depth

  def open_window(self, title = "Edit with..."):
    """Open a modal Gtk window with title 'title'. This window must remain open while running the editor.
       Return window and widgets container."""
    self.opened = True
    self.window = Gtk.Window(title = title,
                             transient_for = self.app.mainwindow.window,
                             modal = True,
                             border_width = 16)
    self.window.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
    self.window.connect("delete-event", self.close_window)
    self.widgets = Container()
    self.widgets.commententry = None
    self.widgets.editbutton = None
    return self.window, self.widgets

  def close_window(self, *args, **kwargs):
    """Close tool window."""
    self.window.destroy()
    self.opened = False
    del self.widgets

  def comment_entry(self):
    """Add a comment entry to the tool widgets.
       Return an Entry object, which must be packed appropriately in the tool window."""
    self.widgets.commententry = Entry(text = "", width = 64)
    return self.widgets.commententry

  def edit_cancel_buttons(self):
    """Add edit & cancel buttons to the tool widgets.
       Return a HButtonBox object, which must be packed appropriately in the tool window."""
    hbox = HButtonBox()
    self.widgets.editbutton = Button(label = "Edit")
    self.widgets.editbutton.connect("clicked", lambda button: self.edit())
    hbox.pack(self.widgets.editbutton)
    self.widgets.cancelbutton = Button(label = "Cancel")
    self.widgets.cancelbutton.connect("clicked", lambda button: self.close_window())
    hbox.pack(self.widgets.cancelbutton)
    return hbox

  def edit(self):
    """Run editor on current image."""

    def run():
      """Run editor in a separate thread."""

      def finalize(image, msg = None, error = False):
        """Finalize run (register image 'image', close window and open info/error dialog with message 'msg')."""
        if image is not None:
          if self.widgets.commententry is not None:
            comment = self.widgets.commententry.get_text().strip()
            if len(comment) > 0: comment = " # "+comment
          else:
            comment = ""
          self.app.finalize_tool(image, f"Edit('{editor}'){comment}")
        self.close_window()
        if msg is not None:
          Dialog = ErrorDialog if error else InfoDialog
          Dialog(self.app.mainwindow.window, str(msg))
        return False

      try:
        with tempfile.TemporaryDirectory() as tmpdir:
          # Set tmp file name.
          tmpfile = os.path.join(tmpdir, self.filename)
          # Process command.
          command = self.command.strip() if self.command is not None else ""
          if command == "": raise RuntimeError("Please specify editor command.")
          file_found = False
          split_command = []
          for item in command.split(" "):
            if item == "$":
              file_found = True
              split_command.append(tmpfile)
            else:
              split_command.append(item)
          if not file_found: raise RuntimeError("No place holder for the image file name ($) in the editor command.")
          editor = os.path.basename(split_command[0])
          # Save image.
          image = self.app.get_image()
          image.save(tmpfile, depth = self.depth)
          ctime = os.path.getmtime(tmpfile)
          # Run editor.
          print(f"Editing with {editor}...")
          subprocess.run(split_command)
          if self.opened: # Cancel operation if the window has been closed in the meantime.
            # Check if the image has been modified by the editor.
            mtime = os.path.getmtime(tmpfile)
            if mtime != ctime: # If so, load and register the new one...
              print(f"The file {tmpfile} has been modified by {editor}; Reloading in eQuimage...")
              image = self.app.ImageClass()
              image.load(tmpfile)
              if not image.is_valid(): raise RuntimeError(f"The image returned by {editor} is invalid.")
              GObject.idle_add(finalize, image, None, False)
            else: # Otherwise, open info dialog and cancel operation.
              print(f"The file {tmpfile} has not been modified by {editor}; Cancelling operation...")
              GObject.idle_add(finalize, None, f"The image has not been modified by {editor}.\nCancelling operation.", False)
      except Exception as err:
        GObject.idle_add(finalize, None, err, True)

    if self.widgets.editbutton is not None:
      self.widgets.editbutton.set_sensitive(False) # Can only be run once.
    thread = threading.Thread(target = run, daemon = False)
    thread.start()

#
# Applications: siril, gimp, etc...
#

def edit_with_siril(app):
  """Edit current image of app 'app' with siril."""
  if not app.get_context("image"): return
  editor = EditTool(app, "siril $", "eQuimage.fits", depth = 32)
  window, widgets = editor.open_window(title = "Edit with siril")
  wbox = VBox()
  window.add(wbox)
  wbox.pack(Label("The image will be saved as a 32 bits float FITS file and edited with siril."))
  wbox.pack(Label("Overwrite the file when leaving siril."))
  wbox.pack(Label("You can enter a comment for the logs below, <b>before</b> closing siril:"))
  wbox.pack(editor.comment_entry().hbox())
  wbox.pack(Label("<b>The operation will be cancelled if you close this window !</b>"))
  wbox.pack(editor.edit_cancel_buttons())
  window.show_all()

def edit_with_gimp(app):
  """Edit current image of app 'app' with gimp."""

  class GimpEditTool(EditTool):
    """Gimp editor subclass."""

    def edit(self):
      """Update image color depth and run gimp on current image."""
      depth = self.widgets.depthbuttons.get_selected()
      self.set_depth(depth)
      super().edit()

  if not app.get_context("image"): return
  editor = GimpEditTool(app, "gimp -n $", "eQuimage.tiff")
  window, widgets = editor.open_window(title = "Edit with gimp")
  wbox = VBox()
  window.add(wbox)
  wbox.pack(Label("The image will be saved as a TIFF file with color depth:"))
  widgets.depthbuttons = RadioButtons((8, "8 bits"), (16, "16 bits"), (32, "32 bits"))
  widgets.depthbuttons.set_selected(32)
  wbox.pack(widgets.depthbuttons.hbox(append = " per channel."))
  wbox.pack(Label("and edited with gimp."))
  wbox.pack(Label("Overwrite the file when leaving gimp."))
  wbox.pack(Label("You can enter a comment for the logs below, <b>before</b> closing gimp:"))
  wbox.pack(editor.comment_entry().hbox())
  wbox.pack(Label("<b>The operation will be cancelled if you close this window !</b>"))
  wbox.pack(editor.edit_cancel_buttons())
  window.show_all()

def edit_with_any(app):
  """Edit current image of app 'app' with any editor."""

  class AnyEditTool(EditTool):
    """Any editor subclass."""

    def edit(self):
      """Update command, image file name & color depth and run editor on current image."""
      command = self.widgets.commandentry.get_text()
      self.set_command(command)
      suffix, depth = self.widgets.filebuttons.get_selected()
      self.set_filename("eQuimage."+suffix, depth)
      super().edit()

  if not app.get_context("image"): return
  editor = AnyEditTool(app)
  window, widgets = editor.open_window(title = "Edit with...")
  wbox = VBox()
  window.add(wbox)
  wbox.pack(Label("The image will be saved as a:"))
  widgets.filebuttons = RadioButtons((("tiff", 8), "8 bits TIFF"), (("tiff", 16), "16 bits TIFF"), (("tiff", 32), "32 bits TIFF"), (("fits", 32), "32 bits float FITS"))
  widgets.filebuttons.set_selected(("tiff", 32))
  wbox.pack(widgets.filebuttons.hbox())
  wbox.pack(Label("file and edited with (type command below and use \"$\" as a place holder\nfor the image file name):"))
  widgets.commandentry = Entry(text = "gimp -n $", width = 64)
  wbox.pack(widgets.commandentry.hbox())
  wbox.pack(Label("Overwrite the file when leaving the editor."))
  wbox.pack(Label("You can enter a comment for the logs below, <b>before</b> closing the editor:"))
  wbox.pack(editor.comment_entry().hbox())
  wbox.pack(Label("<b>The operation will be cancelled if you close this window !</b>"))
  wbox.pack(editor.edit_cancel_buttons())
  window.show_all()
