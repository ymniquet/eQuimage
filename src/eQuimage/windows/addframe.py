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
    self.width, self.height = image.size()
    self.radius = image.get_frame_radius()
    self.frame = image.get_frame()
    self.center_image()
    wbox = Gtk.VBox(spacing = 16)
    self.window.add(wbox)
    hbox = Gtk.HBox(spacing = 8)
    wbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Fade length:"), False, False, 0)
    self.widgets.fadespin = SpinButton(10., 0., 20., 0.1, digits = 1)
    hbox.pack_start(self.widgets.fadespin, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "% radius"), False, False, 0)
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
    self.widgets.ubutton.connect("clicked", lambda button: self.move_image(0, +1))
    self.widgets.ubutton.connect("held", lambda button: self.move_image(0, +10))
    grid.attach_next_to(self.widgets.ubutton, self.widgets.cbutton, Gtk.PositionType.TOP, 1, 1)
    self.widgets.dbutton = HoldButton(delay = self.delay)
    self.widgets.dbutton.add(Gtk.Arrow(arrow_type = Gtk.ArrowType.DOWN, shadow_type = Gtk.ShadowType.NONE))
    self.widgets.dbutton.connect("clicked", lambda button: self.move_image(0, -1))
    self.widgets.dbutton.connect("held", lambda button: self.move_image(0, -10))
    grid.attach_next_to(self.widgets.dbutton, self.widgets.cbutton, Gtk.PositionType.BOTTOM, 1, 1)
    self.widgets.lbutton = HoldButton(delay = self.delay)
    self.widgets.lbutton.add(Gtk.Arrow(arrow_type = Gtk.ArrowType.LEFT, shadow_type = Gtk.ShadowType.NONE))
    self.widgets.lbutton.connect("clicked", lambda button: self.move_image(-1, 0))
    self.widgets.lbutton.connect("held", lambda button: self.move_image(-10, 0))
    grid.attach_next_to(self.widgets.lbutton, self.widgets.cbutton, Gtk.PositionType.LEFT, 1, 1)
    self.widgets.rbutton = HoldButton(delay = self.delay)
    self.widgets.rbutton.add(Gtk.Arrow(arrow_type = Gtk.ArrowType.RIGHT, shadow_type = Gtk.ShadowType.NONE))
    self.widgets.rbutton.connect("clicked", lambda button: self.move_image(+1, 0))
    self.widgets.rbutton.connect("held", lambda button: self.move_image(+10, 0))
    grid.attach_next_to(self.widgets.rbutton, self.widgets.cbutton, Gtk.PositionType.RIGHT, 1, 1)
    self.widgets.gdbutton = CheckButton(label = "Show guide lines")
    self.widgets.gdbutton.set_active(False)
    wbox.pack_start(self.widgets.gdbutton, False, False, 0)
    wbox.pack_start(self.tool_control_buttons(model = "onthefly", reset = False), False, False, 0)
    self.toolparams = self.get_params()
    self.window.show_all()
    return True

  def get_params(self):
    """Return tool parameters."""
    return self.basename, self.xc, self.yc, self.widgets.fadespin.get_value()

  def center_image(self):
    """Center image."""
    self.xc = 0
    self.yc = 0

  def move_image(self, dx, dy):
    """Move image by dx pixels along x and dy pixels along y."""
    self.xc += dx
    self.yc += dy

  def set_blend_mask(self, radius, fade):
    """Set mask for blending the frame and image."""
    x = np.arange(0, self.width)-self.width/2.
    y = np.arange(0, self.height)-self.height/2.
    X, Y = np.meshgrid(x, y, sparse = True)
    r = sqrt(X**2+Y**2)/radius
    self.mask = np.clip((1.-r)/fade, 0., 1.)

  def run(self, params):
    """Run tool for parameters 'params'."""
    reference = self.reference
    self.image = self.mask*reference+(1.-self.mask)*self.frame
    return None, True

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    return f"AddUnistellarFrame('{params[0]}')"

