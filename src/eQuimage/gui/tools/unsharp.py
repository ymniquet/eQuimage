# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.6.0 / 2024.09.01
# GUI updated.

"""Unsharp mask tool."""

from ..gtk.customwidgets import HBox, VBox, RadioButtons, HScaleSpinButton
from ..toolmanager import BaseToolWindow
from ...imageprocessing import imageprocessing
from skimage.filters import unsharp_mask

class UnsharpMaskTool(BaseToolWindow):
  """Unsharp mask tool class."""

  _action_ = "Unsharp masking..."

  _onthefly_ = False # This transformation can not be applied on the fly.

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Unsharp mask"): return False
    wbox = VBox()
    self.window.add(wbox)
    self.widgets.channelbuttons = RadioButtons(("RGB", "RGB"), ("V", "HSV value"), ("L", "Luma"))
    wbox.pack(self.widgets.channelbuttons.hbox(prepend = "Channel(s):"))
    self.widgets.radiusscale = HScaleSpinButton(5., 0., 20., .01, digits = 2, length = 480)
    wbox.pack(self.widgets.radiusscale.layout2("Radius (pixels):"))
    self.widgets.amountscale = HScaleSpinButton(1., 0., 5., .01, digits = 2, length = 480)
    wbox.pack(self.widgets.amountscale.layout2("Amount:"))
    wbox.pack(self.tool_control_buttons())
    self.start(identity = False)
    return True

  def get_params(self):
    """Return tool parameters."""
    return self.widgets.channelbuttons.get_selected(), self.widgets.radiusscale.get_value(), \
           self.widgets.amountscale.get_value(), imageprocessing.get_rgb_luma()

  def set_params(self, params):
    """Set tool parameters 'params'."""
    channels, radius, amount, rgbluma = params
    self.widgets.channelbuttons.set_selected(channels)
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
