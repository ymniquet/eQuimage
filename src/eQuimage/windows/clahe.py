# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.3.0 / 2024.01.29

"""Contrast Limited Adaptive Histogram Equalization (CLAHE) tool."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
from .gtk.customwidgets import SpinButton, HScale
from .tools import BaseToolWindow
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
    return self.widgets.sizebutton.get_value(), self.widgets.clipscale.get_value()

  def set_params(self, params):
    """Set tool parameters 'params'."""
    size, clip = params
    self.widgets.sizebutton.set_value(size)
    self.widgets.clipscale.set_value(clip)

  def run(self, params):
    """Run tool for parameters 'params'."""
    size, clip = params
    if size <= 0. or clip <= 0.: return params, False
    width, height = self.reference.size()
    kwidth = max(int(round(size*width/100.)), 3)
    kheight = max(int(round(size*height/100.)), 3)
    self.image.set_image(equalize_adapthist(self.reference.rgbf(), kernel_size = (kheight, kwidth), clip_limit = clip), channel = -1, copy = True)
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    size, clip = params
    return f"CLAHE(size = {size:.0f}%, clip = {clip:.2f})"
