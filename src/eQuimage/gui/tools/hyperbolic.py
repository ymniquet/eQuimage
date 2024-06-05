# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.5.1 / 2024.06.05
# GUI updated.

"""Hyperbolic stretch tool."""

from .stretch import StretchTool
from ..gtk.customwidgets import HBox, VBox, CheckButton, SpinButton
from ...imageprocessing import imageprocessing
from ...imageprocessing.stretchfunctions import ghyperbolic_stretch_function

class GeneralizedHyperbolicStretchTool(StretchTool):
  """Generalized hyperbolic stretch tool class, derived from the StretchTool class."""

  _action_ = "Stretching histograms (generalized hyperbolic stretch function)..."

  # Build window.

  _window_name_ = "Generalized hyperbolic stretch"

  def options_widgets(self, widgets):
    """Return a box with tool options widgets and store the reference to these widgets in container 'widgets'.
       Return None if there are no tool options widgets."""
    hbox = HBox()
    widgets.bindbutton = CheckButton(label = "Bind RGB channels")
    widgets.bindbutton.set_active(True)
    widgets.bindbutton.connect("toggled", lambda button: self.update("bindrgb"))
    hbox.pack(widgets.bindbutton, expand = True, fill = True)
    widgets.inversebutton = CheckButton(label = "Inverse transformation")
    widgets.inversebutton.set_active(False)
    widgets.inversebutton.connect("toggled", lambda button: self.update("inverse"))
    hbox.pack(widgets.inversebutton)
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
    widgets.logD1spin = SpinButton(0., 0., 10., .1, digits = 3)
    widgets.logD1spin.connect("value-changed", lambda button: self.update("D"))
    hbox.pack("Global log(D+1):")
    hbox.pack(widgets.logD1spin)
    widgets.Bspin = SpinButton(0, -5., 15., .1, digits = 3)
    widgets.Bspin.connect("value-changed", lambda button: self.update("B"))
    hbox.pack(5*" "+"Local B:")
    hbox.pack(widgets.Bspin)
    widgets.SYPspin = SpinButton(.5, 0., 1., step/2., digits = 5)
    widgets.SYPspin.connect("value-changed", lambda button: self.update("SYP"))
    hbox.pack(5*" "+"Symmetry point:")
    hbox.pack(widgets.SYPspin)
    hbox = HBox()
    cbox.pack(hbox)
    widgets.SPPspin = SpinButton(0., 0., .99, step/2., digits = 5)
    widgets.SPPspin.connect("value-changed", lambda button: self.update("SPP"))
    hbox.pack("Shadow protection point:")
    hbox.pack(widgets.SPPspin)
    widgets.HPPspin = SpinButton(1., .01, 1., step, digits = 5)
    widgets.HPPspin.connect("value-changed", lambda button: self.update("HPP"))
    hbox.pack(5*" "+"Highlight protection point:")
    hbox.pack(widgets.HPPspin)
    if key == "L":
      widgets.highlightsbutton = CheckButton(label = "Protect highlights")
      widgets.highlightsbutton.set_active(False)
      widgets.highlightsbutton.connect("toggled", lambda button: self.update(None))
      hbox.pack(5*" ")
      hbox.pack(widgets.highlightsbutton)
    return cbox

  # Tool methods.

  def get_params(self):
    """Return tool parameters."""
    params = {}
    for key in self.channelkeys:
      channel = self.widgets.channels[key]
      logD1 = channel.logD1spin.get_value()
      B = channel.Bspin.get_value()
      SYP = channel.SYPspin.get_value()
      SPP = channel.SPPspin.get_value()
      HPP = channel.HPPspin.get_value()
      params[key] = (logD1, B, SYP, SPP, HPP)
    params["highlights"] = self.widgets.channels["L"].highlightsbutton.get_active()
    params["inverse"] = self.widgets.inversebutton.get_active()
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
      logD1, B, SYP, SPP, HPP = params[key]
      channel.logD1spin.set_value_block(logD1)
      channel.Bspin.set_value_block(B)
      channel.SYPspin.set_value_block(SYP)
      channel.SPPspin.set_value_block(SPP)
      channel.HPPspin.set_value_block(HPP)
    self.widgets.channels["L"].highlightsbutton.set_active_block(params["highlights"])
    self.widgets.inversebutton.set_active(params["inverse"])
    if unbindrgb: self.widgets.bindbutton.set_active_block(False)
    self.update("all")

  def run(self, params):
    """Run tool for parameters 'params'."""
    self.image.copy_image_from(self.reference)
    transformed = False
    inverse = params["inverse"]
    for key in self.channelkeys:
      logD1, B, SYP, SPP, HPP = params[key]
      outofrange = self.outofrange and key in ["R", "G", "B"]
      if not outofrange and logD1 == 0.: continue
      transformed = True
      self.image.generalized_stretch(ghyperbolic_stretch_function, (logD1, B, SYP, SPP, HPP, inverse), channels = key)
    if transformed and params["highlights"]: self.image.protect_highlights()
    return params, transformed

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    operation = "GHStretch("
    if params["inverse"]: operation = "Inverse"+operation
    separator = ""
    for key in self.channelkeys:
      logD1, B, SYP, SPP, HPP = params[key]
      if key == "L":
        red, green, blue = params["rgbluma"]
        operation += f"{separator}L({red:.2f}, {green:.2f}, {blue:.2f}) : (log(D+1) = {logD1:.3f}, B = {B:.3f}, SYP = {SYP:.5f}, SPP = {SPP:.5f}, HPP = {HPP:.5f})"
      else:
        operation += f"{separator}{key} : (log(D+1) = {logD1:.3f}, B = {B:.3f}, SYP = {SYP:.5f}, SPP = {SPP:.5f}, HPP = {HPP:.5f})"
      separator = ", "
    if params["highlights"]: operation += ", protect highlights"
    operation += ")"
    return operation

  # Plot histograms, stretch function, display stats...

  def stretch_function(self, t, params):
    """Return the stretch function f(t) for parameters 'params'."""
    return ghyperbolic_stretch_function(t, params)

  def add_histogram_widgets(self, ax):
    """Add histogram widgets (other than stretch function) in axes 'ax'."""
    self.widgets.SPPline = ax.axvline(0., linestyle = "-.", zorder = -2)
    self.widgets.SYPline = ax.axvline(.5, linestyle = "-.", zorder = -2)
    self.widgets.HPPline = ax.axvline(1., linestyle = "-.", zorder = -2)

  # Update histograms, stats... on widget or key_press events.

  def update_widgets(self, key, changed):
    """Update widgets (other than histograms and stats) on change of 'changed' in channel 'key'."""
    channel = self.widgets.channels[key]
    logD1 = channel.logD1spin.get_value()
    B = channel.Bspin.get_value()
    SYP = channel.SYPspin.get_value()
    SPP = channel.SPPspin.get_value()
    HPP = channel.HPPspin.get_value()
    if changed == "SPP":
      if SPP > HPP-.005:
        SPP = HPP-.005
        channel.SPPspin.set_value_block(SPP)
      if SPP > SYP:
        SYP = SPP
        channel.SYPspin.set_value_block(SYP)
    elif changed == "HPP":
      if HPP < SPP+.005:
        HPP = SPP+.005
        channel.HPPspin.set_value_block(HPP)
      if HPP < SYP:
        SYP = HPP
        channel.SYPspin.set_value_block(SYP)
    elif changed == "SYP":
      if SYP < SPP:
        SPP = SYP
        channel.SPPspin.set_value_block(SPP)
      elif SYP > HPP:
        HPP = SYP
        channel.HPPspin.set_value_block(HPP)
    color = channel.color
    lcolor = channel.lcolor
    self.widgets.SPPline.set_xdata([SPP, SPP])
    self.widgets.SPPline.set_color(.1*lcolor)
    self.widgets.SYPline.set_xdata([SYP, SYP])
    self.widgets.SYPline.set_color(.5*lcolor)
    self.widgets.HPPline.set_xdata([HPP, HPP])
    self.widgets.HPPline.set_color(.9*lcolor)
    inverse = self.widgets.inversebutton.get_active()
    self.plot_stretch_function(lambda t: self.stretch_function(t, (logD1, B, SYP, SPP, HPP, inverse)), color)
    if self.widgets.bindbutton.get_active() and key in ("R", "G", "B"):
      for rgbkey in ("R", "G", "B"):
        rgbchannel = self.widgets.channels[rgbkey]
        rgbchannel.logD1spin.set_value_block(logD1)
        rgbchannel.Bspin.set_value_block(B)
        rgbchannel.SYPspin.set_value_block(SYP)
        rgbchannel.SPPspin.set_value_block(SPP)
        rgbchannel.HPPspin.set_value_block(HPP)
