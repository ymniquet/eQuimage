# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.3.0 / 2024.02.17

"""Unsharp mask tool."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
from .gtk.customwidgets import RadioButton, HScaleSpinButton
from .tools import BaseToolWindow
from ..imageprocessing import imageprocessing
from skimage.filters import unsharp_mask
import numpy as np

class UnsharpMaskTool(BaseToolWindow):
  """Unsharp mask tool class."""

  __action__ = "Unsharp masking..."

  __onthefly__ = False # This transformation can not be applied on the fly.

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Unsharp mask"): return False
    wbox = Gtk.VBox(spacing = 16)
    self.window.add(wbox)
    hbox = Gtk.HBox(spacing = 8)
    wbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Channel(s):"), False, False, 0)
    self.widgets.rgbbutton = RadioButton.new_with_label_from_widget(None, "RGB")
    hbox.pack_start(self.widgets.rgbbutton, False, False, 0)
    self.widgets.valuebutton = RadioButton.new_with_label_from_widget(self.widgets.rgbbutton, "HSV value")
    hbox.pack_start(self.widgets.valuebutton, False, False, 0)
    self.widgets.lumabutton = RadioButton.new_with_label_from_widget(self.widgets.rgbbutton, "Luma")
    hbox.pack_start(self.widgets.lumabutton, False, False, 0)
    self.widgets.radiusscale = HScaleSpinButton(5., 0., 20., .01, digits = 2, length = 320, expand = False)
    wbox.pack_start(self.widgets.radiusscale.layout2("Radius (pixels):"), False, False, 0)
    self.widgets.amountscale = HScaleSpinButton(1., 0., 10., .01, digits = 2, length = 320, expand = False)
    wbox.pack_start(self.widgets.amountscale.layout2("Amount:"), False, False, 0)
    wbox.pack_start(self.tool_control_buttons(), False, False, 0)
    self.start(identity = False)
    return True

  def get_params(self):
    """Return tool parameters."""
    if self.widgets.rgbbutton.get_active():
      channels = "RGB"
    elif self.widgets.valuebutton.get_active():
      channels = "V"
    else:
      channels = "L"
    return channels, self.widgets.radiusscale.get_value(), self.widgets.amountscale.get_value(), imageprocessing.get_rgb_luma()

  def set_params(self, params):
    """Set tool parameters 'params'."""
    channels, radius, amount, rgbluma = params
    if channels == "RGB":
      self.widgets.rgbbutton.set_active(True)
    elif channels == "V":
      self.widgets.valuebutton.get_active(True)
    else:
      self.widgets.lumabutton.set_active(True)
    self.widgets.radiusscale.set_value(radius)
    self.widgets.amountscale.set_value(amount)

  def run(self, params):
    """Run tool for parameters 'params'."""
    channels, radius, amount, rgbluma = params
    if amount <= 0. or radius <= 0.: return params, False
    if channels == "RGB":
      self.image.rgb = unsharp_mask(self.reference.rgb, channel_axis = 0, radius = radius, amount = amount)
    else:
      ref = self.reference.value() if channels == "V" else self.reference.luma()
      img = unsharp_mask(ref, radius = radius, amount = amount)
      self.image.copy_image_from(self.reference)
      self.image.scale_pixels(ref, img)
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    channels, radius, amount, rgbluma = params
    if channels == "L": channels = f"L({rgbluma[0]:.2f}, {rgbluma[1]:.2f}, {rgbluma[2]:.2f})"
    return f"UnsharpMask({channels}, radius = {radius:.2f} pixels, amount = {amount:.2f})"
