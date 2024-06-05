# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.5.1 / 2024.06.05
# GUI updated.

"""Base window classes and widgets."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .gtk.utils import Container
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.backends.backend_gtk3 import NavigationToolbar2GTK3 as NavigationToolbar

class BaseWindow:
  """Generic application window."""

  def __init__(self, app):
    """Bind the window with application 'app'."""
    self.app = app
    self.opened = False

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
    try:
      super().__init__(canvas, parent) # Old API.
    except:
      super().__init__(canvas) # New API.
