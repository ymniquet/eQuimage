# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.4.0 / 2024.02.26

"""Custom Gtk widgets."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject
from .signals import Signals

class Button(Signals, Gtk.Button):
  """A custom Gtk button with extended signal management."""

  def __init__(self, *args, **kwargs):
    """Initialize class."""
    Signals.__init__(self)
    Gtk.Button.__init__(self, *args, **kwargs)

class HoldButton(Signals, Gtk.Button):
  """A custom Gtk "hold" button with extended signal management.
     When pressed, this button emits a "hold" signal every 'delay' ms,
     then a "clicked" signal once released. The 'delay' can be
     specified as a kwarg when creating the button (default 500 ms)."""

  __gsignals__ = { "hold": (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, ()) }

  def __init__(self, *args, **kwargs):
    if "delay" in kwargs.keys():
      self.delay = kwargs["delay"]
      del kwargs["delay"]
    else:
      self.delay = 500
    Signals.__init__(self)
    Gtk.Button.__init__(self, *args, **kwargs)
    self.connect("pressed", self.pressed)
    self.connect("released", self.released)

  def pressed(self, widget):
    self.timer = GObject.timeout_add(self.delay, self.longpressed)

  def longpressed(self):
    self.emit("hold")
    return True

  def released(self, widget):
    GObject.source_remove(self.timer)

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

  @classmethod
  def new_with_label_from_widget(cls, widget, label):
    """Add a radio button with label 'label' to the group of widget 'button'."""
    button = cls(label = label)
    if widget is not None: button.join_group(widget)
    return button

  def set_active_block(self, *args, **kwargs):
    """Set button status, blocking all signals (no callbacks)."""
    self.block_all_signals()
    self.set_active(*args, **kwargs)
    self.unblock_all_signals()

class SpinButton(Signals, Gtk.SpinButton):
  """A custom Gtk spin button with extended signal management."""

  def __init__(self, value, minimum, maximum, step, page = None, digits = 2, climbrate = 0.01):
    """Return a Gtk spin button with current value 'value', minimum value 'minimum', maximum value 'maximum',
       step size 'step', page size 'page' (10*step if None), number of displayed digits 'digits', and climb rate 'climbrate'."""
    Signals.__init__(self)
    Gtk.SpinButton.__init__(self)
    self.configure(Gtk.Adjustment(value = value, lower = minimum, upper = maximum,
                                  step_increment = step, page_increment = 10*step if page is None else page), climbrate, digits)
    self.set_numeric(True)
    self.set_update_policy(Gtk.SpinButtonUpdatePolicy.IF_VALID)

  def set_value_block(self, *args, **kwargs):
    """Set value, blocking all signals (no callbacks)."""
    self.block_all_signals()
    self.set_value(*args, **kwargs)
    self.unblock_all_signals()

class HScale(Signals, Gtk.Scale):
  """A custom Gtk horizontal scale with extended signal management."""

  def __init__(self, value, minimum, maximum, step, page = None, marks = None, digits = 2, length = -1, expand = True):
    """Return a horizontal Gtk scale with current value 'value', minimum value 'minimum', maximum value 'maximum',
       step size 'step', page size 'page' (10*step if None), marks 'marks', number of displayed digits 'digits',
       and default length 'length' expandable if 'expand' is True."""
    Signals.__init__(self)
    Gtk.Scale.__init__(self)
    self.set_adjustment(Gtk.Adjustment(value = value, lower = minimum, upper = maximum,
                                       step_increment = step, page_increment = 10*step if page is None else page))
    self.set_orientation(Gtk.Orientation.HORIZONTAL)
    if marks is not None:
      for mark in marks:
        self.add_mark(mark, Gtk.PositionType.BOTTOM, f"{mark:.{digits}f}")
      self.set_value_pos(Gtk.PositionType.TOP)
    else:
      self.set_value_pos(Gtk.PositionType.RIGHT)
    self.set_value(value)
    self.set_draw_value(True)
    self.set_digits(digits)
    self.set_size_request(length, -1)
    self.set_hexpand(expand)

  def set_value_block(self, *args, **kwargs):
    """Set value, blocking all signals (no callbacks)."""
    self.block_all_signals()
    self.set_value(*args, **kwargs)
    self.unblock_all_signals()

class HScaleSpinButton():
  """A custom Gtk horizontal scale coupled to a custom Gtk spin button, with extended signal management."""

  def __init__(self, value, minimum, maximum, step, page = None, digits = 2, length = -1, expand = True, climbrate = 0.01):
    """Return a Gtk scale/Spin button with current value 'value', minimum value 'minimum', maximum value 'maximum',
       step size 'step', page size 'page' (10*step if None), number of displayed digits 'digits', default length 'length'
       expandable if 'expand' is True, and climb rate 'climbrate'."""
    self.expand = expand
    self.scale = HScale(value, minimum, maximum, step, page = page, digits = digits, length = length, expand = expand)
    self.button = SpinButton(value, minimum, maximum, step, page = page, digits = digits, climbrate = climbrate)
    self.scale.set_draw_value(False)
    self.scale.connect("value-changed", lambda scale: self.__sync__(self.button, self.scale))
    self.button.connect("value-changed", lambda button: self.__sync__(self.scale, self.button))
    self.__callbacks__ = {}

  def __sync__(self, target, source):
    """Synchronize the value of widget 'target' with the value of widget 'source'."""
    target.set_value_block(source.get_value())
    callback = self.__callbacks__.get("value-changed", None)
    if callback is not None: return callback(self)

  def connect(self, signal, callback):
    """Connect signal 'signal' to callback(self)."""
    if signal not in ["value-changed"]:
      raise ValueError("Unknown signal.")
    self.__callbacks__[signal] = callback

  def get_value(self):
    """Return Gtk scale/Spin button value."""
    return self.button.get_value()

  def set_value(self, value):
    """Set Gtk scale/Spin button value 'value'."""
    self.button.set_value(value)

  def set_value_block(self, value):
    """Set Gtk scale/Spin button value 'value', blocking all signals (no callbacks)."""
    self.scale.set_value_block(value)
    self.button.set_value_block(value)

  def layout1(self, label = None, spacing = 8):
    """Single line layout.
       Return a Gtk box with label 'label' (if not None), the Gtk scale and the spin button, spaced by 'spacing'."""
    hbox = Gtk.HBox(spacing = spacing)
    if label is not None: hbox.pack_start(Gtk.Label(label = label), False, False, 0)
    hbox.pack_start(self.scale, self.expand, self.expand, 0)
    hbox.pack_start(self.button, False, False, 0)
    return hbox

  def layout2(self, label = "", spacing = 8):
    """Two lines layout.
       Return a Gtk box with label 'label' and the Gtk spin button on one line (spaced by 'spacing'),
       and the Gtk scale on an other."""
    vbox = Gtk.VBox()
    hbox = Gtk.HBox(spacing = spacing)
    vbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = label, halign = Gtk.Align.START), True, True, 0)
    hbox.pack_start(self.button, False, False, 0)
    vbox.pack_start(self.scale, self.expand, self.expand, 0)
    return vbox

class Notebook(Signals, Gtk.Notebook):
  """A custom Gtk notebook with extended signal management."""

  def __init__(self, *args, **kwargs):
    """Initialize class."""
    Signals.__init__(self)
    Gtk.Notebook.__init__(self, *args, **kwargs)

class Entry(Signals, Gtk.Entry):
  """A custom Gtk entry with extended signal management."""

  def __init__(self, text = "", width = -1):
    """Return a Gtk entry with default text 'text' and width 'width' (in chars)."""
    Signals.__init__(self)
    Gtk.Entry.__init__(self)
    self.set_width_chars(width)
    self.set_text(text)

  def set_text_block(self, *args, **kwargs):
    """Set text, blocking all signals (no callbacks)."""
    self.block_all_signals()
    self.set_text(*args, **kwargs)
    self.unblock_all_signals()
