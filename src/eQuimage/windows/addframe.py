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
import numpy as np

class AddUnistellarFrame(BaseToolWindow):
  """Add Unistellar frame tool class."""

  delay = 333 # Long press delay for "HoldButton".

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
    self.fwidth, self.fheight = self.frame.size()
    self.rwidth, self.rheight = self.reference.size()
    self.xcenter = 0
    self.ycenter = 0
    self.currentfade = None
    self.currentmask = None
    self.currentmove = None
    self.currentcrop = None
    wbox = Gtk.VBox(spacing = 16)
    self.window.add(wbox)
    hbox = Gtk.HBox(spacing = 8)
    wbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Fade length:"), False, False, 0)
    self.widgets.fadespin = SpinButton(10., 0., 20., 0.1, digits = 1)
    self.widgets.fadespin.connect("value-changed", lambda button: self.apply())
    hbox.pack_start(self.widgets.fadespin, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "% frame radius"), False, False, 0)
    frame = Gtk.Frame(label = " Position ")
    frame.set_label_align(0.05, 0.5)
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
    self.widgets.ubutton.connect("hold", lambda button: self.move_image(0, +10, update = False))    
    self.widgets.ubutton.connect("clicked", lambda button: self.move_image(0, +1))
    grid.attach_next_to(self.widgets.ubutton, self.widgets.cbutton, Gtk.PositionType.TOP, 1, 1)
    self.widgets.dbutton = HoldButton(delay = self.delay)
    self.widgets.dbutton.add(Gtk.Arrow(arrow_type = Gtk.ArrowType.DOWN, shadow_type = Gtk.ShadowType.NONE))
    self.widgets.dbutton.connect("hold", lambda button: self.move_image(0, -10, update = False))    
    self.widgets.dbutton.connect("clicked", lambda button: self.move_image(0, -1))
    grid.attach_next_to(self.widgets.dbutton, self.widgets.cbutton, Gtk.PositionType.BOTTOM, 1, 1)
    self.widgets.lbutton = HoldButton(delay = self.delay)
    self.widgets.lbutton.add(Gtk.Arrow(arrow_type = Gtk.ArrowType.LEFT, shadow_type = Gtk.ShadowType.NONE))
    self.widgets.lbutton.connect("hold", lambda button: self.move_image(-10, 0, update = False))    
    self.widgets.lbutton.connect("clicked", lambda button: self.move_image(-1, 0))
    grid.attach_next_to(self.widgets.lbutton, self.widgets.cbutton, Gtk.PositionType.LEFT, 1, 1)
    self.widgets.rbutton = HoldButton(delay = self.delay)
    self.widgets.rbutton.add(Gtk.Arrow(arrow_type = Gtk.ArrowType.RIGHT, shadow_type = Gtk.ShadowType.NONE))
    self.widgets.rbutton.connect("hold", lambda button: self.move_image(+10, 0, update = False))    
    self.widgets.rbutton.connect("clicked", lambda button: self.move_image(+1, 0))
    grid.attach_next_to(self.widgets.rbutton, self.widgets.cbutton, Gtk.PositionType.RIGHT, 1, 1)
    self.widgets.gdbutton = CheckButton(label = "Show guide lines")
    self.widgets.gdbutton.set_active(False)
    self.widgets.gdbutton.connect("toggled", lambda button: self.app.mainwindow.show_guide_lines(self.widgets.gdbutton.get_active()))
    wbox.pack_start(self.widgets.gdbutton, False, False, 0)
    wbox.pack_start(self.tool_control_buttons(model = "onthefly", reset = False), False, False, 0)
    self.toolparams = self.get_params()
    self.apply()
    self.window.show_all()
    return True

  def center_image(self):
    """Center image."""
    self.xcenter = 0
    self.ycenter = 0
    self.apply()

  def move_image(self, dx, dy, update = True):
    """Move image by dx pixels along x and dy pixels along y.
       Update main window only if 'update' is True."""
    self.xcenter += dx
    self.ycenter += dy
    if update: self.apply()

  def blend_mask(self, radius, fade):
    """Return mask for blending image and frame."""
    x = np.arange(0, self.fwidth)-(self.fwidth-1)/2.
    y = np.arange(0, self.fheight)-(self.fheight-1)/2.
    X, Y = np.meshgrid(x, y, sparse = True)
    r = np.sqrt(X**2+Y**2)/radius
    return np.clip(100.*(1.-r)/fade, 0., 1.)

  def get_params(self):
    """Return tool parameters."""
    return self.xcenter, self.ycenter, self.widgets.fadespin.get_value(), self.basename

  def run(self, params):
    """Run tool for parameters 'params'."""
    xcenter, ycenter, fade, *others = params
    # Compute blend mask if needed.
    if fade != self.currentfade:
      self.currentmask = self.blend_mask(self.fradius, fade)
      self.currentfade = fade
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
    return f"AddUnistellarFrame('{params[-1]}')"
