# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2024.01.14

"""Midtone stretch tool."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
from .gtk.customwidgets import CheckButton, RadioButton, SpinButton, Notebook
from .base import BaseWindow, BaseToolbar, Container
from .tools import BaseToolWindow
from .utils import histogram_bins, plot_histograms, update_histograms, highlight_histogram, stats_string
from ..imageprocessing import imageprocessing
from ..imageprocessing.stretchfunctions import midtone_stretch_function
import numpy as np
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as ticker

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
    wbox.pack_start(Gtk.Label("Press [L] to toggle lin/log scale, [C] to plot the contrast enhancement function log(f')", halign = Gtk.Align.START), False, False, 0)
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
    options = self.options_widgets(self.widgets)
    if options is not None: wbox.pack_start(options, False, False, 0)
    self.widgets.rgbtabs = Notebook()
    self.widgets.rgbtabs.set_tab_pos(Gtk.PositionType.TOP)
    wbox.pack_start(self.widgets.rgbtabs, False, False, 0)
    self.reference.stats = self.reference.statistics()
    self.image.stats = self.reference.stats.copy()
    self.histcolors = []    
    self.channelkeys = []
    self.widgets.channels = {}
    for key, name, color, lcolor in (("R", "Red", (1., 0., 0.), (1., 0., 0.)),
                                     ("G", "Green", (0., 1., 0.), (0., 1., 0.)),
                                     ("B", "Blue", (0., 0., 1.), (0., 0., 1.)),
                                     ("V", "HSV value = max(RGB)", (0., 0., 0.), (1., 1., 1.)),
                                     ("L", "Luminance", (0.5, 0.5, 0.5), (1., 1., 1.))):
      color = np.array(color)
      lcolor = np.array(lcolor)
      self.histcolors.append(color)
      channel = Container()
      tab = self.tab_widgets(key, channel)
      if tab is not None:      
        channel.color = color
        channel.lcolor = lcolor     
        self.channelkeys.append(key)        
        self.widgets.channels[key] = channel
        self.widgets.rgbtabs.append_page(tab, Gtk.Label(label = name))
    wbox.pack_start(self.tool_control_buttons(), False, False, 0)
    self.defaultparams = self.get_params()
    self.currentparams = self.defaultparams.copy()
    self.toolparams    = self.defaultparams.copy()
    self.histlogscale = False    
    self.histbins = histogram_bins(self.reference.stats["L"], self.app.get_color_depth())
    self.plotcontrast = False    
    self.stretchbins = min(1024, self.histbins)
    self.widgets.fig.refhistax = self.widgets.fig.add_subplot(211)
    self.widgets.fig.stretchax = self.widgets.fig.refhistax.twinx()
    self.widgets.fig.imghistax = self.widgets.fig.add_subplot(212)
    self.plot_reference_histograms()
    self.plot_image_histograms()
    self.app.mainwindow.set_rgb_luminance_callback(self.update_rgb_luminance)
    self.widgets.rgbtabs.set_current_page(3)
    self.widgets.rgbtabs.connect("switch-page", lambda tabs, tab, itab: self.update("tab", tab = itab))
    self.outofrange = self.reference.is_out_of_range() # Is reference image out-of-range ?
    if self.outofrange: # If so, the stretch tool will clip the image whatever the input parameters.
      print("Reference image is out-of-range...")
      self.default_params_are_identity(False)
      if self.onthefly: self.apply(cancellable = False)
    self.window.show_all()
    self.start_polling()
    return True

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
    self.image.copy_from(self.reference)
    transformed = False
    for key in self.channelkeys:
      shadow, midtone, highlight, low, high = params[key]
      outofrange = self.outofrange and key in ["R", "G", "B"]
      if not outofrange and shadow == 0. and midtone == 0.5 and highlight == 1. and low == 0. and high == 1.: continue
      transformed = True
      self.image.generalized_stretch(midtone_stretch_function, (shadow, midtone, highlight, low, high), channels = key)
    if transformed and params["highlights"]:
      maximum = np.maximum(self.image.image.max(axis = 0), 1.)
      self.image.image /= maximum
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

  def update_gui(self):
    """Update main window and image histogram."""
    self.image.stats = self.image.statistics()
    self.update_image_histograms()
    self.widgets.fig.canvas.draw_idle()
    super().update_gui()

  # Plot histograms, stretch function, display stats...

  def plot_reference_histograms(self):
    """Plot reference histograms."""
    edges, counts = self.reference.histograms(self.histbins)
    ax = self.widgets.fig.refhistax
    ax.histlines = plot_histograms(ax, edges, counts, colors = self.histcolors,
                                   title = "Reference", xlabel = None, ylogscale = self.histlogscale)
    tmin = min(0., edges[0]) # Initialize stretch function plot.
    tmax = max(1., edges[1])
    t = np.linspace(tmin, tmax, int(round(self.stretchbins*(tmax-tmin))))    
    ax = self.widgets.fig.stretchax 
    ax.clear()
    ax.stretchline, = ax.plot(t, t, linestyle = ":", zorder = -1)
    ax.diagline,    = ax.plot([0., 1.], [0., 1.], color = "gray", linestyle = ":", linewidth = 1., zorder = -3)
    ax.zeroline     = ax.axhline(0., color = "gray", linestyle = ":", linewidth = 1., zorder = -3)
    ax.yaxis.set_label_position("right")
    self.update_stretch_function_axes()
    self.add_histogram_widgets(ax)

  def update_reference_histograms(self):
    """Update reference histograms."""
    edges, counts = self.reference.histograms(self.histbins)
    ax = self.widgets.fig.refhistax
    update_histograms(ax, ax.histlines, edges, counts, ylogscale = self.histlogscale)

  def plot_image_histograms(self):
    """Plot image histograms."""
    edges, counts = self.image.histograms(self.histbins)
    ax = self.widgets.fig.imghistax
    ax.histlines = plot_histograms(ax, edges, counts, colors = self.histcolors,
                                   title = "Image", ylogscale = self.histlogscale)

  def update_image_histograms(self):
    """Update image histograms."""
    edges, counts = self.image.histograms(self.histbins)
    ax = self.widgets.fig.imghistax
    update_histograms(ax, ax.histlines, edges, counts, ylogscale = self.histlogscale)
    tab = self.widgets.rgbtabs.get_current_page()
    key = self.channelkeys[tab]
    self.display_stats(key)

  def update_stretch_function_axes(self):
    """Update stretch function plot axis (switch between stretch function and contrast enhancement plots)."""
    ax = self.widgets.fig.stretchax
    if self.plotcontrast:
      ax.diagline.set_visible(False)
      ax.zeroline.set_visible(True)
      ax.set_ylabel("CE function log(f')")
    else:
      ax.diagline.set_visible(True)
      ax.zeroline.set_visible(False)
      ax.set_ylabel("Stretch function f")
      ax.set_ylim(0., 1.)

  def plot_stretch_function(self, f, color):
    """Plot the stretch function f or the contrast enhancement function log(f') with color 'color'."""
    ax = self.widgets.fig.stretchax
    line = ax.stretchline    
    t = line.get_xdata()
    ft = f(t)
    if self.plotcontrast: # Contrast enhancement function.
      ft = np.log(np.maximum(np.gradient(ft, t), 1.e-12))
      ymin = ft[ft > np.log(1.e-12)].min()
      ymax = ft.max()
      dy = ymax-ymin
      ax.set_ylim(ymin-.025*dy, ymax+.025*dy)
    line.set_ydata(ft)
    line.set_color(color)

  def display_stats(self, key):
    """Display reference and image statistics for channel 'key'."""
    self.widgets.refstats.set_label(stats_string(self.reference.stats[key]))
    self.widgets.imgstats.set_label(stats_string(self.image.stats[key]))

  def stretch_function(self, t, params):
    """Return the stretch function f(t) for parameters 'params'."""
    return midtone_stretch_function(t, params)

  def add_histogram_widgets(self, ax):
    """Add histogram widgets (other than stretch function) in axes 'ax'."""
    self.widgets.shadowline = ax.axvline(0., linestyle = "-.", zorder = -2)
    self.widgets.midtoneline = ax.axvline(.5, linestyle = "-.", zorder = -2)
    self.widgets.highlightline = ax.axvline(1., linestyle = "-.", zorder = -2)

  # Update histograms, stats... on widget or keypress events.

  def update(self, changed, **kwargs):
    """Update histograms, stats and widgets."""
    if changed == "tab":
      tab = kwargs["tab"]
      key = self.channelkeys[tab]
      idx = {"R": 0, "G": 1, "B": 2, "V": 3, "L": 4}[key]
      highlight_histogram(self.widgets.fig.refhistax.histlines, idx)
      highlight_histogram(self.widgets.fig.imghistax.histlines, idx)
      self.display_stats(key)
    else:
      tab = self.widgets.rgbtabs.get_current_page()
      key = self.channelkeys[tab]
    if changed is not None:
      self.update_widgets(key, changed)
      self.widgets.fig.canvas.draw_idle()
    self.reset_polling(self.get_params()) # Expedite main window update.

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

  def keypress(self, widget, event):
    """Callback for key press in the stretch tool window."""
    ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
    alt = event.state & Gdk.ModifierType.MOD1_MASK
    if ctrl or alt: return
    keyname = Gdk.keyval_name(event.keyval).upper()
    if keyname == "L": # Toggle log scale.
      self.histlogscale = not self.histlogscale
      self.update_reference_histograms()
      self.update_image_histograms()
      self.widgets.fig.canvas.draw_idle()
      self.window.queue_draw()
    elif keyname == "C": # Toggle stretch function/contrast enhancement function.
      self.plotcontrast = not self.plotcontrast
      tab = self.widgets.rgbtabs.get_current_page()
      key = self.channelkeys[tab]
      self.update_stretch_function_axes()
      self.update_widgets(key, "sfplot")
      self.widgets.fig.canvas.draw_idle()
      self.window.queue_draw()

  # Callbacks on luminance RGB components update in main window.

  def update_rgb_luminance(self, rgblum):
    """Update luminance rgb components."""
    self.reference.stats = self.image.statistics()
    self.update_reference_histograms()
    self.image.stats = self.image.statistics()
    self.update_image_histograms()
    self.widgets.fig.canvas.draw_idle()
    self.window.queue_draw()
