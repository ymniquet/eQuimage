# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.6.1 / 2024.09.01
# GUI updated (+).

"""Bilateral filter tool."""

from ..gtk.customwidgets import VBox, RadioButtons, HScaleSpinButton
from ..toolmanager import BaseToolWindow
from skimage.restoration import denoise_bilateral

class BilateralFilterTool(BaseToolWindow):
  """Bilateral filter tool class."""

  _action_ = "Applying bilateral filter..."

  _help_ = """Bilateral filter.
Convolve the image with a gaussian gs of standard deviation "\u03c3 space" weighted by a gaussian gc in color space (with standard deviation "\u03c3 color"):

    Iout(r) \u221d \u03a3r' Iin(r')*gs(|r-r'|)*gc(|Iin(r)-Iin(r')|)

The image is extended across its boundaries according to the boundary mode:
  \u2022 Reflect: the image is reflected about the edge of the last pixel (abcd -> dcba|abcd|dcba).
  \u2022 Mirror: the image is reflected about the center of the last pixel (abcd -> dcb|abcd|cba).
  \u2022 Nearest: the image is padded with the value of the last pixel (abcd -> aaaa|abcd|dddd).
  \u2022 Zero: the image is padded with zeros (abcd -> 0000|abcd|0000)."""

  _onthefly_ = False # This transformation can not be applied on the fly.

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Bilateral filter"): return False
    wbox = VBox()
    self.window.add(wbox)
    self.widgets.spacescale = HScaleSpinButton(5., 0., 20., .01, digits = 2, length = 480)
    wbox.pack(self.widgets.spacescale.layout2("\u03c3 space (pixels):"))
    self.widgets.colorscale = HScaleSpinButton(.1, 0., .5, .001, digits = 3, length = 480)
    wbox.pack(self.widgets.colorscale.layout2("\u03c3 color:"))
    self.widgets.modebuttons = RadioButtons(("reflect", "Reflect"), ("mirror", "Mirror"), ("nearest", "Nearest"), ("zero", "Zero"))
    wbox.pack(self.widgets.modebuttons.hbox(prepend = "Boundary mode:"))
    wbox.pack(self.tool_control_buttons())
    self.start(identity = False)
    return True

  def get_params(self):
    """Return tool parameters."""
    return self.widgets.spacescale.get_value(), self.widgets.colorscale.get_value(), self.widgets.modebuttons.get_selected()

  def set_params(self, params):
    """Set tool parameters 'params'."""
    sigspace, sigcolor, mode = params
    self.widgets.spacescale.set_value(sigspace)
    self.widgets.colorscale.set_value(sigcolor)
    self.widgets.modebuttons.set_selected(mode)

  def run(self, params):
    """Run tool for parameters 'params'."""
    sigspace, sigcolor, mode = params
    if sigspace <= 0. or sigcolor <= 0.: return params, False
    if mode == "mirror": # Translate modes for denoise_bilateral.
      mode = "symmetric"
    elif mode == "nearest":
      mode = "edge"
    elif mode == "zero":
      mode = "constant"
    self.image.rgb = denoise_bilateral(self.reference.rgb, channel_axis = 0, sigma_spatial = sigspace, sigma_color = sigcolor, mode = mode, cval = 0.)
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    sigspace, sigcolor, mode = params
    return f"BilateralFilter(sigspace = {sigspace:.2f} pixels, sigcolor = {sigcolor:.3f}, mode = {mode})"
