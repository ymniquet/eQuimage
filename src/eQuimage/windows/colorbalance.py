# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 2023.09 *

"""Color balance tool."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .gtk.customwidgets import SpinButton
from .tools import BaseToolWindow
from collections import OrderedDict as OD

class ColorBalanceTool(BaseToolWindow):
  """Color balance tool class."""

  def open(self, image):
    """Open tool window for image 'image'."""
    if self.opened: return
    if not self.app.mainwindow.opened: return
    super().open(image, "Color balance")
    vbox = Gtk.VBox(spacing = 16)
    self.window.add(vbox)
    hbox = Gtk.HBox(spacing = 8)
    vbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Red:"), False, False, 0)
    self.widgets.redspin = SpinButton(1., 0., 2., 0.01)
    hbox.pack_start(self.widgets.redspin, False, False, 0)
    hbox.pack_start(Gtk.Label(label = 8*" "+"Green:"), False, False, 0)
    self.widgets.greenspin = SpinButton(1., 0., 2., 0.01)
    hbox.pack_start(self.widgets.greenspin, False, False, 0)
    hbox.pack_start(Gtk.Label(label = 8*" "+"Blue:"), False, False, 0)
    self.widgets.bluespin = SpinButton(1., 0., 2., 0.01)
    hbox.pack_start(self.widgets.bluespin, False, False, 0)
    vbox.pack_start(self.apply_cancel_reset_close_buttons(), False, False, 0)
    self.app.mainwindow.set_images(OD(Image = self.image, Reference = self.reference), reference = "Reference")
    self.resetparams = (1., 1., 1.)
    self.window.show_all()

  def reset(self, *args, **kwargs):
    """Reset tool."""
    red, green, blue = self.resetparams
    self.widgets.redspin.set_value(red)
    self.widgets.greenspin.set_value(green)
    self.widgets.bluespin.set_value(blue)

  def apply(self, *args, **kwargs):
    """Apply tool."""
    red = self.widgets.redspin.get_value()
    green = self.widgets.greenspin.get_value()
    blue = self.widgets.bluespin.get_value()
    self.image.copy_from(self.reference)
    print("Balancing colors...")    
    self.image.color_balance(red, green, blue)
    self.app.mainwindow.update_image("Image", self.image)
    self.operation = f"ColorBalance(R = {red:.2f}, G = {green:.2f}, B = {blue:.2f})"
    self.resetparams = (red, green, blue)
    self.widgets.cancelbutton.set_sensitive(True)

  def cancel(self, *args, **kwargs):
    """Cancel tool."""
    if self.operation is None: return
    self.image.copy_from(self.reference)
    self.app.mainwindow.update_image("Image", self.image)
    self.widgets.redspin.set_value(1.)
    self.widgets.greenspin.set_value(1.)
    self.widgets.bluespin.set_value(1.)
    self.operation = None
    self.resetparams = (1., 1., 1.)
    self.widgets.cancelbutton.set_sensitive(False)
