# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.5.0 / 2024.05.13

"""Custom Gtk widgets."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GObject
from .signals import Signals
from collections import OrderedDict as OD

##############
# Shortcuts. #
##############

Align = Gtk.Align

###########
# Labels. #
###########

class Label(Gtk.Label):
  """Gtk label with markup enabled."""

  def __init__(self, label = "", markup = True, **kwargs):
    """Initialize a Gtk.Label with label 'label' and default halign = Gtk.Align.START.
       Markup is enabled unless 'markup' is False. All other kwargs are passed to Gtk.Label."""
    kwargs.setdefault("halign", Align.START)
    Gtk.Label.__init__(self, **kwargs)
    if markup:
      self.set_markup(label)
    else:
      self.set_label(label)

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
    """Wrapper for Gtk.HBox.pack_start(widget, expand, fill, padding) with default expand = False, fill = False and padding = 0.
       If a string, 'widget' is converted into a Gtk label."""
    if isinstance(widget, str): widget = Label(widget)
    self.pack_start(widget, expand, fill, padding)

#

class VBox(Gtk.VBox):
  """Gtk vertical box with default settings & wrappers."""

  def __init__(self, *args, **kwargs):
    """Initialize a Gtk.VBox with default spacing = 16."""
    kwargs.setdefault("spacing", 16)
    Gtk.VBox.__init__(self, *args, **kwargs)

  def pack(self, widget, expand = False, fill = False, padding = 0):
    """Wrapper for Gtk.VBox.pack_start(widget, expand, fill, padding) with default expand = False, fill = False and padding = 0.
       If a string, 'widget' is converted into a Gtk label."""
    if isinstance(widget, str): widget = Label(widget)
    self.pack_start(widget, expand, fill, padding)

#

class FramedHBox():
  """Framed horizontal box with default settings & wrappers."""

  def __new__(cls, label = None, align = (.05, .5), **kwargs):
    """Initialize a framed HBox with default margin = 16 (with respect to the frame).
       'label' is the label of the frame. The position of the label within the frame is controlled
       by 'align' (see Gtk.Frame.set_label_align). All other kwargs are passed to HBox.
       Returns the Gtk frame widget and the HBox."""
    kwargs.setdefault("margin", 16)
    hbox = HBox(**kwargs)
    frame = Gtk.Frame(label = label)
    frame.set_label_align(*align)
    frame.add(hbox)
    return frame, hbox

#

class FramedVBox():
  """Framed vertical box with default settings & wrappers."""

  def __new__(cls, label = None, align = (.05, .5), **kwargs):
    """Initialize a framed VBox with default margin = 16 (with respect to the frame).
       'label' is the label of the frame. The position of the label within the frame is controlled
       by 'align' (see Gtk.Frame.set_label_align). All other kwargs are passed to VBox.
       Returns the Gtk frame widget and the HBox."""
    kwargs.setdefault("margin", 16)
    vbox = VBox(**kwargs)
    frame = Gtk.Frame(label = label)
    frame.set_label_align(*align)
    frame.add(vbox)
    return frame, vbox

#

class HButtonBox(Gtk.HButtonBox):
  """Gtk horizontal button box with default settings & wrappers."""

  def __init__(self, *args, **kwargs):
    """Initialize a Gtk.HButtonBox with default homogeneous = True, spacing = 16 and halign = Gtk.Align.START."""
    kwargs.setdefault("homogeneous", True)
    kwargs.setdefault("spacing", 16)
    kwargs.setdefault("halign", Align.START)
    Gtk.HButtonBox.__init__(self, *args, **kwargs)

  def pack(self, widget, expand = False, fill = False, padding = 0):
    """Wrapper for Gtk.HButtonBox.pack_start(widget, expand, fill, padding) with default expand = False, fill = False and padding = 0."""
    self.pack_start(widget, expand, fill, padding)

#

class ScrolledBox(Gtk.ScrolledWindow):
  """Gtk scrolled window with default settings & wrappers."""

  def __init__(self, width, height, *args, **kwargs):
    """Initialize a Gtk.ScrolledWindow with minimal width 'width' and minimal height 'height'."""
    Gtk.ScrolledWindow.__init__(self, *args, **kwargs)
    self.set_min_content_width(width)
    self.set_min_content_height(height)

#

def pack_hbox(widget, prepend = None, append = None, spacing = 8, expand = False):
  """Return a HBox with widgets 'prepend', 'widget', and 'append' spaced by 'spacing'.
     If strings, 'prepend' and 'append' are converted into labels.
     The 'widget' is packed as expandable & filling if 'expand' is True."""
  hbox = HBox(spacing = spacing)
  if prepend is not None:
    if isinstance(prepend, str): prepend = Label(prepend)
    hbox.pack(prepend)
  hbox.pack(widget, expand = expand, fill = expand)
  if append is not None:
    if isinstance(append, str): append = Label(append)
    hbox.pack(append)
  return hbox

##########
# Grids. #
##########

class Grid(Gtk.Grid):
  """Gtk grid with default settings & wrappers."""

  def __init__(self, *args, **kwargs):
    """Initialize a Gtk.Grid with default column_spacing = 8."""
    kwargs.setdefault("column_spacing", 8)
    Gtk.Grid.__init__(self, *args, **kwargs)

  def attach(self, widget, left, top, width = 1, height = 1):
    """Wrapper for Gtk.Grid.attach(widget, left, top, width, height) with default width = 1 and height = 1.
       If a string, 'widget' is converted into a Gtk label."""
    if isinstance(widget, str): widget = Label(widget)
    Gtk.Grid.attach(self, widget, left, top, width, height)

############
# Buttons. #
############

class Button(Signals, Gtk.Button):
  """Custom Gtk button with extended signal management."""

  def __init__(self, *args, **kwargs):
    """Initialize class."""
    Signals.__init__(self)
    Gtk.Button.__init__(self, *args, **kwargs)

#

class HoldButton(Signals, Gtk.Button):
  """Custom Gtk "hold" button with extended signal management.
     When pressed, this button emits a "hold" signal every 'delay' ms,
     then a "clicked" signal once released."""

  __gsignals__ = {"hold": (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, ())}

  def __init__(self, *args, delay = 500, **kwargs):
    """Initialize class. 'delay' is the button hold delay (default 500 ms)."""
    Signals.__init__(self)
    Gtk.Button.__init__(self, *args, **kwargs)
    self.delay = delay
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
  """Custom Gtk check button with extended signal management."""

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
  """Custom Gtk radio button with extended signal management."""

  def __init__(self, *args, **kwargs):
    """Initialize class."""
    Signals.__init__(self)
    Gtk.RadioButton.__init__(self, *args, **kwargs)

  @classmethod
  def new_with_label_from_widget(cls, widget, label):
    """Add a radio button with label 'label' to the group of widget 'widget'."""
    button = cls(label = label)
    if widget is not None: button.join_group(widget)
    return button

  def set_active_block(self, *args, **kwargs):
    """Set button status, blocking all signals (no callbacks)."""
    self.block_all_signals()
    self.set_active(*args, **kwargs)
    self.unblock_all_signals()

#

class RadioButtons:
  """Group of custom Gtk radio buttons."""

  def __init__(self, *args):
    """Initialize a group of custom Gtk radio buttons defined by *args, a
       list of tuples (key, label), where 'key' is a key that uniquely identifies
       the button and 'label' is the button label."""
    firstbutton = None
    self.buttons = OD()
    for key, label in args:
      if key in self.buttons.keys():
        raise KeyError(f"The key '{key}' is already registered.")
      button = RadioButton.new_with_label_from_widget(firstbutton, label)
      button.key = key
      self.buttons[key] = button
      if firstbutton is None: firstbutton = button

  def get_selected(self):
    """Return the key of the selected radio button."""
    for key, button in self.buttons.items():
      if button.get_active(): return key
    return None # Shall not happen !

  def set_selected(self, key):
    """Select the radio button with key 'key'."""
    try:
      self.buttons[key].set_active(True)
    except KeyError:
      raise KeyError(f"There is no button with key '{key}'.")

  def set_selected_block(self, key):
    """Select the radio button with key 'key', blocking all signals (no callbacks)."""
    try:
      self.buttons[key].set_active_block(True)
    except KeyError:
      raise KeyError(f"There is no button with key '{key}'.")

  def connect(self, *args, **kwargs):
    """Connect signal & callback to all buttons."""
    for button in self.buttons.values():
      button.connect(*args, **kwargs)

  def hbox(self, prepend = None, append = None, spacing = 8):
    """Return a HBox with widget 'prepend', the radio buttons, and widget 'append', spaced by 'spacing'.
       If strings, 'prepend' and 'append' are converted into labels."""
    buttonsbox = HBox(spacing = spacing)
    for button in self.buttons.values():
      buttonsbox.pack(button)
    return pack_hbox(buttonsbox, prepend, append, spacing, False)

##########################
# Spin buttons & scales. #
##########################

class SpinButton(Signals, Gtk.SpinButton):
  """Custom Gtk spin button with extended signal management."""

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

  def hbox(self, prepend = None, append = None, spacing = 8):
    """Return a HBox with widget 'prepend', the spin button, and widget 'append', spaced by 'spacing'.
       If strings, 'prepend' and 'append' are converted into labels."""
    return pack_hbox(self, prepend, append, spacing, False)

#

class HScale(Signals, Gtk.Scale):
  """Custom Gtk horizontal scale with extended signal management."""

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

  def hbox(self, prepend = None, append = None, spacing = 8):
    """Return a HBox with widget 'prepend', the horizontal scale, and widget 'append', spaced by 'spacing'.
       If strings, 'prepend' and 'append' are converted into labels."""
    return pack_hbox(self, prepend, append, spacing, self.expand)

#

class HScaleSpinButton():
  """Custom Gtk horizontal scale coupled to a custom Gtk spin button, with extended signal management."""

  def __init__(self, value, minimum, maximum, step, page = None, digits = 2, length = -1, expand = True, climbrate = 0.01):
    """Return a Gtk scale/spin button with current value 'value', minimum value 'minimum', maximum value 'maximum',
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
    """Return Gtk scale/spin button value."""
    return self.button.get_value()

  def set_value(self, value):
    """Set Gtk scale/spin button value 'value'."""
    self.button.set_value(value)

  def set_value_block(self, value):
    """Set Gtk scale/spin button value 'value', blocking all signals (no callbacks)."""
    self.scale.set_value_block(value)
    self.button.set_value_block(value)

  def layout1(self, label = None, spacing = 8):
    """Single line layout.
       Return a HBox with label 'label' (if not None), the Gtk scale and spin button, spaced by 'spacing'."""
    hbox = HBox(spacing = spacing)
    if label is not None: hbox.pack(Label(label))
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
    hbox.pack(Label(label), expand = True, fill = True)
    hbox.pack(self.button)
    vbox.pack(self.scale, expand = self.expand, fill = self.expand)
    return vbox

################
# Combo boxes. #
################

class ComboBoxText(Signals, Gtk.ComboBoxText):
  """Custom Gtk combo box with extended signal management."""

  def __init__(self, *args):
    """Initialize a Gtk combo box with items defined by *args, a list of tuples (key, label),
       where 'key' is a key that uniquely identifies the item and 'label' is the item label."""
    Signals.__init__(self)
    Gtk.ComboBoxText.__init__(self)
    self.keys = []
    for key, label in args:
      if key in self.keys:
        raise KeyError(f"The key '{key}' is already registered.")
      self.keys.append(key)
      self.append_text(label)
    self.set_active(0)

  def get_selected(self):
    """Return the key of the selected combo box item."""
    return self.keys[self.get_active()]

  def set_selected(self, key):
    """Select the combo box item with key 'key'."""
    try:
      self.set_active(self.keys.index(key))
    except ValueError:
      raise KeyError(f"There is no item with key '{key}'.")

  def set_selected_block(self, key):
    """Select the combo box item with key 'key', blocking all signals (no callbacks)."""
    self.block_all_signals()
    try:
      self.set_active(self.keys.index(key))
    except ValueError:
      raise KeyError(f"There is no item with key '{key}'.")
    self.unblock_all_signals()

  def hbox(self, prepend = None, append = None, spacing = 8):
    """Return a HBox with widget 'prepend', the combo box, and widget 'append', spaced by 'spacing'.
       If strings, 'prepend' and 'append' are converted into labels."""
    return pack_hbox(self, prepend, append, spacing, False)

###############
# Text input. #
###############

class Entry(Signals, Gtk.Entry):
  """Custom Gtk entry with extended signal management."""

  def __init__(self, text = "", width = -1):
    """Return a Gtk entry with default text 'text' and width 'width' (in chars)."""
    Signals.__init__(self)
    Gtk.Entry.__init__(self)
    self.expand = (width <= 0)
    self.set_width_chars(width)
    self.set_text(text)

  def set_text_block(self, *args, **kwargs):
    """Set text, blocking all signals (no callbacks)."""
    self.block_all_signals()
    self.set_text(*args, **kwargs)
    self.unblock_all_signals()

  def hbox(self, prepend = None, append = None, spacing = 8):
    """Return a HBox with widget 'prepend', the entry, and widget 'append', spaced by 'spacing'.
       If strings, 'prepend' and 'append' are converted into labels."""
    return pack_hbox(self, prepend, append, spacing, self.expand)

#

class TextBuffer(Signals, Gtk.TextBuffer):
  """Custom Gtk text buffer with extended signal management."""

  def __init__(self):
    """Return a Gtk text buffer."""
    Signals.__init__(self)
    Gtk.TextBuffer.__init__(self)

  def set_text_block(self, *args, **kwargs):
    """Set text, blocking all signals (no callbacks)."""
    self.block_all_signals()
    self.set_text(*args, **kwargs)
    self.unblock_all_signals()

  def append_text(self, text):
    """Append text 'text'."""
    self.insert(self.get_end_iter(), text, -1)

  def append_text_block(self, text):
    """Append text 'text', blocking all signals."""
    self.block_all_signals()
    self.insert(self.get_end_iter(), text, -1)
    self.unblock_all_signals()

  def append_markup(self, text):
    """Append markup text 'text'."""
    self.insert_markup(self.get_end_iter(), text, -1)

  def append_markup_block(self, text):
    """Append markup text 'text', blocking all signals."""
    self.block_all_signals()
    self.insert_markup(self.get_end_iter(), text, -1)
    self.unblock_all_signals()

  def copy_to_clipboard(self, *args, **kwargs):
    """Copy the content of the text buffer to the clipboard."""
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    clipboard.set_text(self.get_text(self.get_start_iter(), self.get_end_iter(), False), -1)

#

class TextView(Signals, Gtk.TextView):
  """Custom Gtk text view with extended signal management."""

  def __init__(self, textbuffer = None, editable = False, wrap = True, justification = Gtk.Justification.LEFT):
    """Return a Gtk text view with text buffer 'textbuffer' (created if None).
       The text view is editable if 'editable' is True, the text is wrapped if 'wrapped' is True, and is justified
       according to 'justification'."""
    Signals.__init__(self)
    Gtk.TextView.__init__(self)
    self.set_editable(editable)
    self.set_cursor_visible(editable)
    self.set_wrap_mode(wrap)
    self.set_justification(justification)
    if textbuffer is None: textbuffer = TextBuffer()
    self.set_buffer(textbuffer)

  def get_text(self, *args, **kwargs):
    """Get text."""
    return self.get_buffer().get_text()

  def set_text(self, *args, **kwargs):
    """Set text."""
    self.get_buffer().set_text(*args, **kwargs)

  def set_text_block(self, *args, **kwargs):
    """Set text, blocking all signals (no callbacks)."""
    self.get_buffer().set_text_block(*args, **kwargs)

  def append_text(self, text):
    """Append text 'text'."""
    self.get_buffer().append_text(text)

  def append_text_block(self, text):
    """Append text 'text', blocking all signals."""
    self.get_buffer().append_text_block(text)

  def append_markup(self, text):
    """Append markup text 'text'."""
    self.get_buffer().append_markup(text)

  def append_markup_block(self, text):
    """Append markup text 'text', blocking all signals."""
    self.get_buffer().append_markup_block(text)

  def copy_to_clipboard(self, *args, **kwargs):
    """Copy the content of the text view to the clipboard."""
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    self.get_buffer().copy_to_clipboard(*args, **kwargs)

##############
# Notebooks. #
##############

class Notebook(Signals, Gtk.Notebook):
  """Custom Gtk notebook with extended signal management."""

  def __init__(self, *args, pos = Gtk.PositionType.TOP, **kwargs):
    """Initialize Gtk notebook with tabs at position 'pos'."""
    Signals.__init__(self)
    Gtk.Notebook.__init__(self, *args, **kwargs)
    self.set_tab_pos(pos)
