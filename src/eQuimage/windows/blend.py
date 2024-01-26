# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2024.01.14

"""Blend tool."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .gtk.customwidgets import CheckButton, HScale
from .gtk.filechoosers import ImageChooserDialog
from .base import ErrorDialog
from .tools import BaseToolWindow
from .picker import ImagePicker
import numpy as np

class BlendTool(BaseToolWindow):
  """Blend tool window class."""

  __action__ = "Blending images..."

  __onthefly__ = False # This transformation can not be applied on the fly.

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Blend images"): return False
    wbox = Gtk.VBox(spacing = 16)
    self.window.add(wbox)
    wbox.pack_start(Gtk.Label("Choose image to blend with:", halign = Gtk.Align.START), False, False, 0)
    self.widgets.picker = ImagePicker(self.app, self.window, wbox)
    hbox = Gtk.HBox(spacing = 8)
    wbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label("Mixing factors:", halign = Gtk.Align.START), False, False, 0)
    self.widgets.bindbutton = CheckButton(label = "Bind channels", halign = Gtk.Align.END)
    self.widgets.bindbutton.set_active(True)
    self.widgets.bindbutton.connect("toggled", lambda button: self.update(0))
    hbox.pack_start(self.widgets.bindbutton, True, True, 0)
    grid = Gtk.Grid(column_spacing = 8)
    wbox.pack_start(grid, False, False, 0)
    self.widgets.mixscales = []
    self.widgets.blackbuttons = []
    for channel, label in ((0, "Red:"), (1, "Green:"), (2, "Blue:")):
      mixscale = HScale(.5, 0., 1., .01, digits = 2, length = 320)
      mixscale.channel = channel
      mixscale.connect("value-changed", lambda scale: self.update(scale.channel))
      if not self.widgets.mixscales:
        grid.add(mixscale)
      else:
        grid.attach_next_to(mixscale, self.widgets.mixscales[-1], Gtk.PositionType.BOTTOM, 1, 1)
      self.widgets.mixscales.append(mixscale)
      grid.attach_next_to(Gtk.Label(label = label, halign = Gtk.Align.END), self.widgets.mixscales[-1], Gtk.PositionType.LEFT, 1, 1)
      blackbutton = CheckButton(label = "Black is transparent", halign = Gtk.Align.START)
      blackbutton.channel = channel
      blackbutton.connect("toggled", lambda button: self.update(button.channel))
      grid.attach_next_to(blackbutton, self.widgets.mixscales[-1], Gtk.PositionType.RIGHT, 1, 1)
      self.widgets.blackbuttons.append(blackbutton)
    wbox.pack_start(self.tool_control_buttons(reset = False), False, False, 0)
    self.start()
    return True

  def get_params(self):
    """Return tool parameters."""
    row = self.widgets.picker.get_selected_row()
    mixings = tuple(self.widgets.mixscales[channel].get_value() for channel in range(3))
    blacks = tuple(self.widgets.blackbuttons[channel].get_active() for channel in range(3))
    return row, mixings, blacks

  def set_params(self, params):
    """Set tool parameters 'params'."""
    row, mixings, blacks = params
    self.widgets.picker.set_selected_row(row)
    for channel in range(3):
      self.widgets.mixscales[channel].set_value(mixings[channel])
      self.widgets.blackbuttons[channel].set_active(blacks[channel])
    if mixings[1] != mixings[0] or mixings[2] != mixings[0]: self.widgets.bindbutton.set_active_block(False)
    if blacks[1] != blacks[0] or blacks[2] != blacks[0]: self.widgets.bindbutton.set_active_block(False)

  def run(self, params):
    """Run tool for parameters 'params'."""
    row, mixings, blacks = params
    if row < 0: return params, False
    selection = self.widgets.picker.get_image(row)
    if selection.size() != self.reference.size():
      ErrorDialog(self.window, "Can not blend images with different sizes.")
      return params, False
    for channel in range(3):
      mixing = mixings[channel]
      transparent = blacks[channel]
      blended = mixing*selection.rgb[channel]+(1.-mixing)*self.reference.rgb[channel]
      if transparent:
        self.image.rgb[channel] = np.where(selection.rgb[channel] > 0., blended, self.reference.rgb[channel])
      else:
        self.image.rgb[channel] = blended
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    row, mixings, blacks = params
    if row < 0: return None
    operation = f"Blend({self.widgets.picker.get_image_tag(row)}"
    for channel in range(3):
      key = ["R", "G", "B"][channel]
      decoration = "'" if blacks[channel] else ""
      operation += f", {key}{decoration} = {mixings[channel]}"
    operation += ")"
    return operation

  # Update widgets.

  def update(self, changed):
    """Update widgets on change of 'changed'."""
    if self.widgets.bindbutton.get_active():
      mixing = self.widgets.mixscales[changed].get_value()
      transparent = self.widgets.blackbuttons[changed].get_active()
      for channel in range(3):
        self.widgets.mixscales[channel].set_value_block(mixing)
        self.widgets.blackbuttons[channel].set_active(transparent)
