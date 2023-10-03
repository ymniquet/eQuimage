# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 2023.09 *

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
from .gtk.customwidgets import RadioButton, SpinButton
from .tools import BaseToolWindow
from ..imageprocessing import imageprocessing
from collections import OrderedDict as OD

"""Remove hot pixels tool."""

class RemoveHotPixelsTool(BaseToolWindow):
  """Remove hot pixels tool window class."""

  INITRATIO = 2.

  def open(self, image):
    """Open tool window for image 'image'."""
    if self.opened: return
    if not self.app.mainwindow.opened: return
    super().open(image, "Remove hot pixels")
    wbox = Gtk.VBox(spacing = 16)
    self.window.add(wbox)
    hbox = Gtk.HBox(spacing = 8)
    wbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Channel(s):"), False, False, 0)
    self.widgets.rgbbutton = RadioButton.new_with_label_from_widget(None, "RGB")
    hbox.pack_start(self.widgets.rgbbutton, False, False, 0)
    self.widgets.lumbutton = RadioButton.new_with_label_from_widget(self.widgets.rgbbutton, "Luminance")
    hbox.pack_start(self.widgets.lumbutton, False, False, 0)
    hbox = Gtk.HBox(spacing = 8)
    wbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Ratio:"), False, False, 0)
    self.widgets.ratiospin = SpinButton(self.INITRATIO, 1., 10., 0.01)
    hbox.pack_start(self.widgets.ratiospin, False, False, 0)
    wbox.pack_start(self.apply_cancel_reset_close_buttons(onthefly = self.app.hotpixlotf), False, False, 0)
    self.app.mainwindow.set_images(OD(Image = self.image, Reference = self.reference), reference = "Reference")
    self.toolparams = self.get_params()
    if self.app.hotpixlotf:
      self.update()
      self.connect_reset_polling(self.widgets.rgbbutton, "toggled")
      self.connect_reset_polling(self.widgets.ratiospin, "value-changed")
      self.start_polling(self.app.polltime)
    self.window.show_all()

  def get_params(self):
    """Return tool parameters."""
    return "RGB" if self.widgets.rgbbutton.get_active() else "L", self.widgets.ratiospin.get_value(), imageprocessing.get_rgb_luminance()

  def reset(self, *args, **kwargs):
    """Reset tool parameters."""
    channels, ratio, rgblum = self.toolparams
    if channels == "RGB":
      self.widgets.rgbbutton.set_active(True)
    else:
      self.widgets.lumbutton.set_active(True)
    self.widgets.ratiospin.set_value(ratio)

  def update(self, *args, **kwargs):
    """Apply tool on the fly."""
    channels, ratio, rgblum = self.get_params()
    self.image.copy_from(self.reference)
    self.image.remove_hot_pixels(ratio, channels = channels)
    self.app.mainwindow.update_image("Image", self.image)
    self.transformed = True
    self.toolparams = (channels, ratio, rgblum)
    self.widgets.cancelbutton.set_sensitive(True)

  def apply(self, *args, **kwargs):
    """Apply tool."""
    channels, ratio, rgblum = self.get_params()
    print(f"Removing hot pixels on {channels} channel(s)...")
    self.update()

  def operation(self):
    """Return tool operation string."""
    if not self.transformed: return None
    channels, ratio, rgblum = self.toolparams
    if channels == "RGB":
      return f"RemoveHotPixels(RGB, ratio = {ratio:.2f})"
    else:
      return f"RemoveHotPixels(L({rgblum[0]:.2f}, {rgblum[1]:.2f}, {rgblum[2]:.2f}), ratio = {ratio:.2f})"

  def cancel(self, *args, **kwargs):
    """Cancel tool."""
    if not self.transformed: return
    self.stop_polling() # Stop polling while restoring original image and tool params.
    self.image.copy_from(self.reference)
    self.app.mainwindow.update_image("Image", self.image)
    self.transformed = False
    if self.app.hotpixlotf:
      self.close()
      return
    self.widgets.ratiospin.set_value(self.INITRATIO)
    self.toolparams = ("RGB" if self.widgets.rgbbutton.get_active() else "L", self.INITRATIO, imageprocessing.get_rgb_luminance())
    self.widgets.cancelbutton.set_sensitive(False)
