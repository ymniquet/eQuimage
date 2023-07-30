#!/usr/bin/python

# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (ymniquet@gmail.com).
# Version: 2023.06

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from matplotlib.backends.backend_gtk3 import NavigationToolbar2GTK3 as NavigationToolbar

"""Gtk helper functions and classes."""

def get_work_area(window):
  """Return the width and height of the monitor dipslaying 'window'."""
  screen = window.get_screen()
  display = screen.get_display()
  monitor = display.get_monitor_at_window(screen.get_root_window())
  workarea = monitor.get_workarea()
  return workarea.width, workarea.height

class ErrorDialog(Gtk.MessageDialog):   
  """Modal error dialog class."""
  
  def __init__(self, parent, message):
    """Open a modal error dialog showing 'message' for window 'parent'.""" 
    super().__init__(title = "Error",
                     transient_for = parent,  
                     destroy_with_parent = True,                           
                     message_type = Gtk.MessageType.ERROR,                             
                     buttons = Gtk.ButtonsType.CLOSE,
                     modal = True)
    self.set_markup(message)        
    self.run()
    self.destroy()
    
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
      
class BaseToolbar(NavigationToolbar):
  """A custom matplotlib navigation toolbar for integration in Gtk.
     This is the default matplotlib navigation toolbar with the
     "Forward", "Back", "Subplots", and "Save" buttons disabled."""
     
  def __init__(self, canvas, parent):
    toolitems = []
    previous = None    
    for tool in self.toolitems:
      name = tool[0]
      if name is None:
        keep = previous is not None
      else:
        keep = name not in ("Forward", "Back", "Subplots", "Save")
      if keep: 
        toolitems.append(tool)
        previous = name
    if toolitems:
      if toolitems[-1][0] is None: toolitems.pop(-1)
    self.toolitems = tuple(toolitems)
    super().__init__(canvas, parent)      
