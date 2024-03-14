# This program is 0free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.4.0 / 2024.02.26

"""Color space management."""

from .defs import IMGTYPE, IMGTOL
import matplotlib.colors as colors
import numpy as np

# Image formats (unless otherwise specified):
#
#  - RGB images are stored as a np.ndarray with dimensions (3, width, height).
#    The first component is red, the second green, and the third blue.
#    They are floats within [0, 1] and type IMGTYPE = np.float32 or np.float64.
#
#  - HSV images are stored as a np.ndarray with dimensions (width, height, 3).
#    The first component is the hue, the second the saturation, and the third the value.
#    They are floats within [0, 1] and type IMGTYPE = np.float32 or np.float64.

#########
# Luma. #
#########

# Weight of the RGB channels in the luma.

rgbluma = IMGTYPE((0.3, 0.6, 0.1))

def get_rgb_luma():
  """Return the RGB components of the luma."""
  return tuple(rgbluma)

def set_rgb_luma(rgb):
  """Set the RGB components 'rgb' of the luma."""
  global rgbluma
  rgbluma = IMGTYPE(rgb)

def luma(image):
  """Return the luma of the RGB image 'image',
     defined as the linear combination of the RGB components weighted by rgbluma."""
  return rgbluma[0]*image[0]+rgbluma[1]*image[1]+rgbluma[2]*image[2]

#############################
# sRGB <-> lRGB conversion. #
#############################

def srgb_to_lrgb(image):
  """Convert the sRGB image 'image' into a linear RGB image."""
  srgb = np.clip(image, 0., 1.)
  return np.where(srgb > 0.04045, ((srgb+0.055)/1.055)**2.4, srgb/12.92)

def lrgb_to_srgb(image):
  """Convert the linear RGB image 'image' into a sRGB image."""
  lrgb = np.clip(image, 0., 1.)
  return np.where(lrgb > 0.0031308, 1.055*lrgb**(1./2.4)-0.055, 12.92*lrgb)

############################
# Luminance and lightness. #
############################

def lrgb_luminance(image):
  """Return the luminance Y of the linear RGB image 'image'."""
  return 0.2126*image[0]+0.7152*image[1]+0.0722*image[2]

def lrgb_lightness(image):
  """Return the CIE lightness L* of the linear RGB image 'image'.
     Warning: L* is defined within [0, 100] rather than [0, 1]."""
  Y = lrgb_luminance(image)
  return np.where(Y > 0.008856, 116.*Y**(1./3.)-16., 903.3*Y)

def srgb_luminance(image):
  """Return the luminance Y of the sRGB image 'image'."""
  return lrgb_luminance(lrgb_to_srgb(image))

def srgb_lightness(image):
  """Return the CIE lightness L* of the sRGB image 'image'.
     Warning: L* is defined within [0, 100] rather than [0, 1]."""
  return lrgb_lightness(lrgb_to_srgb(image))

###########################
# RGB <-> HSV conversion. #
###########################

def hsv_value(image):
  """Return the HSV value = max(RGB) of the RGB image 'image'."""
  return image.max(axis = 0)

def hsv_saturation(image):
  """Return the HSV saturation = 1-min(RGB)/max(RGB) of the RGB image 'image'."""
  return 1.-image.min(axis = 0)/image.max(axis = 0, initial = IMGTOL) # Safe evaluation.

def rgb_to_hsv(image):
  """Convert the RGB image 'image' into a HSV image.
     Warning: The HSV components are returned as an array with dimensions (height, width, 3)."""
  return IMGTYPE(colors.rgb_to_hsv(np.moveaxis(image, 0, -1)))

def hsv_to_rgb(image):
  """Convert the HSV image 'image' into a RGB image.
     Warning: The HSV components 'image' are input as an array with dimensions (height, width, 3)."""
  return IMGTYPE(np.moveaxis(colors.hsv_to_rgb(image), -1, 0))
