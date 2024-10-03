# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.6.1 / 2024.09.01
# GUI updated (+).

"""Color noise reduction tool."""

from ..gtk.customwidgets import HBox, VBox, CheckButton, RadioButtons, HScale, ComboBoxText
from ..toolmanager import BaseToolWindow
from ...imageprocessing.utils import scale_pixels
from ...imageprocessing.colors import srgb_to_lrgb, lrgb_luminance, lrgb_to_srgb
import numpy as np

class ColorNoiseReductionTool(BaseToolWindow):
  """Color noise reduction tool class."""

  _action_ = "Reducing color noise..."

  _help_ = """Reduce color noise for the red (R), yellow (Y), green (G), cyan (C), blue (B) or magenta (M) hue. For the green hue for example,

    \u2022 G \u2192 min(G, m) with m = (R+B)/2 for average neutral protection.
    \u2022 G \u2192 min(G, m) with m = max(R, B) for maximum neutral protection.
    \u2022 G \u2192 G[(1-mixing)+m*mixing] with m = (R+B)/2 for additive mask protection.
    \u2022 G \u2192 G[(1-mixing)+m*mixing] with m = max(R, B) for maximum mask protection.

The RGB components of each pixel are rescaled to preserve the CIE lightness L* if the "preserve lightness" checkbox is ticked."""

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Color noise reduction"): return False
    self.reference.luminance = self.reference.srgb_luminance() # Compute reference luminance.
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
    hbox.pack(self.widgets.lightnessbutton)
    self.widgets.mixingscale = HScale(1., 0., 1., .01, digits = 2, marks = [0., 1.], length = 480, expand = False)
    self.widgets.mixingscale.set_sensitive(False)
    self.widgets.mixingscale.connect("value-changed", lambda scale: self.update("mixing"))
    wbox.pack(self.widgets.mixingscale.hbox(prepend = "Mixing:"))
    #self.widgets.thresholdscale = HScale(0., 0., 1., .01, digits = 2, marks = [0., 1.], length = 480, expand = False)
    #self.widgets.thresholdscale.connect("value-changed", lambda scale: self.update("threshold"))
    #wbox.pack(self.widgets.thresholdscale.hbox(prepend = "Threshold:"))
    wbox.pack(self.tool_control_buttons())
    self.start(identity = True)
    return True

  def get_params(self):
    """Return tool parameters."""
    color = self.widgets.colorbuttons.get_selected()
    model = self.widgets.modelcombo.get_selected()
    mixing = self.widgets.mixingscale.get_value()
    #threshold = self.widgets.thresholdscale.get_value()
    lightness = self.widgets.lightnessbutton.get_active()
    #return color, model, mixing, threshold, lightness
    return color, model, mixing, lightness

  def set_params(self, params):
    """Set tool parameters 'params'."""
    #color, model, mixing, threshold, lightness = params
    color, model, mixing, lightness = params
    self.widgets.colorbuttons.set_selected_block(color)
    self.widgets.modelcombo.set_selected_block(model)
    self.widgets.mixingscale.set_value_block(mixing)
    #self.widgets.thresholdscale.set_value_block(threshold)
    self.widgets.lightnessbutton.set_active_block(lightness)
    self.update("all")

  def run(self, params):
    """Run tool for parameters 'params'."""
    #color, model, mixing, threshold, lightness = params
    color, model, mixing, lightness = params
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
    rgb = self.image.rgb
    #mask = (rgb[icc] >= threshold)
    if model == "AvgNeutral":
      m = (rgb[ic1]+rgb[ic2])/2.
      #rgb[icc] = np.where(mask, np.minimum(rgb[icc], m, rgb[icc])
      rgb[icc] = np.minimum(rgb[icc], m)
    elif model == "MaxNeutral":
      m = np.maximum(rgb[ic1], rgb[ic2])
      #rgb[icc] = np.where(mask, np.minimum(rgb[icc], m, rgb[icc])
      rgb[icc] = np.minimum(rgb[icc], m)
    elif model == "AddMask":
      m = np.minimum(1., rgb[ic1]+rgb[ic2])
      #rgb[icc] *= np.where(mask, (1.-mixing)+m*mixing, 1.)
      rgb[icc] *= (1.-mixing)+m*mixing
    else:
      m = np.maximum(rgb[ic1], rgb[ic2])
      #rgb[icc] *= np.where(mask, (1.-mixing)+m*mixing, 1.)
      rgb[icc] *= (1.-mixing)+m*mixing
    if negative: self.image.negative()
    if lightness:
      lrgb = srgb_to_lrgb(self.image.rgb)
      self.image.rgb = lrgb_to_srgb(scale_pixels(lrgb, lrgb_luminance(lrgb), self.reference.luminance))
      difflight = self.image.srgb_lightness()-self.reference.srgb_lightness()
      print(f"Maximum lightness difference = {abs(difflight).max()}.")
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    #color, model, mixing, threshold, lightness = params
    color, model, mixing, lightness = params
    if color == "None": return None
    operation = f"ReduceColorNoise(color = {color}, model = {model}"
    if model in ["AddMask", "MaxMask"]:
      operation += f", mixing = {mixing:.2f}"
    #operation += f", threshold = {threshold:.2f}"
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
