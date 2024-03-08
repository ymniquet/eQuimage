# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.4.0 / 2024.02.26
# GUI updated.

"""Gray scale conversion tool."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
from .gtk.customwidgets import HBox, VBox, RadioButtons
from .tools import BaseToolWindow
from ..imageprocessing import imageprocessing

class GrayScaleConversionTool(BaseToolWindow):
  """Gray scale conversion tool window class."""

  __action__ = "Converting into a gray scale image..."

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Gray scale conversion"): return False
    wbox = VBox()
    self.window.add(wbox)
    self.widgets.channelbuttons = RadioButtons(("V", "HSV Value"), ("L", "Luma"), ("Y", "Luminance Y"))
    wbox.pack(self.widgets.channelbuttons.hbox(prepend = "Channel:"))
    wbox.pack(self.tool_control_buttons(reset = False))
    if self.onthefly:
      self.connect_update_request(self.widgets.channelbuttons, "toggled")
    self.start(identity = False)
    return True

  def get_params(self):
    """Return tool parameters."""
    return self.widgets.channelbuttons.get_selected(), imageprocessing.get_rgb_luma()

  def set_params(self, params):
    """Set tool parameters 'params'."""
    channel, rgbluma = params
    self.widgets.channelbuttons.set_selected(channel)

  def run(self, params):
    """Run tool for parameters 'params'."""
    channel, rgbluma = params
    self.image.copy_image_from(self.reference)
    self.image.gray_scale(channel = channel)
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    channel, rgbluma = params
    if channel == "L": channel = f"L({rgbluma[0]:.2f}, {rgbluma[1]:.2f}, {rgbluma[2]:.2f})"
    return f"GrayScale(channel = {channel})"
