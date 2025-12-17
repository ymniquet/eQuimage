# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 2.0.0 / 2025.12.17
# Doc OK.

"""Image utils.

The following symbols are imported in the equimage/equimagelab namespaces for convenience:
  "is_valid_image", "clip", "blend".
"""

__all__ = ["is_valid_image", "clip", "blend"]

import numpy as np

from . import params
from . import helpers

#####################
# Image validation. #
#####################

def is_valid_image(image):
  """Return True if the input array is a valid image candidate, False otherwise.

  Args:
    image (numpy.ndarray): The image candidate.

  Returns:
    bool: True if the input array is a valid image candidate, False otherwise.
  """
  if not issubclass(type(image), np.ndarray): return False
  if image.ndim == 3:
    if image.shape[0] not in [1, 3]: return False
  elif image.ndim != 2:
    return False
  if image.dtype not in [np.float32, np.float64]: return False
  return True

##########################
# Image transformations. #
##########################

def clip(image, vmin = 0., vmax = 1., verbose = False):
  """Clip the input image in the range [vmin, vmax].

  Args:
    image (numpy.ndarray): The input image.
    vmin (float, optional): The lower clip bound (default 0).
    vmax (float, optional): The upper clip bound (default 1).
    verbose (bool, optional): If True, print the number of clipped data (default False).

  Returns:
    numpy.ndarray: The clipped image.
  """
  if verbose: print(f"Clipped {np.sum((image < vmin) | (image > vmax))} data.")
  return np.clip(image, vmin, vmax)

def blend(image1, image2, mixing):
  """Blend two images.

  Returns image1*(1-mixing)+image2*mixing.

  Args:
    image1 (numpy.ndarray): The first image.
    image2 (numpy.ndarray): The second image.
    mixing (float or numpy.ndarray for pixel-dependent mixing): The mixing coefficient(s).

  Returns:
    numpy.ndarray: The blended image image1*(1-mixing)+image2*mixing.
  """
  return image1*(1.-mixing)+image2*mixing

#####################################
# For inclusion in the Image class. #
#####################################

class MixinImage:
  """To be included in the Image class."""

  ##################
  # Image queries. #
  ##################

  def is_out_of_range(self):
    """Return True if the image is out-of-range (data < 0 or > 1 in any channel), False otherwise.

    Returns:
      bool: True if the image is out-of-range, False otherwise.
    """
    return np.any(self.image < 0.) or np.any(self.image > 1.)

  ##############
  # Templates. #
  ##############

  def empty(self):
    """Return an empty image with same size as the object.

    Returns:
      Image: An empty image with the same size as self.
    """
    return np.empty_like(self)

  def black(self):
    """Return a black image with same size as the object.

    Returns:
      Image: An black image with the same size as self.
    """
    return np.zeros_like(self)

  ##############################
  # Clipping & scaling pixels. #
  ##############################

  def clip(self, vmin = 0., vmax = 1., verbose = False):
    """Clip the image in the range [vmin, vmax].

    See also:
      :meth:`Image.clip_channels() <.clip_channels>` to clip specific channels.

    Args:
      vmin (float, optional): The lower clip bound (default 0).
      vmax (float, optional): The upper clip bound (default 1).
      verbose (bool, optional): If True, print the number of clipped data (default False).

    Returns:
      Image: The clipped image.
    """
    return self.newImage(clip(self.image, vmin, vmax, verbose))

  def scale_pixels(self, source, target, cutoff = None):
    """Scale all pixels of the image by the ratio target/source.

    Wherever abs(source) < cutoff, set all channels to target.

    Args:
      source (numpy.ndarray): The source values for scaling (must be the same size as the image).
      target (numpy.ndarray): The target values for scaling (must be the same size as the image).
      cutoff (float, optional): Threshold for scaling.
        If None, defaults to `equimage.helpers.fpepsilon(source.dtype)`.

    Returns:
      Image: The scaled image.
    """
    return self.newImage(helpers.scale_pixels(self.image, source, target, cutoff))

  #############
  # Blending. #
  #############

  def blend(self, image, mixing):
    """Blend the object with the input image.

    Returns self*(1-mixing)+image*mixing.
    The images must share the same shape, color space and color model.

    Args:
      image (Image): The image to blend with.
      mixing (float or numpy.ndarray for pixel-dependent mixing): The mixing coefficient(s).

    Returns:
      Image: The blended image self*(1-mixing)+image*mixing.
    """
    if self.get_shape() != image.get_shape():
      raise ValueError("Error, the images must share the same size & number of channels.")
    if self.colorspace != image.colorspace:
      raise ValueError("Error, the images must share the same color space !")
    if self.colormodel != image.colormodel:
      raise ValueError("Error, the images must share the same color model !")
    return self.newImage(blend(self.image, image, mixing))
