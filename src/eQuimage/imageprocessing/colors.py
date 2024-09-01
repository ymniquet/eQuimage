# This program is 0free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.6.0 / 2024.09.01

"""Color space management."""

import numpy as np
import matplotlib.colors as mplcolors
from .defs import IMGTYPE, IMGTOL

#########
# Luma. #
#########

# Weight of the RGB components in the luma.

rgbluma = IMGTYPE((.3, 0.6, 0.1))

def get_rgb_luma():
  """Return the weights of the RGB components in the luma."""
  return tuple(rgbluma)

def set_rgb_luma(rgb):
  """Set the weights 'rgb' of the RGB components in the luma."""
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
  return np.where(srgb > .04045, ((srgb+0.055)/1.055)**2.4, srgb/12.92)

def lrgb_to_srgb(image):
  """Convert the linear RGB image 'image' into a sRGB image."""
  lrgb = np.clip(image, 0., 1.)
  return np.where(lrgb > .0031308, 1.055*lrgb**(1./2.4)-0.055, 12.92*lrgb)

############################
# Luminance and lightness. #
############################

def lrgb_luminance(image):
  """Return the luminance Y of the linear RGB image 'image'."""
  return .2126*image[0]+0.7152*image[1]+0.0722*image[2]

def lrgb_lightness(image):
  """Return the CIE lightness L* of the linear RGB image 'image'.
     Warning: L* is defined within [0, 100] instead of [0, 1]."""
  Y = lrgb_luminance(image)
  return np.where(Y > .008856, 116.*Y**(1./3.)-16., 903.3*Y)

def srgb_luminance(image):
  """Return the luminance Y of the sRGB image 'image'."""
  return lrgb_luminance(srgb_to_lrgb(image))

def srgb_lightness(image):
  """Return the CIE lightness L* of the sRGB image 'image'.
     Warning: L* is defined within [0, 100] instead of [0, 1]."""
  return lrgb_lightness(srgb_to_lrgb(image))

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
  return IMGTYPE(mplcolors.rgb_to_hsv(np.moveaxis(image, 0, -1)))

def hsv_to_rgb(image):
  """Convert the HSV image 'image' into a RGB image.
     Warning: The HSV components 'image' are input as an array with dimensions (height, width, 3)."""
  return IMGTYPE(np.moveaxis(mplcolors.hsv_to_rgb(image), -1, 0))
