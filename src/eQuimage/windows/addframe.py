# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.4.0 / 2024.02.26
# GUI updated.

"""Add Unistellar frame from an other image."""

import os
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .gtk.customwidgets import Label, HBox, VBox, FramedHBox, Grid, Button, HoldButton, CheckButton, SpinButton
from .gtk.filechoosers import ImageChooserDialog
from .base import ErrorDialog
from .tools import BaseToolWindow
from ..imageprocessing import imageprocessing
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
    filename = ImageChooserDialog(self.app.mainwindow.window, Gtk.FileChooserAction.OPEN, path = self.app.get_filename(), preview = True, title = "Open framed image")
    if filename is None:
      self.destroy()
      return False
    try:
      image = Image()
      image.load(filename)
    except Exception as err:
      ErrorDialog(self.window, str(err))
      self.destroy()
      return False
    framed = image.is_valid()
    if framed: framed = image.check_frame()
    if not framed:
      ErrorDialog(self.window, "This image has no frame.")
      self.destroy()
      return False
    print(f"""Image has a frame type '{framed["type"]}'.""")
    self.basename = os.path.basename(filename)
    self.frame = image.get_frame()
    self.fradius = framed["radius"]
    self.fmargin = framed["margin"]
    self.fwidth, self.fheight = self.frame.size()
    self.xcenter = 0
    self.ycenter = 0
    self.currentscale = None
    self.currentmove = None
    self.currentfade = None
    wbox = VBox()
    self.window.add(wbox)
    self.widgets.marginspin = SpinButton(self.fmargin, 0, self.fradius//4, 1, digits = 0)
    self.connect_update_request(self.widgets.marginspin, "value-changed")
    wbox.pack(self.widgets.marginspin.hbox(prepend = "Frame margin:", append = "pixels"))
    self.widgets.fadespin = SpinButton(25, 0, 50, 1, digits = 1)
    self.connect_update_request(self.widgets.fadespin, "value-changed")
    wbox.pack(self.widgets.fadespin.hbox(prepend = "Fade length:", append = "% frame radius"))
    self.widgets.scalespin = SpinButton(1., .25, 4., .01, digits = 3)
    self.connect_update_request(self.widgets.scalespin, "value-changed")
    self.widgets.sizelabel = Label(" (0x0) px")
    wbox.pack(self.widgets.scalespin.hbox(prepend = "Image scale:", append = self.widgets.sizelabel))
    frame, hbox = FramedHBox(" Position ", margin = 32)
    wbox.pack(frame)
    grid = Grid(column_spacing = 0, column_homogeneous = True, row_spacing = 0, row_homogeneous = True)
    hbox.pack(grid, expand = True)
    self.widgets.cbutton = Button(label = "\u2022")
    self.widgets.cbutton.connect("clicked", lambda button: self.center_image())
    grid.attach(self.widgets.cbutton, 1, 1)
    self.widgets.ubutton = HoldButton(delay = self.delay)
    self.widgets.ubutton.add(Gtk.Arrow(arrow_type = Gtk.ArrowType.UP, shadow_type = Gtk.ShadowType.NONE))
    self.widgets.ubutton.connect("hold", lambda button: self.move_image(0, +10))
    self.widgets.ubutton.connect("clicked", lambda button: self.move_image(0, +1))
    grid.attach(self.widgets.ubutton, 1, 0)
    self.widgets.dbutton = HoldButton(delay = self.delay)
    self.widgets.dbutton.add(Gtk.Arrow(arrow_type = Gtk.ArrowType.DOWN, shadow_type = Gtk.ShadowType.NONE))
    self.widgets.dbutton.connect("hold", lambda button: self.move_image(0, -10))
    self.widgets.dbutton.connect("clicked", lambda button: self.move_image(0, -1))
    grid.attach(self.widgets.dbutton, 1, 2)
    self.widgets.lbutton = HoldButton(delay = self.delay)
    self.widgets.lbutton.add(Gtk.Arrow(arrow_type = Gtk.ArrowType.LEFT, shadow_type = Gtk.ShadowType.NONE))
    self.widgets.lbutton.connect("hold", lambda button: self.move_image(-10, 0))
    self.widgets.lbutton.connect("clicked", lambda button: self.move_image(-1, 0))
    grid.attach(self.widgets.lbutton, 0, 1)
    self.widgets.rbutton = HoldButton(delay = self.delay)
    self.widgets.rbutton.add(Gtk.Arrow(arrow_type = Gtk.ArrowType.RIGHT, shadow_type = Gtk.ShadowType.NONE))
    self.widgets.rbutton.connect("hold", lambda button: self.move_image(+10, 0))
    self.widgets.rbutton.connect("clicked", lambda button: self.move_image(+1, 0))
    grid.attach(self.widgets.rbutton, 2, 1)
    self.widgets.gbutton = CheckButton(label = "Show guide lines")
    self.widgets.gbutton.set_active(False)
    self.widgets.gbutton.connect("toggled", lambda button: self.update_guide_lines(self.get_params()))
    wbox.pack(self.widgets.gbutton)
    wbox.pack(self.tool_control_buttons(model = "onthefly"))
    self.start(identity = False)
    return True

  def center_image(self):
    """Center image."""
    self.xcenter = 0
    self.ycenter = 0
    self.apply_idle()

  def move_image(self, dx, dy):
    """Move image by dx pixels along x and dy pixels along y."""
    self.xcenter += dx
    self.ycenter += dy
    self.apply_idle()

  def frame_mask(self, radius, margin, fade):
    """Return the mask for blending the image within the frame.
       'radius' is the frame radius (pixels), 'margin' the frame margin (pixels), and 'fade' the fade length (as a fraction of radius)."""
    x = np.arange(0, self.fwidth)-(self.fwidth-1)/2
    y = np.arange(0, self.fheight)-(self.fheight-1)/2
    X, Y = np.meshgrid(x, y, sparse = True)
    r = np.sqrt(X**2+Y**2)
    r0 = radius-margin
    r1 = radius-margin-fade*radius/100.
    mask = np.clip(self.maxfade+(1.-self.maxfade)*(r0-r)/(r0-r1), self.maxfade, 1.) if r0 > r1 else np.ones_like(r)
    mask = np.where(r <= r0, mask, 0.)
    return imageprocessing.IMGTYPE(mask)

  def plot_guide_lines(self, ax, radius, margin, fade):
    """Plot guide lines in axes 'ax' of the main window.
       'radius' is the frame radius (pixels), 'margin' the frame margin (pixels), and 'fade' the fade length (as a fraction of radius)."""
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    dx = abs(xlim[1]-xlim[0])
    dy = abs(ylim[1]-ylim[0])
    #if abs(dx-self.fwidth) > .5 or abs(dy-self.fheight) > .5: return # Dont't draw guidelines if the image does not match the frame size.
    xc = (xlim[0]+xlim[1])/2.
    yc = (ylim[0]+ylim[1])/2.
    ax.guidelines = []
    ax.guidelines.append(ax.axvline(xc, linestyle = "-.", linewidth = 1., color = "yellow"))
    ax.guidelines.append(ax.axhline(yc, linestyle = "-.", linewidth = 1., color = "yellow"))
    ax.guidelines.append(ax.add_patch(plt.Circle((xc, yc), radius-margin, linestyle = ":", linewidth = 1., color = "yellow", fill = False)))
    ax.guidelines.append(ax.add_patch(plt.Circle((xc, yc), radius-margin-fade*radius/100., linestyle = ":", linewidth = 1., color = "yellow", fill = False)))

  def get_params(self):
    """Return tool parameters."""
    return self.xcenter, self.ycenter, self.widgets.scalespin.get_value(), self.widgets.marginspin.get_value(), self.widgets.fadespin.get_value()

  def set_params(self, params):
    """Set tool parameters 'params'."""
    self.xcenter, self.ycenter, scale, margin, fade = params
    self.widgets.scalespin.set_value(scale)
    self.widgets.marginspin.set_value(margin)
    self.widgets.fadespin.set_value(fade)

  def update_guide_lines(self, params, redraw = True):
    """Update guide lines in main window for parameters 'params'.
       The main window canvas is redrawn if redraw is True."""
    if self.widgets.gbutton.get_active():
      xc, yc, scale, margin, fade = params
      self.app.mainwindow.set_guide_lines(lambda ax: self.plot_guide_lines(ax, self.fradius, margin, fade), redraw)
    else:
      self.app.mainwindow.set_guide_lines(None, redraw)

  def run(self, params):
    """Run tool for parameters 'params'."""
    xcenter, ycenter, scale, margin, fade = params
    # Compute frame mask if needed.
    if (margin, fade) != self.currentfade:
      self.fmask = self.frame_mask(self.fradius, margin, fade)
      self.currentfade = (margin, fade)
      self.update_guide_lines(params, redraw = False) # Will redraw later.
    # Rescale image if needed.
    if scale != self.currentscale:
      if scale == 1.:
        self.rescaled = self.reference.clone()
      else:
        self.rescaled = self.reference.rescale(scale, resample = imageprocessing.LANCZOS, inplace = False)
      self.rwidth, self.rheight = self.rescaled.size()
      self.currentscale = scale
      self.widgets.sizelabel.set_label(f" ({self.rwidth}x{self.rheight} px)")
      self.currentmove = None # Force move & crop image.
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
      self.cropped = imageprocessing.black_image(self.fwidth, self.fheight)
      self.cropped.rgb[:, yfmin:yfmax, xfmin:xfmax] = self.rescaled.rgb[:, ycmin:ycmax, xcmin:xcmax]
      self.currentmove = (xcenter, ycenter)
    # Blend image with frame.
    self.image.rgb = self.fmask*self.cropped.rgb+(1.-self.fmask)*self.frame.rgb
    return params, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    xcenter, ycenter, scale, margin, fade = params
    return f"AddUnistellarFrame(file = '{self.basename}', scale = {scale:.3f}, margin = {margin:.0f}px, fade = {fade/100.:.3f}R)"

  def cleanup(self):
    """Free memory on exit."""
    try:
      del self.frame
      del self.fmask
      del self.rescaled
      del self.cropped
    except:
      pass
