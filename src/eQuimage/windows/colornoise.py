# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2024.01.14

"""Color noise reduction tool."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .gtk.customwidgets import CheckButton, RadioButton, HScale
from .tools import BaseToolWindow
from ..imageprocessing import imageprocessing
import numpy as np

class ColorNoiseReductionTool(BaseToolWindow):
  """Color noise reduction tool class."""

  __action__ = "Reducing color noise..."

  __onthefly__ = False # This transformation can not be applied on the fly.

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Color noise reduction"): return False
    wbox = Gtk.VBox(spacing = 16)
    self.window.add(wbox)
    hbox = Gtk.HBox(spacing = 8)
    wbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Color:"), False, False, 0)
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
    hbox.pack_start(Gtk.Label(label = "Model:"), False, False, 0)
    self.models = ["AvgNeutral", "MaxNeutral", "AddMask", "MaxMask"]
    longmodels = ["Average neutral protection", "Maximal neutral protection", "Additive mask protection", "Maximum mask protection"]
    self.widgets.modelcombo = Gtk.ComboBoxText()
    for model in longmodels: self.widgets.modelcombo.append_text(model)
    self.widgets.modelcombo.set_active(0)
    self.widgets.modelcombo.connect("changed", lambda combo: self.update("model"))
    hbox.pack_start(self.widgets.modelcombo, False, False, 0)
    self.widgets.lumabutton = CheckButton(label = "Preserve lightness")
    self.widgets.lumabutton.set_active(True)
    hbox.pack_start(self.widgets.lumabutton, True, True, 0)
    hbox = Gtk.HBox(spacing = 8)
    wbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Mixing:"), False, False, 0)
    self.widgets.mixscale = HScale(1., 0., 1., 0.01, digits = 2, length = 384, expand = False)
    self.widgets.mixscale.set_sensitive(False)
    hbox.pack_start(self.widgets.mixscale, False, False, 0)
    wbox.pack_start(self.tool_control_buttons(reset = False), False, False, 0)
    self.reference.luminance = self.reference.srgb_luminance()
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
    model = self.models[self.widgets.modelcombo.get_active()]
    mixing = self.widgets.mixscale.get_value()
    preserve = self.widgets.lumabutton.get_active()
    rgbluma = imageprocessing.get_rgb_luma()
    return color, model, mixing, preserve, rgbluma

  def set_params(self, params):
    """Set tool parameters 'params'."""
    color, model, mixing, preserve, rgbluma = params
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
    self.widgets.modelcombo.set_active(self.models.index(model))
    self.widgets.mixscale.set_value(mixing)
    self.widgets.lumabutton.set_active(preserve)

  def run(self, params):
    """Run tool for parameters 'params'."""
    color, model, mixing, preserve, rgbluma = params
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
    self.image.copy_image_from(self.reference)
    if negative: self.image.negative()
    image = self.image.get_image()
    if model == "AvgNeutral":
      image[cc] = np.minimum(image[cc], (image[c1]+image[c2])/2.)
    elif model == "MaxNeutral":
      image[cc] = np.minimum(image[cc], np.maximum(image[c1], image[c2]))
    elif model == "AddMask":
      m = np.minimum(1., image[c1]+image[c2])
      image[cc] *= (1.-mixing)+m*mixing
    else:
      m = np.maximum(image[c1], image[c2])
      image[cc] *= (1.-mixing)+m*mixing
    if negative: self.image.negative()
    if preserve: self.image.scale_pixels(self.image.srgb_luminance(), self.reference.luminance)
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    color, model, mixing, preserve, rgbluma = params
    operation = f"RemoveColorNoise({color}, model = {model}"
    if model in ["AddMask", "MaxMask"]:
      operation += f", mixing = {mixing:.2f}"
    if preserve: operation += f", preserve L*"
    operation += ")"
    return operation

  # Update widgets.

  def update(self, changed):
    """Update widgets on change of 'changed'."""
    if changed == "model":
      model = self.models[self.widgets.modelcombo.get_active()]
      sensitive = (model in ["AddMask", "MaxMask"])
      self.widgets.mixscale.set_sensitive(sensitive)
