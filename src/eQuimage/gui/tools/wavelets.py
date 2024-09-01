# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.6.0 / 2024.09.01
# GUI updated.

"""Wavelets filter tool."""

from ..gtk.customwidgets import Align, HBox, VBox, CheckButton, RadioButtons, SpinButton, ComboBoxText, Entry
from ..toolmanager import BaseToolWindow
from skimage.restoration import estimate_sigma, denoise_wavelet, cycle_spin

class WaveletsFilterTool(BaseToolWindow):
  """Wavelets filter tool class."""

  _action_ = "Applying wavelets filter..."

  _onthefly_ = False # This transformation can not be applied on the fly.

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Wavelets filter"): return False
    sigma = estimate_sigma(self.reference.rgb, channel_axis = 0, average_sigmas = False)
    wbox = VBox()
    self.window.add(wbox)
    hbox = HBox()
    wbox.pack(hbox)
    hbox.pack("Estimated noise level in each channel:")
    self.widgets.bindbutton = CheckButton(label = "Bind RGB channels", halign = Align.END)
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
      hbox.pack(label)
      hbox.pack(entry)
    self.widgets.ycbcrbutton = CheckButton(label = "Apply transformation in the YCbCr color space")
    self.widgets.ycbcrbutton.set_active(True)
    wbox.pack(self.widgets.ycbcrbutton)
    wavelets = [] # Set-up the list of wavelets.
    for i in range(8):
      wavelets.append((f"db{i+1}", f"Daubechies {i+1}"))
    for i in range(7):
      wavelets.append((f"sym{i+2}", f"Symlets {i+2}"))
    for i in range(8):
      wavelets.append((f"coif{i+1}", f"Coiflets {i+1}"))
    self.widgets.waveletcombo = ComboBoxText(*wavelets)
    self.widgets.waveletcombo.set_selected("coif4")
    wbox.pack(self.widgets.waveletcombo.hbox(prepend = "Wavelets:"))
    hbox = HBox()
    wbox.pack(hbox)
    self.widgets.methodbuttons = RadioButtons(("BayesShrink", "Bayes Shrink"), ("VisuShrink", "Visu Shrink"))
    hbox.pack(self.widgets.methodbuttons.hbox(prepend = "Method:"))
    self.widgets.modebuttons = RadioButtons(("Soft", "Soft"), ("Hard", "Hard"))
    hbox.pack(self.widgets.modebuttons.hbox(prepend = "        Mode:"))
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
    return sigma, self.widgets.ycbcrbutton.get_active(), self.widgets.waveletcombo.get_selected(), self.widgets.methodbuttons.get_selected(), \
           self.widgets.modebuttons.get_selected(), int(self.widgets.shiftsbutton.get_value())

  def set_params(self, params):
    """Set tool parameters 'params'."""
    sigma, ycbcr, wavelet, method, mode, shifts = params
    for channel in range(3):
      self.widgets.entries[channel].set_name("")
      self.widgets.entries[channel].set_text_block(f"{sigma[channel]:.5e}")
    if sigma[1] != sigma[0] or sigma[2] != sigma[0]: self.widgets.bindbutton.set_active_block(False)
    self.widgets.ycbcrbutton.set_active(ycbcr)
    self.widgets.waveletcombo.set_selected(wavelet)
    self.widgets.methodbuttons.set_selected(method)
    self.widgets.modebuttons.set_selected(mode)
    self.widgets.shiftsbutton.set_value(shifts)

  def run(self, params):
    """Run tool for parameters 'params'."""
    sigma, ycbcr, wavelet, method, mode, shifts = params
    kwargs = dict(channel_axis = -1, sigma = sigma, wavelet = wavelet, mode = mode.lower(), wavelet_levels = None,
                  convert2ycbcr = ycbcr, method = method, rescale_sigma = True)
    self.image.rgb = cycle_spin(self.reference.rgb, channel_axis = 0, max_shifts = shifts, func = denoise_wavelet, func_kw = kwargs, num_workers = None)
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    sigma, ycbcr, wavelet, method, mode, shifts = params
    operation = f"WaveletsFilter(R = {sigma[0]:.5e}, G = {sigma[1]:.5e}, B = {sigma[2]:.5e}, "
    if ycbcr: operation += " YCbCr,"
    operation += f" wavelets = {wavelet}, method = {method}, mode = {mode}, shifts = {shifts})"
    return operation

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
