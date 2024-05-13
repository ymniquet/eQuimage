# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.5.0 / 2024.05.13

"""Signals management."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

class Signals:
  """Add extended signal management to a given widget class
     See gtk/customwidgets for examples."""

  def __init__(self):
    """Initialize class."""
    self._signals = {}

  def connect(self, signames, *args, **kwargs):
    """Connect signals 'signames' to the callback defined by (args, kwargs)."""
    if not isinstance(signames, tuple): signames = (signames, )
    for signame in signames:
      self._signals[signame] = super().connect(signame, *args, **kwargs)

  def disconnect(self, signames):
    """Disconnect signals 'signames'."""
    if not isinstance(signames, tuple): signames = (signames, )
    for signame in signames:
      super().disconnect(self._signals[signame])
      del self._signals[signame]

  def block(self, signames):
    """Block signals 'signames'."""
    if not isinstance(signames, tuple): signames = (signames, )
    for signame in signames:
      self.handler_block(self._signals[signame])

  def unblock(self, signames):
    """Unblock signals 'signames'."""
    if not isinstance(signames, tuple): signames = (signames, )
    for signame in signames:
      self.handler_unblock(self._signals[signame])

  def block_all_signals(self):
    """Block all signals."""
    for signal in self._signals.values():
      self.handler_block(signal)

  def unblock_all_signals(self):
    """Unblock all signals."""
    for signal in self._signals.values():
      self.handler_unblock(signal)
