# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.4.0 / 2024.02.26

"""Dark mask tool."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GObject
from .gtk.customwidgets import HBox, VBox, RadioButton, HScaleSpinButton
from .tools import BaseToolWindow
from ..imageprocessing import imageprocessing
from skimage.morphology import isotropic_dilation, disk
from scipy.ndimage import convolve, uniform_filter, median_filter, maximum_filter, gaussian_filter
import numpy as np

class DarkMaskTool(BaseToolWindow):
  """Dark Mask tool class."""

  __action__ = "Setting dark mask..."

  __onthefly__ = False # This transformation can not be applied on the fly.

  DARKCOLOR  = np.array([[.5], [0.], [.5]], dtype = imageprocessing.IMGTYPE)
  LIGHTCOLOR = np.array([[0.], [.5], [0.]], dtype = imageprocessing.IMGTYPE)

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Dark mask"): return False
    wbox = VBox()
    self.window.add(wbox)
    hbox = HBox()
    wbox.pack(hbox)
    hbox.pack(Gtk.Label(label = "Filter channel:"))
    self.widgets.valuebutton = RadioButton.new_with_label_from_widget(None, "HSV value")
    hbox.pack(self.widgets.valuebutton)
    self.widgets.lumabutton = RadioButton.new_with_label_from_widget(self.widgets.valuebutton, "Luma")
    hbox.pack(self.widgets.lumabutton)
    self.widgets.lightnessbutton = RadioButton.new_with_label_from_widget(self.widgets.valuebutton, "Lightness L*")
    hbox.pack(self.widgets.lightnessbutton)
    hbox = HBox()
    wbox.pack(hbox)
    hbox.pack(Gtk.Label(label = "Filter function:"))
    self.widgets.meanbutton = RadioButton.new_with_label_from_widget(None, "Mean")
    hbox.pack(self.widgets.meanbutton)
    self.widgets.medianbutton = RadioButton.new_with_label_from_widget(self.widgets.meanbutton, "Median")
    hbox.pack(self.widgets.medianbutton)
    self.widgets.maximumbutton = RadioButton.new_with_label_from_widget(self.widgets.meanbutton, "Maximum")
    hbox.pack(self.widgets.maximumbutton)
    self.widgets.gaussianbutton = RadioButton.new_with_label_from_widget(self.widgets.meanbutton, "Gaussian")
    hbox.pack(self.widgets.gaussianbutton)
    self.widgets.radiusscale = HScaleSpinButton(8., 1., 50., 1., digits = 0, length = 320, expand = False)
    wbox.pack(self.widgets.radiusscale.layout2("Filter radius (pixels):"))
    self.widgets.thresholdscale = HScaleSpinButton(0., 0., .2, .001, digits = 3, length = 320, expand = False)
    wbox.pack(self.widgets.thresholdscale.layout2("Dark/light threshold:"))
    self.widgets.extendscale = HScaleSpinButton(0., 0., 100., 1., digits = 0, length = 320, expand = False)
    wbox.pack(self.widgets.extendscale.layout2("Extend light mask by (pixels):"))
    self.widgets.smoothscale = HScaleSpinButton(0., 0., 100., 1., digits = 0, length = 320, expand = False)
    wbox.pack(self.widgets.smoothscale.layout2("Smooth dark/light masks over (pixels):"))
    self.widgets.weightscale = HScaleSpinButton(0., 0., 1., .01, digits = 2, length = 320, expand = False)
    wbox.pack(self.widgets.weightscale.layout2("Dark weight:"))
    wbox.pack(self.tool_control_buttons())
    self.opentabs = False
    self.fparams = None
    self.start(identity = True)
    return True

  def get_params(self):
    """Return tool parameters."""
    if self.widgets.valuebutton.get_active():
      fchannel = "V"
    elif self.widgets.lumabutton.get_active():
      fchannel = "L"
    else:
      fchannel = "L*"
    if self.widgets.meanbutton.get_active():
      ffunction = "mean"
    elif self.widgets.medianbutton.get_active():
      ffunction = "median"
    elif self.widgets.maximumbutton.get_active():
      ffunction = "maximum"
    else:
      ffunction = "gaussian"
    fradius = int(round(self.widgets.radiusscale.get_value()))
    threshold = self.widgets.thresholdscale.get_value()
    extend = int(round(self.widgets.extendscale.get_value()))
    smooth = int(round(self.widgets.smoothscale.get_value()))
    weight = self.widgets.weightscale.get_value()
    rgbluma = imageprocessing.get_rgb_luma() if fchannel == "L" else None
    return fchannel, ffunction, fradius, threshold, extend, smooth, weight, rgbluma

  def set_params(self, params):
    """Set tool parameters 'params'."""
    fchannel, ffunction, fradius, threshold, extend, smooth, weight, rgbluma = params
    if fchannel == "V":
      self.widgets.valuebutton.set_active(True)
    elif fchannel == "L":
      self.widgets.lumabutton.set_active(True)
    else:
      self.widgets.lightnessbutton.set_active(True)
    if ffunction == "mean":
      self.widgets.meanbutton.set_active(True)
    elif ffunction == "median":
      self.widgets.medianbutton.set_active(True)
    elif ffunction == "maximum":
      self.widgets.maximumbutton.set_active(True)
    else:
      self.widgets.gaussianbutton.set_active(True)
    self.widgets.radiusscale.set_value(fradius)
    self.widgets.thresholdscale.set_value(threshold)
    self.widgets.extendscale.set_value(extend)
    self.widgets.smoothscale.set_value(smooth)
    self.widgets.weightscale.set_value(weight)

  def run(self, params):
    """Run tool for parameters 'params'."""
    fchannel, ffunction, fradius, threshold, extend, smooth, weight, rgbluma = params
    fparams = (fchannel, ffunction, fradius, rgbluma)
    # Compute the filter if needed.
    if fparams != self.fparams:
      if fchannel == "V":
        channel = self.reference.value()
      elif fchannel == "L":
        channel = self.reference.luma()
      else:
        channel = self.reference.srgb_lightness()/100.
      if ffunction == "mean":
        kernel = disk(fradius, dtype = imageprocessing.IMGTYPE)
        kernel /= np.sum(kernel)
        self.filtered = convolve(channel, kernel, mode = "reflect")
      elif ffunction == "median":
        self.filtered = median_filter(channel, footprint = disk(fradius), mode = "reflect")
      elif ffunction == "maximum":
        self.filtered = maximum_filter(channel, footprint = disk(fradius), mode = "reflect")
      else:
        self.filtered = gaussian_filter(channel, sigma = fradius/3., mode = "reflect")
      self.fparams = fparams
    # Threshold the filter.
    lightmask = (self.filtered >= threshold)
    # Extend the light mask.
    if extend > 0: lightmask = isotropic_dilation(lightmask, extend)
    # Display light and dark masks.
    lightmasked = self.reference.clone()
    lightmasked.rgb[:, lightmask] = self.LIGHTCOLOR
    darkmasked = self.reference.clone()
    darkmasked.rgb[:, ~lightmask] = self.DARKCOLOR
    GObject.idle_add(self.update_mask_tabs, lightmasked, darkmasked, priority = GObject.PRIORITY_DEFAULT) # Thread-safe.
    # Return original image if dark mask empty.
    if np.all(lightmask): return params, False
    # Smooth the light mask.
    mask = lightmask.astype(imageprocessing.IMGTYPE)
    if smooth > 0:
      kernel = disk(smooth, dtype = imageprocessing.IMGTYPE)
      kernel /= np.sum(kernel)
      mask = convolve(mask, kernel, mode = "reflect")
    # Apply the mask.
    mask = weight+(1.-weight)*mask
    self.image.copy_image_from(self.reference)
    self.image.rgb *= mask
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    fchannel, ffunction, fradius, threshold, extend, smooth, weight, rgbluma = params
    if fchannel == "L": fchannel = f"L({rgbluma[0]:.2f}, {rgbluma[1]:.2f}, {rgbluma[2]:.2f})"
    return f"DarkMask(channel = {fchannel}, filter = {ffunction}, radius = {fradius} pixels, threshold = {threshold:.3f}, extend = {extend} pixels, smooth = {smooth} pixels, weight = {weight:.2f})"

  def cancel(self, *args, **kwargs):
    """Cancel tool."""
    if self.opentabs:
      self.app.mainwindow.delete_image("Light mask", force = True)
      self.app.mainwindow.delete_image("Dark mask", force = True)
      self.opentabs = False
    super().cancel()

  def cleanup(self):
    """Free memory on exit."""
    try:
      del self.filtered
    except:
      pass

  # Update mask tabs.

  def update_mask_tabs(self, lightmasked, darkmasked):
    """Update light mask tab with image 'lightmasked' and dark mask tab with image 'darkmasked'."""
    if self.opentabs:
      self.app.mainwindow.update_image("Light mask", lightmasked)
      self.app.mainwindow.update_image("Dark mask", darkmasked)
    else:
      self.app.mainwindow.append_image("Light mask", lightmasked)
      self.app.mainwindow.append_image("Dark mask", darkmasked)
      self.opentabs = True
