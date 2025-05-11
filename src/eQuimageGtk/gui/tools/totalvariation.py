# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.7.0 / 2025.05.11
# GUI updated (+).

"""Total variation filter tool."""

from ..gtk.customwidgets import VBox, RadioButtons, HScaleSpinButton
from ..toolmanager import BaseToolWindow
from skimage.restoration import denoise_tv_chambolle, denoise_tv_bregman

class TotalVariationFilterTool(BaseToolWindow):
  """Total variation filter tool class."""

  _action_ = "Applying total variation filter..."

  _help_ = """Total variation denoising.
Given a noisy image f, find an image u with less total variation than f under the constraint that u remains similar to f. This can be expressed as the Rudin–Osher–Fatemi (ROF) minimization problem:

    minmize \u03a3r |\u2207u(r)|+(\u03bb/2)[f(r)-u(r)]²

where the weight 1/\u03bb controls denoising (the larger the weight, the stronger the denoising at the expense of image fidelity).
The minimization can either be performed with the Chambolle or Split Bregman algorithms.
Total variation denoising tends to produce cartoon-like (piecewise-constant) images."""

  _onthefly_ = False # This transformation can not be applied on the fly.

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Total variation filter"): return False
    wbox = VBox()
    self.window.add(wbox)
    self.widgets.weightscale = HScaleSpinButton(.1, 0., 1., .001, digits = 3, length = 480)
    wbox.pack(self.widgets.weightscale.layout2("Weight:"))
    self.widgets.algobuttons = RadioButtons(("Chambolle", "Chambolle"), ("Bregman", "Split Bregman"))
    wbox.pack(self.widgets.algobuttons.hbox(prepend = "Algorithm:"))
    wbox.pack(self.tool_control_buttons())
    self.start(identity = False)
    return True

  def get_params(self):
    """Return tool parameters."""
    return self.widgets.weightscale.get_value(), self.widgets.algobuttons.get_selected()

  def set_params(self, params):
    """Set tool parameters 'params'."""
    weight, algorithm = params
    self.widgets.weightscale.set_value(weight)
    self.widgets.algobuttons.set_selected(algorithm)

  def run(self, params):
    """Run tool for parameters 'params'."""
    weight, algorithm = params
    if weight <= 0.: return params, False
    if algorithm == "Chambolle":
      self.image.rgb = denoise_tv_chambolle(self.reference.rgb, channel_axis = 0, weight = weight)
    else:
      self.image.rgb = denoise_tv_bregman(self.reference.rgb, channel_axis = 0, weight = 1./(2.*weight))
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    weight, algorithm = params
    return f"TotalVariationFilter(weight = {weight:.3f}, algorithm = {algorithm})"
