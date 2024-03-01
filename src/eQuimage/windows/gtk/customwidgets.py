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

##########
# Boxes. #
##########

class HBox(Gtk.HBox):
  """Gtk horizontal box with default settings & wrappers."""

  def __init__(self, *args, **kwargs):
    """Initialize a Gtk.HBox with default spacing = 8."""
    kwargs.setdefault("spacing", 8)
    Gtk.HBox.__init__(self, *args, **kwargs)

  def pack(self, widget, expand = False, fill = False, padding = 0):
    """Wrapper for Gtk.HBox.pack_start(widget, expand, fill, padding) with default expand = False, fill = False and padding = 0."""
    self.pack_start(widget, expand, fill, padding)

class VBox(Gtk.VBox):
  """Gtk vertical box with default settings & wrappers."""

  def __init__(self, *args, **kwargs):
    """Initialize a Gtk.VBox with default spacing = 16."""
    kwargs.setdefault("spacing", 16)
    Gtk.HBox.__init__(self, *args, **kwargs)

  def pack(self, widget, expand = False, fill = False, padding = 0):
    """Wrapper for Gtk.VBox.pack_start(widget, expand, fill, padding) with default expand = False, fill = False and padding = 0."""
    self.pack_start(widget, expand, fill, padding)

def make_hbox(widget, pre = None, post = None, spacing = 8, expand = False):
  """Return a HBox with widgets 'pre', 'widget', and 'post' spaced by 'spacing'.
     If strings, 'pre' and 'post' are converted into Gtk labels.
     The 'widget' is packed as expandable & filling if 'expand' is True."""
  hbox = HBox(spacing = spacing)
  if pre is not None:
    if isinstance(pre, str): pre = Gtk.Label(pre)
    hbox.pack(pre)
  hbox.pack(widget, expand = expand, fill = expand)
  if post is not None:
    if isinstance(post, str): post = Gtk.Label(post)
    hbox.pack(post)
  return hbox

############
# Buttons. #
############

class Button(Signals, Gtk.Button):
  """A custom Gtk button with extended signal management."""

  def __init__(self, *args, **kwargs):
    """Initialize class."""
    Signals.__init__(self)
    Gtk.Button.__init__(self, *args, **kwargs)

#

class HoldButton(Signals, Gtk.Button):
  """A custom Gtk "hold" button with extended signal management.
     When pressed, this button emits a "hold" signal every 'delay' ms,
     then a "clicked" signal once released. The 'delay' can be
     specified as a kwarg when creating the button (default 500 ms)."""

  __gsignals__ = {"hold": (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, ())}

  def __init__(self, *args, **kwargs):
    """Initialize class.
       The button hold delay can be specified as kwarg 'delay' (default 500 ms)."""
    self.delay = kwargs.pop("delay", 500)
    Signals.__init__(self)
    Gtk.Button.__init__(self, *args, **kwargs)
    self.connect("pressed", self.__pressed)
    self.connect("released", self.__released)

  def __pressed(self, widget):
    """Internal callback for button press events."""
    self.timer = GObject.timeout_add(self.delay, self.__longpressed)

  def __longpressed(self):
    """Internal callback for button long press events."""
    self.emit("hold")
    return True

  def __released(self, widget):
    """Internal callback for button release events."""
    GObject.source_remove(self.timer)

#

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

#

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

##########################
# Spin buttons & scales. #
##########################

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

  def hbox(self, pre = None, post = None, spacing = 8):
    """Return a HBox with Gtk widget 'pre', the spin button, and Gtk widget 'post', spaced by 'spacing'.
       If strings, 'pre' and 'post' are converted into Gtk labels."""
    return make_hbox(self, pre, post, spacing, False)

#

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
    self.expand = expand

  def set_value_block(self, *args, **kwargs):
    """Set value, blocking all signals (no callbacks)."""
    self.block_all_signals()
    self.set_value(*args, **kwargs)
    self.unblock_all_signals()

  def hbox(self, pre = None, post = None, spacing = 8):
    """Return a HBox with Gtk widget 'pre', the horizontal scale, and Gtk widget 'post', spaced by 'spacing'.
       If strings, 'pre' and 'post' are converted into Gtk labels."""
    return make_hbox(self, pre, post, spacing, self.expand)

#

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
    self.scale.connect("value-changed", lambda scale: self.__sync(self.button, self.scale))
    self.button.connect("value-changed", lambda button: self.__sync(self.scale, self.button))
    self.__callbacks__ = {}

  def __sync(self, target, source):
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
       Return a HBox with label 'label' (if not None), the Gtk scale and spin button, spaced by 'spacing'."""
    hbox = HBox(spacing = spacing)
    if label is not None: hbox.pack(Gtk.Label(label = label))
    hbox.pack(self.scale, expand = self.expand, fill = self.expand)
    hbox.pack(self.button)
    return hbox

  def layout2(self, label = "", spacing = 8):
    """Two lines layout.
       Return a VBox with label 'label' and the Gtk spin button on one line (spaced by 'spacing'),
       and the Gtk scale on an other."""
    vbox = VBox(spacing = 0)
    hbox = HBox(spacing = spacing)
    vbox.pack(hbox)
    hbox.pack(Gtk.Label(label = label, halign = Gtk.Align.START), expand = True, fill = True)
    hbox.pack(self.button)
    vbox.pack(self.scale, expand = self.expand, fill = self.expand)
    return vbox

###############
# Text input. #
###############

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

  def hbox(self, pre = None, post = None, spacing = 8):
    """Return a HBox with Gtk widget 'pre', the entry, and Gtk widget 'post', spaced by 'spacing'.
       If strings, 'pre' and 'post' are converted into Gtk labels."""
    return make_hbox(self, pre, post, spacing, False)

##############
# Notebooks. #
##############

class Notebook(Signals, Gtk.Notebook):
  """A custom Gtk notebook with extended signal management."""

  def __init__(self, *args, **kwargs):
    """Initialize class."""
    Signals.__init__(self)
    Gtk.Notebook.__init__(self, *args, **kwargs)
