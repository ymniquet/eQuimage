# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.6.1 / 2024.09.01
# GUI updated (+).

"""Butterworth filter tool."""

from ..gtk.customwidgets import HBox, VBox, CheckButton, SpinButton, HScaleSpinButton
from ..toolmanager import BaseToolWindow
from skimage.filters import butterworth

class ButterworthFilterTool(BaseToolWindow):
  """Butterworth filter tool class."""

  _action_ = "Applying Butterworth filter..."

  _help_ = """Butterworth low-pass filter in the frequency domain:
    H(f) = 1/(1+(f/fc^(2n))
where n is the order of the filter and fc = (1-c)*fs/2 is the cut-off frequency, with fs the sampling frequency and c\u2208[0, 1] the normalized cut-off frequency.
If the filter leaves visible artifacts on the edges, the image may be padded (with the edge values) prior to Fourier transform.
Apply the high-pass filter 1-H(f) if the high-pass checkbox is ticked."""

  _onthefly_ = False # This transformation can not be applied on the fly.

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Butterworth filter"): return False
    wbox = VBox()
    self.window.add(wbox)
    self.widgets.cutoffscale = HScaleSpinButton(.5, 0., .9999, .0001, digits = 4, length = 480)
    wbox.pack(self.widgets.cutoffscale.layout2("Normalized cut-off frequency:"))
    self.widgets.orderscale = HScaleSpinButton(2., .1, 10., .1, digits = 1, length = 480)
    wbox.pack(self.widgets.orderscale.layout2("Order:"))
    hbox = HBox()
    wbox.pack(hbox)
    self.widgets.padspin = SpinButton(0., 0., 32., 1., digits = 0)
    hbox.pack(self.widgets.padspin.hbox(prepend = "Padding:", append = "pixels"), expand = True, fill = True)
    self.widgets.highpassbutton = CheckButton(label = "High-pass")
    hbox.pack(self.widgets.highpassbutton)
    wbox.pack(self.tool_control_buttons())
    self.start(identity = False)
    return True

  def get_params(self):
    """Return tool parameters."""
    return self.widgets.cutoffscale.get_value(), self.widgets.orderscale.get_value(), int(round(self.widgets.padspin.get_value())), self.widgets.highpassbutton.get_active()

  def set_params(self, params):
    """Set tool parameters 'params'."""
    cutoff, order, npad, highpass = params
    self.widgets.cutoffscale.set_value(cutoff)
    self.widgets.orderscale.set_value(order)
    self.widgets.padspin.set_value(npad)
    self.widgets.highpassbutton.set_active(highpass)

  def run(self, params):
    """Run tool for parameters 'params'."""
    cutoff, order, npad, highpass = params
    self.image.rgb = butterworth(self.reference.rgb, channel_axis = 0, cutoff_frequency_ratio = (1.-cutoff)/2., order = order, npad = npad, high_pass = highpass, squared_butterworth = True)
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    cutoff, order, npad, highpass = params
    band = "HighPass" if highpass else ""
    padding = f", padding = {npad} pixels" if npad > 0 else ""
    return f"{band}ButterworthFilter(cutoff = {cutoff:.4f}, order = {order:.1f}{padding})"
