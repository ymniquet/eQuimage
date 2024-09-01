# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.6.0 / 2024.09.01
# GUI updated.

"""Threshold mask tool."""

from ..gtk.customwidgets import HBox, VBox, RadioButtons, HScaleSpinButton
from ..toolmanager import BaseToolWindow
from ...imageprocessing import imageprocessing
from skimage.morphology import isotropic_dilation, disk
from scipy.ndimage import convolve, uniform_filter, median_filter, maximum_filter, gaussian_filter
import numpy as np

class ThresholdMaskTool(BaseToolWindow):
  """Threshold Mask tool class."""

  _action_ = "Setting-up threshold mask..."

  _onthefly_ = False # This transformation can not be applied on the fly.

  DARKCOLOR  = np.array([[.5], [0.], [.5]], dtype = imageprocessing.IMGTYPE)
  LIGHTCOLOR = np.array([[0.], [.5], [0.]], dtype = imageprocessing.IMGTYPE)

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Threshold mask"): return False
    wbox = VBox()
    self.window.add(wbox)
    self.widgets.channelbuttons = RadioButtons(("V", "HSV value"), ("L", "Luma"), ("L*", "Lightness L*"))
    wbox.pack(self.widgets.channelbuttons.hbox(prepend = "Filter channel:"))
    self.widgets.functionbuttons = RadioButtons(("gaussian", "Gaussian"), ("mean", "Mean"), ("median", "Median"), ("maximum", "Maximum"))
    wbox.pack(self.widgets.functionbuttons.hbox(prepend = "Filter function:"))
    self.widgets.radiusscale = HScaleSpinButton(8., 1., 50., 1., digits = 0, length = 480)
    wbox.pack(self.widgets.radiusscale.layout2("Filter radius (pixels):"))
    self.widgets.thresholdscale = HScaleSpinButton(0., 0., 1., .001, digits = 3, length = 480)
    wbox.pack(self.widgets.thresholdscale.layout2("Threshold:"))
    self.widgets.extendscale = HScaleSpinButton(0., 0., 100., 1., digits = 0, length = 480)
    wbox.pack(self.widgets.extendscale.layout2("Extend mask by (pixels):"))
    self.widgets.smoothscale = HScaleSpinButton(0., 0., 100., 1., digits = 0, length = 480)
    wbox.pack(self.widgets.smoothscale.layout2("Smooth mask over (pixels):"))
    wbox.pack(self.tool_control_buttons())
    self.fparams = None
    self.start(identity = False)
    return True

  def get_params(self):
    """Return tool parameters."""
    fchannel = self.widgets.channelbuttons.get_selected()
    ffunction = self.widgets.functionbuttons.get_selected()
    fradius = int(round(self.widgets.radiusscale.get_value()))
    threshold = self.widgets.thresholdscale.get_value()
    extend = int(round(self.widgets.extendscale.get_value()))
    smooth = int(round(self.widgets.smoothscale.get_value()))
    rgbluma = imageprocessing.get_rgb_luma() if fchannel == "L" else None
    return fchannel, ffunction, fradius, threshold, extend, smooth, rgbluma

  def set_params(self, params):
    """Set tool parameters 'params'."""
    fchannel, ffunction, fradius, threshold, extend, smooth, rgbluma = params
    self.widgets.channelbuttons.set_selected(fchannel)
    self.widgets.functionbuttons.set_selected(ffunction)
    self.widgets.radiusscale.set_value(fradius)
    self.widgets.thresholdscale.set_value(threshold)
    self.widgets.extendscale.set_value(extend)
    self.widgets.smoothscale.set_value(smooth)

  def run(self, params):
    """Run tool for parameters 'params'."""
    fchannel, ffunction, fradius, threshold, extend, smooth, rgbluma = params
    fparams = (fchannel, ffunction, fradius, rgbluma)
    # Compute the filter if needed.
    if fparams != self.fparams:
      if fchannel == "V":
        channel = self.reference.value()
      elif fchannel == "L":
        channel = self.reference.luma()
      else:
        channel = self.reference.srgb_lightness()/100.
      if ffunction == "gaussian":
        self.filtered = gaussian_filter(channel, sigma = fradius/3., mode = "reflect")
      elif ffunction == "mean":
        kernel = disk(fradius, dtype = imageprocessing.IMGTYPE)
        kernel /= np.sum(kernel)
        self.filtered = convolve(channel, kernel, mode = "reflect")
      elif ffunction == "median":
        self.filtered = median_filter(channel, footprint = disk(fradius), mode = "reflect")
      else:
        self.filtered = maximum_filter(channel, footprint = disk(fradius), mode = "reflect")
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
    self.queue_gui_mainloop(self.update_mask_tabs, lightmasked, darkmasked) # Thread-safe.
    # Smooth the light mask.
    mask = lightmask.astype(imageprocessing.IMGTYPE)
    if smooth > 0:
      kernel = disk(smooth, dtype = imageprocessing.IMGTYPE)
      kernel /= np.sum(kernel)
      mask = convolve(mask, kernel, mode = "reflect")
    self.image.rgb[:] = mask
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    fchannel, ffunction, fradius, threshold, extend, smooth, rgbluma = params
    if fchannel == "L": fchannel = f"L({rgbluma[0]:.2f}, {rgbluma[1]:.2f}, {rgbluma[2]:.2f})"
    return f"ThresholdMask(channel = {fchannel}, filter = {ffunction}, radius = {fradius} pixels, threshold = {threshold:.3f}, extend = {extend} pixels, smooth = {smooth} pixels)"

  def cancel(self, *args, **kwargs):
    """Cancel tool."""
    self.app.mainwindow.delete_image("Light mask", force = True, failsafe = True)
    self.app.mainwindow.delete_image("Dark mask", force = True, failsafe = True)
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
    self.app.mainwindow.update_image("Light mask", lightmasked, create = True)
    self.app.mainwindow.update_image("Dark mask", darkmasked, create = True)
