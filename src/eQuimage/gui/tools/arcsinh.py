# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.5.2 / 2024.06.23
# GUI updated.

"""Arcsinh stretch tool."""

from .stretch import StretchTool
from ..gtk.customwidgets import HBox, VBox, CheckButton, SpinButton
from ...imageprocessing import imageprocessing
from ...imageprocessing.stretchfunctions import arcsinh_stretch_function

class ArcsinhStretchTool(StretchTool):
  """Arcsinh stretch tool class, derived from the StretchTool class."""

  _action_ = "Stretching histograms (arcsinh stretch function)..."

  # Build window.

  _window_name_ = "Arcsinh stretch"

  def options_widgets(self, widgets):
    """Return a box with tool options widgets and store the reference to these widgets in container 'widgets'.
       Return None if there are no tool options widgets."""
    hbox = HBox()
    widgets.bindbutton = CheckButton(label = "Bind RGB channels")
    widgets.bindbutton.set_active(True)
    widgets.bindbutton.connect("toggled", lambda button: self.update("bindrgb"))
    hbox.pack(widgets.bindbutton, expand = True, fill = True)
    return hbox

  def tab_widgets(self, key, widgets):
    """Return a box with tab widgets for channel 'key' in "R" (red), "G" (green), "B" (blue), "S" (saturation), "V" (value) or "L" (luma),
       and store the reference to these widgets in container 'widgets'.
       Return None if there is no tab for this channel."""
    if not key in ["R", "G", "B", "V", "L"]: return None
    percentiles = self.reference.stats["L"].percentiles
    step = (percentiles[2]-percentiles[0])/20. if percentiles is not None else .01
    step = min(max(step, .0001), .01)
    cbox = VBox(margin = 16)
    hbox = HBox()
    cbox.pack(hbox)
    widgets.shadowspin = SpinButton(0., 0., .99, step, digits = 5)
    widgets.shadowspin.connect("value-changed", lambda button: self.update("shadow"))
    hbox.pack("Shadow:")
    hbox.pack(widgets.shadowspin)
    widgets.stretchspin = SpinButton(0., 0., 1000., 1., digits = 1)
    widgets.stretchspin.connect("value-changed", lambda button: self.update("stretch"))
    hbox.pack(8*" "+"Stretch factor:")
    hbox.pack(widgets.stretchspin)
    if key == "L":
      widgets.highlightsbutton = CheckButton(label = "Protect highlights")
      widgets.highlightsbutton.set_active(False)
      widgets.highlightsbutton.connect("toggled", lambda button: self.update(None))
      hbox.pack(8*" ")
      hbox.pack(widgets.highlightsbutton)
    return cbox

  # Tool methods.

  def get_params(self):
    """Return tool parameters."""
    params = {}
    for key in self.channelkeys:
      channel = self.widgets.channels[key]
      shadow = channel.shadowspin.get_value()
      stretch = channel.stretchspin.get_value()
      params[key] = (shadow, stretch)
    params["highlights"] = self.widgets.channels["L"].highlightsbutton.get_active()
    params["rgbluma"] = imageprocessing.get_rgb_luma()
    return params

  def set_params(self, params):
    """Set tool parameters 'params'."""
    unbindrgb = False
    redparams = params["R"]
    for key in self.channelkeys:
      channel = self.widgets.channels[key]
      if key in ("R", "G", "B"):
        unbindrgb = unbindrgb or (params[key] != redparams)
      shadow, stretch = params[key]
      channel.shadowspin.set_value_block(shadow)
      channel.stretchspin.set_value_block(stretch)
    self.widgets.channels["L"].highlightsbutton.set_active_block(params["highlights"])
    if unbindrgb: self.widgets.bindbutton.set_active_block(False)
    self.update("all")

  def run(self, params):
    """Run tool for parameters 'params'."""
    self.image.copy_image_from(self.reference)
    transformed = False
    for key in self.channelkeys:
      shadow, stretch = params[key]
      outofrange = self.outofrange and key in ["R", "G", "B"]
      if not outofrange and shadow == 0. and stretch == 0.: continue
      transformed = True
      self.image.generalized_stretch(arcsinh_stretch_function, (shadow, stretch), channels = key)
    if transformed and params["highlights"]: self.image.protect_highlights()
    return params, transformed

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    operation = "ArcsinhStretch("
    separator = ""
    for key in self.channelkeys:
      shadow, stretch = params[key]
      if key == "L":
        red, green, blue = params["rgbluma"]
        operation += f"{separator}L({red:.2f}, {green:.2f}, {blue:.2f}) : (shadow = {shadow:.5f}, stretch = {stretch:.1f})"
      else:
        operation += f"{separator}{key} : (shadow = {shadow:.5f}, stretch = {stretch:.1f})"
      separator = ", "
    if params["highlights"]: operation += ", protect highlights"
    operation += ")"
    return operation

  # Plot histograms, stretch function, display stats...

  def stretch_function(self, t, params):
    """Return the stretch function f(t) for parameters 'params'."""
    return arcsinh_stretch_function(t, params)

  def add_histogram_widgets(self, ax):
    """Add histogram widgets (other than stretch function) in axes 'ax'."""
    self.widgets.shadowline = ax.axvline(0., linestyle = "-.", zorder = -2)

  # Update histograms, stats... on widget or key_press events.

  def update_widgets(self, key, changed):
    """Update widgets (other than histograms and stats) on change of 'changed' in channel 'key'."""
    channel = self.widgets.channels[key]
    shadow = channel.shadowspin.get_value()
    stretch = channel.stretchspin.get_value()
    color = channel.color
    lcolor = channel.lcolor
    self.widgets.shadowline.set_xdata([shadow, shadow])
    self.widgets.shadowline.set_color(.1*lcolor)
    self.plot_stretch_function(lambda t: self.stretch_function(t, (shadow, stretch)), color)
    if self.widgets.bindbutton.get_active() and key in ("R", "G", "B"):
      for rgbkey in ("R", "G", "B"):
        rgbchannel = self.widgets.channels[rgbkey]
        rgbchannel.shadowspin.set_value_block(shadow)
        rgbchannel.stretchspin.set_value_block(stretch)
