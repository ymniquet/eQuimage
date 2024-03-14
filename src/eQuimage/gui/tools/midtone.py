# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.4.0 / 2024.02.26
# GUI updated.

"""Midtone stretch tool."""

from .stretch import StretchTool
from ..gtk.customwidgets import HBox, VBox, CheckButton, SpinButton
from ...imageprocessing import imageprocessing
from ...imageprocessing.stretchfunctions import midtone_stretch_function

class MidtoneStretchTool(StretchTool):
  """Midtone stretch tool class."""

  __action__ = "Stretching histograms (midtone stretch function)..."

  # Build window.

  __window_name__ = "Midtone stretch"

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
    step = (percentiles[2]-percentiles[0])/10. if percentiles is not None else .01
    step = min(max(step, .0001), .01)
    cbox = VBox(margin = 16)
    hbox = HBox()
    cbox.pack(hbox)
    widgets.shadowspin = SpinButton(0., 0., .99, step/2., digits = 5)
    widgets.shadowspin.connect("value-changed", lambda button: self.update("shadow"))
    hbox.pack("Shadow:")
    hbox.pack(widgets.shadowspin)
    widgets.midtonespin = SpinButton(.5, 0., 1., step, digits = 5)
    widgets.midtonespin.connect("value-changed", lambda button: self.update("midtone"))
    hbox.pack(8*" "+"Midtone:")
    hbox.pack(widgets.midtonespin)
    widgets.highlightspin = SpinButton(1., .01, 1., step, digits = 5)
    widgets.highlightspin.connect("value-changed", lambda button: self.update("highlight"))
    hbox.pack(8*" "+"Highlight:")
    hbox.pack(widgets.highlightspin)
    hbox = HBox()
    cbox.pack(hbox)
    widgets.lowspin = SpinButton(0., -10., 0., .01, digits = 3)
    widgets.lowspin.connect("value-changed", lambda button: self.update("low"))
    hbox.pack("Low range:")
    hbox.pack(widgets.lowspin)
    widgets.highspin = SpinButton(1., 1., 10., .01, digits = 3)
    widgets.highspin.connect("value-changed", lambda button: self.update("high"))
    hbox.pack(8*" "+"High range:")
    hbox.pack(widgets.highspin)
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
      midtone = channel.midtonespin.get_value()
      highlight = channel.highlightspin.get_value()
      low = channel.lowspin.get_value()
      high = channel.highspin.get_value()
      params[key] = (shadow, midtone, highlight, low, high)
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
      shadow, midtone, highlight, low, high = params[key]
      channel.shadowspin.set_value_block(shadow)
      channel.midtonespin.set_value_block(midtone)
      channel.highlightspin.set_value_block(highlight)
      channel.lowspin.set_value_block(low)
      channel.highspin.set_value_block(high)
    self.widgets.channels["L"].highlightsbutton.set_active_block(params["highlights"])
    if unbindrgb: self.widgets.bindbutton.set_active_block(False)
    self.update("all")

  def run(self, params):
    """Run tool for parameters 'params'."""
    self.image.copy_image_from(self.reference)
    transformed = False
    for key in self.channelkeys:
      shadow, midtone, highlight, low, high = params[key]
      outofrange = self.outofrange and key in ["R", "G", "B"]
      if not outofrange and shadow == 0. and midtone == 0.5 and highlight == 1. and low == 0. and high == 1.: continue
      transformed = True
      self.image.generalized_stretch(midtone_stretch_function, (shadow, midtone, highlight, low, high), channels = key)
    if transformed and params["highlights"]: self.image.protect_highlights()
    return params, transformed

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    operation = "MTStretch("
    separator = ""
    for key in self.channelkeys:
      shadow, midtone, highlight, low, high = params[key]
      if key == "L":
        red, green, blue = params["rgbluma"]
        operation += f"{separator}L({red:.2f}, {green:.2f}, {blue:.2f}) : (shadow = {shadow:.5f}, midtone = {midtone:.5f}, highlight = {highlight:.5f}, low = {low:.3f}, high = {high:.3f})"
      else:
        operation += f"{separator}{key} : (shadow = {shadow:.5f}, midtone = {midtone:.5f}, highlight = {highlight:.5f}, low = {low:.3f}, high = {high:.3f})"
      separator = ", "
    if params["highlights"]: operation += ", protect highlights"
    operation += ")"
    return operation

  # Plot histograms, stretch function, display stats...

  def stretch_function(self, t, params):
    """Return the stretch function f(t) for parameters 'params'."""
    return midtone_stretch_function(t, params)

  def add_histogram_widgets(self, ax):
    """Add histogram widgets (other than stretch function) in axes 'ax'."""
    self.widgets.shadowline = ax.axvline(0., linestyle = "-.", zorder = -2)
    self.widgets.midtoneline = ax.axvline(.5, linestyle = "-.", zorder = -2)
    self.widgets.highlightline = ax.axvline(1., linestyle = "-.", zorder = -2)

  # Update histograms, stats... on widget or key_press events.

  def update_widgets(self, key, changed):
    """Update widgets (other than histograms and stats) on change of 'changed' in channel 'key'."""
    channel = self.widgets.channels[key]
    shadow = channel.shadowspin.get_value()
    midtone = channel.midtonespin.get_value()
    highlight = channel.highlightspin.get_value()
    low = channel.lowspin.get_value()
    high = channel.highspin.get_value()
    if changed in ["shadow", "highlight"]:
      if changed == "shadow":
        if shadow > highlight-0.005:
          shadow = highlight-0.005
          channel.shadowspin.set_value_block(shadow)
      else:
        if highlight < shadow+0.005:
          highlight = shadow+0.005
          channel.highlightspin.set_value_block(highlight)
      shadow_, midtone_, highlight_, low_, high_ = self.currentparams[key]
      midtone_ = (midtone_-shadow_)/(highlight_-shadow_)
      midtone = shadow+midtone_*(highlight-shadow)
      channel.midtonespin.set_value_block(midtone)
    if midtone <= shadow:
      midtone = shadow+0.001
      channel.midtonespin.set_value_block(midtone)
    if midtone >= highlight:
      midtone = highlight-0.001
      channel.midtonespin.set_value_block(midtone)
    self.currentparams[key] = (shadow, midtone, highlight, low, high)
    color = channel.color
    lcolor = channel.lcolor
    self.widgets.shadowline.set_xdata([shadow, shadow])
    self.widgets.shadowline.set_color(0.1*lcolor)
    self.widgets.midtoneline.set_xdata([midtone, midtone])
    self.widgets.midtoneline.set_color(0.5*lcolor)
    self.widgets.highlightline.set_xdata([highlight, highlight])
    self.widgets.highlightline.set_color(0.9*lcolor)
    self.plot_stretch_function(lambda t: self.stretch_function(t, (shadow, midtone, highlight, low, high)), color)
    if self.widgets.bindbutton.get_active() and key in ("R", "G", "B"):
      for rgbkey in ("R", "G", "B"):
        rgbchannel = self.widgets.channels[rgbkey]
        rgbchannel.shadowspin.set_value_block(shadow)
        rgbchannel.midtonespin.set_value_block(midtone)
        rgbchannel.highlightspin.set_value_block(highlight)
        rgbchannel.lowspin.set_value_block(low)
        rgbchannel.highspin.set_value_block(high)
        self.currentparams[rgbkey] = (shadow, midtone, highlight, low, high)
