# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 2023.10 *

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .signals import Signals

"""Custom Gtk widgets."""

class Button(Signals, Gtk.Button):
  """A custom Gtk button with extended signal management."""

  def __init__(self, *args, **kwargs):
    """Initialize class."""
    Signals.__init__(self)
    Gtk.Button.__init__(self, *args, **kwargs)

class CheckButton(Signals, Gtk.CheckButton):
  """A custom Gtk check button with extended signal management."""

  def __init__(self, *args, **kwargs):
    """Initialize class."""
    Signals.__init__(self)
    Gtk.CheckButton.__init__(self, *args, **kwargs)

  def set_active_block(self, *args, **kwargs):
    """Set button status, blocking all signals (no callbacks)."""
    self.block_all_signals()
    self.set_active(*args, **kwargs)
    self.unblock_all_signals()

class RadioButton(Signals, Gtk.RadioButton):
  """A custom Gtk radio button with extended signal management."""

  def __init__(self, *args, **kwargs):
    """Initialize class."""
    Signals.__init__(self)
    Gtk.RadioButton.__init__(self, *args, **kwargs)

  def set_active_block(self, *args, **kwargs):
    """Set button status, blocking all signals (no callbacks)."""
    self.block_all_signals()
    self.set_active(*args, **kwargs)
    self.unblock_all_signals()

class SpinButton(Signals, Gtk.SpinButton):
  """A custom Gtk spin button with extended signal management."""

  def __init__(self, value, minimum, maximum, step, page = None, digits = 2):
    """Return a Gtk spin button with current value 'value', minimum value 'minimum', maximum value 'maximum',
       step size 'step', page size 'page' (10*step if None), and number of displayed digits 'digits'."""
    Signals.__init__(self)
    Gtk.SpinButton.__init__(self)
    self.set_adjustment(Gtk.Adjustment(value = value, lower = minimum, upper = maximum,
                                      step_increment = step, page_increment = 10*step if page is None else page))
    self.set_numeric(True)
    self.set_digits(digits)
    self.set_update_policy(Gtk.SpinButtonUpdatePolicy.IF_VALID)

  def set_value_block(self, *args, **kwargs):
    """Set value, blocking all signals (no callbacks)."""
    self.block_all_signals()
    self.set_value(*args, **kwargs)
    self.unblock_all_signals()

class HScale(Signals, Gtk.Scale):
  """A custom Gtk horizontal scale with extended signal management."""

  def __init__(self, value, minimum, maximum, step, page = None, marks =  None, length = 512, expand = True):
    """Return a horizontal Gtk scale with current value 'value', minimum value 'minimum', maximum value 'maximum',
       step size 'step', page size 'page' (10*step if None), marks 'marks', and default length 'length' expandable
       if 'expand' is True."""
    Signals.__init__(self)
    Gtk.Scale.__init__(self)
    self.set_adjustment(Gtk.Adjustment(value = value, lower = minimum, upper = maximum,
                                       step_increment = step, page_increment = 10*step if page is None else page))
    self.set_orientation(Gtk.Orientation.HORIZONTAL)
    if marks is not None:
      for mark in marks:
        self.add_mark(mark, Gtk.PositionType.BOTTOM, f"{mark:.2f}")
      self.set_value_pos(Gtk.PositionType.TOP)
    else:
      self.set_value_pos(Gtk.PositionType.RIGHT)
    self.set_value(value)
    self.set_draw_value(True)
    self.set_digits(2)
    self.set_size_request(length, -1)
    self.set_hexpand(expand)

  def set_value_block(self, *args, **kwargs):
    """Set value, blocking all signals (no callbacks)."""
    self.block_all_signals()
    self.set_value(*args, **kwargs)
    self.unblock_all_signals()
    
class Notebook(Signals, Gtk.Notebook):
  """A custom Gtk notebook with extended signal management."""

  def __init__(self, *args, **kwargs):
    """Initialize class."""
    Signals.__init__(self)
    Gtk.Notebook.__init__(self, *args, **kwargs)

    
