# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2024.01.14

"""Midtone stretch tool."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .gtk.customwidgets import CheckButton, SpinButton
from .stretch import StretchTool
from ..imageprocessing import imageprocessing
from ..imageprocessing.stretchfunctions import midtone_stretch_function
import numpy as np

class MidtoneStretchTool(StretchTool):
  """Midtone stretch tool class."""

  __action__ = "Stretching histograms (midtone stretch function)..."

  # Build window.

  __window_name__ = "Midtone stretch"

  def options_widgets(self, widgets):
    """Return a Gtk box with tool options widgets and store the reference to these widgets in container 'widgets'.
       Return None if there are no tool options widgets."""
    hbox = Gtk.HBox(spacing = 8)
    widgets.bindbutton = CheckButton(label = "Bind RGB channels")
    widgets.bindbutton.set_active(True)
    widgets.bindbutton.connect("toggled", lambda button: self.update("bindrgb"))
    hbox.pack_start(widgets.bindbutton, True, True, 0)
    return hbox

  def tab_widgets(self, key, widgets):
    """Return a Gtk box with tab widgets for channel 'key' in "R" (red), "G" (green), "B" (blue), "V" (value) or "L" (luminance),
       and store the reference to these widgets in container 'widgets'.
       Return None if there is no tab for this channel."""
    percentiles = self.reference.stats["L"].percentiles
    step = (percentiles[2]-percentiles[0])/10. if percentiles is not None else .01
    step = min(max(step, .0001), .01)
    cbox = Gtk.VBox(spacing = 16, margin = 16)
    hbox = Gtk.HBox(spacing = 8)
    cbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Shadow:"), False, False, 0)
    widgets.shadowspin = SpinButton(0., 0., .99, step/2., digits = 5)
    widgets.shadowspin.connect("value-changed", lambda button: self.update("shadow"))
    hbox.pack_start(widgets.shadowspin, False, False, 0)
    hbox.pack_start(Gtk.Label(label = 8*" "+"Midtone:"), False, False, 0)
    widgets.midtonespin = SpinButton(.5, 0., 1., step, digits = 5)
    widgets.midtonespin.connect("value-changed", lambda button: self.update("midtone"))
    hbox.pack_start(widgets.midtonespin, False, False, 0)
    hbox.pack_start(Gtk.Label(label = 8*" "+"Highlight:"), False, False, 0)
    widgets.highlightspin = SpinButton(1., .01, 1., step, digits = 5)
    widgets.highlightspin.connect("value-changed", lambda button: self.update("highlight"))
    hbox.pack_start(widgets.highlightspin, False, False, 0)
    hbox = Gtk.HBox(spacing = 8)
    cbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Low range:"), False, False, 0)
    widgets.lowspin = SpinButton(0., -10., 0., 0.01, digits = 3)
    widgets.lowspin.connect("value-changed", lambda button: self.update("low"))
    hbox.pack_start(widgets.lowspin, False, False, 0)
    hbox.pack_start(Gtk.Label(label = 8*" "+"High range:"), False, False, 0)
    widgets.highspin = SpinButton(1., 1., 10., 0.01, digits = 3)
    widgets.highspin.connect("value-changed", lambda button: self.update("high"))
    hbox.pack_start(widgets.highspin, False, False, 0)
    if key == "L":
      hbox.pack_start(Gtk.Label(label = 8*" "), False, False, 0)
      widgets.highlightsbutton = CheckButton(label = "Protect highlights")
      widgets.highlightsbutton.set_active(False)
      widgets.highlightsbutton.connect("toggled", lambda button: self.update(None))
      hbox.pack_start(widgets.highlightsbutton, False, False, 0)
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
    params["rgblum"] = imageprocessing.get_rgb_luminance()
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
    self.image.copy_rgb_from(self.reference)
    transformed = False
    for key in self.channelkeys:
      shadow, midtone, highlight, low, high = params[key]
      outofrange = self.outofrange and key in ["R", "G", "B"]
      if not outofrange and shadow == 0. and midtone == 0.5 and highlight == 1. and low == 0. and high == 1.: continue
      transformed = True
      self.image.generalized_stretch(midtone_stretch_function, (shadow, midtone, highlight, low, high), channels = key)
    if transformed and params["highlights"]: self.image.normalize_values()
    return params, transformed

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    operation = "MTStretch("
    for key in self.channelkeys:
      shadow, midtone, highlight, low, high = params[key]
      if key != "L":
        operation += f"{key} : (shadow = {shadow:.5f}, midtone = {midtone:.5f}, highlight = {highlight:.5f}, low = {low:.3f}, high = {high:.3f}), "
      else:
        red, green, blue = params["rgblum"]
        operation += f"L({red:.2f}, {green:.2f}, {blue:.2f}) : (shadow = {shadow:.5f}, midtone = {midtone:.5f}, highlight = {highlight:.5f}, low = {low:.3f}, high = {high:.3f})"
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
