# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 2.0.0 / 2025.12.17
# Doc OK.

"""Color spaces and models management.

The following symbols are imported in the equimage/equimagelab namespaces for convenience:
  "luma", "lRGB_lightness", "sRGB_lightness".
"""

__all__ = ["luma", "lRGB_lightness", "sRGB_lightness"]

import numpy as np
import skimage.color as skcolor

from . import params
from . import helpers

#############################
# lRGB <-> sRGB conversion. #
#############################

def lRGB_to_sRGB(image):
  """Convert the input linear RGB image into a sRGB image.

  See also:
    The reciprocal :func:`sRGB_to_lRGB` function.

  Args:
    image (numpy.ndarray): The input lRGB image.

  Returns:
    numpy.ndarray: The converted sRGB image.
  """
  output = image/.07739943839475116
  mask = (image > .0031308072830676845)
  output[mask] = 1.055*image[mask]**(1./2.4)-.055
  return output

def sRGB_to_lRGB(image):
  """Convert the input sRGB image into a linear RGB image.

  See also:
    The reciprocal :func:`lRGB_to_sRGB` function.

  Args:
    image (numpy.ndarray): The input sRGB image.

  Returns:
    numpy.ndarray: The converted lRGB image.
  """
  output = .07739943839475116*image
  mask = (image > .04045)
  output[mask] = ((image[mask]+.055)/1.055)**2.4
  return output

###########################################
# lRGB <-> CIELab and CIELuv conversions. #
###########################################

# RGB <-> XYZ conversion matrices.

RGB2XYZ = np.array([[0.412453, 0.357580, 0.180423],
                    [0.212671, 0.715160, 0.072169],
                    [0.019334, 0.119193, 0.950227]])

XYZ2RGB = np.linalg.inv(RGB2XYZ)

#

def lRGB_to_CIELab(image):
  """Convert the input linear RGB image into a CIELab image.

  Note that the CIE lightness L* is conventionally defined within [0, 100],
  and that the CIE chromatic components a*, b* are signed.
  This function actually returns L*/100, a*/100 and b*/100.

  Note:
    The CIELab components L*, a* and b* depend on the choice of a standard illuminant (default D65)
    and observer (default 2°). See :meth:`params.set_CIE_params() <equimage.params.set_CIE_params>`.

  See also:
    The reciprocal :func:`CIELab_to_lRGB` function.

  Args:
    image (numpy.ndarray): The input lRGB image.

  Returns:
    numpy.ndarray: The converted CIELab image.
  """
  refwhite = skcolor.xyz_tristimulus_values(illuminant = params.CIEilluminant, observer = params.CIEobserver)
  xyz = np.tensordot(np.asarray(RGB2XYZ/refwhite[:, np.newaxis], dtype = image.dtype), image, axes = 1)
  mask = (xyz > .008856451679035631)
  xyz[ mask] = np.cbrt(xyz[mask])
  xyz[~mask] = 7.787037037037035*xyz[~mask]+.13793103448275862
  output = np.empty_like(image)
  output[0] = 1.16*xyz[1]-.16
  output[1] = 5.*(xyz[0]-xyz[1])
  output[2] = 2.*(xyz[1]-xyz[2])
  return output

def CIELab_to_lRGB(image):
  """Convert the input CIELab image into a linear RGB image.

  See also:
    The reciprocal :func:`lRGB_to_CIELab` function.

  Args:
    image (numpy.ndarray): The input CIELab image.

  Returns:
    numpy.ndarray: The converted lRGB image.
  """
  xyz = np.empty_like(image)
  xyz[1] = (image[0]+.16)/1.16
  xyz[0] = image[1]/5.+xyz[1]
  xyz[2] = xyz[1]-image[2]/2.
  ninvalid = np.sum(xyz[2] < 0.)
  if ninvalid > 0.:
    xyz[2] = np.clip(xyz[2], min = 0.)
    print(f"Warning: {ninvalid} negative z values were clipped to 0.")
  mask = (xyz > .20689655172413793)
  xyz[ mask] =  xyz[ mask]**3
  xyz[~mask] = (xyz[~mask]-.13793103448275862)/7.787037037037035
  refwhite = skcolor.xyz_tristimulus_values(illuminant = params.CIEilluminant, observer = params.CIEobserver)
  return np.tensordot(np.asarray(XYZ2RGB*refwhite, dtype = image.dtype), xyz, axes = 1)

def lRGB_to_CIELuv(image):
  """Convert the input linear RGB image into a CIELuv image.

  Note that the CIE lightness L* is conventionally defined within [0, 100],
  and that the CIE chromatic components u*, v* are signed.
  This function actually returns L*/100, u*/100 and v*/100.

  Note:
    The CIELab components L*, u* and v* depend on the choice of a standard illuminant (default D65)
    and observer (default 2°). See :meth:`params.set_CIE_params() <equimage.params.set_CIE_params>`.

  See also:
    The reciprocal :func:`CIELuv_to_lRGB` function.

  Args:
    image (numpy.ndarray): The input lRGB image.

  Returns:
    numpy.ndarray: The converted CIELuv image.
  """
  eps = helpers.fpepsilon(image.dtype)
  refwhite = skcolor.xyz_tristimulus_values(illuminant = params.CIEilluminant, observer = params.CIEobserver, dtype = image.dtype)
  xyz = np.tensordot(np.asarray(RGB2XYZ, dtype = image.dtype), image, axes = 1)
  Lstar = xyz[1]/refwhite[1]
  if np.isscalar(Lstar):
    Lstar = 1.16*np.cbrt(Lstar)-.16 if Lstar > .008856451679035631 else 9.03296296296296*Lstar
  else:
    mask = (Lstar > .008856451679035631)
    Lstar[~mask] *= 9.03296296296296
    Lstar[ mask]  = 1.16*np.cbrt(Lstar[mask])-.16
  output = np.empty_like(image)
  output[0] = Lstar
  D = refwhite[0]+15.*refwhite[1]+3.*refwhite[2]
  u0 = 4.*refwhite[0]/D
  v0 = 9.*refwhite[1]/D
  D = xyz[0]+15.*xyz[1]+3.*xyz[2]+eps # Add eps for blacks.
  output[1] = 13.*Lstar*(4.*xyz[0]/D-u0)
  output[2] = 13.*Lstar*(9.*xyz[1]/D-v0)
  return output

def CIELuv_to_lRGB(image):
  """Convert the input CIELuv image into a linear RGB image.

  See also:
    The reciprocal :func:`lRGB_to_CIELuv` function.

  Args:
    image (numpy.ndarray): The input CIELuv image.

  Returns:
    numpy.ndarray: The converted lRGB image.
  """
  eps = helpers.fpepsilon(image.dtype)
  refwhite = skcolor.xyz_tristimulus_values(illuminant = params.CIEilluminant, observer = params.CIEobserver, dtype = image.dtype)
  y = np.copy(image[0])
  if np.isscalar(y):
    y = ((y+.16)/1.16)**3 if y > .08 else y/9.03296296296296
  else:
    mask = (y > .08)
    y[~mask] /= 9.03296296296296
    y[ mask]  = ((y[mask]+.16)/1.16)**3
  y *= refwhite[1]
  xyz = np.empty_like(image)
  xyz[1] = y
  D = refwhite[0]+15.*refwhite[1]+3.*refwhite[2]
  u0 = 4.*refwhite[0]/D
  v0 = 9.*refwhite[1]/D
  D = 13.*image[0]+eps # Add eps for blacks.
  a = u0+image[1]/D
  b = v0+image[2]/D
  c = 3.*xyz[1]*(5.*b-3.)
  xyz[2] = ((a-4.)*c-15.*a*b*y)/(12.*b)
  xyz[0] = -(c/b+3.*xyz[2])
  return np.tensordot(np.asarray(XYZ2RGB, dtype = image.dtype), xyz, axes = 1)

###########################################
# sRGB <-> CIELab and CIELuv conversions. #
###########################################

def sRGB_to_CIELab(image):
  """Convert the input sRGB image into a CIELab image.

  Note that the CIE lightness L* is conventionally defined within [0, 100],
  and that the CIE chromatic components a*, b* are signed.
  This function actually returns L*/100, a*/100 and b*/100.

  Note:
    The CIELab components L*, a* and b* depend on the choice of a standard illuminant (default D65)
    and observer (default 2°). See :meth:`params.set_CIE_params() <equimage.params.set_CIE_params>`.

  See also:
    The reciprocal :func:`CIELab_to_sRGB` function.

  Args:
    image (numpy.ndarray): The input sRGB image.

  Returns:
    numpy.ndarray: The converted CIELab image.
  """
  return lRGB_to_CIELab(sRGB_to_lRGB(image))

def CIELab_to_sRGB(image):
  """Convert the input CIELab image into a sRGB image.

  See also:
    The reciprocal :func:`sRGB_to_CIELab` function.

  Args:
    image (numpy.ndarray): The input CIELab image.

  Returns:
    numpy.ndarray: The converted sRGB image.
  """
  return lRGB_to_sRGB(CIELab_to_lRGB(image))

def sRGB_to_CIELuv(image):
  """Convert the input sRGB image into a CIELuv image.

  Note that the CIE lightness L* is conventionally defined within [0, 100],
  and that the CIE chromatic components u*, v* are signed.
  This function actually returns L*/100, u*/100 and v*/100.

  Note:
    The CIELab components L*, u* and v* depend on the choice of a standard illuminant (default D65)
    and observer (default 2°). See :meth:`params.set_CIE_params() <equimage.params.set_CIE_params>`.

  See also:
    The reciprocal :func:`CIELuv_to_sRGB` function.

  Args:
    image (numpy.ndarray): The input sRGB image.

  Returns:
    numpy.ndarray: The converted CIELuv image.
  """
  return lRGB_to_CIELuv(sRGB_to_lRGB(image))

def CIELuv_to_sRGB(image):
  """Convert the input CIELuv image into a sRGB image.

  See also:
    The reciprocal :func:`sRGB_to_CIELuv` function.

  Args:
    image (numpy.ndarray): The input CIELuv image.

  Returns:
    numpy.ndarray: The converted sRGB image.
  """
  return lRGB_to_sRGB(CIELuv_to_lRGB(image))

###########################
# RGB <-> HSV conversion. #
###########################

def RGB_to_HSV(image):
  """Convert the input RGB image into a HSV image.

  See also:
    The reciprocal :func:`HSV_to_RGB` function.

  Note:
    This function clips the input image to the [0, 1] range.

  Args:
    image (numpy.ndarray): The input RGB image.

  Returns:
    numpy.ndarray: The converted HSV image.
  """
  return skcolor.rgb2hsv(np.clip(image, 0., 1.), channel_axis = 0)

def HSV_to_RGB(image):
  """Convert the input HSV image into a RGB image.

  See also:
    The reciprocal :func:`RGB_to_HSV` function.

  Note:
    This function clips the input image to the [0, 1] range.

  Args:
    image (numpy.ndarray): The input HSV image.

  Returns:
    numpy.ndarray: The converted RGB image.
  """
  return skcolor.hsv2rgb(np.clip(image, 0., 1.), channel_axis = 0)

############################
# HSV <-> HSL conversions. #
############################

def HSV_to_HSL(image):
  """Convert the input HSV image into a HSL image.

  See also:
    The reciprocal :func:`HSL_to_HSV` function.

  Note:
    This function clips the input image to the [0, 1] range.

  Args:
    image (numpy.ndarray): The input HSV image.

  Returns:
    numpy.ndarray: The converted HSL image.
  """
  output = np.clip(image, 0., 1.)
  SV = output[1]*output[2]
  output[2] -= SV/2.
  D = 1.-abs(2.*output[2]-1.)
  mask = (D > 0.)
  output[1][mask] = SV[mask]/D[mask]
  return output

def HSL_to_HSV(image):
  """Convert the input HSL image into a HSV image.

  See also:
    The reciprocal :func:`HSV_to_HSL` function.

  Note:
    This function clips the input image to the [0, 1] range.

  Args:
    image (numpy.ndarray): The input HSL image.

  Returns:
    numpy.ndarray: The converted HSV image.
  """
  output = np.clip(image, 0., 1.)
  SD = output[1]*(1.-abs(2.*output[2]-1.))
  output[2] += SD/2.
  mask = (output[2] > 0.)
  output[1][mask] = SD[mask]/output[2][mask]
  return output

############################
# RGB <-> HSL conversions. #
############################

def RGB_to_HSL(image):
  """Convert the input RGB image into a HSL image.

  See also:
    The reciprocal :func:`HSL_to_RGB` function.

  Note:
    This function clips the input image to the [0, 1] range.

  Args:
    image (numpy.ndarray): The input RGB image.

  Returns:
    numpy.ndarray: The converted HSL image.
  """
  return HSV_to_HSL(skcolor.rgb2hsv(np.clip(image, 0., 1.), channel_axis = 0))

def HSL_to_RGB(image):
  """Convert the input HSL image into a RGB image.

  See also:
    The reciprocal :func:`RGB_to_HSL` function.

  Note:
    This function clips the input image to the [0, 1] range.

  Args:
    image (numpy.ndarray): The input HSL image.

  Returns:
    numpy.ndarray: The converted RGB image.
  """
  return skcolor.hsv2rgb(HSL_to_HSV(image), channel_axis = 0)

################################
# Lab/Luv <-> Lch conversions. #
################################

def Lxx_to_Lch(image):
  """Convert the input Lab/Luv image into a Lch image.

  See also:
    The reciprocal :func:`Lch_to_Lxx` function.

  Args:
    image (numpy.ndarray): The input Lab/Luv image.

  Returns:
    numpy.ndarray: The converted Lch image.
  """
  output = np.empty_like(image)
  output[0] = image[0]
  output[1] = np.hypot(image[2], image[1])
  output[2] = np.arctan2(image[2], image[1])/(2.*np.pi)
  output[2] += np.where(output[2] < 0., 1., 0.)
  return output

def Lch_to_Lxx(image):
  """Convert the input Lch image into a Lab/Luv image.

  See also:
    The reciprocal :func:`Lxx_to_Lch` function.

  Args:
    image (numpy.ndarray): The input Lch image.

  Returns:
    numpy.ndarray: The converted Lab/Luv image.
  """
  twopi = 2.*np.pi
  output = np.empty_like(image)
  output[0] = image[0]
  output[1] = image[1]*np.cos(twopi*image[2])
  output[2] = image[1]*np.sin(twopi*image[2])
  return output

############################
# Lch <-> Lsh conversions. #
############################

def Lch_to_Lsh(image):
  """Convert the input Lch image into a Lsh image.

  See also:
    The reciprocal :func:`Lsh_to_Lch` function.

  Args:
    image (numpy.ndarray): The input Lch image.

  Returns:
    numpy.ndarray: The converted Lsh image.
  """
  output = image.copy()
  Lstar = image[0]
  mask = (Lstar > 0.)
  output[1][mask] /= Lstar[mask]
  return output

def Lsh_to_Lch(image):
  """Convert the input Lsh image into a Lch image.

  See also:
    The reciprocal :func:`Lch_to_Lsh` function.

  Args:
    image (numpy.ndarray): The input Lsh image.

  Returns:
    numpy.ndarray: The converted Lch image.
  """
  output = image.copy()
  output[1] *= image[0]
  return output

############################
# Luv <-> Lsh conversions. #
############################

def Luv_to_Lsh(image):
  """Convert the input Luv image into a Lsh image.

  See also:
    The reciprocal :func:`Lsh_to_Luv` function.

  Args:
    image (numpy.ndarray): The input Luv image.

  Returns:
    numpy.ndarray: The converted Lsh image.
  """
  return Lch_to_Lsh(Lxx_to_Lch(image))

def Lsh_to_Luv(image):
  """Convert the input Lsh image into a Luv image.

  See also:
    The reciprocal :func:`Luv_to_Lsh` function.

  Args:
    image (numpy.ndarray): The input Lsh image.

  Returns:
    numpy.ndarray: The converted Luv image.
  """
  return Lch_to_Lxx(Lsh_to_Lch(image))

######################################################
# HSV and HSL hue, value, lightness and saturations. #
######################################################

def HSX_hue(image):
  """Return the HSV/HSL hue of the input RGB image.

  Note:
    This function clips the input image below 0.

  Args:
    image (numpy.ndarray): The input RGB image.

  Returns:
    numpy.ndarray: The HSV/HSL hue.
  """
  mini = np.maximum(image.min(axis = 0), 0.)
  maxi = np.maximum(image.max(axis = 0), 0.)
  delta = maxi-mini
  H = np.empty_like(delta)
  mask = (image[0] == maxi) # Red is maximum.
  H[mask] =    helpers.failsafe_divide(image[1][mask]-image[2][mask], delta[mask])
  mask = (image[1] == maxi) # Green is maximum.
  H[mask] = 2.+helpers.failsafe_divide(image[2][mask]-image[0][mask], delta[mask])
  mask = (image[2] == maxi) # Blue is maximum.
  H[mask] = 4.+helpers.failsafe_divide(image[0][mask]-image[1][mask], delta[mask])
  mask = (delta == 0.) # Delta is 0.
  H[mask] = 0.
  return (H/6.)%1.

def HSV_value(image):
  """Return the HSV value V = max(RGB) of the input RGB image.

  Note:
    Compatible with single channel grayscale images.
    This function clips the input image below 0.

  Args:
    image (numpy.ndarray): The input RGB image.

  Returns:
    numpy.ndarray: The HSV value V.
  """
  return np.maximum(image.max(axis = 0), 0.)

def HSV_saturation(image):
  """Return the HSV saturation S = 1-min(RGB)/max(RGB) of the input RGB image.

  Note:
    Compatible with single channel grayscale images.
    This function clips the input image below 0.

  Args:
    image (numpy.ndarray): The input RGB image.

  Returns:
    numpy.ndarray: The HSV saturation S.
  """
  mini = np.maximum(image.min(axis = 0), 0.)
  maxi = np.maximum(image.max(axis = 0), 0.)
  S = np.zeros_like(maxi)
  mask = (maxi > 0.)
  S[mask] = 1.-mini[mask]/maxi[mask]
  return S

def HSL_lightness(image):
  """Return the HSL lightness L' = (max(RGB)+min(RGB))/2 of the input RGB image.

  Note:
    Compatible with single channel grayscale images.
    This function clips the input image to the [0, 1] range.

  Args:
    image (numpy.ndarray): The input RGB image.

  Returns:
    numpy.ndarray: The HSL lightness L'.
  """
  mini = np.clip(image.min(axis = 0), 0., 1.)
  maxi = np.clip(image.max(axis = 0), 0., 1.)
  return (mini+maxi)/2.

def HSL_saturation(image):
  """Return the HSL saturation S' = (max(RGB)-min(RGB))/(1-abs(max(RGB)+min(RGB)-1)) of the input RGB image.

  Note:
    Compatible with single channel grayscale images.
    This function clips the input image to the [0, 1] range.

  Args:
    image (numpy.ndarray): The input RGB image.

  Returns:
    numpy.ndarray: The HSL saturation S'.
  """
  mini = np.clip(image.min(axis = 0), 0., 1.)
  maxi = np.clip(image.max(axis = 0), 0., 1.)
  C = maxi-mini
  D = 1.-abs(mini+maxi-1.)
  S = np.zeros_like(D)
  mask = (D > 0.)
  S[mask] = C[mask]/D[mask]
  return S

#########
# Luma. #
#########

def luma(image):
  """Return the luma L of the input RGB image.

  The luma L is the average of the RGB components weighted by rgbluma = get_RGB_luma():

    L = rgbluma[0]*image[0]+rgbluma[1]*image[1]+rgbluma[2]*image[2].

  Note:
    Compatible with single channel grayscale images.

  Args:
    image (numpy.ndarray): The input RGB image.

  Returns:
    numpy.ndarray: The luma L.
  """
  rgbluma = params.get_RGB_luma()
  return rgbluma[0]*image[0]+rgbluma[1]*image[1]+rgbluma[2]*image[2] if image.shape[0] > 1 else image[0]

############################
# Luminance and lightness. #
############################

def luminance_to_lightness(Y):
  """Compute the CIE lightness L* from the lRGB luminance Y.

  The CIE lightness L* is defined from the lRGB luminance Y as:

    L* = 116*Y**(1/3)-16 if Y > 0.008856 and L* = 903.3*Y if Y < 0.008856.

  Note that L* is conventionally defined within [0, 100].
  However, this function returns the scaled lightness L*/100 within [0, 1].

  See also:
    The reciprocal :func:`lightness_to_luminance` function.

  Args:
    Y (numpy.ndarray): The luminance Y.

  Returns:
    numpy.ndarray: The CIE lightness L*/100.
  """
  if np.isscalar(Y):
    return 1.16*np.cbrt(Y)-.16 if Y > .008856451679035631 else 9.03296296296296*Y
  Lstar = 9.03296296296296*Y
  mask = (Y > .008856451679035631)
  Lstar[mask] = 1.16*np.cbrt(Y[mask])-.16
  return Lstar

def lightness_to_luminance(Lstar):
  """Compute the lRGB luminance Y from the CIE lightness L*.

  See also:
    The reciprocal :func:`luminance_to_lightness` function.

  Args:
    Lstar (numpy.ndarray): The CIE lightness L*/100.

  Returns:
    numpy.ndarray: The luminance Y.
  """
  if np.isscalar(Lstar):
    return ((Lstar+.16)/1.16)**3 if Lstar > .08 else Lstar/9.03296296296296
  Y = Lstar/9.03296296296296
  mask = (Lstar > .08)
  Y[mask] = ((Lstar[mask]+.16)/1.16)**3
  return Y

def lRGB_luminance(image):
  """Return the luminance Y of the input linear RGB image.

  The luminance Y of a lRGB image is defined as:

    Y = 0.212671*R+0.715160*G+0.072169*B

  It is equivalently the luma of the lRGB image for RGB weights (0.212671, 0.715160, 0.072169),
  and is the basic ingredient of the perceptual lightness L* in the CIELab and CIELuv color spaces.

  Note:
    The RGB weights actually depend on the choice of a standard illuminant (default D65) and observer
    (default 2°). See :meth:`params.set_CIE_params() <equimage.params.set_CIE_params>`.

  See also:
    :func:`lRGB_lightness`,
    :func:`sRGB_luminance`,
    :func:`sRGB_lightness`,
    :func:`luma`

  Note:
    Compatible with single channel grayscale images.

  Args:
    image (numpy.ndarray): The input lRGB image.

  Returns:
    numpy.ndarray: The luminance Y.
  """
  if image.shape[0] == 1: return image[0]
  refwhite = skcolor.xyz_tristimulus_values(illuminant = params.CIEilluminant, observer = params.CIEobserver)
  YR = RGB2XYZ[1, 0]/refwhite[1] ; YG = RGB2XYZ[1, 1]/refwhite[1] ; YB = RGB2XYZ[1, 2]/refwhite[1]
  return YR*image[0]+YG*image[1]+YB*image[2]

def lRGB_lightness(image):
  """Return the CIE lightness L* of the input linear RGB image.

  The CIE lightness L* is defined from the lRGB luminance Y as:

    L* = 116*Y**(1/3)-16 if Y > 0.008856 and L* = 903.3*Y if Y < 0.008856.

  It is a measure of the perceptual lightness of the image.
  Note that L* is conventionally defined within [0, 100].
  However, this function returns the scaled lightness L*/100 within [0, 1].

  See also:
    :func:`lRGB_luminance`,
    :func:`sRGB_luminance`,
    :func:`sRGB_lightness`,
    :func:`luma`

  Note:
    Compatible with single channel grayscale images.

  Args:
    image (numpy.ndarray): The input lRGB image.

  Returns:
    numpy.ndarray: The CIE lightness L*/100.
  """
  return luminance_to_lightness(lRGB_luminance(image))

def sRGB_luminance(image):
  """Return the luminance Y of the input sRGB image.

  The image is converted to the lRGB color space to compute the luminance Y.

  Note: Although they have the same functional forms, the luma and luminance are different concepts
  for sRGB images: the luma is computed in the sRGB color space as a *substitute* for the perceptual
  lightness, whereas the luminance is computed after conversion in the lRGB color space and is the
  basic ingredient of the *genuine* perceptual lightness (see lRGB_lightness).

  See also:
    :func:`sRGB_lightness`,
    :func:`lRGB_luminance`,
    :func:`lRGB_lightness`,
    :func:`luma`

  Note:
    Compatible with single channel grayscale images.

  Args:
    image (numpy.ndarray): The input sRGB image.

  Returns:
    numpy.ndarray: The luminance Y.
  """
  return lRGB_luminance(sRGB_to_lRGB(image))

def sRGB_lightness(image):
  """Return the CIE lightness L* of the input sRGB image.

  The image is converted to the lRGB color space to compute the CIE lightness L*.
  L* is a measure of the perceptual lightness of the image.
  Note that L* is conventionally defined within [0, 100].
  However, this function returns the scaled lightness L*/100 within [0, 1].

  See also:
    :func:`sRGB_luminance`,
    :func:`lRGB_luminance`,
    :func:`lRGB_lightness`,
    :func:`luma`

  Note:
    Compatible with single channel grayscale images.
    This function does not clip the input image to the [0, 1] range.

  Args:
    image (numpy.ndarray): The input sRGB image.

  Returns:
    numpy.ndarray: The CIE lightness L*/100.
  """
  return lRGB_lightness(sRGB_to_lRGB(image))

#####################################
# For inclusion in the Image class. #
#####################################

class MixinImage:
  """To be included in the Image class."""

  #####################################
  # Color space and model management. #
  #####################################

  def color_space_error(self):
    """Raise a color space error."""
    class ColorSpaceError(Exception):
      pass
    raise ColorSpaceError(f"Error, this operation is not implemented for {self.colorspace} images.")

  def color_model_error(self):
    """Raise a color model error."""
    class ColorModelError(Exception):
      pass
    raise ColorModelError(f"Error, this operation is not implemented for {self.colormodel} images.")

  def check_color_space(self, *colorspaces):
    """Raise a color space error if the color space of the image is not in the arguments.

    See also:
      :meth:`Image.color_space_error() <.color_space_error>`
    """
    if self.colorspace not in colorspaces: self.color_space_error()

  def check_color_model(self, *colormodels):
    """Raise a color model error if the color model of the image is not in the arguments.

    See also:
      :meth:`Image.color_model_error() <.color_model_error>`
    """
    if self.colormodel not in colormodels: self.color_model_error()

  def check_is_not_gray(self):
    """Raise a color model error if the image is a grayscale.

    See also:
      :meth:`Image.color_model_error() <.color_model_error>`
    """
    if self.colormodel == "gray": self.color_model_error()

  ############################
  # Color space conversions. #
  ############################

  def lRGB(self):
    """Convert the image to the linear RGB color space.

    Warning:
      Does not apply to the HSV, HSL, Lch and Lsh color models.

    Returns:
      Image: The converted lRGB image (a copy of the original image if already lRGB).
    """
    if self.colorspace == "lRGB":
#     self.check_color_model("RGB", "gray")
      return self.copy()
    elif self.colorspace == "sRGB":
      self.check_color_model("RGB", "gray")
      return self.newImage(sRGB_to_lRGB(self.image), colorspace = "lRGB")
    elif self.colorspace == "CIELab":
      self.check_color_model("Lab")
      return self.newImage(CIELab_to_lRGB(self.image), colorspace = "lRGB", colormodel = "RGB")
    elif self.colorspace == "CIELuv":
      self.check_color_model("Luv")
      return self.newImage(CIELuv_to_lRGB(self.image), colorspace = "lRGB", colormodel = "RGB")
    else:
      self.color_space_error()

  def sRGB(self):
    """Convert the image to the sRGB color space.

    Warning:
      Does not apply to the HSV, HSL, Lch and Lsh color models.

    Returns:
      Image: The converted sRGB image (a copy of the original image if already sRGB).
    """
    if self.colorspace == "lRGB":
      self.check_color_model("RGB", "gray")
      return self.newImage(lRGB_to_sRGB(self.image), colorspace = "sRGB")
    elif self.colorspace == "sRGB":
#     self.check_color_model("RGB", "gray")
      return self.copy()
    elif self.colorspace == "CIELab":
      self.check_color_model("Lab")
      return self.newImage(CIELab_to_sRGB(self.image), colorspace = "sRGB", colormodel = "RGB")
    elif self.colorspace == "CIELuv":
      self.check_color_model("Luv")
      return self.newImage(CIELuv_to_sRGB(self.image), colorspace = "sRGB", colormodel = "RGB")
    else:
      self.color_space_error()

  def CIELab(self):
    """Convert the image to the CIELab color space.

    Note that the CIE lightness L* is conventionally defined within [0, 100],
    and that the CIE chromatic components a*, b* are signed.
    This function actually returns L*/100, a*/100 and b*/100.

    Warning:
      Does not apply to the HSV, HSL, Lch and Lsh color models, and to grayscale images.

    Note:
      The CIELab components L*, a* and b* depend on the choice of a standard illuminant (default D65)
      and observer (default 2°). See :meth:`params.set_CIE_params() <equimage.params.set_CIE_params>`.

    Returns:
      Image: The converted CIELab image (a copy of the original image if already CIELab).
    """
    if self.colorspace == "lRGB":
      self.check_color_model("RGB")
      return self.newImage(lRGB_to_CIELab(self.image), colorspace = "CIELab", colormodel = "Lab")
    elif self.colorspace == "sRGB":
      self.check_color_model("RGB")
      return self.newImage(sRGB_to_CIELab(self.image), colorspace = "CIELab", colormodel = "Lab")
    elif self.colorspace == "CIELab":
#     self.check_color_model("Lab")
      return self.copy()
    elif self.colorspace == "CIELuv":
      self.check_color_model("Luv")
      return self.newImage(lRGB_to_CIELab(CIELuv_to_lRGB(self.image)), colorspace = "CIELab", colormodel = "Lab")
    else:
      self.color_space_error()

  def CIELuv(self):
    """Convert the image to the CIELuv color space.

    Note that the CIE lightness L* is conventionally defined within [0, 100],
    and that the CIE chromatic components u*, v* are signed.
    This function actually returns L*/100, u*/100 and v*/100.

    Warning:
      Does not apply to the HSV, HSL, Lch and Lsh color models, and to grayscale images.

    Note:
      The CIELab components L*, u* and u* depend on the choice of a standard illuminant (default D65)
      and observer (default 2°). See :meth:`params.set_CIE_params() <equimage.params.set_CIE_params>`.

    Returns:
      Image: The converted CIELuv image (a copy of the original image if already CIELuv).
    """
    if self.colorspace == "lRGB":
      self.check_color_model("RGB")
      return self.newImage(lRGB_to_CIELuv(self.image), colorspace = "CIELuv", colormodel = "Luv")
    elif self.colorspace == "sRGB":
      self.check_color_model("RGB")
      return self.newImage(sRGB_to_CIELuv(self.image), colorspace = "CIELuv", colormodel = "Luv")
    elif self.colorspace == "CIELab":
      self.check_color_model("Lab")
      return self.newImage(lRGB_to_CIELuv(CIELab_to_lRGB(self.image)), colorspace = "CIELuv", colormodel = "Luv")
    elif self.colorspace == "CIELuv":
#     self.check_color_model("Luv")
      return self.copy()
    else:
      self.color_space_error()

  ############################
  # Color model conversions. #
  ############################

  def RGB(self):
    """Convert the image to the RGB color model.

    Warning:
      Only applies in the lRGB and sRGB color spaces.

    Note:
      This method clips HSV and HSL images to the [0, 1] range.

    Returns:
      Image: The converted RGB image (a copy of the original image if already RGB).
    """
    self.check_color_space("lRGB", "sRGB")
    if self.colormodel == "RGB":
      return self.copy()
    elif self.colormodel == "HSV":
      return self.newImage(HSV_to_RGB(self.image), colormodel = "RGB")
    elif self.colormodel == "HSL":
      return self.newImage(HSL_to_RGB(self.image), colormodel = "RGB")
    elif self.colormodel == "gray":
      return self.newImage(np.repeat(self.image[0, :, :], 3, axis = 0), colormodel = "RGB")
    else:
      self.color_model_error()

  def HSV(self):
    """Convert the image to the HSV color model.

    Warning:
      Only applies in the lRGB and sRGB color spaces.
      The conversion from a grayscale to a HSV image is ill-defined (no hue).

    Note:
      This method clips RGB and HSL images to the [0, 1] range.

    Returns:
      Image: The converted HSV image (a copy of the original image if already HSV).
    """
    self.check_color_space("lRGB", "sRGB")
    if self.colormodel == "RGB":
      return self.newImage(RGB_to_HSV(self.image), colormodel = "HSV")
    elif self.colormodel == "HSV":
      return self.copy()
    elif self.colormodel == "HSL":
      return self.newImage(HSL_to_HSV(self.image), colormodel = "HSV")
    else:
      self.color_model_error()

  def HSL(self):
    """Convert the image to the HSL color model.

    Warning:
      Only applies in the lRGB and sRGB color spaces.
      The conversion from a grayscale to a HSL image is ill-defined (no hue).

    Note:
      This method clips RGB and HSV images to the [0, 1] range.

    Returns:
      Image: The converted HSL image (a copy of the original image if already HSL).
    """
    self.check_color_space("lRGB", "sRGB")
    if self.colormodel == "RGB":
      return self.newImage(RGB_to_HSL(self.image), colormodel = "HSL")
    elif self.colormodel == "HSV":
      return self.newImage(HSV_to_HSL(self.image), colormodel = "HSL")
    elif self.colormodel == "HSL":
      return self.copy()
    else:
      self.color_model_error()

  def Lab(self):
    """Convert the image to the Lab color model.

    Warning:
      Only applies in the CIELab color space.

    Returns:
      Image: The converted Lab image (a copy of the original image if already Lab).
    """
    self.check_color_space("CIELab")
    if self.colormodel == "Lab":
      return self.copy()
    elif self.colormodel == "Lch":
      return self.newImage(Lch_to_Lxx(self.image), colormodel = "Lab")
    else:
      self.color_model_error()

  def Luv(self):
    """Convert the image to the Luv color model.

    Warning:
      Only applies in the CIELuv color space.

    Returns:
      Image: The converted Luv image (a copy of the original image if already Luv).
    """
    self.check_color_space("CIELuv")
    if self.colormodel == "Luv":
      return self.copy()
    elif self.colormodel == "Lch":
      return self.newImage(Lch_to_Lxx(self.image), colormodel = "Luv")
    elif self.colormodel == "Lsh":
      return self.newImage(Lsh_to_Luv(self.image), colormodel = "Luv")
    else:
      self.color_model_error()

  def Lch(self):
    """Convert the image to the Lch color model.

    Warning:
      Only applies in the CIELab and CIELuv color spaces.

    Returns:
      Image: The converted Lch image (a copy of the original image if already Lch).
    """
    self.check_color_space("CIELab", "CIELuv")
    if self.colormodel == "Lab" or self.colormodel == "Luv":
      return self.newImage(Lxx_to_Lch(self.image), colormodel = "Lch")
    elif self.colormodel == "Lch":
      return self.copy()
    elif self.colormodel == "Lsh":
      return self.newImage(Lsh_to_Lch(self.image), colormodel = "Lch")
    else:
      self.color_model_error()

  def Lsh(self):
    """Convert the image to the Lsh color model.

    Warning:
      Only applies in the CIELuv color space.

    Returns:
      Image: The converted Lsh image (a copy of the original image if already Lsh).
    """
    self.check_color_space("CIELuv")
    if self.colormodel == "Luv":
      return self.newImage(Luv_to_Lsh(self.image), colormodel = "Lsh")
    elif self.colormodel == "Lch":
      return self.newImage(Lch_to_Lsh(self.image), colormodel = "Lsh")
    elif self.colormodel == "Lsh":
      return self.copy()
    else:
      self.color_model_error()

  ##########################
  # Arbitrary conversions. #
  ##########################

  def convert(self, colorspace = None, colormodel = None, copy = True):
    """Convert the image to the target color space and color model.

    This method is more versatile than the dedicated conversion methods such as :meth:`Image.sRGB() <.sRGB>`,
    :meth:`Image.HSV() <.HSV>`, etc... In particular, it can chain conversions to reach the target color space
    and model. For example, (sRGB, HSV) → (lRGB, RGB) = (sRGB, HSV) → (sRGB, RGB) → (lRGB, RGB).

    Args:
      colorspace (str, optional): The target color space ("lRGB", "sRGB", "CIELab" or "CIELuv").
        If None (default), keep the original color space.
      colormodel (str, optional): The target color model ("RGB", "HSV" or "HSL" in the lRGB and
        sRGB color spaces, "Lab" or "Lch" in the CIELab color space, "Luv", "Lch" or "Lsh" in
        the CIELuv color space). If None (default), keep (if possible) the original color model.
      copy (bool, optional): If True (default), return a copy of the original image if already
        in the target color space and color model. If False, return the original image.

    Returns:
      Image: The converted image.
    """
    copied = True
    if colorspace is None or colorspace == self.colorspace:
      csconv = self
      copied = False
    else:
      if self.colorspace in ["lRGB", "sRGB"]:
        if self.colormodel not in ["RGB", "gray"]:
          if colormodel == None and colorspace in ["lRGB", "sRGB"]: colormodel = self.colormodel
          imconv = self.RGB()
        else:
          imconv = self
      elif self.colorspace == "CIELab":
        if self.colormodel != "Lab":
          if colormodel == None and colorspace == "CIELuv" and self.colormodel == "Lch": colormodel = self.colormodel
          imconv = self.Lab()
        else:
          imconv = self
      elif self.colorspace == "CIELuv":
        if self.colormodel != "Luv":
          if colormodel == None and colorspace == "CIELab" and self.colormodel == "Lch": colormodel = self.colormodel
          imconv = self.Luv()
        else:
          imconv = self
      if colorspace == "lRGB":
        csconv = imconv.lRGB()
      elif colorspace == "sRGB":
        csconv = imconv.sRGB()
      elif colorspace == "CIELab":
        csconv = imconv.CIELab()
      elif colorspace == "CIELuv":
        csconv = imconv.CIELuv()
      else:
        raise ValueError(f"Error, unknown color space {colorspace}.")
    if colormodel == None or colormodel == csconv.colormodel:
      return csconv.copy() if copy and not copied else csconv
    elif colormodel == "RGB":
      return csconv.RGB()
    elif colormodel == "HSV":
      return csconv.HSV()
    elif colormodel == "HSL":
      return csconv.HSL()
    elif colormodel == "Lab":
      return csconv.Lab()
    elif colormodel == "Luv":
      return csconv.Luv()
    elif colormodel == "Lch":
      return csconv.Lch()
    elif colormodel == "Lsh":
      return csconv.Lsh()
    else:
      raise ValueError(f"Error, unknown color model {colormodel}.")

  #######################
  # Composite channels. #
  #######################

  def HSX_hue(self):
    """Return the HSV/HSL hue of the image.

    Warning:
      Available only for RGB, HSV and HSL images.

    Returns:
      numpy.ndarray: The HSV/HSL hue H.
    """
    if self.colormodel == "RGB":
      return HSX_hue(self.image)
    elif self.colormodel == "HSV" or self.colormodel == "HSL":
      return self.image[0]
    else:
      self.color_model_error()

  def HSV_value(self):
    """Return the HSV value V = max(RGB) of the image.

    Warning:
      Available only for RGB, HSV, and grayscale images.

    Returns:
      numpy.ndarray: The HSV value V.
    """
    if self.colormodel == "RGB" or self.colormodel == "gray":
      return HSV_value(self.image)
    elif self.colormodel == "HSV":
      return self.image[2]
    else:
      self.color_model_error()

  def HSV_saturation(self):
    """Return the HSV saturation S = 1-min(RGB)/max(RGB) of the image.

    Warning:
      Available only for RGB, HSV, and grayscale images.

    Returns:
      numpy.ndarray: The HSV saturation S.
    """
    if self.colormodel == "RGB" or self.colormodel == "gray":
      return HSV_saturation(self.image)
    elif self.colormodel == "HSV":
      return self.image[1]
    else:
      self.color_model_error()

  def HSL_lightness(self):
    """Return the HSL lightness L' = (max(RGB)+min(RGB))/2 of the image.

    Warning:
      Available only for RGB, HSL, and grayscale images.

    Returns:
      numpy.ndarray: The HSL lightness L'.
    """
    if self.colormodel == "RGB" or self.colormodel == "gray":
      return HSL_lightness(self.image)
    elif self.colormodel == "HSL":
      return self.image[2]
    else:
      self.color_model_error()

  def HSL_saturation(self):
    """Return the HSL saturation S' = (max(RGB)-min(RGB))/(1-abs(max(RGB)+min(RGB)-1)) of the image.

    Warning:
      Available only for RGB, HSL, and grayscale images.

    Returns:
      numpy.ndarray: The HSL saturation S'.
    """
    if self.colormodel == "RGB" or self.colormodel == "gray":
      return HSL_saturation(self.image)
    elif self.colormodel == "HSL":
      return self.image[1]
    else:
      self.color_model_error()

  def luma(self):
    """Return the luma L of the image.

    The luma L is the average of the RGB components weighted by rgbluma = get_RGB_luma():

      L = rgbluma[0]*image[0]+rgbluma[1]*image[1]+rgbluma[2]*image[2].

    Warning:
      Available only for RGB and grayscale images.

    Returns:
      numpy.ndarray: The luma L.
    """
    if self.colormodel == "RGB" or self.colormodel == "gray":
      return luma(self.image)
    else:
      self.color_model_error()

  def luminance(self):
    """Return the luminance Y of the image.

    Warning:
      Available only for RGB, grayscale, CIELab and CIELuv images.

    Returns:
      numpy.ndarray: The luminance Y.
    """
    if self.colorspace == "lRGB":
      self.check_color_model("RGB", "gray")
      return lRGB_luminance(self.image)
    elif self.colorspace == "sRGB":
      self.check_color_model("RGB", "gray")
      return sRGB_luminance(self.image)
    elif self.colorspace == "CIELab" or self.colorspace == "CIELuv":
      return lightness_to_luminance(self.image[0])
    else:
      self.color_space_error()

  def lightness(self):
    """Return the CIE lightness L* of the image.

    L* is a measure of the perceptual lightness of the image.
    Note that L* is conventionally defined within [0, 100].
    However, this method returns the scaled lightness L*/100 within [0, 1].

    Warning:
      Available only for RGB, grayscale, CIELab and CIELuv images.

    Returns:
      numpy.ndarray: The CIE lightness L*/100.
    """
    if self.colorspace == "lRGB":
      self.check_color_model("RGB", "gray")
      return lRGB_lightness(self.image)
    elif self.colorspace == "sRGB":
      self.check_color_model("RGB", "gray")
      return sRGB_lightness(self.image)
    elif self.colorspace == "CIELab" or self.colorspace == "CIELuv":
      return self.image[0]
    else:
      raise self.color_space_error()

  def CIE_chroma(self):
    """Return the CIE chroma c* of a CIELab or CIELuv image.

    The CIE chroma is c* = sqrt(a*^2+b*^2) in the CIELab color space and c* = sqrt(u*^2+v*^2) in
    the CIELuv color space. The values of the CIE chroma thus differ in the two color spaces.
    This method actually returns the scaled CIE chroma c*/100.

    Warning:
      Available only for CIELab and CIELuv images.

    Returns:
      numpy.ndarray: The CIE chroma c*/100.
    """
    self.check_color_space("CIELab", "CIELuv")
    if self.colormodel == "Lab" or self.colormodel == "Luv":
      return np.hypot(self.image[1], self.image[2])
    elif self.colormodel == "Lch":
      return self.image[1]
    elif self.colormodel == "Lsh":
      return self.image[0]*self.image[1]
    else:
      self.color_model_error()

  def CIE_saturation(self):
    """Return the CIE saturation s* of a CIELuv image.

    The CIE saturation is s* = c*/L* = sqrt(u*^2+v*^2)/L* in the CIELuv color space.
    This method actually returns the scaled CIE saturation s*/100.

    Warning:
      Available only for CIELuv images.

    Returns:
      numpy.ndarray: The CIE saturation s*/100.
    """
    self.check_color_space("CIELuv")
    if self.colormodel == "Luv":
      cstar = np.hypot(self.image[1], self.image[2])
    elif self.colormodel == "Lch":
      cstar = self.image[1]
    elif self.colormodel == "Lsh":
      return self.image[1]
    else:
      self.color_model_error()
    sstar = np.zeros_like(cstar)
    Lstar = self.image[0]
    mask = (Lstar > 0.)
    sstar[mask] = cstar[mask]/Lstar[mask]
    return sstar

  def CIE_hue(self):
    """Return the hue angle h* of a CIELab or CIELuv image.

    The hue angle is h* = atan2(b*, a*) in the CIELab color space and c* = atan2(v*, u*) in the
    CIELuv color space. The values of the hue angle thus differ in the two color spaces.
    This method actually returns the reduced hue angle h*/(2π) within [0, 1].

    Warning:
      Available only for CIELab and CIELuv images.

    Returns:
      numpy.ndarray: The reduced hue angle h*/(2π).
    """
    self.check_color_space("CIELab", "CIELuv")
    if self.colormodel == "Lab" or self.colormodel == "Luv":
      hstar  = np.arctan2(image[2], image[1])/(2.*np.pi)
      hstar += np.where(hstar < 0., 1., 0.)
      return hstar
    elif self.colormodel == "Lch" or self.colormodel == "Lsh":
      return self.image[2]
    else:
      self.color_model_error()

  #################################
  # Channel-selective operations. #
  #################################

  def get_channel(self, channel):
    """Return the selected channel of the image.

    Args:
      channel (str): The selected channel:

        - "1", "2", "3" (or equivalently "R", "G", "B" for RGB images):
          The first/second/third channel (all images).
        - "V": The HSV value (RGB, HSV and grayscale images).
        - "S": The HSV saturation (RGB, HSV and grayscale images).
        - "L'": The HSL lightness (RGB, HSL and grayscale images).
        - "S'": The HSL saturation (RGB, HSL and grayscale images).
        - "H": The HSV/HSL hue (RGB, HSV and HSL images).
        - "L": The luma (RGB and grayscale images).
        - "Y": The luminance (RGB, grayscale, CIELab and CIELuv images).
        - "L*": The CIE lightness L* (RGB, grayscale, CIELab and CIELuv images).
        - "c*": The CIE chroma c* (CIELab and CIELuv images).
        - "s*": The CIE saturation s* (CIELuv images).
        - "h*": The CIE hue angle h* (CIELab and CIELuv images).

    Also see:
      The magic method :meth:`Image.__getitem__`, which returns self.image[ic] as self[ic],
      with ic the Python channel index within [0, 1, 2].

    Returns:
      numpy.ndarray: The selected channel.
    """
    channel = channel.strip()
    if channel.isdigit():
      ic = int(channel)-1
      if ic < 0 or ic >= self.get_nc(): raise ValueError(f"Error, invalid channel '{channel}'.")
      return self.image[ic]
    elif channel in ["R", "G", "B"]:
      self.check_color_model("RGB", "gray")
      ic = "RGB".index(channel) if self.colormodel == "RGB" else 0
      return self.image[ic]
    elif channel == "V":
      return self.HSV_value()
    elif channel == "S":
      return self.HSV_saturation()
    elif channel == "L'":
      return self.HSL_lightness()
    elif channel == "S'":
      return self.HSL_saturation()
    elif channel == "H":
      return self.HSX_hue()
    elif channel in ["L", "Ls", "Lb", "Ln"]:
      return self.luma()
    elif channel == "Y":
      return self.luminance()
    elif channel in ["L*", "L*/ab", "L*/uv", "L*/sh"]:
      return self.lightness()
    elif channel == "c*":
      return self.CIE_chroma()
    elif channel == "s*":
      return self.CIE_saturation()
    elif channel == "h*":
      return self.CIE_hue()
    else:
      raise ValueError(f"Error, unknown channel '{channel}'.")

  def set_channel(self, channel, data, inplace = False):
    """Update the selected channel of the image.

    Args:
      channel (str): The updated channel:

        - "1", "2", "3" (or equivalently "R", "G", "B" for RGB images):
          Update the first/second/third channel (all images).
        - "V": Update the HSV value (RGB, HSV and grayscale images).
        - "S": Update the HSV saturation (RGB and HSV images).
        - "L'": Update the HSL lightness (RGB, HSL and grayscale images).
        - "S'": Update the HSL saturation (RGB and HSL images).
        - "L": Update the luma (RGB and grayscale images).
        - "Ls": Update the luma, and protect highlights by desaturation.
          (after the operation, the out-of-range pixels are desaturated at constant luma).
        - "Ln": Update the luma, and protect highlights by normalization.
          (after the operation, the image is normalized so that all pixels fall back in the [0, 1] range).
        - "L*": Update the CIE lightness L* (CIELab and CIELuv images; equivalent to "L*/ab"
          for lRGB and sRGB images).
        - "L*/ab": Update the CIE lightness L* in the CIELab/Lab color space and model
          (CIELab, lRGB and sRGB images).
        - "L*/uv": Update the CIE lightness L* in the CIELuv/Luv color space and model
          (CIELuv, lRGB and sRGB images).
        - "L*/sh": Update the CIE lightness L* in the CIELuv/Lsh color space and model
          (CIELuv, lRGB and sRGB images).
        - "c*": Update the CIE chroma c* (CIELab and CIELuv images).
        - "s*": Update the CIE saturation s* (CIELuv images).

      data (numpy.ndarray): The updated channel data, as a 2D array with the same width and height
        as the image.
      inplace (bool, optional): If True, update the image "in place"; if False (default), return a
        new image.

    Also see:
      The magic method :meth:`Image.__setitem__`, which implements self.image[ic] = data
      as self[ic] = data, with ic the Python channel index within [0, 1, 2].

    Returns:
      Image: The updated image.
    """
    dtype = self.dtype if inplace else params.imagetype
    data = np.asarray(data, dtype)
    width, height = self.get_size()
    if data.shape != (height, width):
      raise ValueError("Error, the channel data must be a 2D array with the same with and height as the image.")
    is_RGB  = (self.colormodel == "RGB")
    is_HSV  = (self.colormodel == "HSV")
    is_HSL  = (self.colormodel == "HSL")
    is_gray = (self.colormodel == "gray")
    output = self if inplace else self.copy()
    channel = channel.strip()
    if channel.isdigit():
      ic = int(channel)-1
      if ic < 0 or ic >= self.get_nc(): raise ValueError(f"Error, invalid channel '{channel}'.")
      output.image[ic] = data
      return output
    elif channel in ["R", "G", "B"]:
      if not is_RGB: self.color_model_error()
      ic = "RGB".index(channel)
      output.image[ic] = data
      return output
    elif channel == "V":
      if is_gray:
        output.image[0] = data
      elif is_RGB:
        output.image[:] = helpers.scale_pixels(self.image, self.HSV_value(), data)
      elif is_HSV:
        output.image[2] = data
      else:
        self.color_model_error()
      return output
    elif channel == "S":
      if is_RGB:
        hsv = RGB_to_HSV(self.image)
        hsv[1] = data
        output.image[:] = HSV_to_RGB(hsv)
      elif is_HSV:
        output.image[1] = data
      else:
        self.color_model_error()
      return output
    elif channel == "L'":
      if is_gray:
        output.image[0] = data
      elif is_RGB:
        hsl = RGB_to_HSL(self.image)
        hsl[2] = data
        output.image[:] = HSL_to_RGB(hsl)
      elif is_HSL:
        output.image[2] = data
      else:
        self.color_model_error()
      return output
    elif channel == "S'":
      if is_RGB:
        hsl = RGB_to_HSL(self.image)
        hsl[1] = data
        output.image[:] = HSL_to_RGB(hsl)
      elif is_HSL:
        output.image[1] = data
      else:
        self.color_model_error()
      return output
    elif channel in ["L", "Ls", "Ln"]:
      if is_gray:
        output.image[0] = data
      elif is_RGB:
        output.image[:] = helpers.scale_pixels(self.image, self.luma(), data)
        if channel == "Ls":
          output.image[:] = output.protect_highlights_saturation()
        elif channel == "Ln":
          maximum = np.max(output.image)
          if maximum > 1.: output.image /= maximum
      else:
        self.color_model_error()
      return output
    elif channel in ["L*", "L*/ab", "L*/uv", "L*/sh"]:
      if channel == "L*" and self.colorspace in ["CIELab", "CIELuv"]:
        output.image[0] = data
        return output
      if is_gray:
        luminance = lightness_to_luminance(data)
        if self.colorspace == "lRGB":
          output.image[0] = luminance
        elif self.colorspace == "sRGB":
          output.image[0] = lRGB_to_sRGB(luminance)
        else:
          self.color_space_error()
      else:
        if channel == "L*": channel = "L*/ab"
        if self.colorspace == "CIELab" and channel != "L*/ab": self.color_space_error()
        if self.colorspace == "CIELuv" and channel == "L*/ab": self.color_space_error()
        colormodel = "L"+channel[3:]
        colorspace = "CIELab" if colormodel == "Lab" else "CIELuv"
        CIE = self.convert(colorspace = colorspace, colormodel = colormodel, copy = True)
        CIE.image[0] = data
        output.image[:] = CIE.convert(colorspace = self.colorspace, colormodel = self.colormodel, copy = False).image
      return output
    elif channel == "c*":
      self.check_color_space("CIELab", "CIELuv")
      if self.colormodel == "Lab" or self.colormodel == "Luv":
        output.image[1:3] = helpers.scale_pixels(self.image[1:3], np.hypot(self.image[1], self.image[2]), data)
      elif self.colormodel == "Lch":
        output.image[1] = data
      elif self.colormodel == "Lsh":
        mask = (self.image[0] > 0.)
        output.image[1][mask] = data[mask]/self.image[0][mask]
      else:
        self.color_model_error()
    elif channel == "s*":
      self.check_color_space("CIELuv")
      if self.colomodel == "Luv":
        output.image[1:3] = helpers.scale_pixels(self.image[1:3], np.hypot(self.image[1], self.image[2]), self.image[0]*data)
      elif self.colormodel == "Lch":
        output.image[1] = self.image[0]*data
      elif self.colormodel == "Lsh":
        output.image[1] = data
      else:
        self.color_model_error()
    else:
      raise ValueError(f"Error, unknown channel '{channel}'.")

  def apply_channels(self, f, channels, multi = True, trans = False):
    """Apply the operation f(channel) to selected channels of the image.

    Note:
      When applying an operation to the luma, the RGB components of the image are rescaled
      by the ratio f(luma)/luma. This preserves the hue and HSV saturation, but may result in some
      out-of-range RGB components even though f(luma) fits within [0, 1]. These out-of-range
      components can be regularized with three highlights protection methods:

        - "Desaturation": The out-of-range pixels are desaturated at constant hue and luma (namely,
          the out-of-range components are decreased while the in-range components are increased so
          that the hue and luma are preserved). This tends to bleach the out-of-range pixels.
          f(luma) must fit within [0, 1] to make use of this highlights protection method.
        - "Blending": The out-of-range pixels are blended with f(RGB) (the same operation applied to
          the RGB channels). This tends to bleach the out-of-range pixels too.
          f(RGB) must fit within [0, 1] to make use of this highlights protection method.
        - "Normalization": The whole output image is rescaled so that all pixels fit in the [0, 1]
          range (output → output/max(1., numpy.max(output))).

      Alternatively, applying the operation to the HSV value V also preserves the hue and HSV
      saturation and can not produce out-of-range pixels if f([0, 1]) fits within [0, 1]. However,
      this may strongly affect the balance of the image, the HSV value being a very poor approximation
      to the perceptual lightness L*.

    Args:
      f (function): The function f(numpy.ndarray) → numpy.ndarray applied to the selected channels.
      channels (str): The selected channels:

        - An empty string: Apply the operation to all channels (all images).
        - A combination of "1", "2", "3" (or equivalently "R", "G", "B" for RGB images):
          Apply the operation to the first/second/third channel (all images).
        - "V": Apply the operation to the HSV value (RGB, HSV and grayscale images).
        - "S": Apply the operation to the HSV saturation (RGB and HSV images).
        - "L'": Apply the operation to the HSL lightness (RGB, HSL and grayscale images).
        - "S'": Apply the operation to the HSL saturation (RGB and HSL images).
        - "L": Apply the operation to the luma (RGB and grayscale images).
        - "Ls": Apply the operation to the luma, and protect highlights by desaturation.
          (after the operation, the out-of-range pixels are desaturated at constant luma).
        - "Lb": Apply the operation to the luma, and protect highlights by blending.
          (after the operation, the out-of-range pixels are blended with f(RGB)).
        - "Ln": Apply the operation to the luma, and protect highlights by normalization.
          (after the operation, the image is normalized so that all pixels fall back in the [0, 1] range).
        - "L*": Apply the operation to the CIE lightness L* (CIELab and CIELuv images; equivalent
          to "L*/ab" for lRGB and sRGB images).
        - "L*/ab": Apply the operation to the CIE lightness L* in the CIELab/Lab color space and model
          (CIELab, lRGB and sRGB images).
        - "L*/uv": Apply the operation to the CIE lightness L* in the CIELuv/Luv color space and model
          (CIELuv, lRGB and sRGB images).
        - "L*/sh": Apply the operation to the CIE lightness L* in the CIELuv/Lsh color space and model
          (CIELuv, lRGB and sRGB images).
        - "c*": Apply the operation to the CIE chroma c* (CIELab and CIELuv images).
        - "s*": Apply the operation to the CIE saturation s* (CIELuv images).

      multi (bool, optional): if True (default), the operation can be applied to the whole image at
        once; if False, the operation must be applied one channel at a time.
      trans (bool, optional): If True (default False), embeds the transformation y = f(x in [0, 1])
        in the output image as output.trans, where:

        - output.trans.type = "hist".
        - output.trans.input is a reference to the input image (self).
        - output.trans.channels are the channels selected for the transformation.
        - output.trans.x is a mesh of the [0, 1] interval.
        - output.trans.y = f(output.trans.x)
        - output.trans.ylabel is a label for output.trans.y.
        - output.trans.xticks is a list of remarkable x values for this transformation (if any).

        trans shall be set True only for *local* histogram transformations f.

    Returns:
      Image: The processed image.
    """

    def transformation(f, x, channels):
      """Return the transformation container."""
      xmin = min(0., x.min())
      xmax = max(1., x.max())
      t = helpers.Container()
      t.type = "hist"
      t.input = self
      t.channels = channels
      t.x = np.linspace(xmin, xmax, max(int(round(params.ntranshi*(xmax-xmin))), 2*params.ntranshi))
      t.y = f(t.x)
      t.ylabel = "f"
      return t

    nc = self.get_nc()
    is_RGB  = (self.colormodel == "RGB")
    is_HSV  = (self.colormodel == "HSV")
    is_HSL  = (self.colormodel == "HSL")
    is_gray = (self.colormodel == "gray")
    channels = channels.strip()
    if channels == "":
      if is_gray:
        channels = "L"
      elif is_RGB:
        channels = "RGB"
      else:
        for ic in range(nc): channels += str(ic+1)
    if channels == "V":
      if is_gray:
        output = self.newImage(f(self.image))
        if trans: output.trans = transformation(f, self.image, "V")
      elif is_RGB:
        value = self.HSV_value()
        output = self.scale_pixels(value, f(value))
        if trans: output.trans = transformation(f, value, "V")
      elif is_HSV:
        output = self.copy()
        output.image[2] = f(self.image[2])
        if trans: output.trans = transformation(f, self.image[2], "V")
      else:
        self.color_model_error()
      return output
    elif channels == "S":
      if is_RGB:
        hsv = RGB_to_HSV(self.image)
        if trans: t = transformation(f, hsv[1], "S")
        hsv[1] = f(hsv[1])
        output = self.newImage(HSV_to_RGB(hsv))
        if trans: output.trans = t
      elif is_HSV:
        output = self.copy()
        output.image[1] = f(self.image[1])
        if trans: output.trans = transformation(f, self.image[1], "S")
      else:
        self.color_model_error()
      return output
    elif channels == "L'":
      if is_gray:
        output = self.newImage(f(self.image[0]))
        if trans: output.trans = transformation(f, self.image, "L'")
      elif is_RGB:
        hsl = RGB_to_HSL(self.image)
        if trans: t = transformation(f, hsl[2], "L'")
        hsl[2] = f(hsl[2])
        output = self.newImage(HSL_to_RGB(hsl))
        if trans: output.trans = t
      elif is_HSV:
        output = self.copy()
        output.image[2] = f(self.image[2])
        if trans: output.trans = transformation(f, self.image[2], "L'")
      else:
        self.color_model_error()
      return output
    elif channels == "S'":
      if is_RGB:
        hsl = RGB_to_HSL(self.image)
        if trans: t = transformation(f, hsl[1], "S'")
        hsl[1] = f(hsl[1])
        output = self.newImage(HSL_to_RGB(hsl))
        if trans: output.trans = t
      elif is_HSL:
        output = self.copy()
        output.image[1] = f(self.image[1])
        if trans: output.trans = transformation(f, self.image[1], "S'")
      else:
        self.color_model_error()
      return output
    elif channels in ["L", "Ls", "Lb", "Ln"]:
      if is_gray:
        output = self.newImage(f(self.image[0]))
        if trans: output.trans = transformation(f, self.image, "L")
      elif is_RGB:
        luma = self.luma()
        output = self.scale_pixels(luma, f(luma))
        if trans: t = transformation(f, luma, "L")
        if channels == "Ls":
          output = output.protect_highlights_saturation()
        elif channels == "Lb":
          output = output.protect_highlights_blend(self.apply_channels(f, "RGB", multi))
        elif channels == "Ln":
          maximum = np.max(output.image)
          if maximum > 1.:
            output.image /= maximum
            if trans: t.y /= maximum
        if trans: output.trans = t
      else:
        self.color_model_error()
      return output
    elif channels in ["L*", "L*/ab", "L*/uv", "L*/sh"]:
      if channels == "L*" and self.colorspace in ["CIELab", "CIELuv"]:
        output = self.copy()
        output.image[0] = f(self.image[0])
        if trans: output.trans = transformation(f, self.image[0], "L*")
        return output
      if is_gray:
        lightness = self.lightness()
        flightness = f(lightness)
        fluminance = lightness_to_luminance(flightness)
        if self.colorspace == "lRGB":
          output = self.newImage(fluminance)
        elif self.colorspace == "sRGB":
          output = self.newImage(lRGB_to_sRGB(fluminance))
        else:
          self.color_space_error()
        if trans: output.trans = transformation(f, lightness, "L*")
      else:
        if channels == "L*": channels = "L*/ab"
        if self.colorspace == "CIELab" and channels != "L*/ab": self.color_space_error()
        if self.colorspace == "CIELuv" and channels == "L*/ab": self.color_space_error()
        colormodel = "L"+channels[3:]
        colorspace = "CIELab" if colormodel == "Lab" else "CIELuv"
        CIE = self.convert(colorspace = colorspace, colormodel = colormodel, copy = True)
        if trans: t = transformation(f, CIE.image[0], "L*")
        CIE.image[0] = f(CIE.image[0])
        output = CIE.convert(colorspace = self.colorspace, colormodel = self.colormodel, copy = False)
        if trans: output.trans = t
      return output
    elif channels == "c*":
      cstar = self.CIE_chroma()
      output = self.set_channel("c*", f(cstar))
      if trans: output.trans = transformation(f, cstar, "c*")
      return output
    elif channels == "s*":
      sstar = self.CIE_saturation()
      output = self.set_channel("s*", f(sstar))
      if trans: output.trans = transformation(f, sstar, "s*")
      return output
    else:
      selected = nc*[False]
      for c in channels:
        if c.isdigit():
          ic = int(c)-1
          if ic < 0 or ic >= nc: raise ValueError(f"Error, invalid channel '{c}'.")
        elif c in "RGB":
          if not is_RGB: self.color_model_error()
          ic = "RGB".index(c)
        elif c == " ": # Skip spaces.
          continue
        else:
          raise ValueError(f"Syntax error in the channels string '{channels}'.")
        if selected[ic]: print(f"Warning, channel '{c}' selected twice or more...")
        selected[ic] = True
      if all(selected) and multi:
        output = self.newImage(f(self.image))
      else:
        output = self.newImage(np.empty_like(self.image))
        for ic in range(nc):
          if selected[ic]:
            output.image[ic] = f(self.image[ic])
          else:
            output.image[ic] =   self.image[ic]
      if trans: output.trans = transformation(f, self.image[selected], channels)
      return output

  def clip_channels(self, channels, vmin = 0., vmax = 1., trans = False):
    """Clip selected channels of the image in the range [vmin, vmax].

    Args:
      channels (str, optional): The selected channels (default "" = all channels).
        See :meth:`Image.apply_channels() <.apply_channels>` or https://astro.ymniquet.fr/codes/equimagelab/docs/channels.html.
      vmin (float, optional): The lower clip bound (default 0).
      vmax (float, optional): The upper clip bound (default 1).
      trans (bool, optional): If True, embed the transormation in the output image as output.trans
        (see :meth:`Image.apply_channels() <.apply_channels>`). Default is False.

    Returns:
      Image: The clipped image.
    """
    return self.apply_channels(lambda channel: np.clip(channel, vmin, vmax), channels, trans = trans)

  def protect_highlights_saturation(self):
    """Normalize out-of-range pixels with HSV value > 1 by adjusting the saturation at constant hue
    and luma.

    The out-of-range RGB components of the pixels are decreased while the in-range RGB components
    are increased so that the hue and luma are conserved. This desaturates (whitens) the pixels
    with out-of-range components.
    This aims at protecting the highlights from overflowing when stretching the luma.

    Warning:
      The luma must be <= 1 even though some pixels have HSV value > 1.

    Returns:
      Image: The processed image.
    """
    self.check_color_model("RGB")
    imgluma = self.luma() # Original luma.
    if np.any(imgluma > 1.):
      print("Warning, can not protect highlights if the luma is out-of-range. Returning original image...")
      return self.copy()
    newimage = self.image/np.maximum(self.image.max(axis = 0), 1.) # Rescale maximum HSV value to 1.
    newluma = luma(newimage) # Updated luma.
    # Scale the saturation.
    # Note: The following implementation is failsafe when newluma → 1 (in which case luma is also 1 in principle),
    # at the cost of a small error.
    epsilon = helpers.fpepsilon(self.dtype)
    fs = ((1.-imgluma)+epsilon)/((1.-newluma)+epsilon)
    output = 1.-(1.-newimage)*fs
    diffluma = imgluma-luma(output)
    print(f"Maximum luma difference = {abs(diffluma).max()}.")
    return self.newImage(output)

  def protect_highlights_blend(self, inrange):
    """Normalize out-of-range pixels with HSV value > 1 by blending with an "in-range" image with
    HSV values <= 1.

    Each pixel of the image with out-of-range RGB components is brought back in the [0, 1] range by
    blending with the corresponding pixel of the input "in-range" image.
    This aims at protecting the highlights from overflowing when stretching the luma.

    Args:
      inrange (Image): The "in-range" image to blend with. All pixels must have HSV values <= 1.

    Returns:
      Image: The processed image.
    """
    self.check_color_model("RGB") ; inrange.check_color_model("RGB")
    if np.any(inrange.HSV_value() > 1.):
      print("Warning, can not protect highlights if the input inrange image is out-of-range. Returning original image...")
      return self.copy()
    mixing = np.where(self.image > 1., helpers.failsafe_divide(self.image-1., self.image-inrange.image), 0.)
    return self.blend(inrange, mixing.max(axis = 0))
