# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2024.01.14

"""Image picker widget."""

import os
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject
from .gtk.customwidgets import Button
from .gtk.filechoosers import ImageChooserDialog
from .base import ErrorDialog
from ..imageprocessing.imageprocessing import Image

class ImagePicker():
  """Image picker widget class."""

  def __init__(self, app, window, vbox):
    """Add an image picker widget in Gtk.VBox 'vbox' of window 'window' of app 'app'."""
    self.app = app
    self.window = window
    self.nfiles = 0
    self.nimages = 0    
    self.openedtab = False
    self.imagestore = Gtk.ListStore(str, str, GObject.TYPE_PYOBJECT)
    for operation, image, frame in self.app.operations[:-1]:
      self.nimages += 1
      self.imagestore.append([str(self.nimages), operation, image])
    scrolled = Gtk.ScrolledWindow(vexpand = True, hexpand = True)
    scrolled.set_min_content_width(480)
    scrolled.set_min_content_height(200)
    vbox.pack_start(scrolled, True, True, 0)
    treeview = Gtk.TreeView(model = self.imagestore, search_column = -1)
    scrolled.add(treeview)
    renderer = Gtk.CellRendererText()
    renderer.set_property("xalign", 0.)
    column = Gtk.TreeViewColumn("#", renderer, text = 0)
    column.set_alignment(0.)
    column.set_expand(False)
    treeview.append_column(column)
    renderer = Gtk.CellRendererText()
    renderer.set_property("xalign", 0.)
    column = Gtk.TreeViewColumn("Operation", renderer, text = 1)
    column.set_alignment(0.)
    column.set_expand(True)
    treeview.append_column(column)
    self.selection = treeview.get_selection()
    self.selection.set_mode(Gtk.SelectionMode.SINGLE)
    self.selection.connect("changed", lambda selection: self.update())
    hbox = Gtk.HBox(spacing = 8)
    vbox.pack_start(hbox, False, False, 0)
    filebutton = Button(label = "Load file")
    filebutton.connect("clicked", self.load_file)
    hbox.pack_start(filebutton, False, False, 0)

  def load_file(self, *args, **kwargs):
    """Open file dialog and load extra image file."""
    filename = ImageChooserDialog(self.window, Gtk.FileChooserAction.OPEN, preview = True)
    if filename is None: return
    try:
      image = Image()
      image.load(filename)
    except Exception as err:
      ErrorDialog(self.window, str(err))
      return
    basename = os.path.basename(filename)    
    self.nfiles += 1
    if self.nfiles > 1:
      self.imagestore[-1][1] = f"Load('{basename}')"
      self.imagestore[-1][2] = image
    else:
      self.nimages += 1
      self.imagestore.append([str(self.nimages), f"Load('{basename}')", image])      

  def get_selected_image(self):
    """Return selected image."""
    model, list_iter = self.selection.get_selected()
    return model[list_iter][2] if list_iter is not None else None
  
  def update(self):
    """Update main window selection tab."""
    image = self.get_selected_image()
    if image is None: 
      if self.openedtab:
        self.app.mainwindow.delete_image("Selection")
        self.openedtab = False
    if self.openedtab:
      self.app.mainwindow.update_image("Selection", image)
    else:
      self.app.mainwindow.append_image("Selection", image)    
      self.openedtab = True
