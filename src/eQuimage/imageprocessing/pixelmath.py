# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.4.0 / 2024.02.26

"""Pixel math framework."""

from .imageprocessing import IMGTYPE

class PixelMath:
  """Pixel math class."""

  def __init__(self, images):
    """Initialize the class with the set of images 'images'."""
    self.images = images

  def run(self, command):
    """Run pixel math command 'command' and return the result."""
    import numpy as np
    return IMGTYPE(eval(command))
