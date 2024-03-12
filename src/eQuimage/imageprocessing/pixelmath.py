# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.4.0 / 2024.02.26

"""Pixel math framework."""

from .defs import IMGTYPE
import re

class PixelMath:
  """Pixel math class."""

  def __init__(self, images):
    """Initialize the class with the set of images 'images'."""
    self.images = images

  def get_image(self, n):
    """Return the rgb image #n."""
    if n <= 0 or n > len(self.images): raise ValueError(f"Image #{n} does not exist")
    return self.images[n-1].rgb

  def run(self, command):
    """Run pixel math command 'command' and return the result."""
    import numpy as np
    command = re.sub("IMG([0-9]+)", "self.get_image(\g<1>)", command)
    return IMGTYPE(eval(command))
