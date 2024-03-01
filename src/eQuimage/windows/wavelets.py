# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.4.0 / 2024.02.26
# GUI updated.

"""Wavelets filter tool."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .gtk.customwidgets import HBox, VBox, CheckButton, SpinButton, Entry
from .tools import BaseToolWindow
from skimage.restoration import estimate_sigma, denoise_wavelet, cycle_spin

class WaveletsFilterTool(BaseToolWindow):
  """Wavelets filter tool class."""

  __action__ = "Filtering wavelets..."

  __onthefly__ = False # This transformation can not be applied on the fly.

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Wavelets filter"): return False
    sigma = estimate_sigma(self.reference.rgb, channel_axis = 0, average_sigmas = False)
    wbox = VBox()
    self.window.add(wbox)
    hbox = HBox()
    wbox.pack(hbox)
    hbox.pack(Gtk.Label(label = "Estimated noise level in each channel:"))
    self.widgets.bindbutton = CheckButton(label = "Bind RGB channels", halign = Gtk.Align.END)
    self.widgets.bindbutton.connect("toggled", lambda button: self.update(0))
    hbox.pack(self.widgets.bindbutton, expand = True, fill = True)
    hbox = HBox()
    wbox.pack(hbox)
    self.widgets.entries = []
    for channel, label in ((0, "Red:"), (1, 8*" "+"Green:"), (2, 8*" "+"Blue:")):
      entry = Entry(text = f"{sigma[channel]:.5e}", width = 12)
      entry.channel = channel
      entry.connect("changed", lambda entry: self.update(entry.channel))
      self.widgets.entries.append(entry)
      hbox.pack(Gtk.Label(label = label))
      hbox.pack(entry)
    self.widgets.shiftsbutton = SpinButton(0., 0., 8., 1., page = 1., digits = 0)
    wbox.pack(self.widgets.shiftsbutton.hbox(prepend = "Maximum shift for cycle spinning:"))
    wbox.pack(self.tool_control_buttons())
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
