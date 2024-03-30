# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.4.0 / 2024.03.30

"""Keyboard management."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk
from .utils import Container

def decode_key(event):
  """Decode keypress event and return a container 'key':
       - key.ctrl is True if "Ctrl" is pressed.
       - key.alt  is Trye if "Alt"  is pressed.
       - key.name is the key name.
       - key.uname is the key name in upper case letters."""
  key = Container()
  key.ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
  key.alt  = event.state & Gdk.ModifierType.MOD1_MASK
  key.name = Gdk.keyval_name(event.keyval)
  key.uname = key.name.upper()
  return key
