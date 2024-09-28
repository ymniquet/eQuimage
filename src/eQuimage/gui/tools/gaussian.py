# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.6.1 / 2024.09.01
# GUI updated (+).

"""Gaussian filter tool."""

from ..gtk.customwidgets import HBox, VBox, HScaleSpinButton, RadioButtons
from ..toolmanager import BaseToolWindow
from skimage.filters import gaussian

class GaussianFilterTool(BaseToolWindow):
  """Gaussian filter tool class."""

  _action_ = "Applying gaussian filter..."

  _help_ = """Convolve the image with a gaussian of radius \u03c3.
The image is extended across its boundaries according to the boundary mode:
  - Reflect: the image is reflected about the edge of the last pixel (abcd -> dcba|abcd|dcba).
  - Mirror: the image is reflected about the center of the last pixel (abcd -> dcb|abcd|cba).
  - Nearest: the image is padded with the value of the last pixel (abcd -> aaaa|abcd|dddd)."""

  _onthefly_ = False # This transformation can not be applied on the fly.

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Gaussian filter"): return False
    wbox = VBox()
    self.window.add(wbox)
    self.widgets.sigmascale = HScaleSpinButton(5., 0., 20., .01, digits = 2, length = 480)
    wbox.pack(self.widgets.sigmascale.layout2("\u03c3 (pixels):"))
    self.widgets.modebuttons = RadioButtons(("reflect", "Reflect"), ("mirror", "Mirror"), ("nearest", "Nearest"))
    wbox.pack(self.widgets.modebuttons.hbox(prepend = "Boundary mode:"))
    wbox.pack(self.tool_control_buttons())
    self.start(identity = False)
    return True

  def get_params(self):
    """Return tool parameters."""
    return self.widgets.sigmascale.get_value(), self.widgets.modebuttons.get_selected()

  def set_params(self, params):
    """Set tool parameters 'params'."""
    sigma, mode = params
    self.widgets.sigmascale.set_value(sigma)
    self.widgets.modebuttons.set_selected(mode)

  def run(self, params):
    """Run tool for parameters 'params'."""
    sigma, mode = params
    if sigma <= 0: return params, False
    self.image.rgb = gaussian(self.reference.rgb, channel_axis = 0, sigma = sigma, mode = mode)
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    sigma, mode = params
    return f"GaussianFilter(sigma = {sigma:.2f} pixels, mode = {mode})"
