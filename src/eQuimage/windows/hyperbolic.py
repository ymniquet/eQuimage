# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2024.01.05

"""Hyperbolic stretch tool."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .gtk.customwidgets import CheckButton, SpinButton
from .stretch import StretchTool
from ..imageprocessing import imageprocessing
from ..imageprocessing.stretchfunctions import ghyperbolic_stretch_function
import numpy as np

class GeneralizedHyperbolicStretchTool(StretchTool):
  """Generalized hyperbolic stretch tool class, derived from the StretchTool class."""

  __action__ = "Stretching histograms (generalized hyperbolic stretch function)..."

  # Build window.

  __window_name__ = "Generalized hyperbolic stretch"

  def add_tab_widgets(self, key, channel):
    """Return Gtk box for tab 'key' in "R" (red), "G" (green), "B" (blue), "V" (value) or "L" (luminance).
       Store the tab widgets in container 'channel'."""
    cbox = Gtk.VBox(spacing = 16, margin = 16)
    hbox = Gtk.HBox(spacing = 8)
    cbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Global ln(D+1):"), False, False, 0)
    channel.lnD1spin = SpinButton(0., 0., 10., 0.1, digits = 3)
    channel.lnD1spin.connect("value-changed", lambda button: self.update(changed = "D"))
    hbox.pack_start(channel.lnD1spin, False, False, 0)
    hbox.pack_start(Gtk.Label(label = 6*" "+"Local B:"), False, False, 0)
    channel.Bspin = SpinButton(0, -5., 15., 0.1, digits = 3)
    channel.Bspin.connect("value-changed", lambda button: self.update(changed = "B"))
    hbox.pack_start(channel.Bspin, False, False, 0)
    hbox.pack_start(Gtk.Label(label = 6*" "+"Symmetry point:"), False, False, 0)
    channel.SYPspin = SpinButton(.5, 0., 1., 0.001, digits = 4)
    channel.SYPspin.connect("value-changed", lambda button: self.update(changed = "SYP"))
    hbox.pack_start(channel.SYPspin, False, False, 0)
    hbox = Gtk.HBox(spacing = 8)
    cbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Shadow protection point:"), False, False, 0)
    channel.SPPspin = SpinButton(0., 0., 1., 0.001, digits = 4)
    channel.SPPspin.connect("value-changed", lambda button: self.update(changed = "SPP"))
    hbox.pack_start(channel.SPPspin, False, False, 0)
    hbox.pack_start(Gtk.Label(label = 6*" "+"Highlight protection point:"), False, False, 0)
    channel.HPPspin = SpinButton(1., 0., 1., 0.01, digits = 3)
    channel.HPPspin.connect("value-changed", lambda button: self.update(changed = "HPP"))
    hbox.pack_start(channel.HPPspin, False, False, 0)
    #if key == "L":
      #hbox.pack_start(Gtk.Label(label = 4*" "), False, False, 0)
      #channel.highlightsbutton = CheckButton(label = "Preserve highlights")
      #channel.highlightsbutton.set_active(False)
      #channel.highlightsbutton.connect("toggled", lambda button: self.update(changed = "preserve"))
      #hbox.pack_start(channel.highlightsbutton, False, False, 0)
    return cbox

  def add_extra_options(self, hbox):
    """Add extra options in Gtk box 'hbox'."""
    self.widgets.inversebutton = CheckButton(label = "Inverse transformation")
    self.widgets.inversebutton.set_active(False)
    self.widgets.inversebutton.connect("toggled", lambda button: self.update(changed = "inverse"))
    hbox.pack_start(self.widgets.inversebutton, False, False, 0)
    return

  # Tool methods.

  def get_params(self):
    """Return tool parameters."""
    params = {}
    for key in self.channelkeys:
      channel = self.widgets.channels[key]
      lnD1 = channel.lnD1spin.get_value()
      B = channel.Bspin.get_value()
      SYP = channel.SYPspin.get_value()
      SPP = channel.SPPspin.get_value()
      HPP = channel.HPPspin.get_value()
      params[key] = (lnD1, B, SYP, SPP, HPP)
    #params["highlights"] = self.widgets.channels["L"].highlightsbutton.get_active()
    params["inverse"] = self.widgets.inversebutton.get_active()
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
      lnD1, B, SYP, SPP, HPP = params[key]
      channel.lnD1spin.set_value_block(lnD1)
      channel.Bspin.set_value_block(B)
      channel.SYPspin.set_value_block(SYP)
      channel.SPPspin.set_value_block(SPP)
      channel.HPPspin.set_value_block(HPP)
    #self.widgets.channels["L"].highlightsbutton.set_active_block(params["highlights"])
    self.widgets.inversebutton.set_active(params["inverse"])
    if unlinkrgb: self.widgets.linkbutton.set_active_block(False)
    self.update()

  def run(self, params):
    """Run tool for parameters 'params'."""
    self.image.copy_from(self.reference)
    transformed = False
    inverse = params["inverse"]
    for key in self.channelkeys:
      lnD1, B, SYP, SPP, HPP = params[key]
      if not self.outofrange and lnD1 == 0.: continue
      transformed = True
      self.image.generalized_stretch(ghyperbolic_stretch_function, (lnD1, B, SYP, SPP, HPP, inverse), channels = key)
    #if transformed and params["highlights"]:
      #maximum = self.image.image.max()
      #if maximum > 1.: self.image.image /= maximum
    return params, transformed

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    operation =  "GHStretch("
    if params["inverse"]: operation = "Inverse"+operation
    for key in self.channelkeys:
      lnD1, B, SYP, SPP, HPP = params[key]
      if key != "L":
        operation += f"{key} : (ln(D+1) = {lnD1:.4f}, B = {B:.4f}, SYP = {SYP:.4f}, SPP = {SPP:.4f}, HPP = {HPP:.4f}), "
      else:
        red, green, blue = params["rgblum"]
        operation += f"L({red:.2f}, {green:.2f}, {blue:.2f}) : (ln(D+1) = {lnD1:.4f}, B = {B:.4f}, SYP = {SYP:.4f}, SPP = {SPP:.4f}, HPP = {HPP:.4f})"
    #if params["highlights"]: operation += ", preserve highlights"
    operation += ")"
    return operation

  # Plot histograms, stretch function, display stats...

  def stretch_function(self, params, tmin = 0., tmax = 1.):
    """Return (t, f(t)) on a grid tmin <= t <= tmax, where f is the generalized hyperbolic stretch function
       for parameters 'params'."""
    tmin = min(0., tmin)
    tmax = max(1., tmax)
    t = np.linspace(tmin, tmax, int(round(8192*(tmax-tmin))))
    ft = ghyperbolic_stretch_function(np.clip(t, 0., 1.), params)
    return t, ft

  def add_histogram_widgets(self, ax, key):
    """Add histogram widgets (stretch function, ...) in axes 'ax' for channel 'key'."""
    channel = self.widgets.channels[key]
    lnD1 = channel.lnD1spin.get_value()
    B = channel.Bspin.get_value()
    SYP = channel.SYPspin.get_value()
    SPP = channel.SPPspin.get_value()
    HPP = channel.HPPspin.get_value()
    color = channel.color
    lcolor = channel.lcolor
    self.widgets.SPPline = ax.axvline(SPP, color = 0.1*lcolor, linestyle = "-.", zorder = -2)
    self.widgets.SYPline = ax.axvline(SYP, color = 0.5*lcolor, linestyle = "-.", zorder = -2)
    self.widgets.HPPline = ax.axvline(HPP, color = 0.9*lcolor, linestyle = "-.", zorder = -2)
    t = np.linspace(0., 1., 8192)
    ax.plot(t, t, color = "gray", linestyle = ":", linewidth = 1., zorder = -3)
    inverse = self.widgets.inversebutton.get_active()
    t, ft = self.stretch_function((lnD1, B, SYP, SPP, HPP, inverse), tmin = self.histlims[0], tmax = self.histlims[1])
    self.widgets.tfplot, = ax.plot(t, ft, linestyle = ":", color = color, zorder = -1)

  # Update histograms, stats... on widget or keypress events.

  def update_widgets(self, key, changed):
    """Update widgets (other than histograms and stats) on change of 'changed' in channel 'key'."""
    channel = self.widgets.channels[key]
    lnD1 = channel.lnD1spin.get_value()
    B = channel.Bspin.get_value()
    SYP = channel.SYPspin.get_value()
    SPP = channel.SPPspin.get_value()
    HPP = channel.HPPspin.get_value()
    if SPP > SYP:
      SPP = SYP
      channel.SPPspin.set_value_block(SPP)
    if HPP < SYP:
      HPP = SYP
      channel.HPPspin.set_value_block(HPP)
    self.currentparams[key] = (lnD1, B, SYP, SPP, HPP)
    color = channel.color
    lcolor = channel.lcolor
    self.widgets.SPPline.set_xdata([SPP, SPP])
    self.widgets.SPPline.set_color(0.1*lcolor)
    self.widgets.SYPline.set_xdata([SYP, SYP])
    self.widgets.SYPline.set_color(0.5*lcolor)
    self.widgets.HPPline.set_xdata([HPP, HPP])
    self.widgets.HPPline.set_color(0.9*lcolor)
    inverse = self.widgets.inversebutton.get_active()
    t, ft = self.stretch_function((lnD1, B, SYP, SPP, HPP, inverse), tmin = self.histlims[0], tmax = self.histlims[1])
    self.widgets.tfplot.set_xdata(t)
    self.widgets.tfplot.set_ydata(ft)
    self.widgets.tfplot.set_color(color)
    if self.widgets.linkbutton.get_active() and key in ("R", "G", "B"):
      for rgbkey in ("R", "G", "B"):
        rgbchannel = self.widgets.channels[rgbkey]
        rgbchannel.lnD1spin.set_value_block(lnD1)
        rgbchannel.Bspin.set_value_block(B)
        rgbchannel.SYPspin.set_value_block(SYP)
        rgbchannel.SPPspin.set_value_block(SPP)
        rgbchannel.HPPspin.set_value_block(HPP)
        self.currentparams[rgbkey] = (lnD1, B, SYP, SPP, HPP)

  # Callbacks on luminance RGB components update in main window.

  def update_luminance_range(self):
    return
