# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2024.01.05

"""Midtone stretch tool."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
from .gtk.customwidgets import CheckButton, SpinButton, Notebook
from .base import BaseWindow, BaseToolbar, Container
from .tools import BaseToolWindow
from .utils import plot_histograms, highlight_histogram, stats_string
from ..imageprocessing import imageprocessing
from ..imageprocessing.stretchfunctions import midtone_stretch_function
import numpy as np
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure

class StretchTool(BaseToolWindow):
  """Midtone stretch tool class."""

  __action__ = "Stretching histograms (midtone stretch function)..."

  # Build window.

  __window_name__ = "Midtone stretch"

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, self.__window_name__): return False
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
    reflabel = Gtk.Label(halign = Gtk.Align.START)
    reflabel.set_markup("<b>Reference</b>")
    grid.add(reflabel)
    self.widgets.refstats = Gtk.Label(label = "", halign = Gtk.Align.START)
    grid.attach_next_to(self.widgets.refstats, reflabel, Gtk.PositionType.RIGHT, 1, 1)
    imglabel = Gtk.Label(halign = Gtk.Align.START)
    imglabel.set_markup("<b>Image</b>")
    grid.attach_next_to(imglabel, reflabel, Gtk.PositionType.BOTTOM, 1, 1)
    self.widgets.imgstats = Gtk.Label(label = "", halign = Gtk.Align.START)
    grid.attach_next_to(self.widgets.imgstats, imglabel, Gtk.PositionType.RIGHT, 1, 1)
    hbox = Gtk.HBox(spacing = 8)
    wbox.pack_start(hbox, False, False, 0)
    self.widgets.linkbutton = CheckButton(label = "Link RGB channels")
    self.widgets.linkbutton.set_active(True)
    self.widgets.linkbutton.connect("toggled", lambda button: self.update(changed = "rgblink"))
    hbox.pack_start(self.widgets.linkbutton, False, False, 0)
    self.add_extra_options(hbox)
    hbox.pack_start(Gtk.Label("Press [L] to toggle lin/log scales", halign = Gtk.Align.END), True, True, 0)
    self.widgets.rgbtabs = Notebook()
    self.widgets.rgbtabs.set_tab_pos(Gtk.PositionType.TOP)
    wbox.pack_start(self.widgets.rgbtabs, False, False, 0)
    self.reference.stats = self.reference.statistics() # Reference image statistics.
    self.channelkeys = []
    self.widgets.channels = {}
    for key, name, color, lcolor in (("R", "Red", (1., 0., 0.), (1., 0., 0.)),
                                     ("G", "Green", (0., 1., 0.), (0., 1., 0.)),
                                     ("B", "Blue", (0., 0., 1.), (0., 0., 1.)),
                                     ("V", "HSV value = max(RGB)", (0., 0., 0.), (1., 1., 1.)),
                                     ("L", "Luminance", (0.5, 0.5, 0.5), (1., 1., 1.))):
      self.channelkeys.append(key)
      self.widgets.channels[key] = Container()
      channel = self.widgets.channels[key]
      channel.color = np.array(color)
      channel.lcolor = np.array(lcolor)
      self.widgets.rgbtabs.append_page(self.add_tab_widgets(key, channel), Gtk.Label(label = name))
    wbox.pack_start(self.tool_control_buttons(), False, False, 0)
    self.defaultparams = self.get_params()
    self.currentparams = self.get_params()
    self.toolparams = self.get_params()
    self.histbins = 1024 if self.app.get_color_depth() > 8 else 128
    self.histcolors = (self.widgets.channels["R"].color, self.widgets.channels["G"].color, self.widgets.channels["B"].color,
                       self.widgets.channels["V"].color, self.widgets.channels["L"].color)
    self.histlogscale = False
    self.widgets.fig.refhistax = self.widgets.fig.add_subplot(211)
    self.plot_reference_histograms()
    self.widgets.fig.imghistax = self.widgets.fig.add_subplot(212)
    self.plot_image_histograms()
    self.app.mainwindow.set_rgb_luminance_callback(self.update_rgb_luminance)
    self.widgets.rgbtabs.set_current_page(3)
    self.widgets.rgbtabs.connect("switch-page", lambda tabs, tab, itab: self.update(tab = itab))
    self.outofrange = self.reference.is_out_of_range() # Is reference image out-of-range ?
    if self.outofrange: # If so, stretch tool will clip it whatever the input parameters.
      print("Reference image is out-of-range...")
      self.default_params_are_identity(False)
      if self.onthefly: self.apply(cancellable = False)
    self.window.show_all()
    self.start_polling()
    return True

  def add_tab_widgets(self, key, channel):
    """Return Gtk box for tab 'key' in "R" (red), "G" (green), "B" (blue), "V" (value) or "L" (luminance).
       Store the tab widgets in container 'channel'."""
    minimum = min(0., self.reference.stats[key].minimum)
    maximum = max(1., self.reference.stats[key].maximum)
    cbox = Gtk.VBox(spacing = 16, margin = 16)
    hbox = Gtk.HBox(spacing = 8)
    cbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Shadow:"), False, False, 0)
    channel.shadowspin = SpinButton(0., minimum, 1., 0.001, digits = 3)
    channel.shadowspin.connect("value-changed", lambda button: self.update(changed = "shadow"))
    hbox.pack_start(channel.shadowspin, False, False, 0)
    hbox.pack_start(Gtk.Label(label = 8*" "+"Midtone:"), False, False, 0)
    channel.midtonespin = SpinButton(0.5, minimum, maximum, 0.01, digits = 3)
    channel.midtonespin.connect("value-changed", lambda button: self.update(changed = "midtone"))
    hbox.pack_start(channel.midtonespin, False, False, 0)
    hbox.pack_start(Gtk.Label(label = 8*" "+"Highlight:"), False, False, 0)
    channel.highlightspin = SpinButton(1., 0., maximum, 0.01, digits = 3)
    channel.highlightspin.connect("value-changed", lambda button: self.update(changed = "highlight"))
    hbox.pack_start(channel.highlightspin, False, False, 0)
    hbox = Gtk.HBox(spacing = 8)
    cbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Low range:"), False, False, 0)
    channel.lowspin = SpinButton(0., -10., 0., 0.01, digits = 3)
    channel.lowspin.connect("value-changed", lambda button: self.update(changed = "low"))
    hbox.pack_start(channel.lowspin, False, False, 0)
    hbox.pack_start(Gtk.Label(label = 8*" "+"High range:"), False, False, 0)
    channel.highspin = SpinButton(1., 1., 10., 0.01, digits = 3)
    channel.highspin.connect("value-changed", lambda button: self.update(changed = "high"))
    hbox.pack_start(channel.highspin, False, False, 0)
    if key == "L":
      hbox.pack_start(Gtk.Label(label = 8*" "), False, False, 0)
      channel.highlightsbutton = CheckButton(label = "Preserve highlights")
      channel.highlightsbutton.set_active(False)
      channel.highlightsbutton.connect("toggled", lambda button: self.update(changed = "preserve"))
      hbox.pack_start(channel.highlightsbutton, False, False, 0)
    return cbox

  def add_extra_options(self, hbox):
    """Add extra options in Gtk box 'hbox'."""
    return

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
    unlinkrgb = False
    redparams = params["R"]
    for key in self.channelkeys:
      channel = self.widgets.channels[key]
      if key in ("R", "G", "B"):
        unlinkrgb = unlinkrgb or (params[key] != redparams)
      shadow, midtone, highlight, low, high = params[key]
      channel.shadowspin.set_value_block(shadow)
      channel.midtonespin.set_value_block(midtone)
      channel.highlightspin.set_value_block(highlight)
      channel.lowspin.set_value_block(low)
      channel.highspin.set_value_block(high)
    self.widgets.channels["L"].highlightsbutton.set_active_block(params["highlights"])
    if unlinkrgb: self.widgets.linkbutton.set_active_block(False)
    self.update()

  def run(self, params):
    """Run tool for parameters 'params'."""
    self.image.copy_from(self.reference)
    transformed = False
    for key in self.channelkeys:
      shadow, midtone, highlight, low, high = params[key]
      if not self.outofrange and shadow == 0. and midtone == 0.5 and highlight == 1. and low == 0. and high == 1.: continue
      transformed = True
      self.image.clip_shadows_highlights(shadow, highlight, channels = key)
      self.image.midtone_correction((midtone-shadow)/(highlight-shadow), channels = key)
      self.image.set_dynamic_range((low, high), (0., 1.), channels = key)
    if transformed and params["highlights"]:
      maximum = self.image.image.max()
      if maximum > 1.: self.image.image /= maximum
    return params, transformed

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    operation =  "MTStretch("
    for key in self.channelkeys:
      shadow, midtone, highlight, low, high = params[key]
      if key != "L":
        operation += f"{key} : (shadow = {shadow:.3f}, midtone = {midtone:.3f}, highlight = {highlight:.3f}, low = {low:.3f}, high = {high:.3f}), "
      else:
        red, green, blue = params["rgblum"]
        operation += f"L({red:.2f}, {green:.2f}, {blue:.2f}) : (shadow = {shadow:.3f}, midtone = {midtone:.3f}, highlight = {highlight:.3f}, low = {low:.3f}, high = {high:.3f})"
    if params["highlights"]: operation += ", preserve highlights"
    operation += ")"
    return operation

  def update_gui(self):
    """Update main window and image histogram."""
    self.plot_image_histograms()
    self.widgets.fig.canvas.draw_idle()
    super().update_gui()

  # Plot histograms, stretch function, display stats...

  def plot_reference_histograms(self):
    """Plot reference histograms."""
    edges, hists = self.reference.histograms(self.histbins)
    self.histlims = (edges[0], edges[-1])
    ax = self.widgets.fig.refhistax
    ax.histlines = plot_histograms(ax, (edges, hists), colors = self.histcolors,
                                   title = "Reference", xlabel = None, ylabel = "Count (a.u.)/Stretch fn", ylogscale = self.histlogscale)
    tab = self.widgets.rgbtabs.get_current_page()
    key = self.channelkeys[tab]
    highlight_histogram(self.widgets.fig.refhistax.histlines, tab)
    self.add_histogram_widgets(ax, key)
    self.reference.stats = self.reference.statistics()
    self.display_stats(key)

  def plot_image_histograms(self):
    """Plot image histograms."""
    ax = self.widgets.fig.imghistax
    ax.histlines = plot_histograms(ax, self.image.histograms(self.histbins), colors = self.histcolors,
                                   title = "Image", ylogscale = self.histlogscale)
    tab = self.widgets.rgbtabs.get_current_page()
    key = self.channelkeys[tab]
    highlight_histogram(self.widgets.fig.imghistax.histlines, tab)
    self.image.stats = self.image.statistics()
    self.display_stats(key)

  def display_stats(self, key):
    """Display reference and image statistics for channel 'key'."""
    self.widgets.refstats.set_label(stats_string(self.reference, key))
    self.widgets.imgstats.set_label(stats_string(self.image, key))

  def stretch_function(self, shadow, midtone, highlight, low, high, tmin = 0., tmax = 1.):
    """Return (t, f(t)) on a grid tmin <= t <= tmax, where f is the stretch function for
       'shadow', 'midtone', 'highlight', 'low', and 'high' parameters."""
    tmin = min(0., tmin)
    tmax = max(1., tmax)
    t = np.linspace(tmin, tmax, int(round(256*(tmax-tmin))))
    clipped = np.clip(t, shadow, highlight)
    expanded = np.interp(clipped, (shadow, highlight), (0., 1.))
    corrected = midtone_stretch_function(expanded, (midtone-shadow)/(highlight-shadow))
    ft = np.interp(corrected, (low, high), (0., 1.))
    return t, ft

  def add_histogram_widgets(self, ax, key):
    """Add histogram widgets (stretch function, ...) in axes 'ax' for channel 'key'."""
    channel = self.widgets.channels[key]
    shadow = channel.shadowspin.get_value()
    midtone = channel.midtonespin.get_value()
    highlight = channel.highlightspin.get_value()
    low = channel.lowspin.get_value()
    high = channel.highspin.get_value()
    color = channel.color
    lcolor = channel.lcolor
    self.widgets.shadowline = ax.axvline(shadow, color = 0.1*lcolor, linestyle = "-.", zorder = -2)
    self.widgets.midtoneline = ax.axvline(midtone, color = 0.5*lcolor, linestyle = "-.", zorder = -2)
    self.widgets.highlightline = ax.axvline(highlight, color = 0.9*lcolor, linestyle = "-.", zorder = -2)
    #t = np.linspace(0., 1., 128)
    #ax.plot(t, t, color = "gray", linestyle = ":", linewidth = 1., zorder = -3)
    t, ft = self.stretch_function(shadow, midtone, highlight, low, high, tmin = self.histlims[0], tmax = self.histlims[1])
    self.widgets.tfplot, = ax.plot(t, ft, color = color, linestyle = ":", zorder = -1)

  # Update histograms, stats... on widget or keypress events.

  def update(self, *args, **kwargs):
    """Update histograms, stats and widgets."""
    if "tab" in kwargs.keys():
      tab = kwargs["tab"]
      key = self.channelkeys[tab]
      highlight_histogram(self.widgets.fig.refhistax.histlines, tab)
      highlight_histogram(self.widgets.fig.imghistax.histlines, tab)
      self.display_stats(key)
    else:
      tab = self.widgets.rgbtabs.get_current_page()
      key = self.channelkeys[tab]
    changed = kwargs["changed"] if "changed" in kwargs.keys() else None
    self.update_widgets(key, changed)
    self.widgets.fig.canvas.draw_idle()
    if changed is not None: self.reset_polling(self.get_params()) # Expedite main window update.

  def update_widgets(self, key, changed):
    """Update widgets (other than histograms and stats) on change of 'changed' in channel 'key'."""
    channel = self.widgets.channels[key]
    shadow = channel.shadowspin.get_value()
    midtone = channel.midtonespin.get_value()
    highlight = channel.highlightspin.get_value()
    low = channel.lowspin.get_value()
    high = channel.highspin.get_value()
    if highlight < shadow+0.05:
      highlight = shadow+0.05
      channel.highlightspin.set_value_block(highlight)
    if changed in ["shadow", "highlight"]:
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
    t, ft = self.stretch_function(shadow, midtone, highlight, low, high, tmin = self.histlims[0], tmax = self.histlims[1])
    self.widgets.tfplot.set_xdata(t)
    self.widgets.tfplot.set_ydata(ft)
    self.widgets.tfplot.set_color(color)
    if self.widgets.linkbutton.get_active() and key in ("R", "G", "B"):
      for rgbkey in ("R", "G", "B"):
        rgbchannel = self.widgets.channels[rgbkey]
        rgbchannel.shadowspin.set_value_block(shadow)
        rgbchannel.midtonespin.set_value_block(midtone)
        rgbchannel.highlightspin.set_value_block(highlight)
        rgbchannel.lowspin.set_value_block(low)
        rgbchannel.highspin.set_value_block(high)
        self.currentparams[rgbkey] = (shadow, midtone, highlight, low, high)

  def keypress(self, widget, event):
    """Callback for key press in the stretch tool window."""
    keyname = Gdk.keyval_name(event.keyval).upper()
    if keyname == "L": # Toggle log scale.
      self.histlogscale = not self.histlogscale
      self.plot_reference_histograms()
      self.plot_image_histograms()
      self.widgets.fig.canvas.draw_idle()
      self.window.queue_draw()

  # Callbacks on luminance RGB components update in main window.

  def update_rgb_luminance(self, rgblum):
    """Update luminance rgb components."""
    self.plot_reference_histograms()
    self.plot_image_histograms()
    self.widgets.fig.canvas.draw_idle()
    self.update_luminance_range()
    self.window.queue_draw()

  def update_luminance_range(self):
    """Update luminance range in spin or scale widgets."""
    minimum = min(0., self.reference.stats["L"].minimum)
    maximum = max(1., self.reference.stats["L"].maximum)
    self.widgets.channels["L"].shadowspin.set_range(minimum, 1.)
    self.widgets.channels["L"].midtonespin.set_range(minimum, maximum)
    self.widgets.channels["L"].highlightspin.set_range(0., maximum)
