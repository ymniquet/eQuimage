# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.5.2 / 2024.06.23
# GUI updated.

"""Remove hot pixels tool."""

from ..gtk.customwidgets import HBox, VBox, RadioButtons, SpinButton
from ..toolmanager import BaseToolWindow
from ...imageprocessing import imageprocessing

class RemoveHotPixelsTool(BaseToolWindow):
  """Remove hot pixels tool window class."""

  _action_ = "Removing hot pixels..."

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Remove hot pixels"): return False
    wbox = VBox()
    self.window.add(wbox)
    self.widgets.channelbuttons = RadioButtons(("RGB", "RGB"), ("L", "Luma"))
    wbox.pack(self.widgets.channelbuttons.hbox(prepend = "Channel(s):"))
    self.widgets.ratiospin = SpinButton(2., 1., 10., .01, digits = 2)
    wbox.pack(self.widgets.ratiospin.hbox(prepend = "Ratio:"))
    wbox.pack(self.tool_control_buttons(reset = not self.onthefly))
    if self.onthefly:
      self.connect_update_request(self.widgets.channelbuttons, "toggled")
      self.connect_update_request(self.widgets.ratiospin, "value-changed")
    self.start(identity = False)
    return True

  def get_params(self):
    """Return tool parameters."""
    return self.widgets.channelbuttons.get_selected(), self.widgets.ratiospin.get_value(), imageprocessing.get_rgb_luma()

  def set_params(self, params):
    """Set tool parameters 'params'."""
    channels, ratio, rgbluma = params
    self.widgets.channelbuttons.set_selected(channels)
    self.widgets.ratiospin.set_value(ratio)

  def run(self, params):
    """Run tool for parameters 'params'."""
    channels, ratio, rgbluma = params
    self.image.copy_image_from(self.reference)
    self.image.remove_hot_pixels(ratio, channels = channels)
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    channels, ratio, rgbluma = params
    if channels == "L": channels = f"L({rgbluma[0]:.2f}, {rgbluma[1]:.2f}, {rgbluma[2]:.2f})"
    return f"RemoveHotPixels(channels = {channels}, ratio = {ratio:.2f})"
