# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 3.0.0 / 2026.03.10
# Doc OK.

"""eQuimage top-level symbols.

This imports relevant symbols from the submodules into the equimage/equimagelab namespace.
These symbols are defined by the :py:class:`__all__` dictionary (if any) of each submodule, and
listed in their docstring.

Also, the methods of the :py:class:`MixinImage` class of each submodule are imported in the Image class.
"""

from .params import *
from .image import *
from .image_utils import *
from .image_colorspaces import *
from .image_colors import *
from .image_stretch import *
from .image_masks import *
from .image_multiscale import *
from .image_io import *
