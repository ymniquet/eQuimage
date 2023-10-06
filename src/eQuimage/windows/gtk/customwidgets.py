# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.0.0 / 2023.10.06

"""Custom Gtk widgets."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

class SpinButton(Gtk.SpinButton):
  """A custom Gtk spin button."""

  def __new__(cls, value, minimum, maximum, step, page = None, climb_rate = 2., digits = 2):
    """Return a Gtk spin button with current value 'value', minimum value 'minimum', maximum value 'maximum',
       step size 'step', page size 'page' (10*step if None), climb rate 'climb_rate' (default 2), and number of
       displayed digits 'digits'."""
    if page is None: page = 10.*step
    adjustment = Gtk.Adjustment(value = value, lower = minimum, upper = maximum, step_increment = step, page_increment = page)
    spin = Gtk.SpinButton.new(adjustment, climb_rate, digits)
    spin.set_numeric(True)
    spin.set_update_policy(Gtk.SpinButtonUpdatePolicy.IF_VALID)
    return spin

class HScale(Gtk.Scale):
  """A custom Gtk horizontal scale."""

  def __new__(cls, value, minimum, maximum, step, page = None, marks =  None, length = 512, expand = True):
    """Return a horizontal Gtk scale with current value 'value', minimum value 'minimum', maximum value 'maximum',
       step size 'step', page size 'page' (10*step if None), marks 'marks', and default length 'length' expandable
       if 'expand' is True."""
    if page is None: page = 10.*step
    adjustment = Gtk.Adjustment(value = value, lower = minimum, upper = maximum, step_increment = step, page_increment = page)
    scale = Gtk.Scale.new(Gtk.Orientation.HORIZONTAL, adjustment)
    if marks is not None:
      for mark in marks:
        scale.add_mark(mark, Gtk.PositionType.BOTTOM, f"{mark:.2f}")
      scale.set_value_pos(Gtk.PositionType.TOP)
    else:
      scale.set_value_pos(Gtk.PositionType.RIGHT)
    scale.set_value(value)
    scale.set_draw_value(True)
    scale.set_digits(2)
    scale.set_size_request(length, -1)
    scale.set_hexpand(expand)
    return scale

