# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2023.11.27

"""Custom Gtk file choosers."""

import os
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf

def ImageChooserDialog(window, action, path = None, preview = False):
  """Open file chooser dialog for an image, from window 'window' and for
     action 'action' (either Gtk.FileChooserAction.OPEN to open an image
     or Gtk.FileChooserAction.SAVE to save an image). Start with directory
     and file name 'path', and preview selected image if 'preview' is True.
     Return chosen file name or None if cancelled."""

  def update_preview(dialog):
    """Update preview."""
    filename = dialog.get_preview_filename()
    try:
      pixbuf = GdkPixbuf.Pixbuf.new_from_file(filename)
    except:
      dialog.set_preview_widget_active(False)
    else:
      maxwidth, maxheight = 360, 720 # Scale image.
      width, height = pixbuf.get_width(), pixbuf.get_height()
      scale = min(maxwidth/width, maxheight/height)
      if scale < 1:
        width, height = int(width*scale), int(height*scale)
        pixbuf = pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)
        preview_image.set_from_pixbuf(pixbuf)
        dialog.set_preview_widget_active(True)

  if action == Gtk.FileChooserAction.OPEN:
    title = "Open"
    button = Gtk.STOCK_OPEN
  elif action == Gtk.FileChooserAction.SAVE:
    title = "Save as"
    button = Gtk.STOCK_SAVE
  else:
    raise ValueError("action must be Gtk.FileChooserAction.OPEN or Gtk.FileChooserAction.SAVE.")
  dialog = Gtk.FileChooserDialog(title = title, transient_for = window, action = action)
  dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                     button, Gtk.ResponseType.OK)
  if preview and action == Gtk.FileChooserAction.OPEN:
    preview_image = Gtk.Image()
    dialog.set_preview_widget(preview_image)
    dialog.connect("update-preview", update_preview)
  if path is not None:
    dialog.set_current_name(os.path.basename(path))
    if action == Gtk.FileChooserAction.SAVE: dialog.set_filename(path)
  response = dialog.run()
  filename = dialog.get_filename()
  dialog.destroy()
  return filename if response == Gtk.ResponseType.OK else None
