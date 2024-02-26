# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.4.0 / 2024.02.26

"""Contrast Limited Adaptive Histogram Equalization (CLAHE) tool."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
from .gtk.customwidgets import RadioButton, SpinButton, HScale
from .tools import BaseToolWindow
from ..imageprocessing import imageprocessing
from skimage.exposure import equalize_adapthist
import numpy as np

class CLAHETool(BaseToolWindow):
  """Contrast Limited Adaptive Histogram Equalization (CLAHE) tool class."""

  __action__ = "Running Contrast Limited Adaptive Histogram Equalization (CLAHE)..."

  __onthefly__ = False # This transformation can not be applied on the fly.

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Contrast Limited Adaptive Histogram Equalization (CLAHE)"): return False
    wbox = Gtk.VBox(spacing = 16)
    self.window.add(wbox)
    hbox = Gtk.HBox(spacing = 8)
    wbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Channel:"), False, False, 0)
    self.widgets.valuebutton = RadioButton.new_with_label_from_widget(None, "HSV value")
    hbox.pack_start(self.widgets.valuebutton, False, False, 0)
    self.widgets.lumabutton = RadioButton.new_with_label_from_widget(self.widgets.valuebutton, "Luma")
    hbox.pack_start(self.widgets.lumabutton, False, False, 0)
    hbox = Gtk.HBox(spacing = 8)
    wbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Kernel size: ", halign = Gtk.Align.START), False, False, 0)
    self.widgets.sizebutton = SpinButton(15., 1., 100., 1., digits = 0)
    hbox.pack_start(self.widgets.sizebutton, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "% image width and height", halign = Gtk.Align.START), False, False, 0)
    hbox = Gtk.HBox(spacing = 8)
    wbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Clip limit:"), False, False, 0)
    self.widgets.clipscale = HScale(.5, 0., 1., 0.01, digits = 2, marks = [0., 1.], length = 320, expand = False)
    hbox.pack_start(self.widgets.clipscale, False, False, 0)
    wbox.pack_start(self.tool_control_buttons(), False, False, 0)
    self.start(identity = False)
    return True

  def get_params(self):
    """Return tool parameters."""
    channel = "V" if self.widgets.valuebutton.get_active() else "L"
    return channel, self.widgets.sizebutton.get_value(), self.widgets.clipscale.get_value(), imageprocessing.get_rgb_luma()

  def set_params(self, params):
    """Set tool parameters 'params'."""
    channel, size, clip, rgbluma = params
    if channel == "V":
      self.widgets.valuebutton.get_active(True)
    else:
      self.widgets.lumabutton.set_active(True)
    self.widgets.sizebutton.set_value(size)
    self.widgets.clipscale.set_value(clip)

  def run(self, params):
    """Run tool for parameters 'params'."""
    channel, size, clip, rgbluma = params
    if size <= 0. or clip <= 0.: return params, False
    width, height = self.reference.size()
    kwidth = max(int(round(size*width/100.)), 3)
    kheight = max(int(round(size*height/100.)), 3)
    if channel == "V":
      self.image.set_image(equalize_adapthist(self.reference.rgbf(), kernel_size = (kheight, kwidth), clip_limit = clip), channel = -1, copy = True)
    else:
      ref = self.reference.luma()
      img = equalize_adapthist(ref, kernel_size = (kheight, kwidth), clip_limit = clip)
      self.image.copy_image_from(self.reference)
      self.image.scale_pixels(ref, img)
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    channel, size, clip, rgbluma = params
    if channel == "L": channel = f"L({rgbluma[0]:.2f}, {rgbluma[1]:.2f}, {rgbluma[2]:.2f})"
    return f"CLAHE(channel = {channel}, size = {size:.0f}%, clip = {clip:.2f})"
