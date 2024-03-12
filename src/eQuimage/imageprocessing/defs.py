# This program is 0free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.4.0 / 2024.02.26

"""Image processing definitions."""

import numpy as np
from PIL import Image as PILImage

IMGTYPE = np.float32 # Data type used for images (either np.float32 or np.float64).

IMGTOL = 1.e-6 if IMGTYPE is np.float32 else 1.e-9 # Expected accuracy in np.float32/np.float64 calculations.

NEAREST  = PILImage.Resampling.NEAREST # Resampling methods, imported from PIL.
BILINEAR = PILImage.Resampling.BILINEAR
BICUBIC  = PILImage.Resampling.BICUBIC
LANCZOS  = PILImage.Resampling.LANCZOS
BOX      = PILImage.Resampling.BOX
HAMMING  = PILImage.Resampling.HAMMING

rgbluma = IMGTYPE((0.3, 0.6, 0.1)) # Weight of the R, G, B channels in the luma.

def get_rgb_luma():
  """Return the RGB components of the luma channel."""
  return tuple(rgbluma)

def set_rgb_luma(rgb):
  """Set the RGB components 'rgb' of the luma channel."""
  global rgbluma
  rgbluma = IMGTYPE(rgb)
