# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.7.0 / 2025.05.11
# GUI updated (+).

"""Color balance tool."""

from ..gtk.customwidgets import HBox, VBox, SpinButton
from ..toolmanager import BaseToolWindow

class ColorBalanceTool(BaseToolWindow):
  """Color balance tool class."""

  _action_ = "Balancing colors..."

  _help_ = "Scale the red, blue and green channels by the given factors."

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Color balance"): return False
    wbox = VBox()
    self.window.add(wbox)
    hbox = HBox()
    wbox.pack(hbox)
    self.widgets.redspin = SpinButton(1., 0., 2., .01, digits = 2)
    hbox.pack("Red:")
    hbox.pack(self.widgets.redspin)
    self.widgets.greenspin = SpinButton(1., 0., 2., .01, digits = 2)
    hbox.pack(8*" "+"Green:")
    hbox.pack(self.widgets.greenspin)
    self.widgets.bluespin = SpinButton(1., 0., 2., .01, digits = 2)
    hbox.pack(8*" "+"Blue:")
    hbox.pack(self.widgets.bluespin)
    wbox.pack(self.tool_control_buttons())
    if self.onthefly:
      self.connect_update_request(self.widgets.redspin  , "value-changed")
      self.connect_update_request(self.widgets.greenspin, "value-changed")
      self.connect_update_request(self.widgets.bluespin , "value-changed")
    self.start(identity = True)
    return True

  def get_params(self):
    """Return tool parameters."""
    return self.widgets.redspin.get_value(), self.widgets.greenspin.get_value(), self.widgets.bluespin.get_value()

  def set_params(self, params):
    """Set tool parameters 'params'."""
    red, green, blue = params
    self.widgets.redspin.set_value(red)
    self.widgets.greenspin.set_value(green)
    self.widgets.bluespin.set_value(blue)

  def run(self, params):
    """Run tool for parameters 'params'."""
    red, green, blue = params
    self.image.copy_image_from(self.reference)
    transformed = (red != 1. or green != 1. or blue != 1.)
    if transformed: self.image.color_balance(red, green, blue)
    return params, transformed

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    red, green, blue = params
    return f"ColorBalance(R = {red:.2f}, G = {green:.2f}, B = {blue:.2f})"
