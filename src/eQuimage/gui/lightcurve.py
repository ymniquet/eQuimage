# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.5.0 / 2024.04.28
# GUI updated.

"""Image light curve window."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .gtk.customwidgets import HBox, VBox, Button, RadioButtons
from .base import BaseWindow, FigureCanvas, BaseToolbar, Container
from .misc.imagechooser import ImageChooser
from matplotlib.figure import Figure
import numpy as np

class LightCurveWindow(BaseWindow):
  """Image light curve window class."""

  def open(self, image):
    """Open light curve window and image 'image'."""
    if self.opened: self.close()
    self.opened = True
    self.image = image
    self.window = Gtk.Window(title = "Image light curve", transient_for = self.app.mainwindow.window, destroy_with_parent = True, border_width = 16)
    self.window.connect("delete-event", self.close)
    self.widgets = Container()
    wbox = VBox()
    self.window.add(wbox)
    fbox = VBox(spacing = 0)
    wbox.pack(fbox, expand = True, fill = True)
    self.widgets.fig = Figure(figsize = (8., 8.), layout = "constrained")
    canvas = FigureCanvas(self.widgets.fig)
    canvas.set_size_request(480, 480)
    fbox.pack(canvas, expand = True, fill = True)
    toolbar = BaseToolbar(canvas, self.widgets.fig)
    fbox.pack(toolbar)
    self.widgets.fig.ax = self.widgets.fig.add_subplot(111)
    self.widgets.channelbuttons = RadioButtons(("V", "HSV value"), ("L", "Luma"), ("Y", "Luminance Y"), ("L*", "Lightness L*"))
    self.widgets.channelbuttons.set_selected("L*")
    self.widgets.channelbuttons.connect("toggled", self.update)
    wbox.pack(self.widgets.channelbuttons.hbox(prepend = "Channel:"))
    wbox.pack("Reference:")
    self.widgets.chooser = ImageChooser(self.app, self.window, wbox, tabkey = None, callback = self.update, last = True)
    self.widgets.closebutton = Button(label = "Close")
    self.widgets.closebutton.connect("clicked", self.close)
    self.widgets.chooser.buttonbox.pack(self.widgets.closebutton)
    self.widgets.chooser.set_selected_row(0)
    self.window.show_all()

  def update(self, *args, **kwargs):
    reference = self.widgets.chooser.get_selected_image()
    channel = self.widgets.channelbuttons.get_selected()
    if channel == "V":
      ref = reference.value()
      img = self.image.value()
      label = "HSV value"
    elif channel == "L":
      ref = reference.luma()
      img = self.image.luma()
      label = "luma"
    elif channel == "Y":
      ref = reference.srgb_luminance()
      img = self.image.srgb_luminance()
      label = "luminance"
    else:
      ref = reference.srgb_lightness()/100.
      img = self.image.srgb_lightness()/100.
      label = "lightness"
    ax = self.widgets.fig.ax
    ax.clear()
    ax.set_xlim(0., 1.)
    ax.set_xlabel("Reference "+label)
    ax.set_ylim(0., 1.)
    ax.set_ylabel("Image "+label)
    ax.plot([0., 1.], [0., 1.], color = "gray", linestyle = ":", linewidth = 1., zorder = -3)
    if ref.shape != img.shape:
      ax.plot([1., 0.], [0., 1.], color = "gray", linestyle = ":", linewidth = 1., zorder = -3)
      ax.text(.5, .5, "Image sizes do not match", color = "red", fontsize = 16, ha = "center", va = "center")
    else:
      maxsize = np.max(img.shape)
      n = int(np.ceil(maxsize/1024))
      ax.plot(np.ravel(ref[::n, ::n]), np.ravel(img[::n, ::n]), ".")
      ax.grid()
    self.widgets.fig.canvas.draw_idle()

  def close(self, *args, **kwargs):
    """Close light curve window."""
    if not self.opened: return
    self.window.destroy()
    self.opened = False
    del self.widgets
