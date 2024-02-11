# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.3.0 / 2024.01.29

"""Unsharp mask tool."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
from .tools import BaseToolWindow
from .gtk.customwidgets import HScaleSpinButton
from skimage.filters import unsharp_mask

class UnsharpMaskTool(BaseToolWindow):
  """Unsharp mask tool class."""

  __action__ = "Unsharp masking..."

  __onthefly__ = False # This transformation can not be applied on the fly.

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Unsharp mask"): return False
    wbox = Gtk.VBox(spacing = 16)
    self.window.add(wbox)
    self.widgets.radiusscale = HScaleSpinButton(5., 0., 20., .01, digits = 2, length = 320, expand = False)
    wbox.pack_start(self.widgets.radiusscale.layout2("Radius (pixels):"), False, False, 0)
    self.widgets.amountscale = HScaleSpinButton(1., 0., 10., .01, digits = 2, length = 320, expand = False)
    wbox.pack_start(self.widgets.amountscale.layout2("Amount:"), False, False, 0)
    wbox.pack_start(self.tool_control_buttons(), False, False, 0)
    self.start(identity = False)
    return True

  def get_params(self):
    """Return tool parameters."""
    return self.widgets.radiusscale.get_value(), self.widgets.amountscale.get_value()

  def set_params(self, params):
    """Set tool parameters 'params'."""
    radius, amount = params
    self.widgets.radiusscale.set_value(radius)
    self.widgets.amountscale.set_value(amount)

  def run(self, params):
    """Run tool for parameters 'params'."""
    radius, amount = params
    if amount <= 0. or radius <= 0.: return params, False
    self.image.rgb = unsharp_mask(self.reference.rgb, channel_axis = 0, radius = radius, amount = amount)
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    radius, amount = params
    return f"UnsharpMask(radius = {radius:.2f} pixels, amount = {amount:.2f})"
