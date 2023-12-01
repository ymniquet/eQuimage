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
from .gtk.customwidgets import Button, CheckButton, SpinButton
from .gtk.filechoosers import ImageChooserDialog
from .base import ErrorDialog
from .tools import BaseToolWindow
from ..imageprocessing.Unistellar import UnistellarImage as Image

class AddUnistellarFrame(BaseToolWindow):
  """Add Unistellar frame tool class."""

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
    iframe = image.get_frame()
    self.toolparams = os.path.basename(filename)
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
    grid.add(self.widgets.cbutton)
    self.widgets.ubutton = Button()
    self.widgets.ubutton.add(Gtk.Arrow(arrow_type = Gtk.ArrowType.UP, shadow_type = Gtk.ShadowType.NONE))
    grid.attach_next_to(self.widgets.ubutton, self.widgets.cbutton, Gtk.PositionType.TOP, 1, 1)
    self.widgets.dbutton = Button()
    self.widgets.dbutton.add(Gtk.Arrow(arrow_type = Gtk.ArrowType.DOWN, shadow_type = Gtk.ShadowType.NONE))
    grid.attach_next_to(self.widgets.dbutton, self.widgets.cbutton, Gtk.PositionType.BOTTOM, 1, 1)
    self.widgets.lbutton = Button()
    self.widgets.lbutton.add(Gtk.Arrow(arrow_type = Gtk.ArrowType.LEFT, shadow_type = Gtk.ShadowType.NONE))
    grid.attach_next_to(self.widgets.lbutton, self.widgets.cbutton, Gtk.PositionType.LEFT, 1, 1)
    self.widgets.rbutton = Button()
    self.widgets.rbutton.add(Gtk.Arrow(arrow_type = Gtk.ArrowType.RIGHT, shadow_type = Gtk.ShadowType.NONE))
    grid.attach_next_to(self.widgets.rbutton, self.widgets.cbutton, Gtk.PositionType.RIGHT, 1, 1)
    self.widgets.gdbutton = CheckButton(label = "Show guide lines")
    self.widgets.gdbutton.set_active(False)
    wbox.pack_start(self.widgets.gdbutton, False, False, 0)
    wbox.pack_start(self.tool_control_buttons(model = "onthefly", reset = False), False, False, 0)
    self.window.show_all()
    return True

  def run(self, params):
    """Run tool for parameters 'params'."""
    return None, False

  def apply(self, *args, **kwargs):
    """Apply tool."""
    print("Adding Unistellar frame...")
    super().apply()

  def operation(self, params):
    """Return tool operation string for parameters 'params'."""
    return f"AddUnistellarFrame('{params}')"

