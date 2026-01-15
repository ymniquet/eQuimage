# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 3.0.0 / 2026.01.15
# Doc OK.

"""Image class.

The following symbols are imported in the equimage/equimagelab namespaces for convenience:
  "Image".
"""

__all__ = ["Image"]

import numpy as np

from . import params
from . import image_colorspaces
from . import image_utils
from . import image_geometry
from . import image_colors
from . import image_stretch
from . import image_filters
from . import image_skimage
from . import image_multiscale
from . import image_hdr
from . import image_masks
from . import image_stats
from . import image_editors
from . import image_stars
from . import image_io

class Image(np.lib.mixins.NDArrayOperatorsMixin,
            image_colorspaces.MixinImage, image_utils.MixinImage, image_geometry.MixinImage,
            image_colors.MixinImage, image_stretch.MixinImage, image_filters.MixinImage, image_skimage.MixinImage,
            image_multiscale.MixinImage, image_hdr.MixinImage, image_masks.MixinImage, image_stats.MixinImage,
            image_editors.MixinImage,image_stars.MixinImage, image_io.MixinImage):
  """Image class.

  The image is stored as self.image, a numpy.ndarray with dtype numpy.float32 or numpy.float64.
  Color images are represented as arrays with shape (3, height, width) and grayscale images as
  arrays with shape (1, height, width). The leading axis spans the color channels, and the last
  two the height and width of the image.

  The class embeds colorspace and colormodel attributes for the color space and model of the image.

  The colorspace attribute can be:

    - "lRGB" for the linear RGB color space.
    - "sRGB" for the sRGB color space.
    - "CIELab" for the CIELab color space.
    - "CIELuv" for the CIELuv color space.

  In the lRGB and sRGB color spaces, the colormodel attribute can be:

    - "gray": grayscale image with one single channel within [0, 1].
    - "RGB": the 3 channels of the image are the red, blue, and green levels within [0, 1].
    - "HSV": the 3 channels of the image are the HSV hue, saturation and value within [0, 1].
    - "HSL": the 3 channels of the image are the HSL hue, saturation and lightness within [0, 1].

  In the CIELab color space, the colormodel attribute can be:

    - "Lab": the 3 channels of the image are the CIELab components L*/100, a*/100 and b*/100.
      The lightness L*/100 fits within [0, 1], but a* and b* are signed and not bounded.
    - "Lch": the 3 channels of the image are the CIELab components L*/100, c*/100 and h*/(2π).
      The lightness L*/100 and the reduced hue angle h*/(2π) fit within [0, 1], but the
      chroma c* is not bounded by 1.

  In the CIELuv color space, the colormodel attribute can be:

    - "Luv": the 3 channels of the image are the CIELuv components L*/100, u*/100 and v*/100.
      The lightness L*/100 fits within [0, 1], but u* and v* are signed and not bounded.
    - "Lch": the 3 channels of the image are the CIELuv components L*/100, c*/100 and h*/(2π).
      The lightness L*/100 and the reduced hue angle h*/(2π) fit within [0, 1], but the
      chroma c* is not bounded by 1.
    - "Lsh": the 3 channels of the image are the CIELuv components L*/100, s*/100 and h*/(2π).
      The lightness L*/100 and the reduced hue angle h*/(2π) fit within [0, 1], but the
      saturation s* = c*/L* is not bounded by 1.

  The default color space is sRGB and the default color model is RGB.

  The dtype of the images (numpy.float32 or numpy.float64) can be set with :meth:`params.set_image_type() <equimage.params.set_image_type>`.
  """

  ################
  # Constructor. #
  ################

  def __init__(self, image, channels = 0, colorspace = "sRGB", colormodel = "RGB"):
    """Initialize a new Image object with the input image.

    Args:
      image (numpy.ndarray or Image): The input image.
      channels (int, optional): The position of the channel axis for color images (default 0).
      colorspace (str, optional): The color space of the image (default "sRGB").
        Can be "lRGB" (linear RGB color space), "sRGB" (sRGB color space), "CIELab" (CIELab colorspace),
        or "CIELuv" (CIELuv color space).
      colormodel (str, optional): The color model of the image (default "RGB").
        In the lRGB/SRGB color spaces, can be "RGB" (RGB color model), "HSV" (HSV color model), "HSL"
        (HSL color model) or "gray" (grayscale image).
        In the CIELab color space, can be "Lab" (L*a*b* color model) or "Lch" (L*c*h* color model).
        In the CIELuv color space, can be "Luv" (L*u*v* color model), "Lch" (L*c*h* color model)
        or "Lsh" (L*s*h* model).
    """
    # Check color space and model.
    if colorspace in ["lRGB", "sRGB"]:
      if colormodel not in ["RGB", "HSV", "HSL", "gray"]:
        raise ValueError(f"Error, the color model of {colorspace} images must be 'RGB', 'HSV', 'HSL' or 'gray' (got '{colormodel}').")
    elif colorspace == "CIELab":
      if colormodel not in ["Lab", "Lch"]:
        raise ValueError(f"Error, the color model of {colorspace} images must be 'Lab' or 'Lch' (got '{colormodel}').")
    elif colorspace == "CIELuv":
      if colormodel not in ["Luv", "Lch", "Lsh"]:
        raise ValueError(f"Error, the color model of {colorspace} images must be 'Luv', 'Lch' or 'Lsh' (got '{colormodel}').")
    else:
      raise ValueError(f"Error, the color space must be 'lRGB', 'sRGB', 'CIELab' or 'CIELuv' (got '{colorspace}').")
    # Convert the input image into an array.
    image = np.asarray(image, dtype = params.imagetype)
    # Validate the image.
    if image.ndim == 2:
      colormodel = "gray"  # Enforce colormodel = "gray".
      image = np.expand_dims(image, axis = 0)
    elif image.ndim == 3:
      if channels != 0: image = np.moveaxis(image, channels, 0)
      nc = image.shape[0]
      if nc == 1:
        colormodel = "gray" # Enforce colormodel = "gray".
      elif nc == 3:
        if colormodel == "gray":
          raise ValueError(f"Error, a grayscale image must have one single channel (found {nc}).")
      else:
        raise ValueError(f"Error, an image must have either 1 or 3 channels (found {nc}).")
    else:
      raise ValueError(f"Error, an image must have either 2 or 3 dimensions (found {image.ndim}).")
    if colorspace in ["CIELab", "CIELuv"] and colormodel == "gray":
      raise ValueError(f"Error, a CIELab/CIELuv image must have 3 channels.")
    # Register image, color space and model.
    self.image = image
    self.dtype = self.image.dtype # Add a reference to image type.
    self.colorspace = colorspace
    self.colormodel = colormodel

  def newImage(self, image, **kwargs):
    """Return a new Image object with the input image (with, by default, the same color space and
    color model as self).

    Args:
      image (numpy.ndarray): The input image.
      colorspace (str, optional): The color space of the image (default self.colorspace).
        Can be "lRGB" (linear RGB color space), "sRGB" (sRGB color space), or "CIELab" (CIELab color space).
      colormodel (str, optional): The color model of the image (default self.colormodel).
        In the lRGB/SRGB color spaces, can be "RGB" (RGB color model), "HSV" (HSV color model), "HSL"
        (HSL color model) or "gray" (grayscale image).
        In the CIELab color space, can be "Lab" (L*a*b* color model) or "Lch" (L*c*h* color model).
        In the CIELuv color space, can be "Luv" (L*u*v* color model), "Lch" (L*c*h* color model)
        or "Lsh" (L*s*h* model).

    Returns:
      Image: The new Image object.
    """
    colorspace = kwargs.pop("colorspace", self.colorspace)
    colormodel = kwargs.pop("colormodel", self.colormodel)
    if kwargs: print("Discarding extra keyword arguments in Image.newImage...")
    return Image(image, colorspace = colorspace, colormodel = colormodel)

  def copy(self):
    """Return a copy of the object.

    Returns:
      Image: A copy of the object.
    """
    return self.newImage(self.image.copy())

  ######################
  # Object management. #
  ######################

  def __repr__(self):
    """Return the object representation."""
    return f"{self.__class__.__name__}(size = {self.image.shape[2]}x{self.image.shape[1]} pixels, colorspace = {self.colorspace}, colormodel = {self.colormodel}, type = {self.dtype})"

  def __getitem__(self, channels):
    """Return channel(s) of the image.

    Implements the indexer operator self[channels] as self.image[channels].

    Args:
      channels (int or slice): The channels to be returned.

    Returns
      numpy.ndarray: The channels self.image[channels].
    """
    return self.image[channels]

  def __setitem__(self, channels, data):
    """Set channel(s) of the image.

    Implements the operation self.image[channels] = data as self[channels] = data.

    Args:
      channels (int or slice): The channels to be set.
      data (numpy.ndarray): The new channels data.
    """
    self.image[channels] = data

  def __array__(self, dtype = None, copy = None):
    """Expose an Image object as an numpy.ndarray."""
    return np.array(self.image, dtype = dtype, copy = copy)

  def __array_ufunc__(self, ufunc, method, *args, **kwargs):
    """Apply numpy ufuncs to an Image object."""
    if method != "__call__": raise NotImplemented(f"Operation {method} not implemented on Image ufuncs.")
    reference = None
    mixed = False
    inputs = []
    for arg in args:
      if isinstance(arg, Image):
        if reference is None:
          reference = arg
        else:
          if arg.colorspace != reference.colorspace or arg.colormodel != reference.colormodel and not mixed:
            print("Warning ! This operation mixes images with different color spaces or models !..")
            mixed = True
        inputs.append(arg.image)
      else:
        inputs.append(arg)
    if (out := kwargs.get("out", None)) is not None: # In-place operation.
      outputs = []
      for arg in out:
        if isinstance(arg, Image):
          if arg.colorspace != reference.colorspace or arg.colormodel != reference.colormodel and not mixed:
            print("Warning ! This operation mixes images with different color spaces or models !..")
            mixed = True
          outputs.append(arg.image)
        else:
          outputs.append(arg)
      kwargs["out"] = tuple(outputs)
    output = ufunc(*inputs, **kwargs)
    if isinstance(output, np.ndarray): # Note: If there are multiple outputs, we don't convert these to Images.
      if output.ndim == 0: # Is output actually a scalar ?
        return output[()]
      else:
        if not mixed and output.shape == reference.image.shape:
          return Image(output, colorspace = reference.colorspace, colormodel = reference.colormodel)
        else:
          return output
    else:
      return output

  def __array_function__(self, func, types, args, kwargs):
    """Apply numpy array functions to an Image object."""
    reference = None
    mixed = False
    inputs = []
    for arg in args:
      if isinstance(arg, Image):
        if reference is None:
          reference = arg
        else:
          if arg.colorspace != reference.colorspace or arg.colormodel != reference.colormodel and not mixed:
            print("Warning ! This operation mixes images with different color spaces or models !..")
            mixed = True
        inputs.append(arg.image)
      else:
        inputs.append(arg)
    output = func(*inputs, **kwargs)
    if isinstance(output, np.ndarray):
      if output.ndim == 0: # Is output actually a scalar ?
        return output[()]
      else:
        if not mixed and output.shape == reference.image.shape:
          return Image(output, colorspace = reference.colorspace, colormodel = reference.colormodel)
        else:
          return output
    else:
      return output

  ##################
  # Image queries. #
  ##################

  def get_image(self, channels = 0, copy = False):
    """Return the image data.

    Args:
      channels (int, optional): The position of the channel axis (default 0).
      copy (bool, optional): If True, return a copy of the image data;
                             If False (default), return a view.

    Returns:
      numpy.ndarray: The image data.
    """
    image = self.image
    if channels != 0: image = np.moveaxis(image, 0, channels)
    return image.copy() if copy else image

  def get_shape(self):
    """Return the shape of the image data.

    Returns:
      tuple: (number of channels, height of the image in pixels, width of the image in pixels).
    """
    return self.image.shape

  def get_size(self):
    """Return the height and width of the image.

    Returns:
      tuple: (height, width) of the image in pixels.
    """
    return self.image.shape[1], self.image.shape[2]

  def get_nc(self):
    """Return the number of channels of the image.

    Returns:
      int: The number of channels of the image.
    """
    return self.image.shape[0]

  def get_color_space(self):
    """Return the color space of the image.

    Returns:
      str: The color space of the image.
    """
    return self.colorspace

  def get_color_model(self):
    """Return the color model of the image.

    Returns:
      str: The color model of the image.
    """
    return self.colormodel

  ######################
  # Image conversions. #
  ######################

  def int8(self):
    """Return the image as an array of 8 bits integers with shape (height, width, channels).

    Warning:
      This method maps [0., 1.] onto [0, 255].
      Not suitable for the CIELab and CIELuv color spaces !

    Returns:
      numpy.ndarray: The image as an array of 8 bits integers with shape (height, width, channels).
    """
    image = self.get_image(channels = -1)
    data = np.clip(image*255, 0, 255)
    return np.rint(data).astype("uint8")

  def int16(self):
    """Return the image as an array of 16 bits integers with shape (height, width, channels).

    Warning:
      This method maps [0., 1.] onto [0, 65535].
      Not suitable for the CIELab and CIELuv color spaces !

    Returns:
      numpy.ndarray: The image as an array of 16 bits integers with shape (height, width, channels).
    """
    image = self.get_image(channels = -1)
    data = np.clip(image*65535, 0, 65535)
    return np.rint(data).astype("uint16")

  def int32(self):
    """Return the image as an array of 32 bits integers with shape (height, width, channels).

    Warning:
      This method maps [0., 1.] onto [0, 4294967295].
      Not suitable for the CIELab and CIELuv color spaces !

    Returns:
      numpy.ndarray: The image as an array of 32 bits integers with shape (height, width, channels).
    """
    image = self.get_image(channels = -1)
    data = np.clip(image*4294967295, 0, 4294967295)
    return np.rint(data).astype("uint32")
