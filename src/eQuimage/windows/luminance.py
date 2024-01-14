# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2024.01.14

"""Luminance RGB dialog."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .gtk.customwidgets import Button, SpinButton

class LuminanceRGBDialog(Gtk.Window):
  """Luminance RGB dialog class."""

  # Here we store the data, widgets & methods of this simple dialog directly in the window object.

  def __init__(self, parent, callback, rgblum):
    """Open a luminance RGB dialog for parent window 'parent', with initial
       RGB components 'rgblum'. When the apply button is pressed, close the
       dialog and call 'callback(rgblum)', where rgblum are the updated RGB
       components of the luminance."""
    super().__init__(title = "Luminance RGB",
                     transient_for = parent,
                     modal = True,
                     border_width = 16)
    wbox = Gtk.VBox(spacing = 16)
    self.add(wbox)
    hbox = Gtk.HBox(spacing = 8)
    wbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Red:"), False, False, 0)
    self.redspin = SpinButton(rgblum[0], 0., 1., 0.01)
    hbox.pack_start(self.redspin, False, False, 0)
    hbox.pack_start(Gtk.Label(label = 8*" "+"Green:"), False, False, 0)
    self.greenspin = SpinButton(rgblum[1], 0., 1., 0.01)
    hbox.pack_start(self.greenspin, False, False, 0)
    hbox.pack_start(Gtk.Label(label = 8*" "+"Blue:"), False, False, 0)
    self.bluespin = SpinButton(rgblum[2], 0., 1., 0.01)
    hbox.pack_start(self.bluespin, False, False, 0)
    hbox = Gtk.HButtonBox(homogeneous = True, spacing = 16, halign = Gtk.Align.START)
    wbox.pack_start(hbox, False, False, 0)
    applybutton = Button(label = "OK")
    applybutton.connect("clicked", self.apply)
    hbox.pack_start(applybutton, False, False, 0)
    humanbutton = Button(label = "Human vision")
    humanbutton.connect("clicked", self.set_human_vision)
    hbox.pack_start(humanbutton, False, False, 0)
    uniformbutton = Button(label = "Uniform RGB")
    uniformbutton.connect("clicked", self.set_uniform_rgb)
    hbox.pack_start(uniformbutton, False, False, 0)
    cancelbutton = Button(label = "Cancel")
    cancelbutton.connect("clicked", lambda button: self.destroy())
    hbox.pack_start(cancelbutton, False, False, 0)
    self.callback = callback
    self.show_all()

  def apply(self, *args, **kwargs):
    """Apply luminance RGB settings."""
    red = self.redspin.get_value()
    green = self.greenspin.get_value()
    blue = self.bluespin.get_value()
    total = red+green+blue
    if total <= 0.: return
    rgblum = (red/total, green/total, blue/total)
    self.callback(rgblum)
    self.destroy()

  def set_human_vision(self, *args, **kwargs):
    """Set human vision luminance RGB components."""
    self.redspin.set_value(0.3)
    self.greenspin.set_value(0.6)
    self.bluespin.set_value(0.1)

  def set_uniform_rgb(self, *args, **kwargs):
    """Set uniform luminance RGB components."""
    self.redspin.set_value(1./3.)
    self.greenspin.set_value(1./3.)
    self.bluespin.set_value(1./3.)
