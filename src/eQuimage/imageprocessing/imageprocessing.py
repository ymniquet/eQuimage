# This program is 0free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2024.01.14

"""Image processing tools."""

import re
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import imageio.v3 as iio
from copy import deepcopy
from PIL import Image as PILImage
from scipy.signal import convolve2d
from .utils import scale_pixels, lookup
from .stretchfunctions import midtone_stretch_function

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

class Image:
  """Image class. The RGB components are stored as floats in the range [0, 1].
     Note: No particular color space is assumed. Practically, most RGB images
     are encoded in the non-linear sRGB color space. It is the responsibility
     of the user to make the color transformations appropriate to his needs."""

  # Object constructors, getters & setters.

  def __init__(self, image = None, meta = {}):
    """Initialize object with RGB image 'image' and meta-data 'meta'.
       The meta-data is a dictionary (or any other container) of user-defined data."""
    self.rgb = IMGTYPE(image) if image is not None else None
    self.meta = meta

  @classmethod
  def newImage(cls, self, image = None, meta = {}):
    """Return a new instance with RGB image 'image' and meta-data 'meta'.
       The meta-data is a dictionary (or any other container) of user-defined data."""
    return cls(image = image, meta = meta)

  def set_image(self, image):
    """Set RGB image 'image' and return the object."""
    self.rgb = image
    return self

  def get_image(self):
    """Return (a reference to) the RGB image."""
    return self.rgb

  def get_image_copy(self):
    """Return a copy of the RGB image."""
    return self.rgb.copy()

  def set_meta(self, meta):
    """Set image meta-data 'meta' and return the object."""
    self.meta = meta
    return self

  def get_meta(self):
    """Return (a view on) the meta-data."""
    return self.meta

  # Object inquiries.

  def size(self):
    """Return the image width and height in pixels."""
    return self.rgb.shape[2], self.rgb.shape[1]

  def rgbf(self):
    """Return *a view* of the RGB components as a (height, width, 3) array of floats."""
    return np.moveaxis(self.rgb, 0, -1)

  def rgbf_copy(self):
    """Return *a copy* of the RGB components as a (height, width, 3) array of floats."""
    return np.moveaxis(self.rgb, 0, -1).copy()

  def rgb8(self):
    """Return the RGB components as a (height, width, 3) array of 8 bits integers in the range [0, 255]."""
    data = np.clip(self.rgb*255, 0, 255)
    return np.moveaxis(np.rint(data).astype("uint8"), 0, -1)

  def rgb16(self):
    """Return the RGB components as a (height, width, 3) array of 16 bits integers in the range [0, 65535]."""
    data = np.clip(self.rgb*65535, 0, 65535)
    return np.moveaxis(np.rint(data).astype("uint16"), 0, -1)

  def value(self):
    """Return the HSV value = max(RGB)."""
    return self.rgb.max(axis = 0)

  def saturation(self):
    """Return the HSV saturation = 1-min(RGB)/max(RGB)."""
    return 1.-self.rgb.min(axis = 0)/(abs(self.rgb.max(axis = 0))+IMGTOL) # Safe evaluation.
    
  def luma(self):
    """Return the (generalized) luma defined as the linear combination of the RGB components weighted by rgbluma."""
    return rgbluma[0]*self.rgb[0]+rgbluma[1]*self.rgb[1]+rgbluma[2]*self.rgb[2]

  def luma16(self):
    """Return the luma as a (height, width) array of 16 bits integers in the range [0, 65535]."""
    data = np.clip(self.luma()*65535, 0, 65535)
    return np.rint(data).astype("uint16")

  def rgb_to_hsv(self):
    """Return the hue/saturation/value (HSV) data as a (height, width, 3) array of floats."""
    return IMGTYPE(colors.rgb_to_hsv(np.moveaxis(self.rgb, 0, -1)))

  def set_hsv_image(self, hsv):
    """Set RGB image from hue/saturation/value (HSV) data hsv(height, width, 3)."""
    self.rgb = np.moveaxis(IMGTYPE(colors.hsv_to_rgb(hsv)), -1, 0)

  def srgb_to_lrgb(self):
    """Return the linear RGB components of an sRGB image."""
    srgb = np.clip(self.rgb, 0., 1.)
    return np.where(srgb > 0.04045, ((srgb+0.055)/1.055)**2.4, srgb/12.92)

  def srgb_luminance(self):
    """Return the luminance Y of an sRGB image."""
    lrgb = self.srgb_to_lrgb()
    return 0.2126*lrgb[0]+0.7152*lrgb[1]+0.0722*lrgb[2]

  def srgb_lightness(self):
    """Return the CIE lightness L* of an sRGB image."""
    Y = self.srgb_luminance()
    return np.where(Y > 0.008856, 116.*Y**(1./3.)-16., 903.3*Y)

  def is_valid(self):
    """Return True if the object contains a valid RGB image, False otherwise."""
    if not isinstance(self.rgb, np.ndarray): return False
    if self.rgb.ndim != 3: return False
    if self.rgb.shape[0] != 3: return False
    if self.rgb.dtype != IMGTYPE: return False
    return True

  def is_out_of_range(self):
    """Return True if the RGB image is out-of-range (data < 0 or > 1 in any channel), False otherwise."""
    return np.any(self.rgb < -IMGTOL) or np.any(self.rgb > 1.+IMGTOL)

  def is_gray_scale(self):
    """Return True if the image is a gray scale (same RGB channels), False otherwise."""
    return np.all(abs(self.rgb[1]-self.rgb[0]) < IMGTOL) and np.all(abs(self.rgb[2]-self.rgb[0]) < IMGTOL)

  # Object copies.

  def ref(self, meta = "self"):
    """Return a new Image object with a reference to the RGB image and new meta-data 'meta' (copy of the original if meta = "self")."""
    if meta == "self": meta = deepcopy(self.meta)
    return self.newImage(self, self.rgb, meta)

  def clone(self, meta = "self"):
    """Return a new Image object with a copy of the RGB image and new meta-data 'meta' (copy of the original if meta = "self")."""
    if meta == "self": meta = deepcopy(self.meta)
    return self.newImage(self, self.rgb.copy(), meta)

  def copy_image_from(self, source):
    """Copy the RGB image from 'source'."""
    self.rgb = source.rgb.copy()

  def copy_meta_from(self, source):
    """Copy the meta-data from 'source'."""
    self.meta = deepcopy(source.meta)

  # Image load/save.

  def load(self, filename, meta = {}):
    """Load file 'filename' and set meta-data 'meta' (leave unchanged if meta = "self", or pick the file meta-data if meta = "file").
       Return the file meta-data (including exif if available). The image color space is not transformed and assumed to be sRGB."""
    print(f"Loading file {filename}...")
    header = PILImage.open(filename)
    fmt = header.format
    print(f"Format = {fmt}.")
    if fmt == "PNG": # Load with the FreeImage plugin to enable 16 bits color depth.
      image = iio.imread(filename, plugin = "PNG-FI")
    elif fmt == "TIFF":
      image = iio.imread(filename, plugin = "TIFF")
    elif fmt == "FITS":
      image = iio.imread(filename, plugin = "FITS")
      if image.ndim == 3:                 # Surprisingly, iio.imread returns (channels, height, width)
        image = np.moveaxis(image, 0, -1) # instead of (height, width, channels) for FITS files,
      image = np.flip(image, axis = 0)    # and an upside down image.
    else:
      image = iio.imread(filename)
    if image.ndim == 2:
      nc = 1
    elif image.ndim == 3:
      nc = image.shape[2]
    else:
      raise ValueError(f"Error, invalid image dimensions = {image.shape}.")
    print(f"Number of channels = {nc}.")
    if nc not in [1, 3, 4]:
      raise ValueError(f"Error, images with {nc} channels are not supported.")
    print(f"Image size = {image.shape[1]}x{image.shape[0]} pixels.")
    dtype = str(image.dtype)
    print(f"Data type = {dtype}.")
    if dtype == "uint8":
      bpc = 8
      image = IMGTYPE(image/255)
    elif dtype == "uint16":
      bpc = 16
      image = IMGTYPE(image/65535)
    elif dtype in ["float32", ">f4", "<f4"]: # Assumed normalized in [0, 1] !
      bpc = 32
      image = IMGTYPE(image)
    elif dtype in ["float64", ">f8", "<f8"]: # Assumed normalized in [0, 1] !
      bpc = 64
      image = IMGTYPE(image)
    else:
      raise TypeError(f"Error, image data type {dtype} is not supported.")
    print(f"Bit depth per channel = {bpc}.")
    print(f"Bit depth per pixel = {nc*bpc}.")
    if nc == 1: # Assume single channel images are monochrome.
      image = np.repeat(image[:, :, np.newaxis], 3, axis = 2)
    image = np.moveaxis(image, -1, 0) # Move last (channel) axis to leading position.
    for ic in range(nc):
      print(f"Channel #{ic}: minimum = {image[ic].min():.5f}, maximum = {image[ic].max():.5f}.")
    if nc == 4: # Assume fourth channel is transparency.
      image = image[0:3]*image[3]
    self.rgb = np.ascontiguousarray(image)
    filemeta = iio.immeta(filename)
    filemeta["colordepth"] = bpc # Add color depth.
    #print(f"File meta-data = {filemeta}.")
    if meta == "file":
      self.meta = deepcopy(filemeta)
    elif meta != "self":
      self.meta = meta
    return filemeta

  def save(self, filename, depth = 8, single_channel_gray_scale = True):
    """Save image in file 'filename' with color depth 'depth' (bits/channel).
       The file format is chosen according to the 'filename' extension:
        - .png : PNG file with depth = 8 or 16 bits/channel.
        - .tif, .tiff : TIFF file with depth = 8 or 16 bits/channel.
        - .fit/.fits/.fts : FITS file with 32 bits (floats)/channel (irrespective of depth).
       The image is saved as a single channel gray scale if all RGB channels are the same and 'single_channel_gray_scale' is True.
       The image color space is assumed to be sRGB."""
    is_gray_scale = single_channel_gray_scale and self.is_gray_scale()
    if is_gray_scale:
      print(f"Saving gray scale image as file {filename}...")
    else:
      print(f"Saving RGB image as file {filename}...")
    root, ext = os.path.splitext(filename)
    if ext in [".png", ".tif", ".tiff"]:
      if depth == 8:
        image = self.rgb8()
      elif depth == 16:
        image = self.rgb16()
      else:
        raise ValueError("Error, color depth must be 8 or 16 bits.")
      print(f"Color depth = {depth} bits.")
      if is_gray_scale: image = image[:, : , 0]
      if ext == ".png":
        iio.imwrite(filename, image, plugin = "PNG-FI")
      else:
        iio.imwrite(filename, image, plugin = "TIFF", metadata = {"compress": 5})
    #elif ext in [".fit", ".fits", ".fts"]: # Does not work at present.
      #image = np.clip(self.rgb, 0., 1.)
      #print(f"Color depth = 24 bits (floats).")
      #if is_gray_scale: image = image[0, :, :]
      #iio.imwrite("file:test.fit", image, plugin = "FITS")
    else:
      raise ValueError("Error, file extension must be .png or .tif/.tiff.") #, .tif/.tiff or .fit/.fits/.fts.")

  # Image draw.

  def draw(self, ax):
    """Draw the image in matplotlib axes 'ax'.
       The image color space is assumed to be sRGB."""
    ax.imshow(self.rgb_view())

  # Image statistics & histograms.

  def statistics(self):
    """Compute image statistics for channels "R" (red), "G" (green), "B" (blue), "V" (value) and "L" (luma).
       Return stats[key] for key in ("R", "G", "B", "V", "L"), with:
         - stats[key].name = channel name ("Red", "Green", "Blue", "Value", or "Luma", provided for convenience).
         - stats[key].width = image width (provided for convenience).
         - stats[key].height = image height (provided for convenience).
         - stats[key].npixels = number of image pixels = image width*image height (provided for convenience).
         - stats[key].minimum = minimum value in channel key.
         - stats[key].maximum = maximum value in channel key.
         - stats[key].percentiles = (pr25, pr50, pr75) = the 25th, 50th and 75th percentiles in channel key (excluding pixels <= 0 and >= 1).
         - stats[key].median = pr50 = median value in channel key (excluding pixels <= 0 and >= 1).
         - stats[key].zerocount = number of pixels <= 0 in channel key.
         - stats[key].oorcount = number of pixels  > 1 (out-of-range) in channel key."""
    class Container: pass # An empty container class.
    width, height = self.size()
    npixels = width*height
    stats = {}
    for key, name in (("R", "Red"), ("G", "Green"), ("B", "Blue"), ("V", "Value"), ("L", "Luma")):
      stats[key] = Container()
      stats[key].name = name
      stats[key].width = width
      stats[key].height = height
      stats[key].npixels = npixels
      if key == "V":
        channel = self.value()
      elif key == "L":
        channel = self.luma()
      else:
        channel = self.rgb[{"R": 0, "G": 1, "B": 2}[key]]
      stats[key].minimum = channel.min()
      stats[key].maximum = channel.max()
      mask = (channel >= IMGTOL) & (channel <= 1.-IMGTOL)
      if np.any(mask):
        stats[key].percentiles = np.percentile(channel[mask], [25., 50., 75.])
        stats[key].median = stats[key].percentiles[1]
      else:
        stats[key].percentiles = None
        stats[key].median = None
      stats[key].zerocount = np.sum(channel < IMGTOL)
      stats[key].outcount = np.sum(channel > 1.+IMGTOL)
    return stats

  def histograms(self, nbins = 256):
    """Return image histograms as a tuple (edges, counts), where edges(nbins) are the bin edges and
       counts(5, nbins) are the bin counts for the red, green, blue, value and luma channels.
       'nbins' is the number of bins in the range [0, 1]."""
    minimum = min(0., self.rgb.min())
    maximum = max(1., self.rgb.max())
    nbins = int(round(nbins*(maximum-minimum)))
    counts = np.empty((5, nbins), dtype = IMGTYPE)
    for channel in range(3):
      counts[channel], edges = np.histogram(self.rgb[channel], bins = nbins, range = (minimum, maximum), density = False)
    counts[3], edges = np.histogram(self.value(), bins = nbins, range = (minimum, maximum), density = False)
    counts[4], edges = np.histogram(self.luma(), bins = nbins, range = (minimum, maximum), density = False)
    return edges, counts

  ##########################
  # Image transformations. #
  ##########################

  # Image normalization.

  def scale_pixels(self, source, target):
    """Scale all pixels of the image by the ratio target/source.
       Wherever abs(source) < IMGTOL, set all channels to target."""
    self.rgb = scale_pixels(self.rgb, source, target, cutoff = IMGTOL)

  def normalize_out_of_range_values(self):
    """Normalize out-of-range pixels with values >= 1."""
    self.rgb /= np.maximum(self.rgb.max(axis = 0), 1.)

  # Histogram transformations.

  def clip_shadows_highlights(self, shadow = None, highlight = None, channels = "V", inplace = True, meta = "self"):
    """Clip channels 'channels' below shadow level 'shadow' and above highlight level 'highlight', and
       remap [shadow, highlight] to [0, 1]. 'channels' can be "V" (value), "L" (luma) or any combination
       of "R" (red), "G" (green), and "B" (blue). shadow = min(channel) for each channel if 'shadow' is none,
       and highlight = max(channel) for each channel if 'highlight' is None.  Also set new meta-data 'meta'
       (same as the original if meta = "self"). Update the object if 'inplace' is True or return a new instance
       if 'inplace' is False."""
    if highlight is not None:
      if highlight <= shadow: raise ValueError("Error, highlight must be > shadow.")
    if channels in ["V", "L"]:
      channel = self.value() if channels == "V" else self.luma()
      if shadow is None: shadow = max(channel.min(), 0.)
      if highlight is None: highlight = channel.max()
      clipped = np.clip(channel, shadow, highlight)
      interpd = np.interp(clipped, (shadow, highlight), (0., 1.))
      image = scale_pixels(self.rgb, channel, interpd, cutoff = IMGTOL)
      if inplace: self.rgb = image
    else:
      image = self.rgb if inplace else self.rgb.copy()
      for channel, letter in ((0, "R"), (1, "G"), (2, "B")):
        if letter in channels:
          shadow_ = max(image[channel].min(), 0.) if shadow is None else shadow
          highlight_ = image[channel].max() if highlight is None else highlight
          clipped = np.clip(image[channel], shadow_, highlight_)
          image[channel] = np.interp(clipped, (shadow_, highlight_), (0., 1.))
    if inplace:
      if meta != "self": self.meta = meta
      return None
    else:
      if meta == "self": meta = deepcopy(self.meta)
      return self.newImage(self, image, meta)

  def set_dynamic_range(self, fr = None, to = (0., 1.), channels = "L", inplace = True, meta = "self"):
    """Remap 'channels' from range 'fr' (a tuple) to range 'to' (a tuple, default (0, 1)).
       'channels' can be "V" (value), "L" (luma) or any combination of "R" (red) "G" (green), and "B" (blue).
       fr = (min(channel), max(channel)) for each channel if 'fr' is None. Also set new meta-data 'meta'
       (same as the original if meta = "self"). Update the object if 'inplace' is True or return a new instance
       if 'inplace' is False."""
    if fr is not None:
      if fr[1] <= fr[0]: raise ValueError("Error, fr[1] must be > fr[0].")
    if to[1] <= to[0]: raise ValueError("Error, to[1] must be > to[0].")
    if channels in ["V", "L"]:
      channel = self.value() if channels == "V" else self.luma()
      if fr is None: fr = (channel.min(), channel.max())
      interpd = np.maximum(np.interp(channel, fr, to), 0.)
      image = scale_pixels(self.rgb, channel, interpd, cutoff = IMGTOL)
      if inplace: self.rgb = image
    else:
      image = self.rgb if inplace else self.rgb.copy()
      for channel, letter in ((0, "R"), (1, "G"), (2, "B")):
        if letter in channels:
          fr_ = (image[channel].min(), image[channel].max()) if fr is None else fr
          image[channel] = np.maximum(np.interp(image[channel], fr_, to), 0.)
    if inplace:
      if meta != "self": self.meta = meta
      return None
    else:
      if meta == "self": meta = deepcopy(self.meta)
      return self.newImage(self, image, meta)

  def gamma_correction(self, gamma, channels = "L", inplace = True, meta = "self"):
    """Apply gamma correction with exponent 'gamma' to channels 'channels'.
       'channels' can be "V" (value), "L" (luma) or any combination of "R" (red) "G" (green), and "B" (blue).
       Also set new meta-data 'meta' (same as the original if meta = "self"). Update the object if 'inplace'
       is True or return a new instance if 'inplace' is False."""
    if gamma <= 0.: raise ValueError("Error, gamma must be >= 0.")
    if channels in ["V", "L"]:
      channel = self.value() if channels == "V" else self.luma()
      clipped = np.clip(channel, 0., 1.)
      corrected = clipped**gamma
      image = scale_pixels(self.rgb, channel, corrected, cutoff = IMGTOL)
      if inplace: self.rgb = image
    else:
      image = self.rgb if inplace else self.rgb.copy()
      for channel, letter in ((0, "R"), (1, "G"), (2, "B")):
        if letter in channels:
          clipped = np.clip(image[channel], 0., 1.)
          image[channel] = clipped**gamma
    if inplace:
      if meta != "self": self.meta = meta
      return None
    else:
      if meta == "self": meta = deepcopy(self.meta)
      return self.newImage(self, image, meta)

  def midtone_correction(self, midtone = 0.5, channels = "L", inplace = True, meta = "self"):
    """Apply midtone correction with midtone 'midtone' to channels 'channels'.
       'channels' can be "V" (value), "L" (luma) or any combination of "R" (red) "G" (green), and "B" (blue).
       Also set new meta-data 'meta' (same as the original if meta = "self"). Update the object if 'inplace'
       is True or return a new instance if 'inplace' is False."""
    if midtone <= 0.: raise ValueError("Error, midtone must be >= 0.")
    if channels in ["V", "L"]:
      channel = self.value() if channels == "V" else self.luma()
      clipped = np.clip(channel, 0., 1.)
      corrected = (midtone-1.)*clipped/((2.*midtone-1.)*clipped-midtone)
      image = scale_pixels(self.rgb, channel, corrected, cutoff = IMGTOL)
      if inplace: self.rgb = image
    else:
      image = self.rgb if inplace else self.rgb.copy()
      for channel, letter in ((0, "R"), (1, "G"), (2, "B")):
        if letter in channels:
          clipped = np.clip(image[channel], 0., 1.)
          image[channel] = (midtone-1.)*clipped/((2.*midtone-1.)*clipped-midtone)
    if inplace:
      if meta != "self": self.meta = meta
      return None
    else:
      if meta == "self": meta = deepcopy(self.meta)
      return self.newImage(self, image, meta)

  def generalized_stretch(self, stretch_function, params, channels = "L", inplace = True, meta = "self"):
    """Stretch histogram of channels 'channels' with an arbitrary stretch function 'stretch_function' parametrized
       by 'params'. stretch_function(input, params) shall return the output levels for an array of input
       levels 'input'. 'channels' can be "V" (value), "L" (luma) or any combination of "R" (red) "G" (green),
       and "B" (blue). Also set new meta-data 'meta' (same as the original if meta = "self"). Update the object if
       'inplace' is True or return a new instance if 'inplace' is False."""
    if channels in ["V", "L"]:
      channel = self.value() if channels == "V" else self.luma()
      stretched = IMGTYPE(stretch_function(channel, params))
      image = scale_pixels(self.rgb, channel, stretched, cutoff = IMGTOL)
      if inplace: self.rgb = image
    else:
      image = self.rgb if inplace else self.rgb.copy()
      for channel, letter in ((0, "R"), (1, "G"), (2, "B")):
        if letter in channels:
          image[channel] = IMGTYPE(stretch_function(image[channel], params))
    if inplace:
      if meta != "self": self.meta = meta
      return None
    else:
      if meta == "self": meta = deepcopy(self.meta)
      return self.newImage(self, image, meta)

  def generalized_stretch_lookup(self, stretch_function, params, channels = "L", inplace = True, meta = "self", nlut = 131072):
    """Stretch histogram of channels 'channels' with an arbitrary stretch function 'stretch_function' parametrized
       by 'params'. stretch_function(input, params) shall return the output levels for an array of input
       levels 'input'. 'channels' can be "V" (value), "L" (luma) or any combination of "R" (red) "G" (green),
       and "B" (blue). Also set new meta-data 'meta' (same as the original if meta = "self"). Update the object if
       'inplace' is True or return a new instance if 'inplace' is False.
       This method uses a look-up table with linear interpolation between 'nlut' elements to apply the stretch function
       to the channel(s); It shall be much faster than generalized_stretch(...) when the stretch function is expensive.
       The original image is clipped in the [0, 1] range before stretching."""
    xlut = np.linspace(0., 1., nlut, dtype = IMGTYPE) # Build the look-up table.
    ylut = IMGTYPE(stretch_function(xlut, params))
    slut = (ylut[1:]-ylut[:-1])/(xlut[1:]-xlut[:-1]) # Slopes.
    if channels in ["V", "L"]:
      channel = self.value() if channels == "V" else self.luma()
      clipped = np.clip(channel, 0., 1.)
      stretched = lookup(clipped, xlut, ylut, slut, nlut)
      image = scale_pixels(self.rgb, channel, stretched, cutoff = IMGTOL)
      if inplace: self.rgb = image
    else:
      image = self.rgb if inplace else self.rgb.copy()
      for channel, letter in ((0, "R"), (1, "G"), (2, "B")):
        if letter in channels:
          clipped = np.clip(image[channel], 0., 1.)
          image[channel] = lookup(clipped, xlut, ylut, slut, nlut)
    if inplace:
      if meta != "self": self.meta = meta
      return None
    else:
      if meta == "self": meta = deepcopy(self.meta)
      return self.newImage(self, image, meta)

  # Color transformations.

  def color_balance(self, red = 1., green = 1., blue = 1., inplace = True, meta = "self"):
    """Multiply the red channel by 'red', the green channel by 'green', and the blue channel by 'blue'.
       Also set new meta-data 'meta' (same as the original if meta = "self"). Update the object if 'inplace'
       is True or return a new instance if 'inplace' is False."""
    if red < 0.: raise ValueError("Error, red must be >= 0.")
    if green < 0.: raise ValueError("Error, green must be >= 0.")
    if blue < 0.: raise ValueError("Error, blue must be >= 0.")
    if inplace:
      if meta != "self": self.meta = meta
      image = self.rgb
    else:
      if meta == "self": meta = deepcopy(self.meta)
      image = self.rgb.copy()
    if red   != 1.: image[0] *= red
    if green != 1.: image[1] *= green
    if blue  != 1.: image[2] *= blue
    return None if inplace else self.newImage(self, image, meta)

  def negative(self, inplace = True, meta = "self"):
    """Make a negative and set new meta-data 'meta' (same as the original if meta = "self").
       Update the object if 'inplace' is True or return a new instance if False."""
    image = np.clip(1.-self.rgb, 0., 1.)
    if inplace:
      self.rgb = image
      if meta != "self": self.meta = meta
      return None
    else:
      if meta == "self": meta = deepcopy(self.meta)
      return self.newImage(self, image, meta)

  def gray_scale(self, inplace = True, meta = "self"):
    """Convert to gray scale (using the luma) and set new meta-data 'meta' (same as the original if meta = "self").
       Update the object if 'inplace' is True or return a new instance if False."""
    if inplace:
      if meta != "self": self.meta = meta
      image = self.rgb
    else:
      if meta == "self": meta = deepcopy(self.meta)
      image = np.empty_like(self.rgb)
    image[:] = self.luma()
    return None if inplace else self.newImage(self, image, meta)

  # Image enhancement.

  def sharpen(self, inplace = True, meta = "self"):
    """Apply a sharpening convolution filter and set new meta-data 'meta' (same
       as the original if meta = "self"). Update the object if 'inplace' is True or
       return a new instance if 'inplace' is False."""
    if inplace:
      if meta != "self": self.meta = meta
      image = self.rgb
    else:
      if meta == "self": meta = deepcopy(self.meta)
      image = np.empty_like(self.rgb)
    kernel = np.array([[-1., -1., -1.], [-1., 9., -1.], [-1., -1., -1.]], dtype = IMGTYPE)
    for channel in range(3):
      image[channel] = convolve2d(self.rgb[channel], kernel, mode = "same", boundary = "fill", fillvalue = 0.)
    return None if inplace else self.newImage(self, image, meta)

  def remove_hot_pixels(self, ratio = 2., channels = "L", inplace = True, meta = "self"):
    """Remove hot pixels in channels 'channels'. 'channels' can be "V" (value), "L" (luma) or any
       combination of "R" (red) "G" (green), and "B" (blue). All pixels in a channel whose level is greater
       than 'ratio' times the average of their 8 nearest neighbors are replaced by this average.
       Also set new meta-data 'meta' (same as the original if meta = "self"). Update the object if 'inplace'
       is True or return a new instance if 'inplace' is False."""
    if ratio <= 0.: raise ValueError("Error, ratio must be > 0.")
    if inplace:
      if meta != "self": self.meta = meta
      image = self.rgb
    else:
      if meta == "self": meta = deepcopy(self.meta)
      image = np.empty_like(self.rgb)
    kernel = np.array([[1., 1., 1.], [1., 0., 1.], [1., 1., 1.]], dtype = IMGTYPE)
    if channels in ["V", "L"]:
      channel = self.value() if channels == "V" else self.luma()
      nnn = convolve2d(np.ones_like(channel), kernel, mode = "same", boundary = "fill", fillvalue = 0.)
      avg = convolve2d(channel, kernel, mode = "same", boundary = "fill", fillvalue = 0.)/nnn
      mask = (channel > ratio*avg)
      for channel in range(3):
        avg = convolve2d(self.rgb[channel], kernel, mode = "same", boundary = "fill", fillvalue = 0.)/nnn
        image[channel] = np.where(mask, avg, self.rgb[channel])
    else:
      nnn = convolve2d(np.ones_like(self.rgb[0]), kernel, mode = "same", boundary = "fill", fillvalue = 0.)
      for channel, letter in ((0, "R"), (1, "G"), (2, "B")):
        if letter in channels:
          avg = convolve2d(self.rgb[channel], kernel, mode = "same", boundary = "fill", fillvalue = 0.)/nnn
          image[channel] = np.where(self.rgb[channel] > ratio*avg, avg, self.rgb[channel])
    return None if inplace else self.newImage(self, image, meta)

  # Image resizing & crop.

  def resize(self, width, height, resample = LANCZOS, inplace = True, meta = "self"):
    """Resize image to width 'width' and height 'height' using resampling method 'resample'
       (either NEAREST, BILINEAR, BICUBIC, LANCZOS, BOX or HAMMING). Also set new meta-data
       'meta' (same as the original if meta = "self"). Update the object if 'inplace' is True
       or return a new instance if 'inplace' is False."""
    if width < 1 or width > 32768: raise ValueError("Error, width must be >= 1 and <= 32768 pixels.")
    if height < 1 or height > 32768: raise ValueError("Error, height must be >= 1 and <= 32768 pixels.")
    if width*height > 2**26: raise ValueError("Error, can not resize to > 64 Mpixels.")
    if not resample in [NEAREST, BILINEAR, BICUBIC, LANCZOS, BOX, HAMMING]: raise ValueError("Error, invalid resampling method.")
    image = np.empty((3, height, width), dtype = IMGTYPE)
    for channel in range(3): # Resize each channel using PIL.
      PILchannel = PILImage.fromarray(np.float32(self.rgb[channel]), "F").resize((width, height), resample) # Convert to np.float32 while resizing.
      image[channel] = np.asarray(PILchannel, dtype = IMGTYPE)
    if inplace:
      self.rgb = image
      if meta != "self": self.meta = meta
      return None
    else:
      if meta == "self": meta = deepcopy(self.meta)
      return self.newImage(self, image, meta)

  def rescale(self, scale, resample = LANCZOS, inplace = True, meta = "self"):
    """Rescale image by a factor 'scale' using resampling method 'resample' (either NEAREST,
       BILINEAR, BICUBIC, LANCZOS, BOX or HAMMING). Also set new meta-data 'meta' (same as
       the original if meta = "self"). Update the object if 'inplace' is True or return a new
       instance if 'inplace' is False."""
    if scale <= 0. or scale > 16.: raise ValueError("Error, scale must be > 0 and <= 16.")
    width, height = self.size()
    newwidth, newheight = int(round(scale*width)), int(round(scale*height))
    return self.resize(newwidth, newheight, resample, inplace, meta)

  def crop(self, xmin, xmax, ymin, ymax, inplace = True, meta = "self"):
    """Crop image from x = xmin to x = xmax and from y = ymin to y = ymax.
       Also set new meta-data 'meta' (same as the original if meta = "self").
       Update the object if 'inplace' is True or return a new instance if 'inplace' is False."""
    width, height = self.size()
    xmin = max(int(xmin), 0)
    xmax = min(int(xmax), width)
    ymin = max(int(ymin), 0)
    ymax = min(int(ymax), height)
    if xmax <= xmin: raise ValueError("Error, xmax <= xmin.")
    if ymax <= ymin: raise ValueError("Error, ymax <= ymin.")
    if inplace:
      self.rgb = self.rgb[:, ymin:ymax, xmin:xmax]
      if meta != "self": self.meta = meta
      return None
    else:
      if meta == "self": meta = deepcopy(self.meta)
      return self.newImage(self, self.rgb[:, ymin:ymax, xmin:xmax], meta)

# Special images and shortcuts.

def black_image(width, height, meta = {}):
  """Return a black image with width 'width', height 'height', and meta-data 'meta'."""
  return Image(np.zeros((3, height, width), dtype = IMGTYPE), meta)

def white_image(width, height, meta = {}):
  """Return a white image with width 'width', height 'height', and meta-data 'meta'."""
  return Image(np.ones((3, height, width), dtype = IMGTYPE), meta)

def load_image(filename, meta = "self"):
  """Return the image in file 'filename' and set meta-data 'meta'."""
  image = Image()
  image.load(filename, meta)
  return image
