# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.0.0 / 2023.10.06

"""Misc Gtk utilities."""

def get_work_area(window):
  """Return the width and height of the monitor displaying 'window'."""
  screen = window.get_screen()
  display = screen.get_display()
  monitor = display.get_monitor_at_window(screen.get_root_window())
  workarea = monitor.get_workarea()
  return workarea.width, workarea.height
