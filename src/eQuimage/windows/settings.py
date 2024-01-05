# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2024.01.05

"""Settings window."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .gtk.customwidgets import Button, CheckButton, SpinButton
from .base import BaseWindow, Container

class SettingsWindow(BaseWindow):
  """Settings window class."""

  def open(self):
    """Open tool window with title 'title' for image 'image'."""
    if self.opened: return
    self.opened = True
    self.window = Gtk.Window(title = "Settings",
                             transient_for = self.app.mainmenu.window,
                             border_width = 16,
                             modal = True)
    self.window.connect("delete-event", self.close)
    self.widgets = Container()
    wbox = Gtk.VBox(spacing = 16)
    self.window.add(wbox)
    frame = Gtk.Frame(label = " Apply operations on the fly (disable if not responsive) ")
    frame.set_label_align(0.2, 0.5)
    wbox.pack_start(frame, False, False, 0)
    hbox = Gtk.HBox()
    frame.add(hbox)
    vbox = Gtk.VBox(homogeneous = True, margin = 8)
    hbox.pack_start(vbox, False, False, 0)
    self.widgets.hotpixlbutton = CheckButton(label = "Remove hot pixels")
    self.widgets.hotpixlbutton.set_active(self.app.hotpixlotf)
    vbox.pack_start(self.widgets.hotpixlbutton, False, False, 0)
    self.widgets.colorblbutton = CheckButton(label = "Balance colors")
    self.widgets.colorblbutton.set_active(self.app.colorblotf)
    vbox.pack_start(self.widgets.colorblbutton, False, False, 0)
    self.widgets.stretchbutton = CheckButton(label = "Stretch")
    self.widgets.stretchbutton.set_active(self.app.stretchotf)
    vbox.pack_start(self.widgets.stretchbutton, False, False, 0)
    vbox = Gtk.VBox(margin = 8, valign = Gtk.Align.CENTER)
    hbox.pack_start(vbox, False, False, 0)
    tbox = Gtk.HBox()
    vbox.pack_start(tbox, False, False, 0)
    tbox.pack_start(Gtk.Label(label = "Poll time: "), False, False, 0)
    self.widgets.timespin = SpinButton(self.app.polltime, 100, 1000, 10, digits = 0)
    tbox.pack_start(self.widgets.timespin, False, False, 0)
    tbox.pack_start(Gtk.Label(label = " ms"), False, False, 0)
    hbox = Gtk.HButtonBox(homogeneous = True, spacing = 16, halign = Gtk.Align.START)
    wbox.pack_start(hbox, False, False, 0)
    self.widgets.applybutton = Button(label = "OK")
    self.widgets.applybutton.connect("clicked", self.apply)
    hbox.pack_start(self.widgets.applybutton, False, False, 0)
    self.widgets.applybutton = Button(label = "Reset")
    self.widgets.applybutton.connect("clicked", self.reset)
    hbox.pack_start(self.widgets.applybutton, False, False, 0)
    self.widgets.cancelbutton = Button(label = "Cancel")
    self.widgets.cancelbutton.connect("clicked", self.close)
    hbox.pack_start(self.widgets.cancelbutton, False, False, 0)
    self.window.show_all()

  def reset(self, *args, **kwargs):
    """Reset settings."""
    if not self.opened: return
    settings = self.app.get_default_settings()
    self.widgets.hotpixlbutton.set_active(settings["remove_hot_pixels_on_the_fly"])
    self.widgets.colorblbutton.set_active(settings["balance_colors_on_the_fly"])
    self.widgets.stretchbutton.set_active(settings["stretch_on_the_fly"])
    self.widgets.timespin.set_value(settings["poll_time"])

  def apply(self, *args, **kwargs):
    """Apply settings."""
    if not self.opened: return
    self.app.hotpixlotf = self.widgets.hotpixlbutton.get_active()
    self.app.colorblotf = self.widgets.colorblbutton.get_active()
    self.app.stretchotf = self.widgets.stretchbutton.get_active()
    self.app.polltime = int(self.widgets.timespin.get_value())
    self.app.save_settings() # Save current settings.
    self.close()

  def close(self, *args, **kwargs):
    """Close settings window."""
    if not self.opened: return
    self.window.destroy()
    self.opened = False
    del self.widgets
