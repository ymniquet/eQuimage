# This program is 0free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.5.0 / 2024.04.28

"""Image processing definitions."""

import numpy as np
from PIL import Image as PILImage

# Image formats (unless otherwise specified):
# -------------------------------------------
#
#  - RGB images are stored as a np.ndarray with dimensions (3, width, height).
#    The first component is red, the second green, and the third blue.
#    They are floats within [0, 1] and type IMGTYPE = np.float32 or np.float64.
#
#  - HSV images are stored as a np.ndarray with dimensions (width, height, 3).
#    The first component is the hue, the second the saturation, and the third the value.
#    They are floats within [0, 1] and type IMGTYPE = np.float32 or np.float64.

# Data type used for images (either np.float32 or np.float64).

IMGTYPE = np.float32

# Expected accuracy in np.float32/np.float64 calculations.

IMGTOL = 1.e-6 if IMGTYPE is np.float32 else 1.e-9

# Image resampling methods, imported from PIL.

NEAREST  = PILImage.Resampling.NEAREST
BILINEAR = PILImage.Resampling.BILINEAR
BICUBIC  = PILImage.Resampling.BICUBIC
LANCZOS  = PILImage.Resampling.LANCZOS
BOX      = PILImage.Resampling.BOX
HAMMING  = PILImage.Resampling.HAMMING

