# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2024.01.14

"""Color saturation tool."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .gtk.customwidgets import CheckButton, RadioButton, HScale
from .tools import BaseToolWindow
from .utils import plot_hsv_wheel
import numpy as np
import matplotlib.colors as colors
import matplotlib.ticker as ticker
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure
from scipy.interpolate import interp1d

class ColorSaturationTool(BaseToolWindow):
  """Color saturation tool class."""

  __action__ = "Tuning color saturation..."

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Color saturation"): return False
    self.reference.hsv = self.reference.rgb_to_hsv()
    wbox = Gtk.VBox(spacing = 16)
    self.window.add(wbox)
    hbox = Gtk.HBox(spacing = 16)
    wbox.pack_start(hbox, False, False, 0)
    self.widgets.fig = Figure(figsize = (6., 6.), layout = "constrained")
    canvas = FigureCanvas(self.widgets.fig)
    canvas.set_size_request(256, 256)
    hbox.pack_start(canvas, False, False, 0)
    vbox = Gtk.VBox(spacing = 16)
    hbox.pack_start(vbox, False, False, 0)
    grid = Gtk.Grid(column_spacing = 8)
    vbox.pack_start(grid, False, False, 0)
    self.widgets.bindbutton = CheckButton(label = "Bind hues")
    self.widgets.bindbutton.set_active(True)
    self.widgets.bindbutton.connect("toggled", lambda button: self.update(0))
    grid.add(self.widgets.bindbutton)
    self.widgets.satscales = []
    for hid, label in ((0, "Red:"), (1, "Yellow:"), (2, "Green:"), (3, "Cyan:"), (4, "Blue:"), (5, "Magenta:")):
      satscale = HScale(0., -1., 1., 0.001, digits = 3, length = 384)
      satscale.hid = hid
      satscale.connect("value-changed", lambda scale: self.update(scale.hid))
      if not self.widgets.satscales:
        grid.attach_next_to(satscale, self.widgets.bindbutton   , Gtk.PositionType.BOTTOM, 1, 1)
      else:
        grid.attach_next_to(satscale, self.widgets.satscales[-1], Gtk.PositionType.BOTTOM, 1, 1)
      self.widgets.satscales.append(satscale)
      label = Gtk.Label(label = label, halign = Gtk.Align.END)
      grid.attach_next_to(label, self.widgets.satscales[-1], Gtk.PositionType.LEFT, 1, 1)
    hbox = Gtk.HBox(spacing = 8)
    grid.attach_next_to(hbox, self.widgets.satscales[-1], Gtk.PositionType.BOTTOM, 1, 1)
    self.widgets.nearestbutton = RadioButton.new_with_label_from_widget(None, "Nearest")
    hbox.pack_start(self.widgets.nearestbutton, False, False, 0)
    self.widgets.linearbutton = RadioButton.new_with_label_from_widget(self.widgets.nearestbutton, "Linear")
    hbox.pack_start(self.widgets.linearbutton, False, False, 0)
    self.widgets.cubicbutton = RadioButton.new_with_label_from_widget(self.widgets.linearbutton, "Cubic")
    hbox.pack_start(self.widgets.cubicbutton, False, False, 0)
    self.widgets.cubicbutton.set_active(True)
    self.widgets.nearestbutton.connect("toggled", lambda button: self.update(-1))
    self.widgets.linearbutton.connect("toggled", lambda button: self.update(-1))
    self.widgets.cubicbutton.connect("toggled", lambda button: self.update(-1))
    grid.attach_next_to(Gtk.Label(label = "Interpolation:", halign = Gtk.Align.END), hbox, Gtk.PositionType.LEFT, 1, 1)
    vbox.pack_start(self.tool_control_buttons(), False, False, 0)
    self.widgets.fig.satax = self.widgets.fig.add_subplot(projection = "polar")
    self.plot_hsv_wheel()
    self.start(identity = True)
    return True

  def get_params(self):
    """Return tool parameters."""
    dsat = tuple(self.widgets.satscales[hid].get_value() for hid in range(6))
    if self.widgets.nearestbutton.get_active():
      interpolation = "nearest"
    elif self.widgets.linearbutton.get_active():
      interpolation = "linear"
    else:
      interpolation = "cubic"
    return dsat, interpolation

  def set_params(self, params):
    """Set tool parameters 'params'."""
    dsat, interpolation = params
    dsat = np.array(dsat)
    for hid in range(6): self.widgets.satscales[hid].set_value_block(dsat[hid])
    if np.any(dsat != dsat[0]): self.widgets.bindbutton.set_active_block(False)
    if interpolation == "nearest":
      self.widgets.nearestbutton.set_active_block(True)
    elif interpolation == "linear":
      self.widgets.linearbutton.set_active_block(True)
    else:
      self.widgets.cubicbutton.set_active_block(True)
    self.update(0)

  def run(self, params):
    """Run tool for parameters 'params'."""
    dsat, interpolation = params
    dsat = np.array(dsat)
    if np.all(dsat == 0.): return params, False
    hsv = self.reference.hsv.copy()
    sat = hsv[:, :, 1]
    if np.all(dsat == dsat[0]):
      sat += dsat[0]
    else:
      hsat = np.linspace(0., 6., 7)/6.
      dsat = np.append(dsat, dsat[0])
      fsat = interp1d(hsat, dsat, kind = interpolation)
      sat += fsat(hsv[:, :, 0])
    hsv[:, :, 1] = np.clip(sat, 0., 1.)
    self.image.hsv_to_rgb(hsv)
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    dsat, interpolation = params
    tags = ["R", "Y", "G", "C", "B", "M"]
    operation = "ColorSaturation(model = DeltaSat, "
    for hid in range(6):
      operation += f"{tags[hid]} = {dsat[hid]:.3f}, "
    operation += f" interpolation = {interpolation})"
    return operation

  # Plot HSV wheel.

  def plot_hsv_wheel(self):
    """Plot HSV wheel."""
    ax = self.widgets.fig.satax
    plot_hsv_wheel(ax)
    hues = 2.*np.pi*np.linspace(0., 5., 6)/6.
    ax.set_xticks(hues, labels = ["R", "Y", "G", "C", "B", "M"])
    ax.set_ylim([-.1, .1])
    ax.yaxis.set_major_locator(ticker.LinearLocator(3))
    ax.satpoints, = ax.plot(hues, np.zeros_like(hues), "ko", ms = 8)
    hues = np.linspace(0., 2.*np.pi, 128)
    ax.satcurve, = ax.plot(hues, np.zeros_like(hues), "k--")

  # Update scales and HSV wheel.

  def update(self, changed):
    """Update scales."""
    if changed >= 0:
      if self.widgets.bindbutton.get_active():
        dsat = self.widgets.satscales[changed].get_value()
        for hid in range(6):
          self.widgets.satscales[hid].set_value_block(dsat)
    self.update_hsv_wheel()
    self.reset_polling(self.get_params()) # Expedite main window update.

  def update_hsv_wheel(self):
    """Update HSV wheel."""
    dsat, interpolation = self.get_params()
    dsat = np.array(dsat)
    dmin = dsat.min()
    dmax = dsat.max()
    ax = self.widgets.fig.satax
    ax.satpoints.set_ydata(dsat)
    hsat = 2.*np.pi*np.linspace(0., 6., 7)/6.
    dsat = np.append(dsat, dsat[0])
    fsat = interp1d(hsat, dsat, kind = interpolation)
    ax.satcurve.set_ydata(fsat(ax.satcurve.get_xdata()))
    ymin = max(dmin-.1, -1.)
    ymax = min(dmax+.1,  1.)
    if ymax-ymin < .19999:
      if ymax ==  1.:
        ymin =  .8
      elif ymin == -1.:
        ymax = -.8
    ax.set_ylim(ymin, ymax)
    self.widgets.fig.canvas.draw_idle()
