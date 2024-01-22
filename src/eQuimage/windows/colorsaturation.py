# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2024.01.14

"""Color saturation tool."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .gtk.customwidgets import CheckButton, HScale
from .tools import BaseToolWindow
import numpy as np

class ColorSaturationTool(BaseToolWindow):
  """Color saturation tool class."""

  __action__ = "Tuning color saturation..."

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Color saturation"): return False
    self.reference.hsv = self.reference.rgb_to_hsv()
    wbox = Gtk.VBox(spacing = 16)
    self.window.add(wbox)
    grid = Gtk.Grid(column_spacing = 8)
    wbox.pack_start(grid, False, False, 0)
    self.widgets.bindbutton = CheckButton(label = "Bind hues")
    self.widgets.bindbutton.set_active(True)
    self.widgets.bindbutton.connect("toggled", lambda scale: self.update(0))
    grid.add(self.widgets.bindbutton)
    self.widgets.satscales = []
    for hue, label in ((0, "Red:"), (1, "Yellow:"), (2, "Green:"), (3, "Cyan:"), (4, "Blue:"), (5, "Magenta:")):
      satscale = HScale(0., -1., 1., 0.001, digits = 3, length = 384)
      satscale.hue = hue
      satscale.connect("value-changed", lambda scale: self.update(scale.hue))
      if not self.widgets.satscales:
        grid.attach_next_to(satscale, self.widgets.bindbutton   , Gtk.PositionType.BOTTOM, 1, 1)
      else:
        grid.attach_next_to(satscale, self.widgets.satscales[-1], Gtk.PositionType.BOTTOM, 1, 1)
      self.widgets.satscales.append(satscale)
      grid.attach_next_to(Gtk.Label(label = label, halign = Gtk.Align.END), self.widgets.satscales[-1], Gtk.PositionType.LEFT, 1, 1)
    wbox.pack_start(self.tool_control_buttons(), False, False, 0)
    self.start(identity = True)
    return True

  def get_params(self):
    """Return tool parameters."""
    return tuple(self.widgets.satscales[hue].get_value() for hue in range(6))

  def set_params(self, params):
    """Set tool parameters 'params'."""
    for hue in range(6):
      self.widgets.satscales[hue].set_value_block(params[hue])
    if np.any(np.array(params) != params[0]): self.widgets.bindbutton.set_active_block(False)

  def run(self, params):
    """Run tool for parameters 'params'."""
    transformed = False
    if np.all(np.array(params) == params[0]):
      dsat = params[0]
      if dsat != 0:    
        transformed = True    
        hsv = self.reference.hsv.copy()
        hsv[:, :, 1] = np.clip(self.reference.hsv[:, :, 1]+dsat, 0., 1.)
        self.image.hsv_to_rgb(hsv)
    else:
      hsv = self.reference.hsv.copy()      
      for hue in range(6):
        dsat = params[hue]
        if dsat == 0: continue
        transformed = True  
        hsv[:, :, 1] = np.clip(self.reference.hsv[:, :, 1]+dsat, 0., 1.)        
      if transformed: self.image.hsv_to_rgb(hsv)        
    return params, transformed

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    tags = ["R", "Y", "G", "C", "B", "M"]
    operation = "ColorSaturation("
    for hue in range(6):
      operation += f"{tags[hue]} = {params[hue]:.3f}"
      operation += ", " if hue < 5 else ")"
    return operation

  # Update scales.

  def update(self, changed):
    """Update scales."""
    if self.widgets.bindbutton.get_active():
      dsat = self.widgets.satscales[changed].get_value()
      for hue in range(6):
        self.widgets.satscales[hue].set_value_block(dsat)
    self.reset_polling(self.get_params()) # Expedite main window update.
