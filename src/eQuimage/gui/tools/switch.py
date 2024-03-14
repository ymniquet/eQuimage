# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.4.0 / 2024.02.26
# GUI updated.

"""Switch image tool."""

from ..gtk.customwidgets import HBox, VBox
from ..toolmanager import BaseToolWindow
from ..misc.imagechooser import ImageChooser

class SwitchTool(BaseToolWindow):
  """Switch tool window class."""

  __action__ = "Switching to an other image..."

  __onthefly__ = False # This tool is actually applied on the fly, but uses its own signals & callbacks to track changes.

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Switch image"): return False
    wbox = VBox()
    self.window.add(wbox)
    wbox.pack("Choose image to switch to:")
    self.widgets.chooser = ImageChooser(self.app, self.window, wbox, showtab = False, callback = lambda row, image: self.apply())
    wbox.pack(self.tool_control_buttons(model = "onthefly", reset = False))
    self.start(identity = True)
    return True

  def get_params(self):
    """Return tool parameters."""
    return self.widgets.chooser.get_selected_row()

  def set_params(self, params):
    """Set tool parameters 'params'."""
    row = params
    self.widgets.chooser.set_selected_row(row)

  def run(self, params):
    """Run tool for parameters 'params'."""
    row = params
    if row < 0: return params, False
    self.image.copy_image_from(self.widgets.chooser.get_image(row))
    #self.frame = self.image.get_frame()
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    row = params
    return f"SwitchTo({self.widgets.chooser.get_image_tag(row)})" if row >= 0 else None
