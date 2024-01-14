# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2024.01.14

"""Image statistics window."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
from .base import BaseWindow, BaseToolbar, Container
from .utils import plot_histograms, highlight_histogram
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure

class StatWindow(BaseWindow):
  """Image statistics window class."""

  def open(self, image):
    """Open statistics window for image 'image'."""
    if self.opened: self.close()
    self.opened = True
    self.window = Gtk.Window(title = "Image histograms & statistics", transient_for = self.app.mainwindow.window, destroy_with_parent = True, border_width = 16)
    self.window.connect("delete-event", self.close)
    self.window.connect("key-press-event", self.keypress)
    self.widgets = Container()
    wbox = Gtk.VBox(spacing = 16)
    self.window.add(wbox)
    fbox = Gtk.VBox(spacing = 0)
    wbox.pack_start(fbox, True, True, 0)
    self.widgets.fig = Figure(figsize = (10., 3.), layout = "constrained")
    canvas = FigureCanvas(self.widgets.fig)
    canvas.set_size_request(600, 180)
    fbox.pack_start(canvas, True, True, 0)
    toolbar = BaseToolbar(canvas, self.widgets.fig)
    fbox.pack_start(toolbar, False, False, 0)
    wbox.pack_start(Gtk.Label("Press [L] to toggle lin/log scale", halign = Gtk.Align.START), False, False, 0)
    self.widgets.selection = self.pack_image_statistics_treeview(image, wbox)
    hbox = Gtk.HButtonBox(homogeneous = True, spacing = 16, halign = Gtk.Align.START)
    wbox.pack_start(hbox, False, False, 0)
    self.widgets.closebutton = Gtk.Button(label = "Close")
    self.widgets.closebutton.connect("clicked", self.close)
    hbox.pack_start(self.widgets.closebutton, False, False, 0)
    self.widgets.fig.histax = self.widgets.fig.add_subplot(111)
    self.histcolors = ((1., 0., 0.), (0., 1., 0.), (0., 0., 1.), (0., 0., 0.), (0.5, 0.5, 0.5))
    self.histlogscale = False
    self.histograms = image.histograms(8192 if self.app.get_color_depth() > 8 else 128)
    self.plot_image_histograms()
    self.widgets.selection.connect("changed", lambda selection: self.highlight_image_histogram())
    self.window.show_all()

  def close(self, *args, **kwargs):
    """Close statistics window."""
    if not self.opened: return
    self.window.destroy()
    self.opened = False
    del self.widgets
    del self.histograms

  def plot_image_histograms(self):
    """Plot image histograms."""
    ax = self.widgets.fig.histax
    edges, counts = self.histograms
    ax.histlines = plot_histograms(ax, edges, counts, colors = self.histcolors, ylogscale = self.histlogscale)
    highlight_histogram(ax.histlines, self.get_selected_channel())

  def highlight_image_histogram(self):
    """Highlight image histogram line."""
    highlight_histogram(self.widgets.fig.histax.histlines, self.get_selected_channel())
    self.widgets.fig.canvas.draw_idle()

  def pack_image_statistics_treeview(self, image, box):
    """Pack statistics of image 'image' as a TreeView in box 'box'.
       Return a TreeView selection object to get the selected channel with self.get_selected_channel()."""
    stats = image.statistics()
    width, height = image.size()
    npixels = width*height
    box.pack_start(Gtk.Label(f"Image size = {width}x{height} pixels = {npixels} pixels", halign = Gtk.Align.START), False, False, 0)
    store = Gtk.ListStore(int, str, str, str, str, str, str, str, str, str, str)
    for idx, key, name in ((0, "R", "Red"), (1, "G", "Green"), (2, "B", "Blue"), (3, "V", "Value = max(RGB)"), (4, "L", "Luminance")):
      channel = stats[key]
      if channel.median is None:
        perc25 = "-"
        median = "-"
        perc75 = "-"
      else:
        perc25 = f"{channel.percentiles[0]:.5f}"
        median = f"{channel.median:.5f}"
        perc75 = f"{channel.percentiles[2]:.5f}"
      store.append([idx, name, f"{channel.minimum:.5f}", perc25, median, perc75, f"{channel.maximum:.5f}",
                    f"{channel.zerocount:d}", f"({100.*channel.zerocount/npixels:6.3f}%)", f"{channel.outcount:d}", f"({100.*channel.outcount/npixels:6.3f}%)"])
    tree = Gtk.TreeView(model = store, search_column = -1)
    box.pack_start(tree, False, False, 0)
    renderer = Gtk.CellRendererText()
    column = Gtk.TreeViewColumn("Channel", renderer, text = 1)
    column.set_alignment(0.)
    column.set_expand(True)
    tree.append_column(column)
    renderer = Gtk.CellRendererText()
    renderer.set_property("xalign", 1.)
    column = Gtk.TreeViewColumn("Minimum", renderer, text = 2)
    column.set_alignment(1.)
    column.set_expand(True)
    tree.append_column(column)
    renderer = Gtk.CellRendererText()
    renderer.set_property("xalign", 1.)
    column = Gtk.TreeViewColumn("25th %", renderer, text = 3)
    column.set_alignment(1.)
    column.set_expand(True)
    tree.append_column(column)
    renderer = Gtk.CellRendererText()
    renderer.set_property("xalign", 1.)
    column = Gtk.TreeViewColumn("median", renderer, text = 4)
    column.set_alignment(1.)
    column.set_expand(True)
    tree.append_column(column)
    renderer = Gtk.CellRendererText()
    renderer.set_property("xalign", 1.)
    column = Gtk.TreeViewColumn("75th %", renderer, text = 5)
    column.set_alignment(1.)
    column.set_expand(True)
    tree.append_column(column)
    renderer = Gtk.CellRendererText()
    renderer.set_property("xalign", 1.)
    column = Gtk.TreeViewColumn("Maximum", renderer, text = 6)
    column.set_alignment(1.)
    column.set_expand(True)
    tree.append_column(column)
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
    tree.append_column(column)
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
    tree.append_column(column)
    box.pack_start(Gtk.Label("The medians and percentiles (%) above exclude pixels <= 0 and >= 1", halign = Gtk.Align.START), False, False, 0)
    selection = tree.get_selection()
    selection.set_mode(Gtk.SelectionMode.SINGLE)
    return selection

  def get_selected_channel(self):
    """Return selected channel (-1 if None)."""
    model, list_iter = self.widgets.selection.get_selected()
    return model[list_iter][0] if list_iter is not None else -1

  def keypress(self, widget, event):
    """Callback for key press in the statistics window."""
    keyname = Gdk.keyval_name(event.keyval).upper()
    if keyname == "L": # Toggle log scale.
      self.histlogscale = not self.histlogscale
      self.plot_image_histograms()
      self.widgets.fig.canvas.draw_idle()
      self.window.queue_draw()
