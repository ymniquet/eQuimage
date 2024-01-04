# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2023.11.27

"""Hyperbolic stretch tool."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .gtk.customwidgets import SpinButton
from .stretch import StretchTool
from .utils import highlight_histogram
from ..imageprocessing import imageprocessing
from ..imageprocessing.stretchfunctions import hyperbolic_stretch_function
import numpy as np

class HyperbolicStretchTool(StretchTool):
  """Hyperbolic stretch tool class, derived from StretchTool class."""

  __action__ = "Stretching histograms (hyperbolic stretch function)..."
  __window_name__ = "Hyperbolic stretch"

  def add_tab_widgets(self, key, channel):
    """Return Gtk box for tab 'key' in "R" (red), "G" (green), "B" (blue), "V" (value) or "L" (luminance).
       Store the tab widgets in container 'channel'."""
    cbox = Gtk.VBox(spacing = 16, margin = 16)
    hbox = Gtk.HBox(spacing = 8)
    cbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Stretch:"), False, False, 0)
    channel.stretchspin = SpinButton(0., 0., 10., 0.01, digits = 3)
    channel.stretchspin.connect("value-changed", lambda button: self.update(changed = "stretch"))
    hbox.pack_start(channel.stretchspin, False, False, 0)
    hbox.pack_start(Gtk.Label(label = 8*" "+"Local stretch:"), False, False, 0)
    channel.localspin = SpinButton(0, -5., 10., 0.01, digits = 3)
    channel.localspin.connect("value-changed", lambda button: self.update(changed = "local"))
    hbox.pack_start(channel.localspin, False, False, 0)
    hbox.pack_start(Gtk.Label(label = 8*" "+"Symmetry point:"), False, False, 0)
    channel.symmetryspin = SpinButton(.5, 0., 1., 0.001, digits = 3)
    channel.symmetryspin.connect("value-changed", lambda button: self.update(changed = "symmetry"))
    hbox.pack_start(channel.symmetryspin, False, False, 0)
    hbox = Gtk.HBox(spacing = 8)
    cbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Shadow protection point:"), False, False, 0)
    channel.shadowspin = SpinButton(0., 0., 1., 0.001, digits = 3)
    channel.shadowspin.connect("value-changed", lambda button: self.update(changed = "shadow"))
    hbox.pack_start(channel.shadowspin, False, False, 0)
    hbox.pack_start(Gtk.Label(label = 8*" "+"Highlight protection point:"), False, False, 0)
    channel.highlightspin = SpinButton(1., 0., 1., 0.001, digits = 3)
    channel.highlightspin.connect("value-changed", lambda button: self.update(changed = "highlight"))
    hbox.pack_start(channel.highlightspin, False, False, 0)
    #if key == "L":
      #hbox.pack_start(Gtk.Label(label = 8*" "), False, False, 0)
      #channel.highlightsbutton = CheckButton(label = "Preserve highlights")
      #channel.highlightsbutton.set_active(False)
      #channel.highlightsbutton.connect("toggled", lambda button: self.update(changed = "preserve"))
      #hbox.pack_start(channel.highlightsbutton, False, False, 0)
    return cbox

  def get_params(self):
    """Return tool parameters."""
    params = {}
    for key in self.channelkeys:
      channel = self.widgets.channels[key]
      stretch = channel.stretchspin.get_value()
      local = channel.localspin.get_value()
      symmetry = channel.symmetryspin.get_value()
      shadow = channel.shadowspin.get_value()
      highlight = channel.highlightspin.get_value()
      params[key] = (stretch, local, symmetry, shadow, highlight)
    #params["highlights"] = self.widgets.channels["L"].highlightsbutton.get_active()
    params["rgblum"] = imageprocessing.get_rgb_luminance()
    return params

  def set_params(self, params):
    """Set tool parameters 'params'."""
    unlinkrgb = False
    redparams = params["R"]
    for key in self.channelkeys:
      channel = self.widgets.channels[key]
      if key in ("R", "G", "B"):
        unlinkrgb = unlinkrgb or (params[key] != redparams)
      stretch, local, symmetry, shadow, highlight = params[key]
      channel.stretchspin.set_value_block(stretch)
      channel.localspin.set_value_block(local)
      channel.symmetryspin.set_value_block(symmetry)
      channel.shadowspin.set_value_block(shadow)
      channel.highlightspin.set_value_block(highlight)
    #self.widgets.channels["L"].highlightsbutton.set_active_block(params["highlights"])
    if unlinkrgb: self.widgets.linkbutton.set_active_block(False)
    self.update()

  def run(self, params):
    """Run tool for parameters 'params'."""
    self.image.copy_from(self.reference)
    transformed = False
    for key in self.channelkeys:
      stretch, local, symmetry, shadow, highlight = params[key]
      if not self.outofrange and stretch == 0.: continue
      transformed = True
      self.image.clip_shadows_highlights(0., 1., channels = key)
      self.image.generalized_stretch(hyperbolic_stretch_function, (stretch, local, symmetry, shadow, highlight), channels = key)
    #if transformed and params["highlights"]:
      #maximum = self.image.image.max()
      #if maximum > 1.: self.image.image /= maximum
    return params, transformed

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    operation =  "HyperbolicStretch("
    for key in self.channelkeys:
      stretch, local, symmetry, shadow, highlight = params[key]
      if key != "L":
        operation += f"{key} : (stretch = {stretch:.3f}, local = {local:.3f}, symmetry = {symmetry:.3f}, shadow = {shadow:.3f}, highlight = {highlight:.3f}), "
      else:
        red, green, blue = params["rgblum"]
        operation += f"L({red:.2f}, {green:.2f}, {blue:.2f}) : (stretch = {stretch:.3f}, local = {local:.3f}, symmetry = {symmetry:.3f}, shadow = {shadow:.3f}, highlight = {highlight:.3f})"
    #if params["highlights"]: operation += ", preserve highlights"
    operation += ")"
    return operation

  # Plot histograms, stretch function, display stats...

  def stretch_function(self, stretch, local, symmetry, shadow, highlight, tmin = 0., tmax = 1.):
    """Return (t, f(t)) on a grid tmin < t < tmax, where f is the hyperbolic stretch function for
       'stretch', 'local', 'symmetry', 'shadow' and 'highlight' parameters."""
    tmin = min(0., tmin)
    tmax = max(1., tmax)
    t = np.linspace(tmin, tmax, int(round(256*(tmax-tmin))))
    ft = hyperbolic_stretch_function(np.clip(t, 0., 1.), (stretch, local, symmetry, shadow, highlight))
    return t, ft

  def add_histogram_widgets(self, ax, key):
    """Add histogram widgets (stretch function, ...) in axes 'ax' for channel 'key'."""
    channel = self.widgets.channels[key]
    stretch = channel.stretchspin.get_value()
    local = channel.localspin.get_value()
    symmetry = channel.symmetryspin.get_value()
    shadow = channel.shadowspin.get_value()
    highlight = channel.highlightspin.get_value()
    color = channel.color
    lcolor = channel.lcolor
    self.widgets.shadowline = ax.axvline(shadow, color = 0.1*lcolor, linestyle = "-.")
    self.widgets.symmetryline = ax.axvline(symmetry, color = 0.5*lcolor, linestyle = "-.")
    self.widgets.highlightline = ax.axvline(highlight, color = 0.9*lcolor, linestyle = "-.")
    t, ft = self.stretch_function(stretch, local, symmetry, shadow, highlight, tmin = self.histlims[0], tmax = self.histlims[1])
    self.widgets.tfplot, = ax.plot(t, ft, linestyle = ":", color = color)

  # Update histograms, stats... on widget or keypress events.

  def update_widgets(self, key, changed):
    """Update widgets (other than histograms and stats) on change of 'changed' in channel 'key'."""
    channel = self.widgets.channels[key]
    color = channel.color
    lcolor = channel.lcolor
    stretch = channel.stretchspin.get_value()
    local = channel.localspin.get_value()
    symmetry = channel.symmetryspin.get_value()
    shadow = channel.shadowspin.get_value()
    highlight = channel.highlightspin.get_value()
    if shadow > symmetry:
      shadow = symmetry
      channel.shadowspin.set_value_block(shadow)
    if highlight < symmetry:
      highlight = symmetry
      channel.highlightspin.set_value_block(highlight)
    self.currentparams[key] = (stretch, local, symmetry, shadow, highlight)
    self.widgets.shadowline.set_xdata([shadow, shadow])
    self.widgets.shadowline.set_color(0.1*lcolor)
    self.widgets.symmetryline.set_xdata([symmetry, symmetry])
    self.widgets.symmetryline.set_color(0.5*lcolor)
    self.widgets.highlightline.set_xdata([highlight, highlight])
    self.widgets.highlightline.set_color(0.9*lcolor)
    t, ft = self.stretch_function(stretch, local, symmetry, shadow, highlight, tmin = self.histlims[0], tmax = self.histlims[1])
    self.widgets.tfplot.set_xdata(t)
    self.widgets.tfplot.set_ydata(ft)
    self.widgets.tfplot.set_color(color)
    if self.widgets.linkbutton.get_active() and key in ("R", "G", "B"):
      for rgbkey in ("R", "G", "B"):
        rgbchannel = self.widgets.channels[rgbkey]
        rgbchannel.stretchspin.set_value_block(stretch)
        rgbchannel.localspin.set_value_block(local)
        rgbchannel.symmetryspin.set_value_block(symmetry)
        rgbchannel.shadowspin.set_value_block(shadow)
        rgbchannel.highlightspin.set_value_block(highlight)
        self.currentparams[rgbkey] = (stretch, local, symmetry, shadow, highlight)

  # Callbacks on luminance RGB components update in main window.

  def update_luminance_range(self):
    return
