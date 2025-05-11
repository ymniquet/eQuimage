# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.7.0 / 2025.05.11
# GUI updatedi (+).

"""Blend tool."""

from ..gtk.customwidgets import Align, Label, HBox, VBox, Grid, CheckButton, HScale
from ..misc.imagechooser import ImageChooser
from ..toolmanager import BaseToolWindow
import numpy as np

class BlendTool(BaseToolWindow):
  """Blend tool window class."""

  _action_ = "Blending images..."

  _help_ = """Blend the current image IMG with an other image BLEND of your choice:

    OUT = f*BLEND+(1-f)*IMG

The mixing factor f can be tuned independently for each red/blue/green channel (untick the "bind RGB channels" checkbox).
If a checkbox "zero is transparent" is ticked, the zero pixels in that channel of BLEND are treated as transparent (not blended with the current image)."""

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Blend images"): return False
    wbox = VBox()
    self.window.add(wbox)
    wbox.pack("Choose image to blend with:")
    self.widgets.chooser = ImageChooser(self.app, self.window, wbox, callback = lambda row, image: self.update("image"))
    self.message = Label(" ")
    wbox.pack(self.message)
    hbox = HBox()
    wbox.pack(hbox)
    hbox.pack("Mixing factors:", expand = True, fill = True)
    self.widgets.bindbutton = CheckButton(label = "Bind RGB channels")
    self.widgets.bindbutton.set_active(True)
    self.widgets.bindbutton.connect("toggled", lambda button: self.update(0))
    hbox.pack(self.widgets.bindbutton)
    grid = Grid()
    wbox.pack(grid)
    self.widgets.mixingscales = []
    self.widgets.zerobuttons = []
    for channel, label in ((0, "Red:"), (1, "Green:"), (2, "Blue:")):
      mixingscale = HScale(0., -1., 2., .01, digits = 2, marks = [-1., 0., 1., 2.], length = 320)
      mixingscale.channel = channel
      mixingscale.connect("value-changed", lambda scale: self.update(scale.channel))
      self.widgets.mixingscales.append(mixingscale)
      zerobutton = CheckButton(label = "Zero is transparent")
      zerobutton.channel = channel
      zerobutton.connect("toggled", lambda button: self.update(button.channel))
      self.widgets.zerobuttons.append(zerobutton)
      grid.attach(Label(label, halign = Align.END), 0, channel)
      grid.attach(mixingscale, 1, channel)
      grid.attach(zerobutton, 2, channel)
    wbox.pack(self.tool_control_buttons())
    self.start(identity = True)
    return True

  def get_params(self):
    """Return tool parameters."""
    row = self.widgets.chooser.get_selected_row()
    mixings = tuple(self.widgets.mixingscales[channel].get_value() for channel in range(3))
    zeros = tuple(self.widgets.zerobuttons[channel].get_active() for channel in range(3))
    return row, mixings, zeros

  def set_params(self, params):
    """Set tool parameters 'params'."""
    row, mixings, zeros = params
    self.widgets.chooser.set_selected_row(row)
    for channel in range(3):
      self.widgets.mixingscales[channel].set_value_block(mixings[channel])
      self.widgets.zerobuttons[channel].set_active_block(zeros[channel])
    if mixings[1] != mixings[0] or mixings[2] != mixings[0]: self.widgets.bindbutton.set_active_block(False)
    if zeros[1] != zeros[0] or zeros[2] != zeros[0]: self.widgets.bindbutton.set_active_block(False)
    self.update("all")

  def run(self, params):
    """Run tool for parameters 'params'."""
    row, mixings, zeros = params
    if row < 0: return params, False
    selection = self.widgets.chooser.get_image(row)
    if selection.size() != self.reference.size():
      self.set_message("<span foreground='red'>Can not blend images with different sizes.</span>")
      return params, False
    self.set_message()
    for channel in range(3):
      mixing = mixings[channel]
      zero = zeros[channel]
      blended = mixing*selection.rgb[channel]+(1.-mixing)*self.reference.rgb[channel]
      if zero:
        self.image.rgb[channel] = np.where(selection.rgb[channel] > 0., blended, self.reference.rgb[channel])
      else:
        self.image.rgb[channel] = blended
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    row, mixings, zeros = params
    if row < 0: return None
    operation = f"Blend({self.widgets.chooser.get_image_tag(row)}"
    for channel in range(3):
      key = ["R", "G", "B"][channel]
      decoration = "'" if zeros[channel] else ""
      operation += f", {key}{decoration} = {mixings[channel]:.2f}"
    operation += ")"
    return operation

  # Update widgets.

  def update(self, changed):
    """Update widgets on change of 'changed'."""
    if changed in [0, 1, 2]:
      if self.widgets.bindbutton.get_active():
        mixing = self.widgets.mixingscales[changed].get_value()
        transparent = self.widgets.zerobuttons[changed].get_active()
        for channel in range(3):
          self.widgets.mixingscales[channel].set_value_block(mixing)
          self.widgets.zerobuttons[channel].set_active_block(transparent)
    self.reset_polling(self.get_params()) # Expedite main window update.

  def set_message(self, message = " "):
    """Set message 'message'."""
    self.message.set_markup(message)
