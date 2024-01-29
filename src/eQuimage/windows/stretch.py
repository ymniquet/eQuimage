# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.3.0 / 2024.01.29

"""Template for histogram stretch tools."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
from .gtk.customwidgets import Notebook
from .base import  BaseToolbar, Container
from .tools import BaseToolWindow
from .utils import histogram_bins, plot_histograms, update_histograms, highlight_histogram, stats_string
import numpy as np
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as ticker

class StretchTool(BaseToolWindow):
  """Histogram stretch tool class."""

  # Build window.

  __window_name__ = "" # Window name.

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, self.__window_name__): return False
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
    self.reference.stats = self.reference.statistics(channels = "RGBSVL")
    self.image.stats = self.reference.stats.copy()
    self.statchannels = ""     # Keys for the image statistics.
    self.histchannels = ""     # Keys for the image histograms.
    self.histcolors = []       # Colors of the image histograms.
    self.channelkeys = []      # Keys of the different channels/tabs.
    self.widgets.channels = {} # Widgets of the different channels/tabs.
    self.widgets.rgbtabs = Notebook()
    self.widgets.rgbtabs.set_tab_pos(Gtk.PositionType.TOP)
    wbox.pack_start(self.widgets.rgbtabs, False, False, 0)
    for key, name, color, lcolor in (("R", "Red", (1., 0., 0.), (1., 0., 0.)),
                                     ("G", "Green", (0., 1., 0.), (0., 1., 0.)),
                                     ("B", "Blue", (0., 0., 1.), (0., 0., 1.)),
                                     ("S", "HSV saturation", (1., .5, 0.), (1., .5, 0.)),
                                     ("V", "HSV value = max(RGB)", (0., 0., 0.), (1., 1., 1.)),
                                     ("L", "Luma", (.5, .5, .5), (1., 1., 1.))):
      channel = Container()
      tab = self.tab_widgets(key, channel)
      if tab is not None:
        channel.color = np.array(color)
        channel.lcolor = np.array(lcolor)
        self.statchannels += key
        self.histchannels += key
        self.histcolors.append(channel.color)
        self.channelkeys.append(key)
        self.widgets.channels[key] = channel
        self.widgets.rgbtabs.append_page(tab, Gtk.Label(label = name))
    self.widgets.rgbtabs.connect("switch-page", lambda tabs, tab, itab: self.update("tab", tab = itab))
    wbox.pack_start(self.tool_control_buttons(), False, False, 0)
    if "R" not in self.histchannels: # Always include red, blue, green...
      self.histchannels += "R"
      self.histcolors.append(np.array((1., 0., 0.)))
    if "G" not in self.histchannels: # ...in the histograms even though...
      self.histchannels += "G"
      self.histcolors.append(np.array((0., 1., 0.)))
    if "B" not in self.histchannels: # ...there are no tabs for these channels.
      self.histchannels += "B"
      self.histcolors.append(np.array((0., 0., 1.)))
    self.histlogscale = False # Plot histograms with y log scale.
    self.histbins = histogram_bins(self.reference.stats["L"], self.app.get_color_depth()) # Number of histogram bins.
    self.plotcontrast = False # Plot contrast (instead of stretch) function.
    self.stretchpoints = min(1024, self.histbins) # Number of points on the stretch/contrast function plot.
    self.plot_reference_histograms()
    self.plot_image_histograms()
    self.outofrange = self.reference.is_out_of_range() # Is the reference image out-of-range ?
    if self.outofrange: print("Reference image is out-of-range...")
    self.currentparams = self.get_params()
    self.app.mainwindow.set_rgb_luma_callback(self.update_rgb_luma)
    self.start(identity = not self.outofrange) # If so, the stretch tool may clip the image whatever the parameters.
    return True

  def options_widgets(self, widgets):
    """Return a Gtk box with tool options widgets and store the reference to these widgets in container 'widgets'.
       Return None if there are no tool options widgets.
       Must be defined (if needed) in each subclass."""
    return None

  def tab_widgets(self, key, widgets):
    """Return a Gtk box with tab widgets for channel 'key' in "R" (red), "G" (green), "B" (blue), "S" (saturation), "V" (value) or "L" (luma),
       and store the reference to these widgets in container 'widgets'.
       Return None if there is no tab for this channel.
       Must be defined (if needed) in each subclass."""
    return None

  # Tool methods.

  def get_params(self):
    """Return tool parameters.
       Must be defined (if needed) in each subclass."""
    return None

  def set_params(self, params):
    """Set tool parameters 'params'.
       Must be defined (if needed) in each subclass."""
    return

  def run(self, params):
    """Run tool for parameters 'params'.
       Must be defined (if needed) in each subclass."""
    return None, False

  def operation(self, params):
    """Return tool operation string for parameters 'params'.
       Must be defined (if needed) in each subclass."""
    return None

  def update_gui(self):
    """Update main window and image histogram."""
    if not self.opened: return
    self.image.stats = self.image.statistics(channels = self.statchannels)
    self.update_image_histograms()
    self.widgets.fig.canvas.draw_idle()
    super().update_gui()

  # Plot histograms, stretch function, display stats...

  def plot_reference_histograms(self):
    """Plot reference histograms."""
    edges, counts = self.reference.histograms(channels = self.histchannels, nbins = self.histbins)
    ax = self.widgets.fig.add_subplot(211)
    self.widgets.fig.refhistax = ax
    ax.histlines = plot_histograms(ax, edges, counts, colors = self.histcolors,
                                   title = "Reference", xlabel = None, ylogscale = self.histlogscale)
    tmin = min(0., edges[0]) # Initialize stretch function plot.
    tmax = max(1., edges[1])
    t = np.linspace(tmin, tmax, int(round(self.stretchpoints*(tmax-tmin))))
    self.widgets.fig.stretchax = self.widgets.fig.refhistax.twinx()
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
    edges, counts = self.reference.histograms(channels = self.histchannels, nbins = self.histbins)
    ax = self.widgets.fig.refhistax
    update_histograms(ax, ax.histlines, edges, counts, ylogscale = self.histlogscale)

  def plot_image_histograms(self):
    """Plot image histograms."""
    ax = self.widgets.fig.add_subplot(212)
    self.widgets.fig.imghistax = ax
    edges, counts = self.image.histograms(channels = self.histchannels, nbins = self.histbins)
    ax.histlines = plot_histograms(ax, edges, counts, colors = self.histcolors,
                                   title = "Image", ylogscale = self.histlogscale)

  def update_image_histograms(self):
    """Update image histograms."""
    edges, counts = self.image.histograms(channels = self.histchannels, nbins = self.histbins)
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
    """Return the stretch function f(t) for parameters 'params'.
       Must be defined (if needed) in each subclass."""
    return t

  def add_histogram_widgets(self, ax):
    """Add histogram widgets (other than stretch function) in axes 'ax'.
       Must be defined (if needed) in each subclass."""
    return

  # Update histograms, stats... on widget or key_press events.

  def update(self, changed, **kwargs):
    """Update histograms, stats and widgets."""
    if changed == "tab":
      tab = kwargs["tab"]
      key = self.channelkeys[tab]
      idx = self.histchannels.index(key)
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
    """Update widgets (other than histograms and stats) on change of 'changed' in channel 'key'.
       Must be defined (if needed) in each subclass."""
    return

  def key_press(self, widget, event):
    """Callback for key press in the stretch tool window."""
    ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
    alt = event.state & Gdk.ModifierType.MOD1_MASK
    if not ctrl and not alt:
      keyname = Gdk.keyval_name(event.keyval).upper()
      if keyname == "L": # Toggle log scale.
        self.histlogscale = not self.histlogscale
        self.update_reference_histograms()
        self.update_image_histograms()
        self.widgets.fig.canvas.draw_idle()
        self.window.queue_draw()
        return
      elif keyname == "C": # Toggle stretch function/contrast enhancement function.
        self.plotcontrast = not self.plotcontrast
        tab = self.widgets.rgbtabs.get_current_page()
        key = self.channelkeys[tab]
        self.update_stretch_function_axes()
        self.update_widgets(key, "sfplot")
        self.widgets.fig.canvas.draw_idle()
        self.window.queue_draw()
        return
    super().key_press(widget, event)

  # Callbacks on luma RGB components update in main window.

  def update_rgb_luma(self, rgbluma):
    """Update luma rgb components."""
    self.reference.stats = self.image.statistics(channels = self.statchannels)
    self.update_reference_histograms()
    self.image.stats = self.image.statistics(channels = self.statchannels)
    self.update_image_histograms()
    self.widgets.fig.canvas.draw_idle()
    self.window.queue_draw()
