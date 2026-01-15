# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 3.0.0 / 2026.01.15
# Doc OK.

"""eQuimage package."""

__version__ = "3.0.0"
__packagepath__ = __path__[0]

# Import top-level symbols.

from .imports import *

# NB : Here is the list of functions which explicitely deal with channels.
# Please crosscheck/update these functions when adding new channels.
#  - Image.get_channel
#  - Image.set_channel
#  - Image.apply_channel
#  - Image.histograms
#  - Image.statistics
#  - Image.statistical_stretch
#  - Image.LDBS
#  - Image.filter
