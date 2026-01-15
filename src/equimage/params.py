# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 3.0.0 / 2026.01.15
# Doc OK.

"""Image processing parameters.

The following symbols are imported in the equimage/equimagelab namespaces for convenience:
  "get_RGB_luma", "set_RGB_luma".
"""

__all__ = ["get_RGB_luma", "set_RGB_luma"]

import numpy as np

# Use imageio or imread module ?

IMAGEIO = False

# Image type.

imagetype = np.float32

def get_image_type():
  """Return the image type.

  Returns:
    str: The image type, either "float32" (for 32 bits floats) or "float64" (for 64 bits floats).
  """
  return "float32" if imagetype == np.float32 else "float64"

def set_image_type(dtype):
  """Set image type.

  Args:
    dtype (str): The image type.
      Can be either "float32" (for 32 bits floats) or "float64" (for 64 bits floats).
  """
  global imagetype
  if dtype == "float32":
    imagetype = np.float32
  elif dtype == "float64":
    imagetype = np.float64
  else:
    raise ValueError(f"Error, the image type must be 'float32' or 'float64' (got '{dtype}').")

# CIE color spaces parameters.

CIEilluminant = "D65" # Illuminant.
CIEobserver = "2" # Observer.

def get_CIE_params():
  """Return the CIE illuminant and observer.

  Returns:
    str, str: The CIE illuminant and observer as a tuple of strings.
  """
  return CIEilluminant, CIEobserver

def set_CIE_params(illuminant, observer):
  """Set CIE illuminant and observer.

  Args:
    illuminant (str): The name of the standard illuminant.
      Can be "A", "B", "C", "D50", "D55", "D65", "D75", or "E".
      See https://en.wikipedia.org/wiki/Standard_illuminant.
    observer (str): The name of the observer.
      Can be "2" (2-degree observer) or "10" (10-degree observer).
  """
  if illuminant not in ["A", "B", "C", "D50", "D55", "D65", "D75", "E"]:
    raise ValueError("Error, the CIE illuminant must be 'A', 'B', 'C', 'D50', 'D55', 'D65', 'D75' or 'E'.")
  if observer not in ["2", "10"]:
    raise ValueError("Error, the observer must be '2' or '10'.")
  global CIEilluminant, CIEobserver
  CIEilluminant = illuminant
  CIEobserver = observer

# Weights of the RGB components in the luma.

rgbluma = (.212671, .715160, .072169)

def get_RGB_luma():
  """Return the RGB weights rgbluma of the luma.

  The luma L of an image is the average of the RGB components weighted by rgbluma:

    L = rgbluma[0]*image[0]+rgbluma[1]*image[1]+rgbluma[2]*image[2]

  Returns:
    float, float, float: The red, blue, green weights rgbluma of the luma.
  """
  return rgbluma

def set_RGB_luma(rgb, verbose = True):
  """Set the RGB weights of the luma.

  Args:
    rgb: The RGB weights of the luma as:

      - a tuple, list or array of the (red, green, blue) weights. They will be normalized so that
        their sum is 1.
      - the string "uniform": the RGB weights are set to (1/3, 1/3, 1/3).
      - the string "human": the RGB weights are set to (.212671, .715160, .072169). The luma is then
        the luminance for lRGB images, and an approximate substitute for the lightness for sRGB images.

    verbose (bool, optional): If True (default), print the updated definition of
      the luma.
  """
  if isinstance(rgb, str):
    if rgb == "uniform":
      set_RGB_luma((1./3., 1./3., 1./3.))
    elif rgb == "human":
      set_RGB_luma((.212671, .715160, .072169))
    else:
      raise ValueError("Error, the input rgb weights must be a tuple/list/array with three scalar elements, the string 'uniform' or the string 'human'.")
  else:
    w = np.array(rgb)
    if w.shape != (3,): raise ValueError("Error, the input rgb weights must be a tuple/list/array with three scalar elements, the string 'uniform' or the string 'human'.")
    if any(w < 0.): raise ValueError("Error, the input rgb weights must be >= 0.")
    s = np.sum(w)
    if s == 0.: raise ValueError("Error, the sum of the input rgb weights must be > 0.")
    global rgbluma ; rgbluma = w/s
    if verbose: print(f"Luma = {rgbluma[0]:.4f}R+{rgbluma[1]:.4f}G+{rgbluma[2]:.4f}B.")

# Number of bins in the histograms.

maxhistbins = 8192 # Maximum number of bins within [0, 1].
defhistbins = 0    # Default number of bins within [0, 1] (see set_default_hist_bins).

def set_max_hist_bins(n):
  """Set the maximum number of bins in the histograms.

  Args:
    n (int): The maximum number of bins within [0, 1].
  """
  global maxhistbins
  maxhistbins = n

def set_default_hist_bins(n):
  """Set the default number of bins in the histograms.

  Args:
    n (int): If strictly positive, the default number of bins within [0, 1] (practically
      limited to `equimage.params.maxhistbins`). If zero, the number of bins is computed
      according to the statistics of each image. If strictly negative, the number of bins
      is set to `equimage.params.maxhistbins`.
  """
  global defhistbins
  defhistbins = n if n >= 0 else maxhistbins

# Number of x mesh points for transformation function plots y = f(x in [0, 1]).

ntranslo = 128 # Low  resolution.
ntranshi = 256 # High resolution.

# Exclude pixels <= 0 or >= 1 from the percentiles in image statistics ?

exclude01 = False

# Default wavelet.

defwavelet = "coif4"

# Target image median for star masks and StarNet.

starsmed = .25
