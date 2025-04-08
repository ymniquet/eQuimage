# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.6.1 / 2024.09.01
# GUI updated.

"""Contrast Limited Adaptive Histogram Equalization (CLAHE) tool."""

from ..gtk.customwidgets import HBox, VBox, CheckButton, RadioButtons, HScaleSpinButton
from ..toolmanager import BaseToolWindow
from ...imageprocessing import imageprocessing
from skimage.exposure import equalize_adapthist

class CLAHETool(BaseToolWindow):
  """Contrast Limited Adaptive Histogram Equalization (CLAHE) tool class."""

  _action_ = "Running Contrast Limited Adaptive Histogram Equalization (CLAHE)..."

  _onthefly_ = False # This transformation can not be applied on the fly.

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Contrast Limited Adaptive Histogram Equalization (CLAHE)"): return False
    wbox = VBox()
    self.window.add(wbox)
    self.widgets.highlightsbutton = CheckButton(label = "Protect highlights")
    self.widgets.highlightsbutton.set_sensitive(False)
    self.widgets.channelbuttons = RadioButtons(("V", "HSV value"), ("L", "Luma"))
    self.widgets.channelbuttons.buttons["L"].connect("toggled", \
      lambda button: self.widgets.highlightsbutton.set_sensitive(self.widgets.channelbuttons.get_selected() == "L"))
    wbox.pack(self.widgets.channelbuttons.hbox(prepend = "Channel:", append = self.widgets.highlightsbutton))
    self.widgets.sizebutton = HScaleSpinButton(12.5, 1., 99., .01, digits = 2, length = 480)
    wbox.pack(self.widgets.sizebutton.layout2("Kernel size (% image width and height):"))
    self.widgets.clipscale = HScaleSpinButton(.01, 0., .1, .0001, digits = 4, length = 480)
    wbox.pack(self.widgets.clipscale.layout2("Clip limit:"))
    wbox.pack(self.tool_control_buttons())
    self.start(identity = False)
    return True

  def get_params(self):
    """Return tool parameters."""
    return self.widgets.channelbuttons.get_selected(), self.widgets.sizebutton.get_value(), self.widgets.clipscale.get_value(), \
           self.widgets.highlightsbutton.get_active(), imageprocessing.get_rgb_luma()

  def set_params(self, params):
    """Set tool parameters 'params'."""
    channel, size, clip, highlights, rgbluma = params
    self.widgets.channelbuttons.set_selected(channel)
    self.widgets.sizebutton.set_value(size)
    self.widgets.clipscale.set_value(clip)
    self.widgets.highlightsbutton.set_active(highlights)

  def run(self, params):
    """Run tool for parameters 'params'."""
    channel, size, clip, highlights, rgbluma = params
    if size <= 0. or clip <= 0.: return params, False
    width, height = self.reference.size()
    kwidth = max(int(round(size*width/100.)), 3)
    kheight = max(int(round(size*height/100.)), 3)
    nbins = min(2**self.app.get_color_depth(), 1024)
    print(f"Using {nbins} bins...")
    reference = self.reference.clone()
    reference.clip() # Clip before CLAHE.
    if channel == "V":
      self.image.set_image(equalize_adapthist(reference.rgbf_view(), kernel_size = (kheight, kwidth), clip_limit = clip, nbins = nbins), channels = -1)
    else:
      ref = reference.luma()
      img = equalize_adapthist(ref, kernel_size = (kheight, kwidth), clip_limit = clip, nbins = nbins)
      self.image.copy_image_from(reference)
      self.image.scale_pixels(ref, img)
      if highlights: self.image.protect_highlights()
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    channel, size, clip, highlights, rgbluma = params
    optstring = ""
    if channel == "L":
      channel = f"L({rgbluma[0]:.2f}, {rgbluma[1]:.2f}, {rgbluma[2]:.2f})"
      if highlights: optstring = ", protect highlights"
    return f"CLAHE(channel = {channel}, size = {size:.2f}%, clip = {clip:.4f}{optstring})"
