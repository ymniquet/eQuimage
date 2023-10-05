# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 2023.10 *

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
from .gtk.customwidgets import CheckButton, SpinButton, Notebook
from .base import BaseWindow, BaseToolbar, Container
from .tools import BaseToolWindow
from ..imageprocessing import imageprocessing
import numpy as np
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as ticker

"""Stretch tool."""

class StretchTool(BaseToolWindow):
  """Stretch tool class."""

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Stretch (Shadow/Midtone/Highlight)"): return
    self.window.connect("key-press-event", self.keypress)
    wbox = Gtk.VBox(spacing = 16)
    self.window.add(wbox)
    fbox = Gtk.VBox(spacing = 0)
    wbox.pack_start(fbox, True, True, 0)
    self.widgets.fig = Figure(figsize = (10., 6.), layout = "constrained")
    canvas = FigureCanvas(self.widgets.fig)
    canvas.set_size_request(800, 480)
    fbox.pack_start(canvas, True, True, 0)
    toolbar = BaseToolbar(canvas, self.widgets.fig)
    fbox.pack_start(toolbar, False, False, 0)
    grid = Gtk.Grid(column_spacing = 8)
    wbox.pack_start(grid, True, True, 0)
    reflabel = Gtk.Label(label = "[Reference]", halign = Gtk.Align.START)
    grid.add(reflabel)
    self.widgets.refstats = Gtk.Label(label = "", halign = Gtk.Align.START)
    grid.attach_next_to(self.widgets.refstats, reflabel, Gtk.PositionType.RIGHT, 1, 1)
    imglabel = Gtk.Label(label = "[Image]", halign = Gtk.Align.START)
    grid.attach_next_to(imglabel, reflabel, Gtk.PositionType.BOTTOM, 1, 1)
    self.widgets.imgstats = Gtk.Label(label = "", halign = Gtk.Align.START)
    grid.attach_next_to(self.widgets.imgstats, imglabel, Gtk.PositionType.RIGHT, 1, 1)
    hbox = Gtk.HBox(spacing = 8)
    wbox.pack_start(hbox, False, False, 0)
    self.widgets.linkbutton = CheckButton(label = "Link RGB channels")
    self.widgets.linkbutton.set_active(True)
    self.widgets.linkbutton.connect("toggled", lambda button: self.update(suspend = self.suspendcallbacks))
    hbox.pack_start(self.widgets.linkbutton, True, True, 0)
    self.widgets.lrgbtabs = Notebook()
    self.widgets.lrgbtabs.set_tab_pos(Gtk.PositionType.TOP)
    self.widgets.lrgbtabs.connect("switch-page", lambda tabs, tab, itab: self.update(tab = itab))
    wbox.pack_start(self.widgets.lrgbtabs, False, False, 0)
    self.channelkeys = []
    self.prevparams = {}
    self.currparams = {}
    self.widgets.channels = {}
    for key, name, color, lcolor in (("R", "Red", (1., 0., 0.), (1., 0., 0.)),
                                     ("G", "Green", (0., 1., 0.), (0., 1., 0.)),
                                     ("B", "Blue", (0., 0., 1.), (0., 0., 1.)),
                                     ("V", "HSV value = max(RGB)", (0., 0., 0.), (1., 1., 1.)),
                                     ("L", "Luminance", (0.5, 0.5, 0.5), (1., 1., 1.))):
      self.channelkeys.append(key)
      self.prevparams[key] = (0., 0.5, 1., 0., 1.)
      self.currparams[key] = (0., 0.5, 1., 0., 1.)
      self.widgets.channels[key] = Container()
      channel = self.widgets.channels[key]
      channel.color = np.array(color)
      channel.lcolor = np.array(lcolor)
      tbox = Gtk.VBox(spacing = 16, margin = 16)
      hbox = Gtk.HBox(spacing = 8)
      tbox.pack_start(hbox, False, False, 0)
      hbox.pack_start(Gtk.Label(label = "Shadow:"), False, False, 0)
      channel.shadowspin = SpinButton(0., 0., 0.25, 0.001, digits = 3)
      channel.shadowspin.connect("value-changed", lambda button: self.update(updated = "shadow"))
      hbox.pack_start(channel.shadowspin, False, False, 0)
      hbox.pack_start(Gtk.Label(label = 8*" "+"Midtone:"), False, False, 0)
      channel.midtonespin = SpinButton(0.5, 0., 1., 0.01, digits = 3)
      channel.midtonespin.connect("value-changed", lambda button: self.update(updated = "midtone"))
      hbox.pack_start(channel.midtonespin, False, False, 0)
      hbox.pack_start(Gtk.Label(label = 8*" "+"Highlight:"), False, False, 0)
      channel.highlightspin = SpinButton(1., 0., 1., 0.01, digits = 3)
      channel.highlightspin.connect("value-changed", lambda button: self.update(updated = "highlight"))
      hbox.pack_start(channel.highlightspin, False, False, 0)
      hbox = Gtk.HBox(spacing = 8)
      tbox.pack_start(hbox, False, False, 0)
      hbox.pack_start(Gtk.Label(label = "Low range:"), False, False, 0)
      channel.lowspin = SpinButton(0., -10., 0., 0.01, digits = 3)
      channel.lowspin.connect("value-changed", lambda button: self.update(updated = "low"))
      hbox.pack_start(channel.lowspin, False, False, 0)
      hbox.pack_start(Gtk.Label(label = 8*" "+"High range:"), False, False, 0)
      channel.highspin = SpinButton(1., 1., 10., 0.01, digits = 3)
      channel.highspin.connect("value-changed", lambda button: self.update(updated = "high"))
      hbox.pack_start(channel.highspin, False, False, 0)
      self.widgets.lrgbtabs.append_page(tbox, Gtk.Label(label = name))
    wbox.pack_start(self.apply_cancel_reset_close_buttons(), False, False, 0)
    self.widgets.logscale = False
    self.widgets.fig.refhistax = self.widgets.fig.add_subplot(211)
    self.plot_reference_histogram()
    self.widgets.fig.imghistax = self.widgets.fig.add_subplot(212)
    self.plot_image_histogram()
    self.app.mainwindow.set_images(OD(Image = self.image, Reference = self.reference), reference = "Reference")
    self.app.mainwindow.set_rgb_luminance_callback(self.update_rgb_luminance)
    self.window.show_all()
    self.widgets.lrgbtabs.set_current_page(3)

  def reset(self, *args, **kwargs):
    """Reset tool."""
    unlinkrgb = False
    redparams = self.prevparams["R"]
    for key in self.channelkeys:
      channel = self.widgets.channels[key]
      if key in ("R", "G", "B"):
        unlinkrgb = unlinkrgb or (self.prevparams[key] != redparams)
      shadow, midtone, highlight, low, high = self.prevparams[key]
      channel.shadowspin.set_value_block(shadow)
      channel.midtonespin.set_value_block(midtone)
      channel.highlightspin.set_value_block(highlight)
      channel.lowspin.set_value_block(low)
      channel.highspin.set_value_block(high)
    if unlinkrgb: self.widgets.linkbutton.set_active(False)
    self.update()

  def apply(self, *args, **kwargs):
    """Apply tool."""
    self.image.copy_from(self.reference)
    self.operation = "Stretch("
    for key in self.channelkeys:
      channel = self.widgets.channels[key]
      shadow = channel.shadowspin.get_value()
      midtone = channel.midtonespin.get_value()
      highlight = channel.highlightspin.get_value()
      low = channel.lowspin.get_value()
      high = channel.highspin.get_value()
      if key != "L":
        self.operation += f"{key} : (shadow = {shadow:.3f}, midtone = {midtone:.3f}, highlight = {highlight:.3f}, low = {low:.3f}, high = {high:.3f}), "
      else:
        red, green, blue = imageprocessing.get_rgb_luminance()
        self.operation += f"L({red:.2f}, {green:.2f}, {blue:.2f}) : (shadow = {shadow:.3f}, midtone = {midtone:.3f}, highlight = {highlight:.3f}, low = {low:.3f}, high = {high:.3f}))"
      self.prevparams[key] = (shadow, midtone, highlight, low, high)
      if shadow == 0. and midtone == 0.5 and highlight == 1. and low == 0. and high == 1.: continue
      print(f"Stretching {key} channel...")
      self.image.clip_shadows_highlights(shadow, highlight, channels = key)
      self.image.midtone_correction((midtone-shadow)/(highlight-shadow), channels = key)
      self.image.set_dynamic_range((low, high), (0., 1.), channels = key)
    self.app.mainwindow.update_image("Image", self.image)
    self.plot_image_histogram()
    self.widgets.cancelbutton.set_sensitive(True)

  def cancel(self, *args, **kwargs):
    """Cancel tool."""
    if self.operation is None: return
    self.image.copy_from(self.reference)
    self.app.mainwindow.update_image("Image", self.image)
    self.plot_image_histogram()
    self.operation = None
    for key in self.channelkeys:
      channel = self.widgets.channels[key]
      channel.shadowspin.set_value_block(0.)
      channel.midtonespin.set_value_block(0.5)
      channel.highlightspin.set_value_block(1.)
      channel.lowspin.set_value_block(0.)
      channel.highspin.set_value_block(1.)
      self.prevparams[key] = (0., 0.5, 1., 0., 1.)
    self.update()
    self.widgets.cancelbutton.set_sensitive(False)

  # Display stats, histograms, transfer function...

  def display_stats(self, key):
    """Display reference and image stats for channel 'key'."""
    channel = {"R": "Red", "G": "Green", "B": "Blue", "V": "Value", "L": "Luminance"}[key]
    npixels = self.reference.image[0].size
    if self.reference.stats is not None:
      minimum, maximum, median, zerocount, orngcount = self.reference.stats[key]
      string = f"{channel} : min = {minimum:.3f}, max = {maximum:.3f}, med = {median:.3f}, {zerocount} ({100.*zerocount/npixels:.2f}%) zeros, {orngcount} ({100.*orngcount/npixels:.2f}%) out-of-range"
      self.widgets.refstats.set_label(string)
    if self.image.stats is not None:
      minimum, maximum, median, zerocount, orngcount = self.image.stats[key]
      string = f"{channel} : min = {minimum:.3f}, max = {maximum:.3f}, med = {median:.3f}, {zerocount} ({100.*zerocount/npixels:.2f}%) zeros, {orngcount} ({100.*orngcount/npixels:.2f}%) out-of-range"
      self.widgets.imgstats.set_label(string)

  def transfer_function(self, shadow, midtone, highlight, low, high, maxlum = 2.):
    """Return (t, f(t)) on a grid 0 < t < 'maxlum', where f is the transfer function for
       'shadow', 'midtone', 'highlight', 'low', and 'high' parameters."""
    t = np.linspace(0., maxlum, int(256*maxlum))
    clipped = np.clip(t, shadow, highlight)
    expanded = np.interp(clipped, (shadow, highlight), (0., 1.))
    corrected = imageprocessing.midtone_transfer_function(expanded, (midtone-shadow)/(highlight-shadow))
    ft = np.interp(corrected, (low, high), (0., 1.))
    return t, ft

  def plot_histogram(self, ax, image, title = None, xlabel = "Level", ylabel = "Count (a.u.)", ylogscale = False):
    """Plot histogram for image 'image' on axes 'ax' with title 'title', x label 'xlabel' and y label 'ylabel'.
       Use log scale on y-axis if ylogscale is True."""
    edges, hists = image.histograms(nbins = 128)
    centers = (edges[:-1]+edges[1:])/2.
    hists /= hists[:, 1:].max()
    ax.clear()
    ax.plot(centers, hists[0], "-", color = self.widgets.channels["R"].color)
    ax.plot(centers, hists[1], "-", color = self.widgets.channels["G"].color)
    ax.plot(centers, hists[2], "-", color = self.widgets.channels["B"].color)
    ax.plot(centers, hists[3], "-", color = self.widgets.channels["V"].color)
    ax.plot(centers, hists[4], "-", color = self.widgets.channels["L"].color)
    xmax = max(1., centers[-1])
    ax.set_xlim(0., xmax)
    if xlabel is not None: ax.set_xlabel(xlabel)
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(5))
    if ylogscale:
      ax.set_yscale("log")
      ax.set_ylim(np.min(hists[hists > 0.]), 1.)
    else:
      ax.set_yscale("linear")
      ax.set_ylim(0., 1.)
      ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(5))
    if ylabel is not None: ax.set_ylabel(ylabel)
    ax.axvspan(1., 10., color = "gray", alpha = 0.25)
    if title is not None: ax.set_title(title)

  def plot_reference_histogram(self):
    """Plot reference histogram."""
    suspendcallbacks = self.suspendcallbacks
    self.suspendcallbacks = True
    ax = self.widgets.fig.refhistax
    ax.clear()
    self.plot_histogram(ax, self.reference, title = "[Reference]", xlabel = None, ylabel = "Count (a.u.)/Transf. func.", ylogscale = self.widgets.logscale)
    tab = self.widgets.lrgbtabs.get_current_page()
    key = self.channelkeys[tab]
    channel = self.widgets.channels[key]
    shadow = channel.shadowspin.get_value()
    midtone = channel.midtonespin.get_value()
    highlight = channel.highlightspin.get_value()
    low = channel.lowspin.get_value()
    high = channel.highspin.get_value()
    color = channel.color
    lcolor = channel.lcolor
    self.widgets.shadowline = ax.axvline(shadow, color = 0.1*lcolor, linestyle = "-.")
    self.widgets.midtoneline = ax.axvline(midtone, color = 0.5*lcolor, linestyle = "-.")
    self.widgets.highlightline = ax.axvline(highlight, color = 0.9*lcolor, linestyle = "-.")
    t, ft = self.transfer_function(shadow, midtone, highlight, low, high)
    self.widgets.tfplot, = ax.plot(t, ft, linestyle = ":", color = color)
    self.widgets.fig.canvas.draw_idle()
    self.reference.stats = self.reference.statistics()
    self.display_stats(key)
    self.suspendcallbacks = suspendcallbacks

  def plot_image_histogram(self):
    """Plot image histogram."""
    suspendcallbacks = self.suspendcallbacks
    self.suspendcallbacks = True
    ax = self.widgets.fig.imghistax
    ax.clear()
    self.plot_histogram(ax, self.image, title = "[Image]", ylogscale = self.widgets.logscale)
    self.widgets.fig.canvas.draw_idle()
    self.image.stats = self.image.statistics()
    tab = self.widgets.lrgbtabs.get_current_page()
    key = self.channelkeys[tab]
    self.display_stats(key)
    self.suspendcallbacks = suspendcallbacks

  # Update stats, histograms, transfer function... on widget or keypress events.

  def update(self, *args, **kwargs):
    """Update histograms."""
    if "suspend" in kwargs.keys():
      if kwargs["suspend"]: return
    self.suspendcallbacks = True
    if "tab" in kwargs.keys():
      tab = kwargs["tab"]
      key = self.channelkeys[tab]
      self.display_stats(key)
    else:
      tab = self.widgets.lrgbtabs.get_current_page()
      key = self.channelkeys[tab]
    updated = kwargs["updated"] if "updated" in kwargs.keys() else None
    channel = self.widgets.channels[key]
    color = channel.color
    lcolor = channel.lcolor
    shadow = channel.shadowspin.get_value()
    midtone = channel.midtonespin.get_value()
    highlight = channel.highlightspin.get_value()
    low = channel.lowspin.get_value()
    high = channel.highspin.get_value()
    if highlight < shadow+0.05:
      highlight = shadow+0.05
      channel.highlightspin.set_value_block(highlight)
    if updated in ["shadow", "highlight"]:
      shadow_, midtone_, highlight_, low_, high_ = self.currparams[key]
      midtone_ = (midtone_-shadow_)/(highlight_-shadow_)
      midtone = shadow+midtone_*(highlight-shadow)
      channel.midtonespin.set_value_block(midtone)
    if midtone <= shadow:
      midtone = shadow+0.001
      channel.midtonespin.set_value_block(midtone)
    if midtone >= highlight:
      midtone = highlight-0.001
      channel.midtonespin.set_value_block(midtone)
    self.currparams[key] = (shadow, midtone, highlight, low, high)
    self.widgets.shadowline.set_color(0.1*lcolor)
    self.widgets.shadowline.set_xdata([shadow, shadow])
    self.widgets.midtoneline.set_color(0.5*lcolor)
    self.widgets.midtoneline.set_xdata([midtone, midtone])
    self.widgets.highlightline.set_color(0.9*lcolor)
    self.widgets.highlightline.set_xdata([highlight, highlight])
    self.widgets.tfplot.set_color(color)
    t, ft = self.transfer_function(shadow, midtone, highlight, low, high)
    self.widgets.tfplot.set_xdata(t)
    self.widgets.tfplot.set_ydata(ft)
    self.widgets.fig.canvas.draw_idle()
    if self.widgets.linkbutton.get_active() and key in ("R", "G", "B"):
      for rgbkey in ("R", "G", "B"):
        rgbchannel = self.widgets.channels[rgbkey]
        rgbchannel.shadowspin.set_value_block(shadow)
        rgbchannel.midtonespin.set_value_block(midtone)
        rgbchannel.highlightspin.set_value_block(highlight)
        rgbchannel.lowspin.set_value_block(low)
        rgbchannel.highspin.set_value_block(high)
        self.currparams[rgbkey] = (shadow, midtone, highlight, low, high)
    self.suspendcallbacks = False

  def keypress(self, widget, event):
    """Callback for key press in the stretch tool window."""
    keyname = Gdk.keyval_name(event.keyval).upper()
    if keyname == "L":
      self.widgets.logscale = not self.widgets.logscale
      self.plot_reference_histogram()
      self.plot_image_histogram()

  # Callback on luminance RGB components update in main window.

  def update_rgb_luminance(self, rgblum):
    """Update luminance rgb components."""
    self.plot_reference_histogram()
    self.plot_image_histogram()
