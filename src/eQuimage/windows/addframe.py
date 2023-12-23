# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2023.11.27

"""Add Unistellar frame from an other image."""

import os
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .gtk.customwidgets import Button, HoldButton, CheckButton, SpinButton
from .gtk.filechoosers import ImageChooserDialog
from .base import ErrorDialog
from .tools import BaseToolWindow
from ..imageprocessing.Unistellar import UnistellarImage as Image
import matplotlib.pyplot as plt
import numpy as np

class AddUnistellarFrame(BaseToolWindow):
  """Add Unistellar frame tool class."""

  __action__ = "Adding Unistellar frame..."

  delay = 333 # Long press delay for "HoldButton".
  maxfade = 0.05 # Maximum fade.

  def open(self, image):
    """Open tool window for image 'image'."""
    if not super().open(image, "Add frame"): return False
    filename = ImageChooserDialog(self.app.mainmenu.window, Gtk.FileChooserAction.OPEN, path = self.app.get_filename(), preview = True, title = "Open framed image")
    if filename is None:
      self.destroy()
      return False
    image = Image()
    image.load(filename, description = "Framed image")
    hasframe = image.check_frame()
    if not hasframe:
      ErrorDialog(self.window, "This image has no frame.")
      self.destroy()
      return False
    print(f"Image has a frame type '{image.get_frame_type()}'.")
    self.basename = os.path.basename(filename)
    self.frame = image.get_frame()
    self.fradius = image.get_frame_radius()
    self.fmargin = image.get_frame_margin()
    self.fwidth, self.fheight = self.frame.size()
    self.rwidth, self.rheight = self.reference.size()
    self.xcenter = 0
    self.ycenter = 0
    self.currentfade = None
    self.currentmove = None
    self.currentmask = None
    self.currentcrop = None
    wbox = Gtk.VBox(spacing = 16)
    self.window.add(wbox)
    hbox = Gtk.HBox(spacing = 8)
    wbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Frame margin:"), False, False, 0)
    self.widgets.marginspin = SpinButton(self.fmargin, 0, self.fradius//4, 1, digits = 0)
    self.connect_update_request(self.widgets.marginspin, "value-changed")
    hbox.pack_start(self.widgets.marginspin, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "pixels"), False, False, 0)
    hbox = Gtk.HBox(spacing = 8)
    wbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Fade length:"), False, False, 0)
    self.widgets.fadespin = SpinButton(25, 0, 50, 1, digits = 1)
    self.connect_update_request(self.widgets.fadespin, "value-changed")
    hbox.pack_start(self.widgets.fadespin, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "% frame radius"), False, False, 0)
    hbox = Gtk.HBox(spacing = 8)
    wbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Image scale:"), False, False, 0)
    self.widgets.scalespin = SpinButton(1., .5, 2., .01, digits = 2)
    self.connect_update_request(self.widgets.scalespin, "value-changed")
    hbox.pack_start(self.widgets.scalespin, False, False, 0)
    self.widgets.sizelabel = Gtk.Label(label = f" ({self.rwidth:.0f}x{self.rheight:.0f} px)")
    hbox.pack_start(self.widgets.sizelabel, False, False, 0)
    frame = Gtk.Frame(label = " Position ")
    frame.set_label_align(0.025, 0.5)
    wbox.pack_start(frame, False, False, 0)
    hbox = Gtk.HBox()
    frame.add(hbox)
    grid = Gtk.Grid(margin = 16)
    grid.set_column_homogeneous(True)
    grid.set_row_homogeneous(True)
    hbox.pack_start(grid, True, False, 0)
    self.widgets.cbutton = Button(label = "\u2022")
    self.widgets.cbutton.connect("clicked", lambda button: self.center_image())
    grid.add(self.widgets.cbutton)
    self.widgets.ubutton = HoldButton(delay = self.delay)
    self.widgets.ubutton.add(Gtk.Arrow(arrow_type = Gtk.ArrowType.UP, shadow_type = Gtk.ShadowType.NONE))
    self.widgets.ubutton.connect("hold", lambda button: self.move_image(0, +10))
    self.widgets.ubutton.connect("clicked", lambda button: self.move_image(0, +1))
    grid.attach_next_to(self.widgets.ubutton, self.widgets.cbutton, Gtk.PositionType.TOP, 1, 1)
    self.widgets.dbutton = HoldButton(delay = self.delay)
    self.widgets.dbutton.add(Gtk.Arrow(arrow_type = Gtk.ArrowType.DOWN, shadow_type = Gtk.ShadowType.NONE))
    self.widgets.dbutton.connect("hold", lambda button: self.move_image(0, -10))
    self.widgets.dbutton.connect("clicked", lambda button: self.move_image(0, -1))
    grid.attach_next_to(self.widgets.dbutton, self.widgets.cbutton, Gtk.PositionType.BOTTOM, 1, 1)
    self.widgets.lbutton = HoldButton(delay = self.delay)
    self.widgets.lbutton.add(Gtk.Arrow(arrow_type = Gtk.ArrowType.LEFT, shadow_type = Gtk.ShadowType.NONE))
    self.widgets.lbutton.connect("hold", lambda button: self.move_image(-10, 0))
    self.widgets.lbutton.connect("clicked", lambda button: self.move_image(-1, 0))
    grid.attach_next_to(self.widgets.lbutton, self.widgets.cbutton, Gtk.PositionType.LEFT, 1, 1)
    self.widgets.rbutton = HoldButton(delay = self.delay)
    self.widgets.rbutton.add(Gtk.Arrow(arrow_type = Gtk.ArrowType.RIGHT, shadow_type = Gtk.ShadowType.NONE))
    self.widgets.rbutton.connect("hold", lambda button: self.move_image(+10, 0))
    self.widgets.rbutton.connect("clicked", lambda button: self.move_image(+1, 0))
    grid.attach_next_to(self.widgets.rbutton, self.widgets.cbutton, Gtk.PositionType.RIGHT, 1, 1)
    self.widgets.gbutton = CheckButton(label = "Show guide lines")
    self.widgets.gbutton.set_active(False)
    self.widgets.gbutton.connect("toggled", lambda button: self.update_guide_lines(self.get_params()))
    wbox.pack_start(self.widgets.gbutton, False, False, 0)
    wbox.pack_start(self.tool_control_buttons(model = "onthefly", reset = False), False, False, 0)
    self.defaultparams = self.get_params()
    self.apply(cancellable = False)
    self.window.show_all()
    self.start_polling()
    return True

  def center_image(self):
    """Center image."""
    self.xcenter = 0
    self.ycenter = 0
    self.apply_async()

  def move_image(self, dx, dy):
    """Move image by dx pixels along x and dy pixels along y."""
    self.xcenter += dx
    self.ycenter += dy
    self.apply_async()

  def blend_mask(self, radius, margin, fade):
    """Return the mask for blending the image and frame.
       'radius' is the frame radius (pixels), 'margin' the frame margin (pixels), and 'fade' the fade length (as a fraction of radius)."""
    x = np.arange(0, self.fwidth)-(self.fwidth-1)/2
    y = np.arange(0, self.fheight)-(self.fheight-1)/2
    X, Y = np.meshgrid(x, y, sparse = True)
    r = np.sqrt(X**2+Y**2)
    r0 = radius-margin
    r1 = radius-margin-fade*radius/100.
    mask = np.clip(self.maxfade+(1.-self.maxfade)*(r0-r)/(r0-r1), self.maxfade, 1.) if r0 > r1 else np.ones_like(r)
    return np.where(r <= r0, mask, 0.)

  def plot_guide_lines(self, ax, radius, margin, fade):
    """Plot guide lines in axes 'ax' of the main window.
       'radius' is the frame radius (pixels), 'margin' the frame margin (pixels), and 'fade' the fade length (as a fraction of radius)."""
    x = ax.get_xlim()
    y = ax.get_ylim()
    xc = (x[0]+x[1])/2.
    yc = (y[0]+y[1])/2.
    ax.guidelines = []
    ax.guidelines.append(ax.axvline(xc, linestyle = "-.", linewidth = 1., color = "yellow"))
    ax.guidelines.append(ax.axhline(yc, linestyle = "-.", linewidth = 1., color = "yellow"))
    ax.guidelines.append(ax.add_patch(plt.Circle((xc, yc), radius-margin, linestyle = ":", linewidth = 1., color = "yellow", fill = False)))
    ax.guidelines.append(ax.add_patch(plt.Circle((xc, yc), radius-margin-fade*radius/100., linestyle = ":", linewidth = 1., color = "yellow", fill = False)))

  def get_params(self):
    """Return tool parameters."""
    return self.xcenter, self.ycenter, self.widgets.marginspin.get_value(), self.widgets.fadespin.get_value()

  def set_params(self, params):
    """Set tool parameters 'params'."""
    self.xcenter, self.ycenter, margin, fade = params
    self.widgets.marginspin.set_value(margin)
    self.widgets.fadespin.set_value(fade)

  def update_guide_lines(self, params):
    """Update guide lines in main window for parameters 'params'."""
    if self.widgets.gbutton.get_active():
      xc, yc, margin, fade = params
      self.app.mainwindow.set_guide_lines(lambda ax: self.plot_guide_lines(ax, self.fradius, margin, fade))
    else:
      self.app.mainwindow.set_guide_lines(None)

  def run(self, params):
    """Run tool for parameters 'params'."""
    xcenter, ycenter, margin, fade = params
    # Compute blend mask if needed.
    if (margin, fade) != self.currentfade:
      self.currentmask = self.blend_mask(self.fradius, margin, fade)
      self.currentfade = (margin, fade)
      self.update_guide_lines(params)
    # Move & crop image if needed.
    if (xcenter, ycenter) != self.currentmove:
      xcmin = (self.rwidth-self.fwidth)//2-xcenter
      xcmax = xcmin+self.fwidth
      ycmin = (self.rheight-self.fheight)//2+ycenter
      ycmax = ycmin+self.fheight
      xfmin = 0
      xfmax = self.fwidth
      yfmin = 0
      yfmax = self.fheight
      if xcmin < 0:
        dx = -xcmin
        xcmin += dx
        xfmin += dx
      if xcmax > self.rwidth:
        dx = self.rwidth-xcmax
        xcmax += dx
        xfmax += dx
      if ycmin < 0:
        dy = -ycmin
        ycmin += dy
        yfmin += dy
      if ycmax > self.rheight:
        dy = self.rheight-ycmax
        ycmax += dy
        yfmax += dy
      self.currentcrop = np.zeros((3, self.fheight, self.fwidth))
      self.currentcrop[:, yfmin:yfmax, xfmin:xfmax] = self.reference.image[:, ycmin:ycmax, xcmin:xcmax]
      self.currentmove = (xcenter, ycenter)
    # Blend image with frame.
    self.image = Image(self.currentmask*self.currentcrop[:]+(1.-self.currentmask)*self.frame.image[:], self.image.description)
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    return f"AddUnistellarFrame('{self.basename}')"

  def cleanup(self):
    """Free memory on exit."""
    try:
      del self.frame
      del self.currentmask
      del self.currentcrop
    except:
      pass
