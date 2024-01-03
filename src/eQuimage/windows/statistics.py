# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2023.11.27

"""Image statistics window."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
from .base import BaseWindow, BaseToolbar, Container
from .helpers import plot_histograms
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
    self.widgets.fig.histax = self.widgets.fig.add_subplot(111)
    self.histcolors = ((1., 0., 0.), (0., 1., 0.), (0., 0., 1.), (0., 0., 0.), (0.5, 0.5, 0.5))
    self.histlogscale = False
    self.histograms = image.histograms(1024 if self.app.get_color_depth() > 8 else 128)
    self.plot_image_histograms()
    wbox.pack_start(Gtk.Label("Press [L] to toggle lin/log scale", halign = Gtk.Align.START), False, False, 0)
    self.pack_image_statistics(image, wbox)
    hbox = Gtk.HButtonBox(homogeneous = True, spacing = 16, halign = Gtk.Align.START)
    wbox.pack_start(hbox, False, False, 0)
    self.widgets.closebutton = Gtk.Button(label = "Close")
    self.widgets.closebutton.connect("clicked", self.close)
    hbox.pack_start(self.widgets.closebutton, False, False, 0)
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
    plot_histograms(ax, self.histograms, colors = self.histcolors, title = None, ylogscale = self.histlogscale)

  def pack_image_statistics(self, image, box):
    """Pack statistics of image 'image' in box 'box'."""
    stats = image.statistics()
    width, height = image.size()
    npixels = width*height
    box.pack_start(Gtk.Label(f"Image size = {width}x{height} pixels = {npixels} pixels", halign = Gtk.Align.START), False, False, 0)
    store = Gtk.ListStore(str, str, str, str, str, str, str, str)
    for key, name in (("R", "Red"), ("G", "Green"), ("B", "Blue"), ("V", "Value = max(RGB)"), ("L", "Luminance")):
      channel = stats[key]
      store.append([name, f"{channel.minimum:.5f}", f"{channel.maximum:.5f}", f"{channel.median:.5f}",
                    f"{channel.zerocount:d}", f"({100.*channel.zerocount/npixels:6.3f}%)", f"{channel.outcount:d}", f"({100.*channel.outcount/npixels:6.3f}%)"])
    tree = Gtk.TreeView(model = store, search_column = -1)
    box.pack_start(tree, False, False, 0)
    renderer = Gtk.CellRendererText()
    column = Gtk.TreeViewColumn("Channel", renderer, text = 0)
    column.set_alignment(0.)
    column.set_expand(True)
    tree.append_column(column)
    renderer = Gtk.CellRendererText()
    renderer.set_property("xalign", 1.)
    column = Gtk.TreeViewColumn("Minimum", renderer, text = 1)
    column.set_alignment(1.)
    column.set_expand(True)
    tree.append_column(column)
    renderer = Gtk.CellRendererText()
    renderer.set_property("xalign", 1.)
    column = Gtk.TreeViewColumn("Maximum", renderer, text = 2)
    column.set_alignment(1.)
    column.set_expand(True)
    tree.append_column(column)
    renderer = Gtk.CellRendererText()
    renderer.set_property("xalign", 1.)
    column = Gtk.TreeViewColumn("Median", renderer, text = 3)
    column.set_alignment(1.)
    column.set_expand(True)
    tree.append_column(column)
    column = Gtk.TreeViewColumn("Zeros")
    column.set_alignment(1.)
    column.set_expand(True)
    count = Gtk.CellRendererText()
    count.set_property("xalign", 1.)
    column.pack_start(count, True)
    column.add_attribute(count, "text", 4)
    percent = Gtk.CellRendererText()
    percent.set_property("xalign", 1.)
    column.pack_start(percent, False)
    column.add_attribute(percent, "text", 5)
    tree.append_column(column)
    column = Gtk.TreeViewColumn("Out-of-range")
    column.set_alignment(1.)
    column.set_expand(True)
    count = Gtk.CellRendererText()
    count.set_property("xalign", 1.)
    column.pack_start(count, True)
    column.add_attribute(count, "text", 6)
    percent = Gtk.CellRendererText()
    percent.set_property("xalign", 1.)
    column.pack_start(percent, False)
    column.add_attribute(percent, "text", 7)
    tree.append_column(column)

  def keypress(self, widget, event):
    """Callback for key press in the statistics window."""
    keyname = Gdk.keyval_name(event.keyval).upper()
    if keyname == "L": # Toggle log scale.
      self.histlogscale = not self.histlogscale
      self.plot_image_histograms()
      self.widgets.fig.canvas.draw_idle()      
      self.window.queue_draw()
