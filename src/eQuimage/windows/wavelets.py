# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.4.0 / 2024.02.26

"""Wavelets filter tool."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
from .gtk.customwidgets import CheckButton, SpinButton, Entry
from .tools import BaseToolWindow
from skimage.restoration import estimate_sigma, denoise_wavelet, cycle_spin

class WaveletsFilterTool(BaseToolWindow):
  """Wavelets filter tool class."""

  __action__ = "Filtering wavelets..."

  __onthefly__ = False # This transformation can not be applied on the fly.

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Wavelets filter"): return False
    self.update_css()
    sigma = estimate_sigma(self.reference.rgb, channel_axis = 0, average_sigmas = False)
    wbox = Gtk.VBox(spacing = 16)
    self.window.add(wbox)
    hbox = Gtk.HBox(spacing = 8)
    wbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Estimated noise level in each channel:"), False, False, 0)
    self.widgets.bindbutton = CheckButton(label = "Bind RGB channels", halign = Gtk.Align.END)
    self.widgets.bindbutton.connect("toggled", lambda button: self.update(0))
    hbox.pack_start(self.widgets.bindbutton, True, True, 0)
    hbox = Gtk.HBox(spacing = 8)
    wbox.pack_start(hbox, False, False, 0)
    self.widgets.entries = []
    for channel, label in ((0, "Red:"), (1, 8*" "+"Green:"), (2, 8*" "+"Blue:")):
      entry = Entry(text = f"{sigma[channel]:.5e}", width = 12)
      entry.channel = channel
      entry.connect("changed", lambda entry: self.update(entry.channel))
      self.widgets.entries.append(entry)
      hbox.pack_start(Gtk.Label(label = label), False, False, 0)
      hbox.pack_start(entry, False, False, 0)
    self.widgets.shiftsbutton = SpinButton(0., 0., 8., 1., page = 1., digits = 0)
    hbox = self.widgets.shiftsbutton.hbox(pre = "Maximum shift for cycle spinning:")
    wbox.pack_start(hbox, False, False, 0)
    wbox.pack_start(self.tool_control_buttons(), False, False, 0)
    self.start(identity = False)
    return True

  def get_params(self):
    """Return tool parameters."""
    try:
      sigma = tuple(float(self.widgets.entries[channel].get_text()) for channel in range(3))
    except:
      return None
    return sigma, int(self.widgets.shiftsbutton.get_value())

  def set_params(self, params):
    """Set tool parameters 'params'."""
    sigma, shifts = params
    for channel in range(3):
      self.widgets.entries[channel].set_name("")
      self.widgets.entries[channel].set_text_block(f"{sigma[channel]:.5e}")
    if sigma[1] != sigma[0] or sigma[2] != sigma[0]: self.widgets.bindbutton.set_active_block(False)
    self.widgets.shiftsbutton.set_value(shifts)

  def run(self, params):
    """Run tool for parameters 'params'."""
    sigma, shifts = params
    kwargs = dict(channel_axis = -1, sigma = sigma, wavelet = "db1", mode = "soft", wavelet_levels = None,
                  convert2ycbcr = True, method = "BayesShrink", rescale_sigma = True)
    self.image.rgb = cycle_spin(self.reference.rgb, channel_axis = 0, max_shifts = shifts, func = denoise_wavelet, func_kw = kwargs, num_workers = None)
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    sigma, shifts = params
    return f"WaveletsFilter(R = {sigma[0]:.5e}, G = {sigma[1]:.5e}, B = {sigma[2]:.5e}, shifts = {shifts})"

 # Update CSS.

  def update_css(self):
    """Update CSS for Gtk.Entry."""
    screen = Gdk.Screen.get_default()
    provider = Gtk.CssProvider()
    stylecontext = Gtk.StyleContext()
    stylecontext.add_provider_for_screen(screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    css = b"""#red-entry {color: red}"""
    provider.load_from_data(css)

 # Update widgets.

  def update(self, changed):
    """Update widgets on change of 'changed'."""
    text = self.widgets.entries[changed].get_text()
    try:
      value = float(text)
    except:
      self.widgets.entries[changed].set_name("red-entry")
      return
    self.widgets.entries[changed].set_name("")
    if self.widgets.bindbutton.get_active():
      for channel in range(3):
        self.widgets.entries[channel].set_text_block(text)
