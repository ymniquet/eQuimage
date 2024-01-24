# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2024.01.14

"""Color noise tool."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .gtk.customwidgets import CheckButton, RadioButton
from .tools import BaseToolWindow
from ..imageprocessing import imageprocessing
import numpy as np

class RemoveColorNoiseTool(BaseToolWindow):
  """Color noise tool class."""

  __action__ = "Removing color noise..."

  __onthefly__ = False # This transformation can not be applied on the fly.

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Remove color noise"): return False
    wbox = Gtk.VBox(spacing = 16)
    self.window.add(wbox)
    hbox = Gtk.HBox(spacing = 8)
    wbox.pack_start(hbox, False, False, 0)
    self.widgets.redbutton = RadioButton.new_with_label_from_widget(None, "Red")
    hbox.pack_start(self.widgets.redbutton, False, False, 0)
    self.widgets.yellowbutton = RadioButton.new_with_label_from_widget(self.widgets.redbutton, "Yellow")
    hbox.pack_start(self.widgets.yellowbutton, False, False, 0)
    self.widgets.greenbutton = RadioButton.new_with_label_from_widget(self.widgets.redbutton, "Green")
    hbox.pack_start(self.widgets.greenbutton, False, False, 0)
    self.widgets.cyanbutton = RadioButton.new_with_label_from_widget(self.widgets.redbutton, "Cyan")
    hbox.pack_start(self.widgets.cyanbutton, False, False, 0)
    self.widgets.bluebutton = RadioButton.new_with_label_from_widget(self.widgets.redbutton, "Blue")
    hbox.pack_start(self.widgets.bluebutton, False, False, 0)
    self.widgets.magentabutton = RadioButton.new_with_label_from_widget(self.widgets.redbutton, "Magenta")
    hbox.pack_start(self.widgets.magentabutton, False, False, 0)
    self.widgets.greenbutton.set_active(True)
    hbox = Gtk.HBox(spacing = 8)
    wbox.pack_start(hbox, False, False, 0)
    self.widgets.lumbutton = CheckButton(label = "Preserve luminance")
    self.widgets.lumbutton.set_active(True)
    hbox.pack_start(self.widgets.lumbutton, True, True, 0)
    wbox.pack_start(self.tool_control_buttons(), False, False, 0)
    self.start()
    return True

  def get_params(self):
    """Return tool parameters."""
    if self.widgets.redbutton.get_active():
      color = "red"
    elif self.widgets.yellowbutton.get_active():
      color = "yellow"
    elif self.widgets.greenbutton.get_active():
      color = "green"
    elif self.widgets.cyanbutton.get_active():
      color = "cyan"
    elif self.widgets.bluebutton.get_active():
      color = "blue"
    else:
      color = "magenta"
    preserve = self.widgets.lumbutton.get_active()
    rgblum = imageprocessing.get_rgb_luminance()
    return color, preserve, rgblum

  def set_params(self, params):
    """Set tool parameters 'params'."""
    color, preserve, rgblum = params
    if color == "red":
      self.widgets.redbutton.set_active(True)
    elif color == "yellow":
      self.widgets.yellowbutton.set_active(True)
    elif color == "green":
      self.widgets.greenbutton.set_active(True)
    elif color == "cyan":
      self.widgets.cyanbutton.set_active(True)
    elif color == "blue":
      self.widgets.bluebutton.set_active(True)
    else:
      self.widgets.magentabutton.set_active(True)
    self.widgets.lumbutton.set_active(preserve)

  def run(self, params):
    """Run tool for parameters 'params'."""
    color, preserve, rgblum = params
    if color == "red":
      cc, c1, c2, negative = 0, 1, 2, False
    elif color == "yellow":
      cc, c1, c2, negative = 2, 0, 1, True
    elif color == "green":
      cc, c1, c2, negative = 1, 0, 2, False
    elif color == "cyan":
      cc, c1, c2, negative = 0, 1, 2, True
    elif color == "blue":
      cc, c1, c2, negative = 2, 0, 1, False
    else:
      cc, c1, c2, negative = 1, 0, 2, True
    self.image.copy_rgb_from(self.reference)
    if negative: self.image.negative()
    image = self.image.get_image()
    image[cc] = np.minimum(image[cc], (image[c1]+image[c2])/2.)
    if negative: self.image.negative()
    if preserve: self.image.scale_pixels(self.image.luminance(), self.reference.luminance())
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    color, preserve, rgblum = params
    operation = f"RemoveColorNoise({color}"
    if preserve:
      red, green, blue = rgblum
      operation += f", preserve L({red:.2f}, {green:.2f}, {blue:.2f})"
    operation += ")"
    return operation
