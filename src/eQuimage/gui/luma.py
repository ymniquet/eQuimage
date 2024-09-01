# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.6.0 / 2024.09.01
# GUI updated.

"""Luma RGB dialog."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .gtk.customwidgets import HBox, VBox, HButtonBox, Button, SpinButton

class LumaRGBDialog(Gtk.Window):
  """Luma RGB dialog class."""

  # Here we store the data, widgets & methods of this simple dialog directly in the window object.

  def __init__(self, parent, callback, rgbluma):
    """Open a luma RGB dialog for parent window 'parent', with initial
       RGB components 'rgbluma'. When the apply button is pressed, close the
       dialog and call 'callback(rgbluma)', where rgbluma are the updated RGB
       components of the luma."""
    super().__init__(title = "Luma RGB",
                     transient_for = parent,
                     modal = True,
                     border_width = 16)
    wbox = VBox()
    self.add(wbox)
    hbox = HBox()
    wbox.pack(hbox)
    self.redspin = SpinButton(rgbluma[0], 0., 1., .01, digits = 2)
    hbox.pack("Red:")
    hbox.pack(self.redspin)
    self.greenspin = SpinButton(rgbluma[1], 0., 1., .01, digits = 2)
    hbox.pack(8*" "+"Green:")
    hbox.pack(self.greenspin)
    self.bluespin = SpinButton(rgbluma[2], 0., 1., .01, digits = 2)
    hbox.pack(8*" "+"Blue:")
    hbox.pack(self.bluespin)
    hbox = HButtonBox()
    wbox.pack(hbox)
    applybutton = Button(label = "OK")
    applybutton.connect("clicked", self.apply)
    hbox.pack(applybutton)
    humanbutton = Button(label = "Human")
    humanbutton.connect("clicked", self.set_human_vision)
    hbox.pack(humanbutton)
    uniformbutton = Button(label = "Uniform")
    uniformbutton.connect("clicked", self.set_uniform_rgb)
    hbox.pack(uniformbutton)
    cancelbutton = Button(label = "Cancel")
    cancelbutton.connect("clicked", lambda button: self.destroy())
    hbox.pack(cancelbutton)
    self.callback = callback
    self.show_all()

  def apply(self, *args, **kwargs):
    """Apply luma RGB settings."""
    red = self.redspin.get_value()
    green = self.greenspin.get_value()
    blue = self.bluespin.get_value()
    total = red+green+blue
    if total <= 0.: return
    rgbluma = (red/total, green/total, blue/total)
    self.callback(rgbluma)
    self.destroy()

  def set_human_vision(self, *args, **kwargs):
    """Set human vision luma RGB components."""
    self.redspin.set_value(.3)
    self.greenspin.set_value(.6)
    self.bluespin.set_value(.1)

  def set_uniform_rgb(self, *args, **kwargs):
    """Set uniform luma RGB components."""
    self.redspin.set_value(1./3.)
    self.greenspin.set_value(1./3.)
    self.bluespin.set_value(1./3.)
