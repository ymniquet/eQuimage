# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 2.0.0 / 2025.12.17
# Doc OK.

"""Image masks.

The following symbols are imported in the equimage/equimagelab namespaces for convenience:
  "float_mask", "extend_bmask", "smooth_mask", "threshold_bmask", "threshold_fmask", "shape_bmask".
"""

__all__ = ["float_mask", "extend_bmask", "smooth_mask", "threshold_bmask", "threshold_fmask", "shape_bmask"]

import numpy as np
import scipy.ndimage as ndimg
import skimage.draw as skdraw
import skimage.morphology as skimo

from . import params

####################################
# Binary & float masks management. #
####################################

def float_mask(mask):
  """Convert a binary mask into a float mask.

  Args:
    mask (numpy.ndarray): The input binary mask.

  Returns:
    numpy.ndarray: A float mask with datatype `equimage.params.imagetype` and values 1 where mask
    is True and 0 where mask is False. If already a float array, the input mask is returned as is.
  """
  return np.asarray(mask, dtype = params.imagetype)

def extend_bmask(mask, extend):
  """Extend or erode a binary mask.

  Args:
    mask (bool numpy.ndarray): The input binary mask.
    extend (int): The number of pixels by which the mask is extended.
      The mask is extended if extend > 0, and eroded if extend < 0.

  Returns:
    numpy.ndarray: The extended binary mask.
  """
  if extend > 0:
    return skimo.isotropic_dilation(mask, extend)
  else:
    return skimo.isotropic_erosion(mask, -extend)

def smooth_mask(mask, radius, kernel = "disk", mode = "zero"):
  """Smooth a binary or float mask.

  The input mask is converted into a float mask and convolved with either a gaussian or a disk.

  Args:
    mask (numpy.ndarray): The input binary or float mask.
    radius (float): The smoothing radius (pixels) [either the radius of the disk or four times the 
      standard deviation of the gaussian].
    kernel (str, optional): The convolution kernel [either "gaussian" for a gaussian or "disk" for
      a constant disk (smoothed edges with approximately constant slope)]. Default is "disk".
    mode (str, optional): How to extend the mask across its boundaries for the convolution:

      - "reflect": the mask is reflected about the edge of the last pixel (abcd → dcba|abcd|dcba).
      - "mirror": the mask is reflected about the center of the last pixel (abcd → dcb|abcd|cba).
      - "nearest": the mask is padded with the value of the last pixel (abcd → aaaa|abcd|dddd).
      - "zero" (default): the mask is padded with zeros (abcd → 0000|abcd|0000).
      - "one": the mask is padded with ones (abcd → 1111|abcd|1111).

  Returns:
    numpy.ndarray: The smoothed, float mask.
  """
  # Translate modes.
  cval = 0.
  if mode == "zero":
    mode = "constant"
  elif mode == "one":
    mode = "constant"
    cval = 1.
  # Convert into a float mask.
  fmask = float_mask(mask)
  # Smooth the float mask.
  if radius <= 0.: return fmask
  if kernel == "disk":
    kernel = skimo.disk(radius, dtype = params.imagetype)
    kernel /= np.sum(kernel)
    return ndimg.convolve(fmask, kernel, mode = mode, cval = cval)
  elif kernel == "gaussian":
    return ndimg.gaussian_filter(fmask, sigma = radius/4., truncate = 4., mode = mode, cval = cval)
  else:
    raise ValueError("Error, kernel must be either 'disk' or 'gaussian'.")

def threshold_bmask(filtered, threshold, extend = 0):
  """Set-up a threshold binary mask.

  Returns the pixels of the image such that filtered >= threshold as a binary mask.

  See also:
    :meth:`Image.filter() <.filter>`,
    :func:`threshold_fmask`

  Args:
    filtered (numpy.ndarray): The output of a filter (e.g., local average, ...) applied to the image
      (see :meth:`Image.filter() <.filter>`).
    threshold (float): The threshold for the mask. The mask is True wherever filtered >= threshold,
      and False elsewhere.
    extend (int, optional): Once computed, the mask can be extended/eroded by extend pixels (default 0).
      The mask is is extended if extend > 0, and eroded if extend < 0.

  Returns:
    numpy.ndarray: The mask as a boolean array with the same shape as filtered.
  """
  return extend_bmask(filtered >= threshold, extend)

def threshold_fmask(filtered, threshold, extend = 0, smooth = 0., mode = "zero"):
  """Set-up a threshold float mask.

  Returns the pixels of the image such that filtered >= threshold as a float mask.

  See also:
    :meth:`Image.filter() <.filter>`,
    :func:`smooth_mask`,
    :func:`threshold_bmask`

  Args:
    filtered (numpy.ndarray): The output of a filter (e.g., local average, ...) applied to the image
      (see :meth:`Image.filter() <.filter>`).
    threshold (float): The threshold for the mask. The mask is 1 wherever filtered >= threshold,
      and 0 elsewhere.
    extend (int, optional): Once computed, the mask can be extended/eroded by extend pixels (default 0).
      The mask is is extended if extend > 0, and eroded if extend < 0.
    smooth (float, optional): Once extended, the edges of the mask can be smoothed over 2*smooth pixels
      (default 0; see :func:`smooth_mask`).
    mode (str, optional): How to extend the mask across its boundaries for smoothing:

      - "reflect": the mask is reflected about the edge of the last pixel (abcd → dcba|abcd|dcba).
      - "mirror": the mask is reflected about the center of the last pixel (abcd → dcb|abcd|cba).
      - "nearest": the mask is padded with the value of the last pixel (abcd → aaaa|abcd|dddd).
      - "zero" (default): the mask is padded with zeros (abcd → 0000|abcd|0000).
      - "one": the mask is padded with ones (abcd → 1111|abcd|1111).

  Returns:
    numpy.ndarray: The mask as a float array with the same shape as filtered.
  """
  return smooth_mask(threshold_bmask(filtered, threshold, extend), smooth, mode = mode)

def shape_bmask(shape, x, y, width, height):
    """Return a binary mask defined by the input shape.

    Args:
      shape (str): Either "rectangle" for a rectangle, "ellipse" for an ellipse, or "polygon" for
        a polygon.
      x (tuple, list or numpy.ndarray) : The x coordinates of the shape (pixels along the width).
      y (tuple, list or numpy.ndarray) : The y coordinates of the shape (pixels along the height):

        - If shape = "rectangle", x = (x1, x2) and y = (y1, y2) define the coordinates of two opposite
          corners C1 = (x1, y1) and C2 = (x2, y2) of the rectangle.
        - If shape = "ellipse", x = (x1, x2) and y = (y1, y2) define the coordinates of two opposite
          corners C1 = (x1, y1) and C2 = (x2, y2) of the rectangle that bounds the ellipse.
        - If shape = "polygon", the points P[n] = (x[n], y[n]) (0 <= n < len(x)) are the vertices of
          the polygon.

      width (int): The width of the mask (pixels).
      height (int): The height of the mask (pixels).

    Returns:
      numpy.ndarray: A boolean array with shape (height, width) and values True in the shape and
      False outside.
    """
    if shape == "rectangle":
      if len(x) != 2 or len(y) != 2: raise ValueError("Error, x and y must have exactly two elements for shape = 'rect'.")
      x1 = max(int(np.rint(min(x)))  , 0)
      x2 = min(int(np.rint(max(x)))+1, width)
      y1 = max(int(np.rint(min(y)))  , 0)
      y2 = min(int(np.rint(max(y)))+1, height)
      bmask = np.zeros((height, width), dtype = bool)
      bmask[y1:y2, x1:x2] = True
    elif shape == "ellipse":
      if len(x) != 2 or len(y) != 2: raise ValueError("Error, x and y must have exactly two elements for shape = 'ellipse'.")
      xc = (x[0]+x[1])/2.
      yc = (y[0]+y[1])/2.
      rx = abs(x[1]-x[0])/2.
      ry = abs(y[1]-y[0])/2.
      bmask = np.zeros((height, width), dtype = bool)
      rs, cs = skdraw.ellipse(yc, xc, ry, rx, shape = (height, width))
      bmask[rs, cs] = True
    elif shape == "polygon":
      if len(x) != len(y): raise ValueError("Error, x and y must have the same length for shape = 'polygon'.")
      bmask = skdraw.polygon2mask((height, width), np.column_stack((y, x)))
    else:
      raise ValueError(f"Error, unknown shape '{shape}'.")
    return bmask

#####################################
# For inclusion in the Image class. #
#####################################

class MixinImage:
  """To be included in the Image class."""

  def filter(self, channel, filter, radius, mode = "reflect"):
    """Apply a spatial filter to a selected channel of the image.

    The main purpose of this method is to prepare masks for image processing.

    See also:
      :func:`threshold_bmask`,
      :func:`threshold_fmask`

    Args:
      channel (str): The selected channel:

        - "1", "2", "3" (or equivalently "R", "G", "B" for RGB images):
          The first/second/third channel (all images).
        - "H": The HSV/HSL hue (RGB, HSV and HSL images).
        - "V": The HSV value (RGB, HSV and grayscale images).
        - "S": The HSV saturation (RGB, HSV and grayscale images).
        - "L'": The HSL lightness (RGB, HSL and grayscale images).
        - "S'": The HSL saturation (RGB, HSL and grayscale images).
        - "L": The luma (RGB and grayscale images).
        - "L*": The CIE lightness L* (RGB, grayscale, CIELab and CIELuv images).
        - "c*": The CIE chroma c* (CIELab and CIELuv images).
        - "s*": The CIE saturation s* (CIELuv images).

      filter (str): The filter:

        - "mean": Return the average of the channel within a disk around each pixel.
        - "median": Return the median of the channel within a disk around each pixel.
        - "gaussian": Return the gaussian average of the channel around each pixel.
        - "maximum": Return the maximum of the channel within a disk around each pixel.

      radius (float): The radius of the disk (pixels). The standard deviation for gaussian average
        is radius/3.
      mode (str, optional): How to extend the image across its boundaries:

        - "reflect" (default): the image is reflected about the edge of the last pixel (abcd → dcba|abcd|dcba).
        - "mirror": the image is reflected about the center of the last pixel (abcd → dcb|abcd|cba).
        - "nearest": the image is padded with the value of the last pixel (abcd → aaaa|abcd|dddd).
        - "zero": the image is padded with zeros (abcd → 0000|abcd|0000).

    Returns:
      numpy.ndarray: The output of the filter as an array with shape (image height, image width).
    """
    if mode == "zero": mode = "constant" # Translate modes.
    data = self.get_channel(channel)
    if filter == "gaussian":
      return ndimg.gaussian_filter(data, sigma = radius/3., mode = mode, cval = 0.)
    elif filter == "mean":
      kernel = skimo.disk(radius, dtype = self.dtype)
      kernel /= np.sum(kernel)
      return ndimg.convolve(data, kernel, mode = mode, cval = 0.)
    elif filter == "median":
      return ndimg.median_filter(data, footprint = skimo.disk(radius, dtype = bool), mode = mode, cval = 0.)
    elif filter == "maximum":
      return ndimg.maximum_filter(data, footprint = skimo.disk(radius, dtype = bool), mode = mode, cval = 0.)
    else:
      raise ValueError(f"Error, unknown filter '{filter}'.")

  def shape_bmask(self, shape, x, y):
    """Return a binary mask defined by the input shape.

    Args:
      shape (str): Either "rectangle" for a rectangle, "ellipse" for an ellipse, or "polygon" for
        a polygon.
      x (tuple, list or numpy.ndarray) : The x coordinates of the shape (pixels along the width).
      y (tuple, list or numpy.ndarray) : The y coordinates of the shape (pixels along the height):

        - If shape = "rectangle", x = (x1, x2) and y = (y1, y2) define the coordinates of two opposite
          corners C1 = (x1, y1) and C2 = (x2, y2) of the rectangle.
        - If shape = "ellipse", x = (x1, x2) and y = (y1, y2) define the coordinates of two opposite
          corners C1 = (x1, y1) and C2 = (x2, y2) of the rectangle that bounds the ellipse.
        - If shape = "polygon", the points P[n] = (x[n], y[n]) (0 <= n < len(x)) are the vertices of
          the polygon.

    Returns:
      numpy.ndarray: A boolean array with shape (image height, image width), and values True in the
      shape and False outside.
    """
    height, width = self.get_size()
    return shape_bmask(shape, x, y, width, height)
