# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 2023.10 *

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .gtk.customwidgets import SpinButton
from .tools import BaseToolWindow

"""Color balance tool."""

class ColorBalanceTool(BaseToolWindow):
  """Color balance tool class."""

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Color balance"): return
    wbox = Gtk.VBox(spacing = 16)
    self.window.add(wbox)
    hbox = Gtk.HBox(spacing = 8)
    wbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Red:"), False, False, 0)
    self.widgets.redspin = SpinButton(1., 0., 2., 0.01)
    hbox.pack_start(self.widgets.redspin, False, False, 0)
    hbox.pack_start(Gtk.Label(label = 8*" "+"Green:"), False, False, 0)
    self.widgets.greenspin = SpinButton(1., 0., 2., 0.01)
    hbox.pack_start(self.widgets.greenspin, False, False, 0)
    hbox.pack_start(Gtk.Label(label = 8*" "+"Blue:"), False, False, 0)
    self.widgets.bluespin = SpinButton(1., 0., 2., 0.01)
    hbox.pack_start(self.widgets.bluespin, False, False, 0)
    wbox.pack_start(self.apply_cancel_reset_close_buttons(onthefly = self.app.colorblotf), False, False, 0)
    self.toolparams = self.get_params()
    if self.app.colorblotf:
      self.connect_reset_polling(self.widgets.redspin  , "value-changed")
      self.connect_reset_polling(self.widgets.greenspin, "value-changed")
      self.connect_reset_polling(self.widgets.bluespin , "value-changed")
      self.start_polling(self.app.polltime)
    self.window.show_all()

  def get_params(self):
    """Return tool parameters."""
    return self.widgets.redspin.get_value(), self.widgets.greenspin.get_value(), self.widgets.bluespin.get_value()

  def reset(self, *args, **kwargs):
    """Reset tool parameters."""
    red, green, blue = self.toolparams
    self.widgets.redspin.set_value(red)
    self.widgets.greenspin.set_value(green)
    self.widgets.bluespin.set_value(blue)

  def run(self, *args, **kwargs):
    """Run tool."""
    red, green, blue = self.get_params()
    self.image.copy_from(self.reference)
    self.image.color_balance(red, green, blue)
    return red, green, blue

  def apply(self, *args, **kwargs):
    """Apply tool."""
    print("Balancing colors...")
    super().apply()

  def operation(self):
    """Return tool operation string."""
    if not self.transformed: return None
    red, green, blue = self.toolparams
    return f"ColorBalance(R = {red:.2f}, G = {green:.2f}, B = {blue:.2f})"

  def cancel(self, *args, **kwargs):
    """Cancel tool."""
    super().cancel()
    self.widgets.redspin.set_value(1.)
    self.widgets.greenspin.set_value(1.)
    self.widgets.bluespin.set_value(1.)
    self.toolparams = (1., 1., 1.)
    self.restart_polling() # Restart polling.
