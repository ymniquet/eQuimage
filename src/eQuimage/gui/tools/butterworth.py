# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.5.1 / 2024.06.05
# GUI updated.

"""Butterworth filter tool."""

from ..gtk.customwidgets import HBox, VBox, HScaleSpinButton
from ..toolmanager import BaseToolWindow
from skimage.filters import butterworth

class ButterworthFilterTool(BaseToolWindow):
  """Butterworth filter tool class."""

  _action_ = "Applying Butterworth filter..."

  _onthefly_ = False # This transformation can not be applied on the fly.

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Butterworth filter"): return False
    wbox = VBox()
    self.window.add(wbox)
    self.widgets.cutoffscale = HScaleSpinButton(.5, 0., .9999, .0001, digits = 4, length = 480)
    wbox.pack(self.widgets.cutoffscale.layout2("Cut-off:"))
    self.widgets.orderscale = HScaleSpinButton(2., .1, 10., .1, digits = 1, length = 480)
    wbox.pack(self.widgets.orderscale.layout2("Order:"))
    wbox.pack(self.tool_control_buttons())
    self.start(identity = False)
    return True

  def get_params(self):
    """Return tool parameters."""
    return self.widgets.cutoffscale.get_value(), self.widgets.orderscale.get_value()

  def set_params(self, params):
    """Set tool parameters 'params'."""
    cutoff, order = params
    self.widgets.cutoffscale.set_value(cutoff)
    self.widgets.orderscale.set_value(order)

  def run(self, params):
    """Run tool for parameters 'params'."""
    cutoff, order = params
    self.image.rgb = butterworth(self.reference.rgb, channel_axis = 0, cutoff_frequency_ratio = (1.-cutoff)/2., order = order, high_pass = False, squared_butterworth = True)
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    cutoff, order = params
    return f"ButterworthFilter(cutoff = {cutoff:.4f}, order = {order:.1f})"
