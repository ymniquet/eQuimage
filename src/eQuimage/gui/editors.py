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
from .gtk.customwidgets import HButtonBox, Button, RadioButtons, Entry
from .base import BaseWindow, Container, InfoDialog, ErrorDialog
import os
import tempfile
import threading
import subprocess

class EditTool(BaseWindow):
  """External editor class."""

  def __init__(self, app, editor, command, filename, depth = 32):
    """Initialize editor for app 'app'.
        - 'editor' is the name of the editor (SIRIL, GIMP, ...).
        - 'command' is the command to be run (e.g., ["gimp", "-n", "$"]). "$" is replaced by the image file to be opened by the editor.
        - 'filename' is the image file to be opened by the editor, created in a temporary directory.
        - 'depth' is the default color depth of this file."""
    super().__init__(app)
    self.editor = editor
    self.command = command
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
    self.widgets.depthbuttons = None
    self.widgets.editbutton = None
    return self.window, self.widgets

  def close_window(self, *args, **kwargs):
    """Close tool window."""
    self.window.destroy()
    self.opened = False
    del self.widgets

  def depth_buttons(self):
    """Add depth buttons to the tool window.
       Return a RadioButtons object, which must be packed appropriately in the tool window."""
    self.widgets.depthbuttons = RadioButtons((8, "8 bits"), (16, "16 bits"), (32, "32 bits"))
    self.widgets.depthbuttons.set_selected(self.depth)
    return self.widgets.depthbuttons

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
    """Run editor."""

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
        with tempfile.TemporaryDirectory() as tmpdir:
          tmpfile = os.path.join(tmpdir, self.filename)
          # Save image.
          image = self.app.get_image()
          if self.widgets.depthbuttons is not None:
            depth = self.widgets.depthbuttons.get_selected()
          else:
            depth = self.depth
          image.save(tmpfile, depth = depth)
          ctime = os.path.getmtime(tmpfile)
          # Run editor.
          print(f"Editing with {self.editor}...")
          subprocess.run([item if item != "$" else tmpfile for item in self.command])
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
