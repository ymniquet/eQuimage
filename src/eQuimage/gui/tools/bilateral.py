# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.5.2 / 2024.06.23
# GUI updated.

"""Bilateral filter tool."""

from ..gtk.customwidgets import HBox, VBox, HScaleSpinButton
from ..toolmanager import BaseToolWindow
from skimage.restoration import denoise_bilateral

class BilateralFilterTool(BaseToolWindow):
  """Bilateral filter tool class."""

  _action_ = "Applying bilateral filter..."

  _onthefly_ = False # This transformation can not be applied on the fly.

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Bilateral filter"): return False
    wbox = VBox()
    self.window.add(wbox)
    self.widgets.colorscale = HScaleSpinButton(.1, 0., .5, .001, digits = 3, length = 480)
    wbox.pack(self.widgets.colorscale.layout2("\u03c3 color:"))
    self.widgets.spacescale = HScaleSpinButton(5., 0., 20., .01, digits = 2, length = 480)
    wbox.pack(self.widgets.spacescale.layout2("\u03c3 space (pixels):"))
    wbox.pack(self.tool_control_buttons())
    self.start(identity = False)
    return True

  def get_params(self):
    """Return tool parameters."""
    return self.widgets.colorscale.get_value(), self.widgets.spacescale.get_value()

  def set_params(self, params):
    """Set tool parameters 'params'."""
    sigcolor, sigspace = params
    self.widgets.colorscale.set_value(sigcolor)
    self.widgets.spacescale.set_value(sigspace)

  def run(self, params):
    """Run tool for parameters 'params'."""
    sigcolor, sigspace = params
    if sigcolor <= 0. or sigspace <= 0.: return params, False
    self.image.rgb = denoise_bilateral(self.reference.rgb, channel_axis = 0, sigma_color = sigcolor, sigma_spatial = sigspace)
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    sigcolor, sigspace = params
    return f"BilateralFilter(sigcolor = {sigcolor:.3f}, sigspace = {sigspace:.2f} pixels)"
