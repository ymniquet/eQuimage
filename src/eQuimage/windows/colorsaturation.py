# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.4.0 / 2024.02.26

"""Color saturation tool."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .gtk.customwidgets import CheckButton, RadioButton, HScaleSpinButton
from .tools import BaseToolWindow
import numpy as np
import matplotlib.colors as colors
import matplotlib.ticker as ticker
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure
from scipy.interpolate import interp1d, splrep, splev

class ColorSaturationTool(BaseToolWindow):
  """Color saturation tool class."""

  __action__ = "Enhancing color saturation..."

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Color saturation"): return False
    self.reference.hsv = self.reference.rgb_to_hsv()
    wbox = Gtk.VBox(spacing = 16)
    self.window.add(wbox)
    hbox = Gtk.HBox(spacing = 16)
    wbox.pack_start(hbox, False, False, 0)
    self.widgets.fig = Figure(figsize = (6., 6.))
    canvas = FigureCanvas(self.widgets.fig)
    canvas.set_size_request(300, 300)
    hbox.pack_start(canvas, False, False, 0)
    vbox = Gtk.VBox(spacing = 8)
    hbox.pack_start(vbox, True, True, 0)
    grid = Gtk.Grid(column_spacing = 8)
    vbox.pack_start(grid, False, False, 0)
    hbox = Gtk.HBox(spacing = 8)
    grid.add(hbox)
    self.widgets.deltasatbutton = RadioButton.new_with_label_from_widget(None, "\u0394Sat")
    hbox.pack_start(self.widgets.deltasatbutton, False, False, 0)
    self.widgets.msstretchbutton = RadioButton.new_with_label_from_widget(self.widgets.deltasatbutton, "MidSat stretch")
    hbox.pack_start(self.widgets.msstretchbutton, False, False, 0)
    self.widgets.deltasatbutton.connect("toggled", lambda button: self.update(-2))
    self.widgets.msstretchbutton.connect("toggled", lambda button: self.update(-2))
    self.widgets.bindbutton = CheckButton(label = "Bind hues", halign = Gtk.Align.END)
    self.widgets.bindbutton.set_active(True)
    self.widgets.bindbutton.connect("toggled", lambda button: self.update(0))
    hbox.pack_start(self.widgets.bindbutton, True, True, 0)
    grid.attach_next_to(Gtk.Label(label = "Model:", halign = Gtk.Align.END), hbox, Gtk.PositionType.LEFT, 1, 1)
    anchor = hbox
    self.widgets.satscales = []
    for hid, label in ((0, "Red:"), (1, "Yellow:"), (2, "Green:"), (3, "Cyan:"), (4, "Blue:"), (5, "Magenta:")):
      satscale = HScaleSpinButton(0., -1., 1., .001, digits = 3, length = 320)
      satscale.hid = hid
      satscale.connect("value-changed", lambda scale: self.update(scale.hid))
      self.widgets.satscales.append(satscale)
      satscalebox = satscale.layout1()
      grid.attach_next_to(satscalebox, anchor, Gtk.PositionType.BOTTOM, 1, 1)
      grid.attach_next_to(Gtk.Label(label = label, halign = Gtk.Align.END), satscalebox, Gtk.PositionType.LEFT, 1, 1)
      anchor = satscalebox
    hbox = Gtk.HBox(spacing = 8)
    grid.attach_next_to(hbox, anchor, Gtk.PositionType.BOTTOM, 1, 1)
    self.widgets.nearestbutton = RadioButton.new_with_label_from_widget(None, "Nearest")
    hbox.pack_start(self.widgets.nearestbutton, False, False, 0)
    self.widgets.linearbutton = RadioButton.new_with_label_from_widget(self.widgets.nearestbutton, "Linear")
    hbox.pack_start(self.widgets.linearbutton, False, False, 0)
    self.widgets.cubicbutton = RadioButton.new_with_label_from_widget(self.widgets.nearestbutton, "Cubic")
    hbox.pack_start(self.widgets.cubicbutton, False, False, 0)
    self.widgets.cubicbutton.set_active(True)
    self.widgets.nearestbutton.connect("toggled", lambda button: self.update(-1))
    self.widgets.linearbutton.connect("toggled", lambda button: self.update(-1))
    self.widgets.cubicbutton.connect("toggled", lambda button: self.update(-1))
    grid.attach_next_to(Gtk.Label(label = "Interpolation:", halign = Gtk.Align.END), hbox, Gtk.PositionType.LEFT, 1, 1)
    vbox.pack_start(self.tool_control_buttons(), False, False, 8)
    self.plot_hsv_wheel()
    self.outofrange = self.reference.is_out_of_range() # Is the reference image out-of-range ?
    if self.outofrange: print("Reference image is out-of-range...")
    self.start(identity = not self.outofrange) # If so, the color saturation tool will clip the image whatever the parameters
    return True

  def get_params(self):
    """Return tool parameters."""
    model = "DeltaSat" if self.widgets.deltasatbutton.get_active() else "MidSatStretch"
    psat = tuple(self.widgets.satscales[hid].get_value() for hid in range(6))
    if self.widgets.nearestbutton.get_active():
      interpolation = "nearest"
    elif self.widgets.linearbutton.get_active():
      interpolation = "linear"
    else:
      interpolation = "cubic"
    return model, psat, interpolation

  def set_params(self, params):
    """Set tool parameters 'params'."""
    model, psat, interpolation = params
    psat = np.array(psat)
    if model == "DeltaSat":
      self.widgets.deltasatbutton.set_active_block(True)
    else:
      self.widgets.msstretchbutton.set_active_block(True)
    for hid in range(6): self.widgets.satscales[hid].set_value_block(psat[hid])
    if np.any(psat != psat[0]): self.widgets.bindbutton.set_active_block(False)
    if interpolation == "nearest":
      self.widgets.nearestbutton.set_active_block(True)
    elif interpolation == "linear":
      self.widgets.linearbutton.set_active_block(True)
    else:
      self.widgets.cubicbutton.set_active_block(True)
    self.update(0)

  def run(self, params):
    """Run tool for parameters 'params'."""
    model, psat, interpolation = params
    psat = np.array(psat)
    if not self.outofrange and np.all(psat == 0.): return params, False
    hsv = self.reference.hsv.copy()
    sat = hsv[:, :, 1]
    if np.all(psat == psat[0]):
      if model == "DeltaSat":
        sat += psat[0]
      else:
        midsat = min(max(.5*(1.-psat[0]), .005), .995)
        sat = (midsat-1.)*sat/((2.*midsat-1.)*sat-midsat)
    else:
      hsat = np.linspace(0., 6., 7)/6.
      psat = np.append(psat, psat[0])
      if interpolation == "nearest":
        fsat = interp1d(hsat, psat, kind = "nearest")
      else:
        k = 3 if interpolation == "cubic" else 1
        tck = splrep(hsat, psat, k = k, per = True)
        def fsat(x): return splev(x, tck)
      hue = hsv[:, :, 0]
      if model == "DeltaSat":
        sat += fsat(hue)
      else:
        midsat = np.clip(.5*(1.-fsat(hue)), .005, .995)
        sat = (midsat-1.)*sat/((2.*midsat-1.)*sat-midsat)
    hsv[:, :, 1] = np.clip(sat, 0., 1.)
    self.image.set_hsv_image(hsv)
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    model, psat, interpolation = params
    tags = ["R", "Y", "G", "C", "B", "M"]
    operation = f"ColorSaturation(model = {model}, "
    for hid in range(6):
      operation += f"{tags[hid]} = {psat[hid]:.3f}, "
    operation += f" interpolation = {interpolation})"
    return operation

  # Plot HSV wheel.

  def plot_hsv_wheel(self):
    """Plot HSV wheel."""
    ax = self.widgets.fig.add_axes([.1, .1, .8, .8], projection = "polar")
    self.widgets.fig.satax = ax
    ax.patch.set_alpha(0.)
    ax2 = ax.figure.add_axes(ax.get_position(), projection = "polar", zorder = -3)
    ax2.axis("off")
    ax2.set_ylim(0., 1.)
    rho = np.linspace(1., 1.2, 32)
    phi = np.linspace(0., 2.*np.pi, 256)
    RHO, PHI = np.meshgrid(rho, phi)
    h = np.ravel(PHI/(2.*np.pi))
    s = np.ones_like(h)
    v = s
    hsv = np.column_stack((h, s, v))
    rgb = colors.hsv_to_rgb(hsv)
    ax2.scatter(PHI, RHO, c = rgb, clip_on = False)
    hue = 2.*np.pi*np.linspace(0., 5., 6)/6.
    ax.set_xticks(hue, labels = ["R", "Y", "G", "C", "B", "M"])
    ax.set_ylim([-1., 1.])
    ax.yaxis.set_major_locator(ticker.LinearLocator(5))
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.2f"))
    ax.satpoints, = ax.plot(hue, np.zeros_like(hue), "ko", ms = 8)
    hue = np.linspace(0., 2.*np.pi, 128)
    ax.satcurve, = ax.plot(hue, np.zeros_like(hue), "k--")

  # Update widgets.

  def update(self, changed):
    """Update widgets on change of 'changed'."""
    if changed >= 0:
      if self.widgets.bindbutton.get_active():
        psat = self.widgets.satscales[changed].get_value()
        for hid in range(6):
          self.widgets.satscales[hid].set_value_block(psat)
    if changed >= -1: self.update_hsv_wheel()
    self.reset_polling(self.get_params()) # Expedite main window update.

  def update_hsv_wheel(self):
    """Update HSV wheel."""
    model, psat, interpolation = self.get_params()
    psat = np.array(psat)
    pmin = psat.min()
    pmax = psat.max()
    ax = self.widgets.fig.satax
    ax.satpoints.set_ydata(psat)
    hsat = 2.*np.pi*np.linspace(0., 6., 7)/6.
    psat = np.append(psat, psat[0])
    if interpolation == "nearest":
      fsat = interp1d(hsat, psat, kind = "nearest")
    else:
      k = 3 if interpolation == "cubic" else 1
      tck = splrep(hsat, psat, k = k, per = True)
      def fsat(x): return np.clip(splev(x, tck), -1., 1.)
    ax.satcurve.set_ydata(fsat(ax.satcurve.get_xdata()))
    if np.all(psat == psat[0]) or pmax-pmin > .25:
      ymin = -1.
      ymax =  1.
    else:
      ymin = max(pmin-.125, -1.)
      ymax = min(pmax+.125,  1.)
      if ymax-ymin < .2:
        if ymax ==  1.:
          ymin =  .8
        elif ymin == -1.:
          ymax = -.8
    ax.set_ylim(ymin, ymax)
    self.widgets.fig.canvas.draw_idle()
