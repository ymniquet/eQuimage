# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.5.0 / 2024.04.28
# GUI updated.

"""Image statistics window."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .gtk.customwidgets import HBox, VBox, HButtonBox, Button
from .gtk.keyboard import decode_key
from .base import BaseWindow, FigureCanvas, BaseToolbar, Container
from .misc.utils import histogram_bins, plot_histograms, highlight_histogram
from matplotlib.figure import Figure

class StatsWindow(BaseWindow):
  """Image statistics window class."""

  def open(self, image):
    """Open statistics window for image 'image'."""
    if self.opened: self.close()
    self.opened = True
    self.window = Gtk.Window(title = "Image histograms & statistics", transient_for = self.app.mainwindow.window, destroy_with_parent = True, border_width = 16)
    self.window.connect("delete-event", self.close)
    self.window.connect("key-press-event", self.key_press)
    self.widgets = Container()
    wbox = VBox()
    self.window.add(wbox)
    fbox = VBox(spacing = 0)
    wbox.pack(fbox, expand = True, fill = True)
    self.widgets.fig = Figure(figsize = (10., 3.), layout = "constrained")
    canvas = FigureCanvas(self.widgets.fig)
    canvas.set_size_request(600, 180)
    fbox.pack(canvas, expand = True, fill = True)
    toolbar = BaseToolbar(canvas, self.widgets.fig)
    fbox.pack(toolbar)
    wbox.pack("Press [L] to toggle lin/log scale")
    stats = image.statistics()
    self.widgets.selection = self.pack_image_statistics_treeview(stats, wbox)
    hbox = HButtonBox()
    wbox.pack(hbox)
    self.widgets.closebutton = Button(label = "Close")
    self.widgets.closebutton.connect("clicked", self.close)
    hbox.pack(self.widgets.closebutton)
    self.widgets.fig.histax = self.widgets.fig.add_subplot(111)
    self.histlogscale = False
    self.histcolors = ((1., 0., 0.), (0., 1., 0.), (0., 0., 1.), (0., 0., 0.), (0.5, 0.5, 0.5))
    self.histograms = image.histograms(nbins = histogram_bins(stats["L"], self.app.get_color_depth()))
    self.plot_histograms()
    self.widgets.selection.connect("changed", lambda selection: self.highlight_histogram())
    self.window.show_all()

  def close(self, *args, **kwargs):
    """Close statistics window."""
    if not self.opened: return
    self.window.destroy()
    self.opened = False
    del self.widgets
    del self.histograms

  def pack_image_statistics_treeview(self, stats, box):
    """Pack image statistics 'stats' (see imageprocessing.Image.statistics) as a TreeView in box 'box'.
       Return a TreeView selection object to get the selected channel with self.get_selected_channel()."""
    width, height, npixels = stats["L"].width, stats["L"].height, stats["L"].npixels
    box.pack(f"Image size = {width}x{height} pixels = {npixels} pixels")
    store = Gtk.ListStore(int, str, str, str, str, str, str, str, str, str, str)
    idx = 0
    for key in ("R", "G", "B", "V", "L"):
      channel = stats[key]
      if channel.median is None:
        perc25 = "-"
        median = "-"
        perc75 = "-"
      else:
        perc25 = f"{channel.percentiles[0]:.5f}"
        median = f"{channel.median:.5f}"
        perc75 = f"{channel.percentiles[2]:.5f}"
      store.append([idx, channel.name, f"{channel.minimum:.5f}", perc25, median, perc75, f"{channel.maximum:.5f}",
                    f"{channel.zerocount:d}", f"({100.*channel.zerocount/npixels:6.3f}%)", f"{channel.outcount:d}", f"({100.*channel.outcount/npixels:6.3f}%)"])
      idx += 1
    treeview = Gtk.TreeView(model = store, search_column = -1)
    box.pack(treeview)
    renderer = Gtk.CellRendererText()
    renderer.set_property("xalign", 0.)
    column = Gtk.TreeViewColumn("Channel", renderer, text = 1)
    column.set_alignment(0.)
    column.set_expand(True)
    treeview.append_column(column)
    renderer = Gtk.CellRendererText()
    renderer.set_property("xalign", 1.)
    column = Gtk.TreeViewColumn("Minimum", renderer, text = 2)
    column.set_alignment(1.)
    column.set_expand(True)
    treeview.append_column(column)
    renderer = Gtk.CellRendererText()
    renderer.set_property("xalign", 1.)
    column = Gtk.TreeViewColumn("25th %", renderer, text = 3)
    column.set_alignment(1.)
    column.set_expand(True)
    treeview.append_column(column)
    renderer = Gtk.CellRendererText()
    renderer.set_property("xalign", 1.)
    column = Gtk.TreeViewColumn("median", renderer, text = 4)
    column.set_alignment(1.)
    column.set_expand(True)
    treeview.append_column(column)
    renderer = Gtk.CellRendererText()
    renderer.set_property("xalign", 1.)
    column = Gtk.TreeViewColumn("75th %", renderer, text = 5)
    column.set_alignment(1.)
    column.set_expand(True)
    treeview.append_column(column)
    renderer = Gtk.CellRendererText()
    renderer.set_property("xalign", 1.)
    column = Gtk.TreeViewColumn("Maximum", renderer, text = 6)
    column.set_alignment(1.)
    column.set_expand(True)
    treeview.append_column(column)
    column = Gtk.TreeViewColumn("Zeros (<= 0)")
    column.set_alignment(1.)
    column.set_expand(True)
    count = Gtk.CellRendererText()
    count.set_property("xalign", 1.)
    column.pack_start(count, True)
    column.add_attribute(count, "text", 7)
    percent = Gtk.CellRendererText()
    percent.set_property("xalign", 1.)
    column.pack_start(percent, False)
    column.add_attribute(percent, "text", 8)
    treeview.append_column(column)
    column = Gtk.TreeViewColumn("Out-of-range (> 1)")
    column.set_alignment(1.)
    column.set_expand(True)
    count = Gtk.CellRendererText()
    count.set_property("xalign", 1.)
    column.pack_start(count, True)
    column.add_attribute(count, "text", 9)
    percent = Gtk.CellRendererText()
    percent.set_property("xalign", 1.)
    column.pack_start(percent, False)
    column.add_attribute(percent, "text", 10)
    treeview.append_column(column)
    box.pack("The medians and percentiles (%) above exclude pixels &lt;= 0 and &gt;= 1")
    selection = treeview.get_selection()
    selection.set_mode(Gtk.SelectionMode.SINGLE)
    return selection

  def get_selected_channel(self):
    """Return selected channel (-1 if None)."""
    model, list_iter = self.widgets.selection.get_selected()
    return model[list_iter][0] if list_iter is not None else -1

  def plot_histograms(self):
    """Plot histograms."""
    ax = self.widgets.fig.histax
    ax.histlines = plot_histograms(ax, *self.histograms, colors = self.histcolors, ylogscale = self.histlogscale)
    highlight_histogram(ax.histlines, self.get_selected_channel())

  def highlight_histogram(self):
    """Highlight histogram line."""
    highlight_histogram(self.widgets.fig.histax.histlines, self.get_selected_channel())
    self.widgets.fig.canvas.draw_idle()

  def key_press(self, widget, event):
    """Callback for key press in the statistics window."""
    key = decode_key(event)
    if key.ctrl or key.alt: return
    if key.uname == "L": # Toggle log scale.
      self.histlogscale = not self.histlogscale
      self.plot_histograms()
      self.widgets.fig.canvas.draw_idle()
      self.window.queue_draw()
