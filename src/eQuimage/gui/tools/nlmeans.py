# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.4.0 / 2024.02.26
# GUI updated.

"""Non-local means filter tool."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
from ..gtk.customwidgets import HBox, VBox, HScaleSpinButton
from ..toolmanager import BaseToolWindow
from skimage.restoration import denoise_nl_means

class NonLocalMeansFilterTool(BaseToolWindow):
  """Non-local means filter tool class."""

  __action__ = "Applying non-local means filter..."

  __onthefly__ = False # This transformation can not be applied on the fly.

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Non-local means filter"): return False
    wbox = VBox()
    self.window.add(wbox)
    self.widgets.psizescale = HScaleSpinButton(7., 1., 25., 1., digits = 0, length = 320, expand = False)
    wbox.pack(self.widgets.psizescale.layout2("Patch size (pixels):"))
    self.widgets.pdistscale = HScaleSpinButton(11., 1., 50., 1., digits = 0, length = 320, expand = False)
    wbox.pack(self.widgets.pdistscale.layout2("Patch distance (pixels):"))
    self.widgets.cutoffscale = HScaleSpinButton(.1, 0., .2, .001, digits = 3, length = 320, expand = False)
    wbox.pack(self.widgets.cutoffscale.layout2("Cut-off (gray levels):"))
    wbox.pack(self.tool_control_buttons())
    self.start(identity = False)
    return True

  def get_params(self):
    """Return tool parameters."""
    return int(round(self.widgets.psizescale.get_value())), int(round(self.widgets.pdistscale.get_value())), self.widgets.cutoffscale.get_value()

  def set_params(self, params):
    """Set tool parameters 'params'."""
    psize, pdist, cutoff = params
    self.widgets.psizescale.set_value(psize)
    self.widgets.pdistscale.set_value(pdist)
    self.widgets.cutoffscale.set_value(cutoff)

  def run(self, params):
    """Run tool for parameters 'params'."""
    psize, pdist, cutoff = params
    if psize <= 0 or pdist <= 0 or cutoff <= 0.: return params, False
    self.image.rgb = denoise_nl_means(self.reference.rgb, channel_axis = 0, patch_size = psize, patch_distance = pdist, h = cutoff)
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    psize, pdist, cutoff = params
    return f"NonLocalMeansFilter(patch size = {psize} pixels, patch distance = {pdist} pixels, cutoff = {cutoff:.3f})"
