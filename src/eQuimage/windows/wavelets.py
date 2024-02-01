# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.3.0 / 2024.01.29

"""Wavelets filter tool."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
from .tools import BaseToolWindow
from skimage.restoration import estimate_sigma, denoise_wavelet

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
    grid = Gtk.Grid(column_spacing = 8)
    wbox.pack_start(grid, False, False, 0)
    self.widgets.entries = []
    for channel, label in ((0, "Red:"), (1, "Green:"), (2, "Blue:")):
      entry = Gtk.Entry()
      entry.channel = channel
      entry.lastvalid = f"{sigma[channel]:.5e}"
      entry.set_max_length(16)
      entry.set_text(entry.lastvalid)
      entry.connect("changed", lambda entry: self.update(entry.channel))
      if not self.widgets.entries:
        grid.add(entry)
      else:
        grid.attach_next_to(entry, self.widgets.entries[-1], Gtk.PositionType.BOTTOM, 1, 1)
      self.widgets.entries.append(entry)
      grid.attach_next_to(Gtk.Label(label = label, halign = Gtk.Align.END), entry, Gtk.PositionType.LEFT, 1, 1)
    grid.attach_next_to(Gtk.Label(label = "Enter estimated noise level\nin each channel:", halign = Gtk.Align.START), self.widgets.entries[0], Gtk.PositionType.TOP, 1, 1)
    wbox.pack_start(self.tool_control_buttons(), False, False, 0)
    self.start(identity = True)
    return True

  def get_params(self):
    """Return tool parameters."""
    return None

  def set_params(self, params):
    """Set tool parameters 'params'."""
    return

  def run(self, params):
    """Run tool for parameters 'params'."""
    return params, False

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    return f"WaveletsFilter()"

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
    if changed >= 0:
      text = self.widgets.entries[changed].get_text()
      try:
        value = float(text)
      except:
        self.widgets.entries[changed].set_name("red-entry")
        return
      self.widgets.entries[changed].set_name("")
      self.widgets.entries[changed].lastvalid = text
