# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.6.0 / 2024.09.01

"""Misc Gtk utilities."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

# Shortcuts.
from gi.repository.GLib import markup_escape_text

class Container:
  """Empty class as a container."""
  pass

def get_work_area(window):
  """Return the width and height of the monitor displaying 'window'."""
  screen = window.get_screen()
  display = screen.get_display()
  monitor = display.get_monitor_at_window(screen.get_root_window())
  workarea = monitor.get_workarea()
  return workarea.width, workarea.height

def flush_gtk_events():
  """Flush all pending gtk events."""
  while Gtk.events_pending(): Gtk.main_iteration()

