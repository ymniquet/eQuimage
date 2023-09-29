# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 2023.09 *

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
from .gtk.customwidgets import SpinButton
from .tools import BaseToolWindow
from ..imageprocessing import imageprocessing
from collections import OrderedDict as OD

"""Remove hot pixels tool."""

class RemoveHotPixelsTool(BaseToolWindow):
  """Remove hot pixels tool window class."""

  initratio = 2.

  def open(self, image):
    """Open tool window for image 'image'."""
    if self.opened: return
    if not self.app.mainwindow.opened: return
    super().open(image, "Remove hot pixels")
    vbox = Gtk.VBox(spacing = 16)
    self.window.add(vbox)
    hbox = Gtk.HBox(spacing = 8)
    vbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Channel(s):"), False, False, 0)
    self.widgets.rgbbutton = Gtk.RadioButton.new_with_label_from_widget(None, "RGB")
    hbox.pack_start(self.widgets.rgbbutton, False, False, 0)
    self.widgets.lumbutton = Gtk.RadioButton.new_with_label_from_widget(self.widgets.rgbbutton, "Luminance")
    hbox.pack_start(self.widgets.lumbutton, False, False, 0)
    hbox = Gtk.HBox(spacing = 8)
    vbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Ratio:"), False, False, 0)
    self.widgets.ratiospin = SpinButton(self.initratio, 1., 10., 0.01)
    hbox.pack_start(self.widgets.ratiospin, False, False, 0)
    vbox.pack_start(self.apply_cancel_reset_close_buttons(onthefly = self.app.hotpixotf), False, False, 0)
    self.app.mainwindow.set_images(OD(Image = self.image, Reference = self.reference), reference = "Reference")
    self.toolparams = ("RGB", self.initratio, imageprocessing.get_rgb_luminance())
    if self.app.hotpixotf:
      self.signals.append((self.widgets.rgbbutton, self.widgets.rgbbutton.connect("toggled", self.update, True)))
      self.signals.append((self.widgets.ratiospin, self.widgets.ratiospin.connect("button-release-event", self.update, False)))
      self.signals.append((self.widgets.ratiospin, self.widgets.ratiospin.connect("key-release-event", self.update, False)))
      self.update(True)
    self.window.show_all()

  def reset(self, *args):
    """Reset tool."""
    channels, ratio, rgblum = self.toolparams
    if channels == "RGB":
      self.widgets.rgbbutton.set_active(True)
    else:
      self.widgets.lumbutton.set_active(True)
    self.widgets.ratiospin.set_value(ratio)

  def update(self, *args):
    """Apply tool on the fly."""
    ratio = self.widgets.ratiospin.get_value()
    if args[-1] is False and ratio == self.toolparams[1]: return # Nothing to update.
    self.window.get_root_window().set_cursor(Gdk.Cursor(Gdk.CursorType.WATCH))
    channels = "RGB" if self.widgets.rgbbutton.get_active() else "L"
    self.image.copy_from(self.reference)
    self.image.remove_hot_pixels(ratio, channels = channels)
    self.app.mainwindow.update_image("Image", self.image)
    self.transformed = True
    self.toolparams = (channels, ratio, imageprocessing.get_rgb_luminance())
    self.window.get_root_window().set_cursor(Gdk.Cursor(Gdk.CursorType.ARROW))
    self.widgets.cancelbutton.set_sensitive(True)

  def apply(self, *args):
    """Apply tool."""
    channels = "RGB" if self.widgets.rgbbutton.get_active() else "L"
    print(f"Removing hot pixels on {channels} channel(s)...")
    self.update(True)

  def operation(self):
    """Return tool operation string."""
    if not self.transformed: return None
    channels, ratio, rgblum = self.toolparams
    if channels == "RGB":
      return f"RemoveHotPixels(RGB, ratio = {ratio:.2f})"
    else:
      return f"RemoveHotPixels(L({rgblum[0]:.2f}, {rgblum[1]:.2f}, {rgblum[2]:.2f}), ratio = {ratio:.2f})"

  def cancel(self, *args):
    """Cancel tool."""
    if not self.transformed: return
    self.block_all_signals() # Block all signals while restoring original image and tool params.
    self.image.copy_from(self.reference)
    self.app.mainwindow.update_image("Image", self.image)
    self.transformed = False
    if self.app.hotpixotf:
      self.close()
      return
    self.widgets.ratiospin.set_value(self.initratio)
    self.toolparams = ("RGB" if self.widgets.rgbbutton.get_active() else "L", self.initratio)
    self.widgets.cancelbutton.set_sensitive(False)
    self.unblock_all_signals() # Unblock signals.

