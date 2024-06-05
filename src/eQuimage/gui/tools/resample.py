# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.5.1 / 2024.06.05
# GUI updated.

"""Resampling tool."""

from ..gtk.customwidgets import HBox, VBox, Label, SpinButton, HScaleSpinButton
from ..base import ErrorDialog
from ..toolmanager import BaseToolWindow
from ...imageprocessing import imageprocessing

class ResampleTool(BaseToolWindow):
  """Resampling tool."""

  _action_ = "Resampling image..."

  _onthefly_ = False # This transformation can not be applied on the fly.

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Resampling image"): return False
    wbox = VBox()
    self.window.add(wbox)
    self.rwidth, self.rheight = self.reference.size()
    self.aratio = self.rwidth/self.rheight
    wbox.pack(Label(f"Original image size: {self.rwidth}x{self.rheight} pixels"))
    hbox = HBox()
    wbox.pack(hbox)
    hbox.pack(Label("Target image size:"))
    self.widgets.widthbutton = SpinButton(self.rwidth, self.rwidth//4, 4*self.rwidth, 1., digits = 0)
    self.widgets.widthbutton.connect("value-changed", lambda button: self.update("width"))
    hbox.pack(self.widgets.widthbutton)
    hbox.pack(Label("x"))
    self.widgets.heightbutton = SpinButton(self.rheight, self.rheight//4, 4*self.rheight, 1., digits = 0)
    self.widgets.heightbutton.connect("value-changed", lambda button: self.update("height"))
    hbox.pack(self.widgets.heightbutton)
    hbox.pack(Label("pixels"))
    self.widgets.scalescale = HScaleSpinButton(1., .25, 4., .1, digits = 4, length = 320, expand = True)
    self.widgets.scalescale.connect("value-changed", lambda button: self.update("scale"))
    wbox.pack(self.widgets.scalescale.layout2(label = "Scale:"))
    wbox.pack(self.tool_control_buttons(model = "applyonce"))
    self.start(identity = False)
    return True

  def get_params(self):
    """Return tool parameters."""
    return int(round(self.widgets.widthbutton.get_value())), int(round(self.widgets.heightbutton.get_value()))

  def set_params(self, params):
    """Set tool parameters 'params'."""
    width, height = params
    self.widgets.widthbutton.set_value(width)

  def run(self, params):
    """Run tool for parameters 'params'."""

    def Error(message):
      """Open error message dialog."""
      ErrorDialog(self.window, message)
      return False

    width, height = params
    try:
      self.image = self.reference.resize(width, height, inplace = False)
    except Exception as err:
      self.queue_gui_mainloop(Error, str(err))
      return (self.rwidth, self.rheight), False
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    width, height = params
    return f"Resample(size = {width}x{height} pixels)"

 # Update widgets.

  def update(self, changed):
    """Update widgets."""
    if changed == "width":
      width = round(self.widgets.widthbutton.get_value())
      height = round(width/self.aratio)
      scale = width/self.rwidth
    elif changed == "height":
      height = round(self.widgets.heightbutton.get_value())
      width = round(height*self.aratio)
      scale = width/self.rwidth
    else:
      scale = self.widgets.scalescale.get_value()
      width = round(self.rwidth*scale)
      height = round(self.rheight*scale)
    self.widgets.widthbutton.set_value_block(width)
    self.widgets.heightbutton.set_value_block(height)
    self.widgets.scalescale.set_value_block(scale)
