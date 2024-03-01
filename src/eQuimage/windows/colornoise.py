# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.4.0 / 2024.02.26

"""Color noise reduction tool."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .gtk.customwidgets import HBox, VBox, CheckButton, RadioButton, HScale
from .tools import BaseToolWindow
from ..imageprocessing import imageprocessing
import numpy as np

class ColorNoiseReductionTool(BaseToolWindow):
  """Color noise reduction tool class."""

  __action__ = "Reducing color noise..."

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Color noise reduction"): return False
    wbox = VBox()
    self.window.add(wbox)
    hbox = HBox()
    wbox.pack(hbox)
    hbox.pack(Gtk.Label(label = "Color:"))
    self.widgets.nonebutton = RadioButton.new_with_label_from_widget(None, "None")
    self.widgets.nonebutton.connect("toggled", lambda button: self.update("color"))
    hbox.pack(self.widgets.nonebutton)
    self.widgets.redbutton = RadioButton.new_with_label_from_widget(self.widgets.nonebutton, "Red")
    self.widgets.redbutton.connect("toggled", lambda button: self.update("color"))
    hbox.pack(self.widgets.redbutton)
    self.widgets.yellowbutton = RadioButton.new_with_label_from_widget(self.widgets.nonebutton, "Yellow")
    self.widgets.yellowbutton.connect("toggled", lambda button: self.update("color"))
    hbox.pack(self.widgets.yellowbutton)
    self.widgets.greenbutton = RadioButton.new_with_label_from_widget(self.widgets.nonebutton, "Green")
    self.widgets.greenbutton.connect("toggled", lambda button: self.update("color"))
    hbox.pack(self.widgets.greenbutton)
    self.widgets.cyanbutton = RadioButton.new_with_label_from_widget(self.widgets.nonebutton, "Cyan")
    self.widgets.cyanbutton.connect("toggled", lambda button: self.update("color"))
    hbox.pack(self.widgets.cyanbutton)
    self.widgets.bluebutton = RadioButton.new_with_label_from_widget(self.widgets.nonebutton, "Blue")
    self.widgets.bluebutton.connect("toggled", lambda button: self.update("color"))
    hbox.pack(self.widgets.bluebutton)
    self.widgets.magentabutton = RadioButton.new_with_label_from_widget(self.widgets.nonebutton, "Magenta")
    self.widgets.magentabutton.connect("toggled", lambda button: self.update("color"))
    hbox.pack(self.widgets.magentabutton)
    hbox = HBox()
    wbox.pack(hbox)
    hbox.pack(Gtk.Label(label = "Model:"))
    self.models = ["AvgNeutral", "MaxNeutral", "AddMask", "MaxMask"]
    longmodels = ["Average neutral protection", "Maximal neutral protection", "Additive mask protection", "Maximum mask protection"]
    self.widgets.modelcombo = Gtk.ComboBoxText()
    for model in longmodels: self.widgets.modelcombo.append_text(model)
    self.widgets.modelcombo.set_active(0)
    self.widgets.modelcombo.connect("changed", lambda combo: self.update("model"))
    hbox.pack(self.widgets.modelcombo)
    self.widgets.lightnessbutton = CheckButton(label = "Preserve lightness")
    self.widgets.lightnessbutton.set_active(True)
    self.widgets.lightnessbutton.connect("toggled", lambda button: self.update("lightness"))
    hbox.pack(self.widgets.lightnessbutton, expand = True, fill = True)
    self.widgets.mixingscale = HScale(1., 0., 1., 0.01, digits = 2, marks = [0., 1.], length = 464, expand = False)
    self.widgets.mixingscale.set_sensitive(False)
    self.widgets.mixingscale.connect("value-changed", lambda scale: self.update("mixing"))
    wbox.pack(self.widgets.mixingscale.hbox(prepend = "Mixing:"))
    self.widgets.thresholdscale = HScale(0., 0., 1., 0.01, digits = 2, marks = [0., 1.], length = 464, expand = False)
    self.widgets.thresholdscale.connect("value-changed", lambda scale: self.update("threshold"))
    wbox.pack(self.widgets.thresholdscale.hbox(prepend = "Threshold:"))
    wbox.pack(self.tool_control_buttons())
    self.reference.luminance = self.reference.srgb_luminance()
    self.start(identity = True)
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
    elif self.widgets.magentabutton.get_active():
      color = "magenta"
    else:
      color = None
    model = self.models[self.widgets.modelcombo.get_active()]
    mixing = self.widgets.mixingscale.get_value()
    threshold = self.widgets.thresholdscale.get_value()
    lightness = self.widgets.lightnessbutton.get_active()
    return color, model, mixing, threshold, lightness

  def set_params(self, params):
    """Set tool parameters 'params'."""
    color, model, mixing, threshold, lightness = params
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
    elif color == "magenta":
      self.widgets.magentabutton.set_active(True)
    else:
      self.widgets.nonebutton.set_active(True)
    self.widgets.modelcombo.set_active(self.models.index(model))
    self.widgets.mixingscale.set_value(mixing)
    self.widgets.thresholdscale.set_value(threshold)
    self.widgets.lightnessbutton.set_active(lightness)

  def run(self, params):
    """Run tool for parameters 'params'."""
    color, model, mixing, threshold, lightness = params
    self.image.copy_image_from(self.reference)
    if color == "red":
      icc, ic1, ic2, negative = 0, 1, 2, False
    elif color == "yellow":
      icc, ic1, ic2, negative = 2, 0, 1, True
    elif color == "green":
      icc, ic1, ic2, negative = 1, 0, 2, False
    elif color == "cyan":
      icc, ic1, ic2, negative = 0, 1, 2, True
    elif color == "blue":
      icc, ic1, ic2, negative = 2, 0, 1, False
    elif color == "magenta":
      icc, ic1, ic2, negative = 1, 0, 2, True
    else:
      return params, False
    if negative: self.image.negative()
    image = self.image.get_image()
    mask = (image[icc] >= threshold)
    if model == "AvgNeutral":
      image[icc] = np.where(mask, np.minimum(image[icc], (image[ic1]+image[ic2])/2.), image[icc])
    elif model == "MaxNeutral":
      image[icc] = np.where(mask, np.minimum(image[icc], np.maximum(image[ic1], image[ic2])), image[icc])
    elif model == "AddMask":
      m = np.minimum(1., image[ic1]+image[ic2])
      image[icc] *= np.where(mask, (1.-mixing)+m*mixing, 1.)
    else:
      m = np.maximum(image[ic1], image[ic2])
      image[icc] *= np.where(mask, (1.-mixing)+m*mixing, 1.)
    if negative: self.image.negative()
    if lightness: self.image.scale_pixels(self.image.srgb_luminance(), self.reference.luminance)
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    color, model, mixing, threshold, lightness = params
    if color is None: return None
    operation = f"ReduceColorNoise(color = {color}, model = {model}"
    if model in ["AddMask", "MaxMask"]:
      operation += f", mixing = {mixing:.2f}"
    operation += f", threshold = {threshold:.2f}"
    if lightness: operation += f", preserve L*"
    operation += ")"
    return operation

  # Update widgets.

  def update(self, changed):
    """Update widgets on change of 'changed'."""
    if changed == "model":
      model = self.models[self.widgets.modelcombo.get_active()]
      sensitive = (model in ["AddMask", "MaxMask"])
      self.widgets.mixingscale.set_sensitive(sensitive)
    self.reset_polling(self.get_params()) # Expedite main window update.
