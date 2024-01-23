# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2024.01.14

"""Color saturation tool."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .gtk.customwidgets import CheckButton, HScale
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
    self.widgets.bindbutton.connect("toggled", lambda scale: self.update(0))
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
      grid.attach_next_to(Gtk.Label(label = label, halign = Gtk.Align.END), self.widgets.satscales[-1], Gtk.PositionType.LEFT, 1, 1)
    vbox.pack_start(self.tool_control_buttons(), False, False, 0)
    self.widgets.fig.satax = self.widgets.fig.add_subplot(projection = "polar")
    self.plot_hsv_wheel()
    self.start(identity = True)
    return True

  def get_params(self):
    """Return tool parameters."""
    return tuple(self.widgets.satscales[hid].get_value() for hid in range(6))

  def set_params(self, params):
    """Set tool parameters 'params'."""
    for hid in range(6): self.widgets.satscales[hid].set_value_block(params[hid])
    if np.any(np.array(params) != params[0]): self.widgets.bindbutton.set_active_block(False)
    self.update(0)

  def run(self, params):
    """Run tool for parameters 'params'."""
    dsat = np.array(params)
    if np.all(dsat == 0.): return params, False
    hsv = self.reference.hsv.copy()
    sat = hsv[:, :, 1]
    if np.all(dsat == dsat[0]):
      sat += dsat[0]
    else:
      hsat = np.linspace(0., 6., 7)/6.
      dsat = np.append(dsat, dsat[0])
      fsat = interp1d(hsat, dsat, kind = "linear")
      sat += fsat(hsv[:, :, 0])
    hsv[:, :, 1] = np.clip(sat, 0., 1.)
    self.image.hsv_to_rgb(hsv)
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    tags = ["R", "Y", "G", "C", "B", "M"]
    operation = "ColorSaturation("
    for hid in range(6):
      operation += f"{tags[hid]} = {params[hid]:.3f}"
      operation += ", " if hid < 5 else ")"
    return operation

  # Plot HSV wheel.

  def plot_hsv_wheel(self):
    """Plot HSV wheel."""
    ax = self.widgets.fig.satax
    plot_hsv_wheel(ax)
    hues = 2.*np.pi*np.arange(0., 6., 7.)/6.
    ax.set_xticks(hues, labels = ["R", "Y", "G", "C", "B", "M"])
    ax.set_ylim([-.1, .1])
    ax.yaxis.set_major_locator(ticker.LinearLocator(3))
    ax.satpoints, = ax.plot(hues, np.zeros_like(hues), "ko", ms = 8)
    hues = np.linspace(0., 2.*np.pi, 128)
    ax.satcurve, = ax.plot(hues, np.zeros_like(hues), "k--")

  # Update scales and HSV wheel.

  def update(self, changed):
    """Update scales."""
    if self.widgets.bindbutton.get_active():
      dsat = self.widgets.satscales[changed].get_value()
      for hid in range(6):
        self.widgets.satscales[hid].set_value_block(dsat)
    self.update_hsv_wheel()
    self.reset_polling(params) # Expedite main window update.

  def update_hsv_wheel(self):
    """Update HSV wheel."""
    params = self.get_params()
    dsat = np.array(params)
    dmin = dsat.min()
    dmax = dsat.max()
    ax = self.widgets.fig.satax
    ax.satpoints.set_ydata(dsat)
    hsat = 2.*np.pi*np.linspace(0., 6., 7)/6.
    dsat = np.append(dsat, dsat[0])
    fsat = interp1d(hsat, dsat, kind = "linear")
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

