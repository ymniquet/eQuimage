# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 3.0.0 / 2026.03.10
# Doc OK.

"""Image I/O management.

The following symbols are imported in the equimage/equimagelab namespaces for convenience:
  "load_image", "save_image".
"""

__all__ = ["load_image", "save_image"]

import os
import numpy as np

from . import params

from PIL import Image as PILImage
if params.IMAGEIO:
  import imageio.v3 as iio
else:
  import tifffile
  import skimage.io as skio
import astropy.io.fits as pyfits

def load_image_as_array(filename, verbose = True):
  """Load a RGB or grayscale image from a file.

  Args:
    filename (str): The file name.
    verbose (bool, optional): If True (default), print information about the image.

  Returns:
    The image as numpy.ndarray and the file meta-data (including exif if available) as a dictionary.
  """
  if verbose: print(f"Loading file {filename}...")
  try:
    header = PILImage.open(filename)
  except:
    header = None
    fmt = None
    if verbose: print("Failed to identify image file format; Attempting to load anyway...")
  else:
    fmt = header.format
    if verbose: print(f"Format = {fmt}.")
  if fmt == "PNG": # Load with the FreeImage plugin to enable 16 bits color depth.
    image = iio.imread(filename, plugin = "PNG-FI") if params.IMAGEIO else skio.imread(filename)
  elif fmt == "TIFF":
    # skimage.io plugin architecture deprecated from skimage 0.25.
    image = iio.imread(filename, plugin = "TIFF") if params.IMAGEIO else tifffile.imread(filename) # skio.imread(filename, plugin = "tifffile")
  elif fmt == "FITS":
    hdus = pyfits.open(filename)
    image = hdus[0].data
    if image.ndim == 3:                 # Pyfits returns (channels, height, width)
      image = np.moveaxis(image, 0, -1) # instead of (height, width, channels),
    image = np.flip(image, axis = 0)    # and an upside down image.
  else:
    image = iio.imread(filename) if params.IMAGEIO else skio.imread(filename)
  if image.ndim == 2: # Assume single channel images are monochrome.
    nc = 1
    image = np.expand_dims(image, axis = -1)
  elif image.ndim == 3:
    nc = image.shape[2]
  else:
    raise ValueError(f"Error, invalid image shape {image.shape}.")
  if verbose: print(f"Image size = {image.shape[1]}x{image.shape[0]} pixels.")
  if verbose: print(f"Number of channels = {nc}.")
  if nc not in [1, 3, 4]: raise ValueError(f"Error, images with {nc} channels are not supported.")
  dtype = str(image.dtype)
  if verbose: print(f"Data type = {dtype}.")
  if dtype == "uint8":
    bpc = 8
    image = params.imagetype(image/255)
  elif dtype == "uint16":
    bpc = 16
    image = params.imagetype(image/65535)
  elif dtype == "uint32":
    bpc = 32
    image = params.imagetype(image/4294967295)
  elif dtype in ["float32", ">f4", "<f4"]: # Assumed normalized in [0, 1] !
    bpc = 32
    image = params.imagetype(image)
  elif dtype in ["float64", ">f8", "<f8"]: # Assumed normalized in [0, 1] !
    bpc = 64
    image = params.imagetype(image)
  else:
    raise TypeError(f"Error, image data type {dtype} is not supported.")
  if verbose: print(f"Bit depth per channel = {bpc}.")
  if verbose: print(f"Bit depth per pixel = {nc*bpc}.")
  image = np.moveaxis(image, -1, 0) # Move last (channel) axis to leading position.
  for ic in range(nc):
    if verbose: print(f"Channel #{ic}: minimum = {image[ic].min():.5f}, maximum = {image[ic].max():.5f}.")
  if nc == 4: image = image[0:3]*image[3] # Assume fourth channel is transparency.
  try:
    exif = header.getexif()
  except:
    exif = None
  else:
    if verbose: print("Succesfully read EXIF data...")
  meta = {"exif": exif, "colordepth": bpc}
  return np.ascontiguousarray(image), meta

def load_image(filename, colorspace = "sRGB", verbose = True):
  """Load a RGB or grayscale image from a file.

  Args:
    filename (str): The file name.
    colorspace (str, optional): The colorspace of the image [either "sRGB" (default) or "lRGB" for
      linear RGB images].
    verbose (bool, optional): If True (default), print information about the image.

  Returns:
    The image as an Image object and the file meta-data (including exif if available) as a dictionary.
  """
  from .image import Image
  image, meta = load_image_as_array(filename, verbose = verbose)
  return Image(image, colorspace = colorspace, colormodel = "RGB"), meta

def save_image(image, filename, depth = 8, compress = 6, verbose = True):
  """Save a RGB or grayscale image as a file.

  Note: The color space is *not* embedded in the file at present.

  Args:
    image (Image): The image.
    filename (str): The file name. The file format is chosen according to the extension:

      - .png: PNG file with depth = 8 or 16 bits integer per channel.
      - .tif, .tiff: TIFF file with depth = 8, 16 or 32 bits integer per channel.
      - .fit, .fits, .fts: FITS file with 32 bits float per channel (irrespective of depth).

    depth (int, optional): The color depth of the file in bits per channel (default 8).
    compress (int, optional): The compression level for TIFF files
      (Default 6; 0 = no zlib compression; 9 = maximum zlib compression).
    verbose (bool, optional): If True (default), print information about the file.
  """
  image.check_color_model("RGB", "gray")
  is_gray = (image.colormodel == "gray")
  if is_gray:
    if verbose: print(f"Saving grayscale image as file {filename}...")
  else:
    if verbose: print(f"Saving RGB image as file {filename}...")
  root, ext = os.path.splitext(filename)
  if ext in [".png", ".tif", ".tiff"]:
    if depth == 8:
      image = image.int8()
    elif depth == 16:
      image = image.int16()
    elif depth == 32:
      image = image.int32()
    else:
      raise ValueError("Error, color depth must be 8 or 16, or 32 bits per channel.")
    if verbose: print(f"Color depth = {depth} bits integer per channel.")
    if is_gray: image = image[:, :, 0]
    if ext == ".png":
      if params.IMAGEIO:
        if depth > 16: raise ValueError("Error, color depth of png files must be 8 or 16 bits per channel.")
        iio.imwrite(filename, image, plugin = "PNG-FI")
      else:
        if depth > 8: raise ValueError("Error, color depth of png files must be 8 bits per channel.")
        skio.imsave(filename, image, check_contrast = False)
    elif ext == ".tif" or ext == ".tiff":
      if params.IMAGEIO:
        iio.imwrite(filename, image, plugin = "TIFF", metadata = {"compress": compress})
      else:
        # skimage.io plugin architecture deprecated from skimage 0.25.
        # skio.imsave(filename, image, check_contrast = False, plugin = "tifffile",
        #             compression = "zlib" if compress > 0 else None, compressionargs = {"level": compress})
        tifffile.imwrite(filename, image, compression = "zlib" if compress > 0 else None, compressionargs = {"level": compress})
  elif ext in [".fit", ".fits", ".fts"]:
    if verbose: print(f"Color depth = 32 bits float per channel.")
    image = np.asarray(image.flipud().get_image(), dtype = np.float32) # Flip image upside down.
    if is_gray: image = image[0]
    hdu = pyfits.PrimaryHDU(image)
    hdu.writeto(filename, overwrite = True)
  else:
    raise ValueError("Error, file extension must be .png, .tif/.tiff, or .fit/.fits/.fts.")

#####################################
# For inclusion in the Image class. #
#####################################

class MixinImage:
  """To be included in the Image class."""

  def save(self, filename, depth = 8, compress = 6, verbose = True):
    """Save image as a file.

    Note: The color model must be "RGB" or "gray", but the color space is *not* embedded
    in the file at present.

    Args:
      filename (str): The file name. The file format is chosen according to the extension:

        - .png: PNG file with depth = 8 or 16 bits integer per channel.
        - .tif, .tiff: TIFF file with depth = 8, 16 or 32 bits integer per channel.
        - .fit, .fits, .fts: FITS file with 32 bits float per channel (irrespective of depth).

      depth (int, optional): The color depth of the file in bits per channel (default 8).
      compress (int, optional): The compression level for TIFF files
        (Default 6; 0 = no zlib compression; 9 = maximum zlib compression).
      verbose (bool, optional): If True (default), print information about the file.
    """
    save_image(self, filename, depth = depth, compress = compress, verbose = verbose)
