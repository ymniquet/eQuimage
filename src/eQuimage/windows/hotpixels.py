# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.0.0 / 2023.10.06

"""Remove hot pixels tool."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .gtk.customwidgets import SpinButton
from .tools import BaseToolWindow
from ..imageprocessing import imageprocessing
from collections import OrderedDict as OD

class RemoveHotPixelsTool(BaseToolWindow):
  """Remove hot pixels tool window class."""

  initratio = 2.

  def open(self, image):
    """Open tool window for image 'image'."""
    if self.opened: return
    if not self.app.mainwindow.opened: return
    super().open(image, "Remove hot pixels")
    vbox = Gtk.VBox(spacing = 16)
    self.window.add(vbox)
    hbox = Gtk.HBox(spacing = 8)
    vbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Channel(s):"), False, False, 0)
    self.widgets.rgbbutton = Gtk.RadioButton.new_with_label_from_widget(None, "RGB")
    hbox.pack_start(self.widgets.rgbbutton, False, False, 0)
    self.widgets.lumbutton = Gtk.RadioButton.new_with_label_from_widget(self.widgets.rgbbutton, "Luminance")
    hbox.pack_start(self.widgets.lumbutton, False, False, 0)
    hbox = Gtk.HBox(spacing = 8)
    vbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Ratio:"), False, False, 0)
    self.widgets.ratiospin = SpinButton(self.initratio, 1., 10., 0.01)
    hbox.pack_start(self.widgets.ratiospin, False, False, 0)
    vbox.pack_start(self.apply_cancel_reset_close_buttons(), False, False, 0)
    self.app.mainwindow.set_images(OD(Image = self.image, Reference = self.reference), reference = "Reference")
    self.resetparams = ("RGB", self.initratio)
    self.window.show_all()

  def reset(self, *args, **kwargs):
    """Reset tool."""
    channels, ratio = self.resetparams
    if channels == "RGB":
      self.widgets.rgbbutton.set_active(True)
    else:
      self.widgets.lumbutton.set_active(True)
    self.widgets.ratiospin.set_value(ratio)

  def apply(self, *args, **kwargs):
    """Apply tool."""
    ratio = self.widgets.ratiospin.get_value()
    if self.widgets.rgbbutton.get_active():
      channels = "RGB"
      self.operation = f"RemoveHotPixels(RGB, ratio = {ratio:.2f})"
    else:
      channels = "L"
      red, green, blue = imageprocessing.get_rgb_luminance()
      self.operation = f"RemoveHotPixels(L({red:.2f}, {green:.2f}, {blue:.2f}), ratio = {ratio:.2f})"
    self.image.copy_from(self.reference)
    print(f"Removing hot pixels on {channels} channel(s)...")
    self.image.remove_hot_pixels(ratio, channels = channels)
    self.app.mainwindow.update_image("Image", self.image)
    self.resetparams = (channels, ratio)
    self.widgets.cancelbutton.set_sensitive(True)

  def cancel(self, *args, **kwargs):
    """Cancel tool."""
    if self.operation is None: return
    self.image.copy_from(self.reference)
    self.app.mainwindow.update_image("Image", self.image)
    self.widgets.ratiospin.set_value(self.initratio)
    self.operation = None
    self.resetparams = ("RGB" if self.widgets.rgbbutton.get_active() else "L", self.initratio)
    self.widgets.cancelbutton.set_sensitive(False)
