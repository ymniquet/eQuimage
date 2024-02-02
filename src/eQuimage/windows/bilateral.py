# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.3.0 / 2024.01.29

"""Bilateral filter tool."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
from .tools import BaseToolWindow
from .gtk.customwidgets import HScale
from skimage.restoration import denoise_bilateral

class BilateralFilterTool(BaseToolWindow):
  """Bilateral filter tool class."""

  __action__ = "Bilateral filtering..."

  __onthefly__ = False # This transformation can not be applied on the fly.

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Bilateral filter"): return False
    wbox = Gtk.VBox(spacing = 16)
    self.window.add(wbox)
    hbox = Gtk.HBox(spacing = 8)
    wbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "\u03c3 color:"), False, False, 0)
    self.widgets.colorscale = HScale(.05, .001, .2, .001, digits = 3, length = 320, expand = False)
    hbox.pack_start(self.widgets.colorscale, False, False, 0)
    hbox = Gtk.HBox(spacing = 8)
    wbox.pack_start(hbox, False, False, 0)    
    hbox.pack_start(Gtk.Label(label = "\u03c3 space:"), False, False, 0)
    self.widgets.spacescale = HScale(5., .2, 32., .2, digits = 1, length = 320, expand = False)
    hbox.pack_start(self.widgets.spacescale, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "pixels"), False, False, 0)    
    wbox.pack_start(self.tool_control_buttons(), False, False, 0)
    self.start(identity = False)
    return True

  def get_params(self):
    """Return tool parameters."""
    return self.widgets.colorscale.get_value(), self.widgets.spacescale.get_value()

  def set_params(self, params):
    """Set tool parameters 'params'."""
    sigcolor, sigspace = params
    self.widgets.colorscale.set_value(sigcolor)
    self.widgets.spacescale.set_value(sigspace)

  def run(self, params):
    """Run tool for parameters 'params'."""
    sigcolor, sigspace = params
    self.image.rgb = denoise_bilateral(self.reference.rgb, channel_axis = 0, sigma_color = sigcolor, sigma_spatial = sigspace)
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    sigcolor, sigspace = params
    return f"BilateralFilter(sigcolor = {sigcolor:.3f}, sigspace = {sigspace:.1f} pixels)"
