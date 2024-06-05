# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.5.1 / 2024.06.05

"""Pixel math framework."""

import re
from .defs import IMGTYPE
from . import colors

class PixelMath:
  """Pixel math class."""

  def __init__(self, images):
    """Initialize the class with the set of images 'images'."""
    self.images = images

  def run(self, command):
    """Run pixel math command 'command' and return the result."""

    globs = {"__builtins__": {}} # Hide all globals including python builtins for (minimal) security.

    # Set-up command environment.

    import numpy as np

    def midtone_stretch(image, midtone):
      """Apply midtone stretch function with midtone 'midtone' to image 'image'."""
      return (midtone-1.)*image/((2.*midtone-1.)*image-midtone) if midtone != 0.5 else image

    def value(image, midtone = .5):
      """Return the HSV value of image 'image' with midtone correction 'midtone'."""
      return midtone_stretch(colors.hsv_value(image), midtone)

    def luma(image, midtone = .5):
      """Return the luma of image 'image' with midtone correction 'midtone'."""
      return midtone_stretch(colors.luma(image), midtone)

    def luminance(image, midtone = .5):
      """Return the luminance of image 'image' with midtone correction 'midtone'."""
      return midtone_stretch(colors.lrgb_to_srgb(colors.srgb_luminance(image)), midtone)

    def blend(image1, image2, mix):
      """Blend images 'image1' and 'image2' as (1-mix)*image1+mix*image2."""
      return (1.-mix)*image1+mix*image2

    # Register the environment as globals.

    globs.update({"np": np, "value": value, "luma": luma, "luminance": luminance, "blend": blend})

    # Register all images as locals.

    locls = {f"IMG{n+1}": self.images[n].rgb for n in range(len(self.images))}

    # Execute the command and return the result converted to IMGTYPE.

    return IMGTYPE(eval(command, globs, locls))
