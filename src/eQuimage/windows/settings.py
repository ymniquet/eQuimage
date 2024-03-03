# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.4.0 / 2024.02.26
# GUI updated.

"""Settings window."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .gtk.customwidgets import HBox, VBox, FramedHBox, HButtonBox, Button, CheckButton, SpinButton
from .base import BaseWindow, Container

class SettingsWindow(BaseWindow):
  """Settings window class."""

  def open(self):
    """Open tool window with title 'title' for image 'image'."""
    if self.opened: return
    self.opened = True
    self.window = Gtk.Window(title = "Settings",
                             transient_for = self.app.mainwindow.window,
                             border_width = 16,
                             modal = True)
    self.window.connect("delete-event", self.close)
    self.widgets = Container()
    wbox = VBox()
    self.window.add(wbox)
    frame, hbox = FramedHBox(" Apply operations on the fly (disable if not responsive) ", spacing = 16)
    wbox.pack(frame)
    vbox = VBox(spacing = 0, homogeneous = True)
    hbox.pack(vbox)
    self.widgets.hotpixelsbutton = CheckButton(label = "Hot pixels")
    self.widgets.hotpixelsbutton.set_active(self.app.hotpixelsotf)
    vbox.pack(self.widgets.hotpixelsbutton)
    self.widgets.stretchbutton = CheckButton(label = "Stretch tools")
    self.widgets.stretchbutton.set_active(self.app.stretchotf)
    vbox.pack(self.widgets.stretchbutton)
    self.widgets.colorbutton = CheckButton(label = "Color balance/saturation/noise")
    self.widgets.colorbutton.set_active(self.app.colorotf)
    vbox.pack(self.widgets.colorbutton)
    self.widgets.blendbutton = CheckButton(label = "Blend images")
    self.widgets.blendbutton.set_active(self.app.blendotf)
    vbox.pack(self.widgets.blendbutton)
    vbox = VBox(spacing = 0, valign = Gtk.Align.CENTER)
    hbox.pack(vbox)
    self.widgets.timespin = SpinButton(self.app.polltime, 100, 1000, 10, digits = 0)
    vbox.pack(self.widgets.timespin.hbox(prepend = "Poll time:", append = "ms"))
    hbox = HButtonBox()
    wbox.pack(hbox)
    self.widgets.applybutton = Button(label = "OK")
    self.widgets.applybutton.connect("clicked", self.apply)
    hbox.pack(self.widgets.applybutton)
    self.widgets.applybutton = Button(label = "Reset")
    self.widgets.applybutton.connect("clicked", self.reset)
    hbox.pack(self.widgets.applybutton)
    self.widgets.cancelbutton = Button(label = "Cancel")
    self.widgets.cancelbutton.connect("clicked", self.close)
    hbox.pack(self.widgets.cancelbutton)
    self.window.show_all()

  def reset(self, *args, **kwargs):
    """Reset settings."""
    if not self.opened: return
    settings = self.app.get_default_settings()
    self.widgets.hotpixelsbutton.set_active(settings["remove_hot_pixels_on_the_fly"])
    self.widgets.colorbutton.set_active(settings["colors_on_the_fly"])
    self.widgets.stretchbutton.set_active(settings["stretch_on_the_fly"])
    self.widgets.blendbutton.set_active(settings["blend_on_the_fly"])
    self.widgets.timespin.set_value(settings["poll_time"])

  def apply(self, *args, **kwargs):
    """Apply settings."""
    if not self.opened: return
    self.app.hotpixelsotf = self.widgets.hotpixelsbutton.get_active()
    self.app.colorotf = self.widgets.colorbutton.get_active()
    self.app.stretchotf = self.widgets.stretchbutton.get_active()
    self.app.blendotf = self.widgets.blendbutton.get_active()
    self.app.polltime = int(self.widgets.timespin.get_value())
    self.app.save_settings() # Save current settings.
    self.close()

  def close(self, *args, **kwargs):
    """Close settings window."""
    if not self.opened: return
    self.window.destroy()
    self.opened = False
    del self.widgets
