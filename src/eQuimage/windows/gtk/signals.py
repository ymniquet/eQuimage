# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 2023.09

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject
from matplotlib.backends.backend_gtk3 import NavigationToolbar2GTK3 as NavigationToolbar

"""Signals management."""

class Signals:
  """Signals management."""

  def __init__(self):
    """Initialize object."""
    self.signals = []

  def connect(self, widgets, signals, *args, **kwargs):
    """Connect signals 'signals' of widgets 'widgets' to the callback defined by (args, kwargs)."""
    if not isinstance(signals, (list, tuple)): signals = (signals, )
    if not isinstance(widgets, (list, tuple)): widgets = (widgets, )
    for widget in widgets:
      for signal in signals:
        self.signals.append((widget, widget.connect(signal, *args, **kwargs)))

  def block(self):
    """Block all signals."""
    for widget, signal in self.signals:
      widget.handler_block(signal)

  def unblock(self):
    """Unblock all signals."""
    for widget, signal in self.signals:
      widget.handler_unblock(signal)
