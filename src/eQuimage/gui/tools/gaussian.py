# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.5.2 / 2024.06.23
# GUI updated.

"""Gaussian filter tool."""

from ..gtk.customwidgets import HBox, VBox, HScaleSpinButton
from ..toolmanager import BaseToolWindow
from skimage.filters import gaussian

class GaussianFilterTool(BaseToolWindow):
  """Gaussian filter tool class."""

  _action_ = "Applying gaussian filter..."

  _onthefly_ = False # This transformation can not be applied on the fly.

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Gaussian filter"): return False
    wbox = VBox()
    self.window.add(wbox)
    self.widgets.sigmascale = HScaleSpinButton(5., 0., 20., .01, digits = 2, length = 480)
    wbox.pack(self.widgets.sigmascale.layout2("\u03c3 (pixels):"))
    wbox.pack(self.tool_control_buttons())
    self.start(identity = False)
    return True

  def get_params(self):
    """Return tool parameters."""
    return self.widgets.sigmascale.get_value()

  def set_params(self, params):
    """Set tool parameters 'params'."""
    sigma = params
    self.widgets.sigmascale.set_value(sigma)

  def run(self, params):
    """Run tool for parameters 'params'."""
    sigma = params
    if sigma <= 0: return params, False
    self.image.rgb = gaussian(self.reference.rgb, channel_axis = 0, sigma = sigma)
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    sigma = params
    return f"GaussianFilter(sigma = {sigma:.2f} pixels)"
