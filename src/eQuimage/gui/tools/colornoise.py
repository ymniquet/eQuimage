# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.5.1 / 2024.06.05
# GUI updated.

"""Color noise reduction tool."""

from ..gtk.customwidgets import HBox, VBox, CheckButton, RadioButtons, HScale, ComboBoxText
from ..toolmanager import BaseToolWindow
from ...imageprocessing.colors import lrgb_luminance
import numpy as np

class ColorNoiseReductionTool(BaseToolWindow):
  """Color noise reduction tool class."""

  _action_ = "Reducing color noise..."

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Color noise reduction"): return False
    wbox = VBox()
    self.window.add(wbox)
    self.widgets.colorbuttons = RadioButtons(("None", "None"), ("red", "Red"), ("yellow", "Yellow"), ("green", "Green"), \
                                             ("cyan", "Cyan"), ("blue", "Blue"), ("magenta", "Magenta"))
    self.widgets.colorbuttons.connect("toggled", lambda button: self.update("color"))
    wbox.pack(self.widgets.colorbuttons.hbox(prepend = "Color:"))
    hbox = HBox()
    wbox.pack(hbox)
    self.widgets.modelcombo = ComboBoxText(("AvgNeutral", "Average neutral protection"), ("MaxNeutral", "Maximal neutral protection"), \
                                           ("AddMask", "Additive mask protection"), ("MaxMask", "Maximum mask protection"))
    self.widgets.modelcombo.connect("changed", lambda combo: self.update("model"))
    hbox.pack("Model:")
    hbox.pack(self.widgets.modelcombo)
    self.widgets.lightnessbutton = CheckButton(label = "Preserve lightness")
    self.widgets.lightnessbutton.set_active(True)
    self.widgets.lightnessbutton.connect("toggled", lambda button: self.update("lightness"))
    hbox.pack(self.widgets.lightnessbutton, expand = True, fill = True)
    self.widgets.mixingscale = HScale(1., 0., 1., .01, digits = 2, marks = [0., 1.], length = 480, expand = False)
    self.widgets.mixingscale.set_sensitive(False)
    self.widgets.mixingscale.connect("value-changed", lambda scale: self.update("mixing"))
    wbox.pack(self.widgets.mixingscale.hbox(prepend = "Mixing:"))
    self.widgets.thresholdscale = HScale(0., 0., 1., .01, digits = 2, marks = [0., 1.], length = 480, expand = False)
    self.widgets.thresholdscale.connect("value-changed", lambda scale: self.update("threshold"))
    wbox.pack(self.widgets.thresholdscale.hbox(prepend = "Threshold:"))
    wbox.pack(self.tool_control_buttons())
    self.reference.lightscale = lrgb_luminance(np.clip(self.reference.rgb, 0., 1.)**2.2)**(1./2.2) # Approximate back and forth transformation between sRGB & lRGB color spaces.
    self.start(identity = True)
    return True

  def get_params(self):
    """Return tool parameters."""
    color = self.widgets.colorbuttons.get_selected()
    model = self.widgets.modelcombo.get_selected()
    mixing = self.widgets.mixingscale.get_value()
    threshold = self.widgets.thresholdscale.get_value()
    lightness = self.widgets.lightnessbutton.get_active()
    return color, model, mixing, threshold, lightness

  def set_params(self, params):
    """Set tool parameters 'params'."""
    color, model, mixing, threshold, lightness = params
    self.widgets.colorbuttons.set_selected_block(color)
    self.widgets.modelcombo.set_selected_block(model)
    self.widgets.mixingscale.set_value_block(mixing)
    self.widgets.thresholdscale.set_value_block(threshold)
    self.widgets.lightnessbutton.set_active_block(lightness)
    self.update("all")

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
    self.image.clip() # Clip before reducing color noise.
    if negative: self.image.negative()
    image = self.image.get_image() # This is a ref to self.image.rgb.
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
    if lightness:
      lightscale = lrgb_luminance(self.image.rgb**2.2)**(1./2.2)     # Approximate back and forth transformation between sRGB & lRGB color spaces.
      self.image.scale_pixels(lightscale, self.reference.lightscale) # This preserves exact sRGB hue at the cost of an approximate lightness conservation.
    #difflight = self.image.srgb_lightness()-self.reference.srgb_lightness()
    #print(f"Maximum lightness difference = {abs(difflight).max()}.")
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    color, model, mixing, threshold, lightness = params
    if color == "None": return None
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
    if changed in ["model", "all"]:
      model = self.widgets.modelcombo.get_selected()
      self.widgets.mixingscale.set_sensitive(model in ["AddMask", "MaxMask"])
    self.reset_polling(self.get_params()) # Expedite main window update.
