# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.3.0 / 2024.02.11

"""Total variation filter tool."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
from .gtk.customwidgets import RadioButton, HScaleSpinButton
from .tools import BaseToolWindow
from skimage.restoration import denoise_tv_chambolle, denoise_tv_bregman

class TotalVariationFilterTool(BaseToolWindow):
  """Total variation filter tool class."""

  __action__ = "Filtering total variation..."

  __onthefly__ = False # This transformation can not be applied on the fly.

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Total variation filter"): return False
    wbox = Gtk.VBox(spacing = 16)
    self.window.add(wbox)
    self.widgets.weightscale = HScaleSpinButton(.1, 0., 1., .001, digits = 3, length = 320, expand = False)
    wbox.pack_start(self.widgets.weightscale.layout2("Weight:"), False, False, 0)
    hbox = Gtk.HBox(spacing = 8)
    wbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Algorithm:"), False, False, 0)
    self.widgets.chambollebutton = RadioButton.new_with_label_from_widget(None, "Chambolle")
    hbox.pack_start(self.widgets.chambollebutton, False, False, 0)
    self.widgets.bregmanbutton = RadioButton.new_with_label_from_widget(self.widgets.chambollebutton, "Split Bregman")
    hbox.pack_start(self.widgets.bregmanbutton, False, False, 0)
    wbox.pack_start(self.tool_control_buttons(), False, False, 0)
    self.start(identity = False)
    return True

  def get_params(self):
    """Return tool parameters."""
    algorithm = "Chambolle" if self.widgets.chambollebutton.get_active() else "Bregman"
    weight = self.widgets.weightscale.get_value()
    return algorithm, weight

  def set_params(self, params):
    """Set tool parameters 'params'."""
    algorithm, weight = params
    if algorithm == "Chambolle":
      self.widgets.chambollebutton.set_active(True)
    else:
      self.widgets.bregmanbutton.set_active(True)
    self.widgets.weightscale.set_value(weight)

  def run(self, params):
    """Run tool for parameters 'params'."""
    algorithm, weight = params
    if weight <= 0.: return params, False
    if algorithm == "Chambolle":
      self.image.rgb = denoise_tv_chambolle(self.reference.rgb, channel_axis = 0, weight = weight)
    else:
      self.image.rgb = denoise_tv_bregman(self.reference.rgb, channel_axis = 0, weight = 1./(2.*weight))
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    algorithm, weight = params
    return f"TotalVariationFilter(algorithm = {algorithm}, weight = {weight})"
