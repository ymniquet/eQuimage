# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2024.01.05

"""Remove hot pixels tool."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
from .gtk.customwidgets import RadioButton, SpinButton
from .tools import BaseToolWindow
from ..imageprocessing import imageprocessing

class RemoveHotPixelsTool(BaseToolWindow):
  """Remove hot pixels tool window class."""

  __action__ = "Removing hot pixels..."

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Remove hot pixels"): return False
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
    self.widgets.ratiospin = SpinButton(2., 1., 10., 0.01)
    hbox.pack_start(self.widgets.ratiospin, False, False, 0)
    wbox.pack_start(self.tool_control_buttons(reset = not self.onthefly), False, False, 0)
    self.defaultparams = self.get_params()
    self.toolparams = self.defaultparams
    if self.onthefly:
      self.apply(cancellable = False)
      self.connect_update_request(self.widgets.rgbbutton, "toggled")
      self.connect_update_request(self.widgets.ratiospin, "value-changed")
    self.window.show_all()
    self.start_polling()
    return True

  def get_params(self):
    """Return tool parameters."""
    return "RGB" if self.widgets.rgbbutton.get_active() else "L", self.widgets.ratiospin.get_value(), imageprocessing.get_rgb_luminance()

  def set_params(self, params):
    """Set tool parameters 'params'."""
    channels, ratio, rgblum = params
    if channels == "RGB":
      self.widgets.rgbbutton.set_active(True)
    else:
      self.widgets.lumbutton.set_active(True)
    self.widgets.ratiospin.set_value(ratio)

  def run(self, params):
    """Run tool for parameters 'params'."""
    channels, ratio, rgblum = params
    self.image.copy_from(self.reference)
    self.image.remove_hot_pixels(ratio, channels = channels)
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    channels, ratio, rgblum = params
    if channels == "RGB":
      return f"RemoveHotPixels(RGB, ratio = {ratio:.2f})"
    else:
      return f"RemoveHotPixels(L({rgblum[0]:.2f}, {rgblum[1]:.2f}, {rgblum[2]:.2f}), ratio = {ratio:.2f})"
