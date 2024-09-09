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

  def __init__(self, app, editor, command, filename, depth = 32):
    """Initialize external editor for app 'app'.
        - 'editor' is the name of the editor (SIRIL, GIMP, ...).
        - 'command' is the command to be run (e.g., "gimp -n $"]). "$" is replaced by the name of the image file to be opened by the editor.
        - 'filename' is the name of the image file to be opened by the editor, created in a temporary directory.
        - 'depth' is the default color depth of this file."""
    super().__init__(app)
    self.editor = editor
    self.set_command(command)
    self.set_filename(filename, depth)

  def set_command(self, command):
    """(Re)Set editor command 'command'."""
    self.command = command.strip()

  def set_filename(self, filename, depth = 32):
    """(Re)Set image file name 'filename' and color depth 'depth'."""
    self.filename = filename
    self.depth = depth

  def open_window(self):
    """Open a modal Gtk window that must remain open while running the editor.
       Return window and widgets container."""
    self.opened = True
    self.window = Gtk.Window(title = f"Edit with {self.editor}",
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
    """Add a comment entry to the tool window.
       Return an Entry object, which must be packed appropriately in the tool window."""
    self.widgets.commententry = Entry(text = "", width = 64)
    return self.widgets.commententry

  def edit_cancel_buttons(self):
    """Add edit & cancel buttons to the tool window.
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
          self.app.finalize_tool(image, f"Edit('{self.editor}'){comment}")
        self.close_window()
        if msg is not None:
          Dialog = ErrorDialog if error else InfoDialog
          Dialog(self.app.mainwindow.window, str(msg))
        return False

      try:
        if self.command == "": raise RuntimeError("Please specify editor command.")
        with tempfile.TemporaryDirectory() as tmpdir:
          tmpfile = os.path.join(tmpdir, self.filename)
          # Save image.
          image = self.app.get_image()
          image.save(tmpfile, depth = self.depth)
          ctime = os.path.getmtime(tmpfile)
          # Run editor.
          print(f"Editing with {self.editor}...")
          subprocess.run([item if item != "$" else tmpfile for item in self.command.split(" ")])
          if self.opened: # Cancel operation if the window has been closed in the meantime.
            # Check if the image has been modified by the editor.
            mtime = os.path.getmtime(tmpfile)
            if mtime != ctime: # If so, load and register the new one...
              print(f"The file {tmpfile} has been modified by {self.editor}; Reloading in eQuimage...")
              image = self.app.ImageClass()
              image.load(tmpfile)
              if not image.is_valid(): raise RuntimeError(f"The image returned by {self.editor} is invalid.")
              GObject.idle_add(finalize, image, None, False)
            else: # Otherwise, open info dialog and cancel operation.
              print(f"The file {tmpfile} has not been modified by {self.editor}; Cancelling operation...")
              GObject.idle_add(finalize, None, f"The image has not been modified by {self.editor}.\nCancelling operation.", False)
      except Exception as err:
        GObject.idle_add(finalize, None, err, True)

    if self.widgets.editbutton is not None:
      self.widgets.editbutton.set_sensitive(False) # Can only be run once.
    thread = threading.Thread(target = run, daemon = False)
    thread.start()

#
# Applications: SIRIL, GIMP, etc...
#

def edit_with_siril(app):
  """Edit current image of app 'app' with SIRIL."""
  if not app.get_context("image"): return
  editor = EditTool(app, "SIRIL", "siril $", "eQuimage.fits", depth = 32)
  window, widgets = editor.open_window()
  wbox = VBox()
  window.add(wbox)
  wbox.pack(Label("The image will be saved as a 32 bits float FITS file and edited with SIRIL."))
  wbox.pack(Label("Overwrite the file when leaving SIRIL."))
  wbox.pack(Label("You can enter a comment for the logs below, <b>before</b> closing SIRIL:"))
  wbox.pack(editor.comment_entry().hbox())
  wbox.pack(Label("<b>The operation will be cancelled if you close this window !</b>"))
  wbox.pack(editor.edit_cancel_buttons())
  window.show_all()

def edit_with_gimp(app):
  """Edit current image of app 'app' with GIMP."""
  if not app.get_context("image"): return
  editor = EditTool(app, "GIMP", "gimp -n $", "eQuimage.tiff", depth = 32)
  window, widgets = editor.open_window()
  wbox = VBox()
  window.add(wbox)
  wbox.pack(Label("The image will be saved as a TIFF file with color depth:"))
  widgets.depthbuttons = RadioButtons((8, "8 bits"), (16, "16 bits"), (32, "32 bits"))
  widgets.depthbuttons.set_selected(32)
  widgets.depthbuttons.connect("toggled", lambda button: editor.set_filename("eQuimage.tiff", widgets.depthbuttons.get_selected()))
  wbox.pack(widgets.depthbuttons.hbox(append = " per channel."))
  wbox.pack(Label("and edited with GIMP."))
  wbox.pack(Label("Overwrite the file when leaving GIMP."))
  wbox.pack(Label("You can enter a comment for the logs below, <b>before</b> closing GIMP:"))
  wbox.pack(editor.comment_entry().hbox())
  wbox.pack(Label("<b>The operation will be cancelled if you close this window !</b>"))
  wbox.pack(editor.edit_cancel_buttons())
  window.show_all()

def edit_with_x(app):
  """Edit current image of app 'app' with an arbitrary editor."""
  if not app.get_context("image"): return
  editor = EditTool(app, "[editor]", "gimp -n $", "eQuimage.tiff", depth = 32)
  window, widgets = editor.open_window()
  wbox = VBox()
  window.add(wbox)
  wbox.pack(Label("The image will be saved as:"))
  widgets.filebuttons = RadioButtons(((8, "tiff"), "8 bits TIFF"), ((16, "tiff"), "16 bits TIFF"), ((32, "tiff"), "32 bits TIFF"), ((32, "fits"), "32 bits float FITS"))
  widgets.filebuttons.set_selected((32, "tiff"))
  widgets.filebuttons.connect("toggled", lambda button: editor.set_filename("eQuimage."+widgets.filebuttons.get_selected()[1], widgets.filebuttons.get_selected()[0]))
  wbox.pack(widgets.filebuttons.hbox())
  wbox.pack(Label("and edited with [editor] (type command below and use \"$\" as a place holder\nfor the image file name):"))
  widgets.commandentry = Entry(text = "gimp -n $", width = 64)
  widgets.commandentry.connect("changed", lambda entry: editor.set_command(entry.get_text()))
  wbox.pack(widgets.commandentry.hbox())
  wbox.pack(Label("Overwrite the file when leaving [editor]."))
  wbox.pack(Label("You can enter a comment for the logs below, <b>before</b> closing [editor]:"))
  wbox.pack(editor.comment_entry().hbox())
  wbox.pack(Label("<b>The operation will be cancelled if you close this window !</b>"))
  wbox.pack(editor.edit_cancel_buttons())
  window.show_all()
