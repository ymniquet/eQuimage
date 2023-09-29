# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 2023.09 *

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .gtk.customwidgets import SpinButton
from .tools import BaseToolWindow
from collections import OrderedDict as OD

"""Color balance tool."""

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
    vbox.pack_start(self.apply_cancel_reset_close_buttons(onthefly = self.app.colorotf), False, False, 0)
    self.app.mainwindow.set_images(OD(Image = self.image, Reference = self.reference), reference = "Reference")
    self.toolparams = (1., 1., 1.)
    if self.app.colorotf:
      self.signals.append((self.widgets.redspin, self.widgets.redspin.connect("button-release-event", self.update)))
      self.signals.append((self.widgets.redspin, self.widgets.redspin.connect("key-release-event", self.update)))
      self.signals.append((self.widgets.greenspin, self.widgets.greenspin.connect("button-release-event", self.update)))
      self.signals.append((self.widgets.greenspin, self.widgets.greenspin.connect("key-release-event", self.update)))
      self.signals.append((self.widgets.bluespin, self.widgets.bluespin.connect("button-release-event", self.update)))
      self.signals.append((self.widgets.bluespin, self.widgets.bluespin.connect("key-release-event", self.update)))
    self.window.show_all()

  def reset(self, *args):
    """Reset tool."""
    red, green, blue = self.toolparams
    self.widgets.redspin.set_value(red)
    self.widgets.greenspin.set_value(green)
    self.widgets.bluespin.set_value(blue)

  def apply(self, *args):
    """Apply tool."""
    red = self.widgets.redspin.get_value()
    green = self.widgets.greenspin.get_value()
    blue = self.widgets.bluespin.get_value()
    print("Balancing colors...")
    self.image.copy_from(self.reference)
    self.image.color_balance(red, green, blue)
    self.app.mainwindow.update_image("Image", self.image)
    self.transformed = True
    self.toolparams = (red, green, blue)
    self.widgets.cancelbutton.set_sensitive(True)

  def update(self, *args):
    """Apply tool on the fly."""
    red = self.widgets.redspin.get_value()
    green = self.widgets.greenspin.get_value()
    blue = self.widgets.bluespin.get_value()
    self.image.color_balance(red/self.toolparams[0], green/self.toolparams[1], blue/self.toolparams[2]) # Incremental adjustment.
    self.app.mainwindow.update_image("Image", self.image)
    self.transformed = True
    self.toolparams = (red, green, blue)
    self.widgets.cancelbutton.set_sensitive(True)

  def operation(self):
    """Return tool operation string."""
    if not self.transformed: return None
    return f"ColorBalance(R = {self.toolparams[0]:.2f}, G = {self.toolparams[1]:.2f}, B = {self.toolparams[2]:.2f})"

  def cancel(self, *args):
    """Cancel tool."""
    if not self.transformed: return
    self.block_all_signals() # Block all signals while restoring original image and tool params.
    self.image.copy_from(self.reference)
    self.app.mainwindow.update_image("Image", self.image)
    self.transformed = False
    self.widgets.redspin.set_value(1.)
    self.widgets.greenspin.set_value(1.)
    self.widgets.bluespin.set_value(1.)
    self.toolparams = (1., 1., 1.)
    self.widgets.cancelbutton.set_sensitive(False)
    self.unblock_all_signals() # Unblock signals.
