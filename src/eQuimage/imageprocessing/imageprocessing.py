# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 12.0 / 2023.1127

"""Image processing tools."""

import re
import os
import numpy as np
import matplotlib.pyplot as plt
import imageio.v3 as iio
from PIL import Image as PILImage
from scipy.signal import convolve2d
from .utils import failsafe_divide, lookup
from .stretchfunctions import midtone_stretch_function

imgtype = np.float32 # Data type used for images (either np.float32 or np.float64).

NEAREST  = PILImage.Resampling.NEAREST # Resampling methods, imported from PIL.
BILINEAR = PILImage.Resampling.BILINEAR
BICUBIC  = PILImage.Resampling.BICUBIC
LANCZOS  = PILImage.Resampling.LANCZOS
BOX      = PILImage.Resampling.BOX
HAMMING  = PILImage.Resampling.HAMMING

rgbluminance = imgtype((0.3, 0.6, 0.1)) # Weight of the R, G, B channels in the luminance.

def get_rgb_luminance():
  """Return the RGB components of the luminance channel."""
  return tuple(rgbluminance)

def set_rgb_luminance(rgb):
  """Set the RGB components 'rgb' of the luminance channel."""
  global rgbluminance
  rgbluminance = imgtype(rgb)

class Image:
  """Image class. The RGB components are stored as floats in the range [0, 1]."""

  CUTOFF = 1.e-12

  def __init__(self, image = None, description = ""):
    """Initialize object with RGB image 'image' and description 'description'."""
    self.image = imgtype(image) if image is not None else None
    self.description = description

  @classmethod
  def newImage(cls, self, image = None, description = ""):
    """Return a new instance with RGB image 'image' and description 'description'."""
    return cls(image = image, description = description)

  def is_valid(self):
    """Return True if the object contains a valid image, False otherwise."""
    if not isinstance(self.image, np.ndarray): return False
    if self.image.ndim != 3: return False
    if self.image.shape[0] != 3: return False
    if self.image.dtype != imgtype: return False
    return True

  def load(self, filename, description = None):
    """Load file 'filename' and set description 'description'. Return meta data (including exif) if available."""
    if description is None: description = self.description
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
        image = np.moveaxis(image, 0, -1) # instead of (height, width, channels) for FITS files.
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
      image = imgtype(image/255)
    elif dtype == "uint16":
      bpc = 16
      image = imgtype(image/65535)
    elif dtype in ["float32", ">f4", "<f4"]: # Assumed normalized in [0, 1] !
      bpc = 32
      image = imgtype(image)
    elif dtype in ["float64", ">f8", "<f8"]: # Assumed normalized in [0, 1] !
      bpc = 64
      image = imgtype(image)
    else:
      raise TypeError(f"Error, image data type {dtype} is not supported.")
    print(f"Bit depth per channel = {bpc}.")
    print(f"Bit depth per pixel = {nc*bpc}.")
    if nc == 1: # Assume single channel images are monochrome.
      image = np.repeat(image[:, :, np.newaxis], 3, axis = 2)
    image = np.moveaxis(image, -1, 0) # Move last (channel) axis to leading position.
    for ic in range(nc):
      print(f"Channel #{ic}: minimum = {image[ic].min():.3f}, maximum = {image[ic].max():.3f}.")
    if nc == 4: # Assume fourth channel is transparency.
      image = image[0:3]*image[3]
    self.image = np.ascontiguousarray(image)
    self.description = description
    meta = iio.immeta(filename)
    meta["colordepth"] = bpc # Add color depth.
    #print(f"Meta = {meta}.")
    return meta

  def set_description(self, description):
    """Set description 'description'."""
    self.description = description

  def size(self):
    """Return the image width and height in pixels."""
    return self.image.shape[2], self.image.shape[1]

  def value(self):
    """Return the value = max(RGB)."""
    return self.image.max(axis = 0)

  def luminance(self):
    """Return the luminance."""
    return rgbluminance[0]*self.image[0]+rgbluminance[1]*self.image[1]+rgbluminance[2]*self.image[2]

  def rgb8(self):
    """Return the RGB components as 8 bits integers in the range [0, 255]."""
    data = np.clip(self.image*255, 0, 255)
    return np.moveaxis(np.rint(data).astype("uint8"), 0, -1)

  def rgb16(self):
    """Return the RGB components as 16 bits integers in the range [0, 65535]."""
    data = np.clip(self.image*65535, 0, 65535)
    return np.moveaxis(np.rint(data).astype("uint16"), 0, -1)

  def luminance16(self):
    """Return the luminance as 16 bits integers in the range [0, 65535]."""
    data = np.clip(self.luminance()*65535, 0, 65535)
    return np.rint(data).astype("uint16")

  def draw(self, ax):
    """Draw the image in matplotlib axes 'ax'."""
    ax.imshow(self.rgb8())

  def save(self, filename, depth = 8, single_channel_gray_scale = True):
    """Save image in file 'filename' with color depth 'depth' (bits/channel).
       The file format is chosen according to the 'filename' extension:
        - .png : PNG file with depth = 8 or 16 bits/channel.
        - .tif, .tiff : TIFF file with depth = 8 or 16 bits/channel.
        - .fit/.fits/.fts : FITS file with 32 bits (floats)/channel (irrespective of depth).
       The image is saved as a single channel gray scale if all RGB channels are the same and 'single_channel_gray_scale' is True."""
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
      #image = np.clip(self.image, 0, 1)
      #print(f"Color depth = 24 bits (floats).")
      #if is_gray_scale: image = image[0, :, :]
      #iio.imwrite("file:test.fit", image, plugin = "FITS")
    else:
      raise ValueError("Error, file extension must be .png or .tif/.tiff.") #, .tif/.tiff or .fit/.fits/.fts.")

  def clone(self, description = None):
    """Return a clone of the image with new description 'description' (same as the original if None)."""
    if description is None: description = self.description
    return self.newImage(self, self.image.copy(), description)

  def copy_from(self, source):
    """Copy the RGB data from 'source'."""
    self.image = source.image.copy()

  def statistics(self):
    """Compute image statistics for channels "R" (red), "G" (green), "B" (blue), "V" (value) and "L" (luminance).
       Return stats[key] for key in ("R", "G", "B", "V", "L"), with:
         - stats[key].minimum = minimum value in channel key.
         - stats[key].maximum = maximum value in channel key.
         - stats[key].median  = median  value in channel key (excluding pixels <= 0 and >= 1).
         - stats[key].zerocount = number of pixels <= 0 in channel key.
         - stats[key].oorcount  = number of pixels  > 1 in channel key (out-of-range)."""
    class Container: pass # An empty container class.
    stats = {}
    for key in ("R", "G", "B", "V", "L"):
      if key == "V":
        channel = self.value()
      elif key == "L":
        channel = self.luminance()
      else:
        channel = self.image[{"R": 0, "G": 1, "B": 2}[key]]
      stats[key] = Container()
      stats[key].minimum = channel.min()
      stats[key].maximum = channel.max()
      mask = (channel > 0) & (channel < 1)
      if np.any(mask):
        stats[key].percentiles = np.percentile(channel[mask], [25., 50., 75.])
        stats[key].median = stats[key].percentiles[1]
      else:
        stats[key].percentiles = None
        stats[key].median = None
      stats[key].zerocount = np.sum(channel <= 0)
      stats[key].outcount = np.sum(channel > 1)
    return stats

  def histograms(self, nbins = 256):
    """Return image histograms as a tuple (edges, counts), where edges(nbins) are the bin edges and
       counts(5, nbins) are the bin counts for the red, green, blue, value and luminance channels.
       'nbins' is the number of bins in the range [0, 1]."""
    minimum = min(0, self.image.min())
    maximum = max(1, self.image.max())
    nbins = int(round(nbins*(maximum-minimum)))
    hists = np.empty((5, nbins), dtype = imgtype)
    for channel in range(3):
      hists[channel], edges = np.histogram(self.image[channel], bins = nbins, range = (minimum, maximum), density = False)
    hists[3], edges = np.histogram(self.value(), bins = nbins, range = (minimum, maximum), density = False)
    hists[4], edges = np.histogram(self.luminance(), bins = nbins, range = (minimum, maximum), density = False)
    return edges, hists

  def is_out_of_range(self):
    """Return True if the image is out-of-range (values < 0 or > 1 in any channel), False otherwise."""
    return np.any(self.image < 0) or np.any(self.image > 1)

  def gray_scale(self, inplace = True, description = None):
    """Convert to gray scale and set new description 'description' (same as the original if None).
       Update the object if 'inplace' is True or return a new instance if False."""
    if inplace:
      if description is not None: self.description = description
      image = self.image
    else:
      if description is None: description = self.description
      image = self.image.copy()
    image[0:3] = self.luminance()
    return None if inplace else self.newImage(self, image, description)

  def is_gray_scale(self):
    """Return True if the image is a gray scale (same RGB channels), False otherwise."""
    return np.all(self.image[0] == self.image[1]) and np.all(self.image[0] == self.image[2])

  def clip_shadows_highlights(self, shadow = None, highlight = None, channels = "V", inplace = True, description = None):
    """Clip channels 'channels' below shadow level 'shadow' and above highlight level 'highglight', and
       remap [shadow, highglight] to [0, 1]. 'channels' can be "V" (value), "L" (luminance) or any combination of "R" (red),
       "G" (green), and "B" (blue). shadow = min(channel) for each channel if 'shadow' is none, and highglight = max(channel)
       for each channel if 'highglight' is None.  Also set new description 'description' (same as the original if None).
       Update the object if 'inplace' is True or return a new instance if 'inplace' is False."""
    if highlight is not None:
      if highlight <= shadow: raise ValueError("Error, highlight must be > shadow.")
    if inplace:
      if description is not None: self.description = description
      image = self.image
    else:
      if description is None: description = self.description
      image = self.image.copy()
    if channels in ["V", "L"]:
      channel = self.value() if channels == "V" else self.luminance()
      if shadow is None: shadow = max(channel.min(), 0)
      if highlight is None: highlight = channel.max()
      clipped = np.clip(channel, shadow, highlight)
      expanded = np.interp(clipped, (shadow, highlight), (0, 1))
      image[:] = np.where(abs(channel) > self.CUTOFF, failsafe_divide(image*expanded, channel), 0)
    else:
      for channel, letter in ((0, "R"), (1, "G"), (2, "B")):
        if letter in channels:
          shadow_ = max(image[channel].min(), 0) if shadow is None else shadow
          highlight_ = image[channel].max() if highlight is None else highlight
          clipped = np.clip(image[channel], shadow_, highlight_)
          image[channel] = np.interp(clipped, (shadow_, highlight_), (0, 1))
    return None if inplace else self.newImage(self, image, description)

  def set_dynamic_range(self, fr = None, to = (0, 1), channels = "L", inplace = True, description = None):
    """Remap 'channels' from range 'fr' (a tuple) to range 'to' (a tuple, default (0, 1)).
       'channels' can be "V" (value), "L" (luminance) or any combination of "R" (red) "G" (green), and "B" (blue).
       fr = (min(channel), max(channel)) for each channel if 'fr' is None. Also set new description 'description'
       (same as the original if None). Update the object if 'inplace' is True or return a new instance
       if 'inplace' is False."""
    if fr is not None:
      if fr[1] <= fr[0]: raise ValueError("Error, fr[1] must be > fr[0].")
    if to[1] <= to[0]: raise ValueError("Error, to[1] must be > to[0].")
    if inplace:
      if description is not None: self.description = description
      image = self.image
    else:
      if description is None: description = self.description
      image = self.image.copy()
    if channels in ["V", "L"]:
      channel = self.value() if channels == "V" else self.luminance()
      if fr is None: fr = (channel.min(), channel.max())
      expanded = np.maximum(np.interp(channel, fr, to), 0)
      image[:] = np.where(abs(channel) > self.CUTOFF, failsafe_divide(image*expanded, channel), expanded)
    else:
      for channel, letter in ((0, "R"), (1, "G"), (2, "B")):
        if letter in channels:
          fr_ = (image[channel].min(), image[channel].max()) if fr is None else fr
          image[channel] = np.maximum(np.interp(image[channel], fr_, to), 0)
    return None if inplace else self.newImage(self, image, description)

  def gamma_correction(self, gamma, channels = "L", inplace = True, description = None):
    """Apply gamma correction with exponent 'gamma' to channels 'channels'.
       'channels' can be "V" (value), "L" (luminance) or any combination of "R" (red) "G" (green), and "B" (blue).
       Also set new description 'description' (same as the original if None). Update the object if 'inplace'
       is True or return a new instance if 'inplace' is False."""
    if gamma <= 0: raise ValueError("Error, gamma must be >= 0.")
    if inplace:
      if description is not None: self.description = description
      image = self.image
    else:
      if description is None: description = self.description
      image = self.image.copy()
    if channels in ["V", "L"]:
      channel = self.value() if channels == "V" else self.luminance()
      clipped = np.clip(channel, 0, 1)
      corrected = clipped**gamma
      image[:] = np.where(abs(channel) > self.CUTOFF, failsafe_divide(image*corrected, channel), 0)
    else:
      for channel, letter in ((0, "R"), (1, "G"), (2, "B")):
        if letter in channels:
          clipped = np.clip(image[channel], 0, 1)
          image[channel] = clipped**gamma
    return None if inplace else self.newImage(self, image, description)

  def midtone_correction(self, midtone = 0.5, channels = "L", inplace = True, description = None):
    """Apply midtone correction with midtone 'midtone' to channels 'channels'.
       'channels' can be "V" (value), "L" (luminance) or any combination of "R" (red) "G" (green), and "B" (blue).
       Also set new description 'description' (same as the original if None). Update the object if  'inplace'
       is True or return a new instance if 'inplace' is False."""
    if midtone <= 0: raise ValueError("Error, midtone must be >= 0.")
    if inplace:
      if description is not None: self.description = description
      image = self.image
    else:
      if description is None: description = self.description
      image = self.image.copy()
    if channels in ["V", "L"]:
      channel = self.value() if channels == "V" else self.luminance()
      clipped = np.clip(channel, 0, 1)
      corrected = midtone_stretch_function(clipped, midtone)
      image[:] = np.where(abs(channel) > self.CUTOFF, failsafe_divide(image*corrected, channel), 0)
    else:
      for channel, letter in ((0, "R"), (1, "G"), (2, "B")):
        if letter in channels:
          clipped = np.clip(image[channel], 0, 1)
          image[channel] = midtone_stretch_function(clipped, midtone)
    return None if inplace else self.newImage(self, image, description)

  def midtone_correction_lookup(self, midtone = 0.5, channels = "L", inplace = True, description = None, nlut = 131072):
    """Apply midtone correction with midtone 'midtone' to channels 'channels'.
       'channels' can be "V" (value), "L" (luminance) or any combination of "R" (red) "G" (green), and "B" (blue).
       Also set new description 'description' (same as the original if None). Update the object if  'inplace'
       is True or return a new instance if 'inplace' is False.
       This method uses a look-up table with linear interpolation between 'nlut' elements to apply the stretch function
       to the channel(s); It shall be faster than midtone_correction(...), especially for large images."""
    if midtone <= 0: raise ValueError("Error, midtone must be >= 0.")
    if inplace:
      if description is not None: self.description = description
      image = self.image
    else:
      if description is None: description = self.description
      image = self.image.copy()
    # Build the look-up table.
    xlut = np.linspace(0, 1, nlut, dtype = imgtype)
    ylut = midtone_stretch_function(xlut, midtone)
    slut = (ylut[1:]-ylut[:-1])/(xlut[1:]-xlut[:-1]) # Slopes.      
    if channels in ["V", "L"]:
      channel = self.value() if channels == "V" else self.luminance()
      clipped = np.clip(channel, 0, 1)
      corrected = lookup(clipped, xlut, ylut, slut, nlut)
      image[:] = np.where(abs(channel) > self.CUTOFF, failsafe_divide(image*corrected, channel), 0)
    else:
      for channel, letter in ((0, "R"), (1, "G"), (2, "B")):
        if letter in channels:
          clipped = np.clip(image[channel], 0, 1)
          image[channel] = lookup(clipped, xlut, ylut, slut, nlut)
    return None if inplace else self.newImage(self, image, description)
  
  def generalized_stretch(self, stretch_function, params, channels = "L", inplace = True, description = None):
    """Stretch histogram of channels 'channels' with an arbitrary stretch function 'stretch_function' parametrized
       by 'params'. 'stretch_function(input, params)' shall return the output levels for an array of input
       levels 'input'. 'channels' can be "V" (value), "L" (luminance) or any combination of "R" (red) "G" (green),
       and "B" (blue). Also set new description 'description' (same as the original if None). Update the object if
       'inplace' is True or return a new instance if 'inplace' is False."""
    if inplace:
      if description is not None: self.description = description
      image = self.image
    else:
      if description is None: description = self.description
      image = self.image.copy()
    if channels in ["V", "L"]:
      channel = self.value() if channels == "V" else self.luminance()
      clipped = np.clip(channel, 0, 1)
      corrected = imgtype(stretch_function(clipped, params))
      image[:] = np.where(abs(channel) > self.CUTOFF, failsafe_divide(image*corrected, channel), 0)
    else:
      for channel, letter in ((0, "R"), (1, "G"), (2, "B")):
        if letter in channels:
          clipped = np.clip(image[channel], 0, 1)
          image[channel] = imgtype(stretch_function(clipped, params))
    return None if inplace else self.newImage(self, image, description)
  
  def generalized_stretch_lookup(self, stretch_function, params, channels = "L", inplace = True, description = None, nlut = 131072):
    """Stretch histogram of channels 'channels' with an arbitrary stretch function 'stretch_function' parametrized
       by 'params'. 'stretch_function(input, params)' shall return the output levels for an array of input
       levels 'input'. 'channels' can be "V" (value), "L" (luminance) or any combination of "R" (red) "G" (green),
       and "B" (blue). Also set new description 'description' (same as the original if None). Update the object if
       'inplace' is True or return a new instance if 'inplace' is False.
       This method uses a look-up table with linear interpolation between 'nlut' elements to apply the stretch function
       to the channel(s); It shall be much faster than generalized_stretch(...) and may be more appropriate when the
       strech function is expensive."""
    if inplace:
      if description is not None: self.description = description
      image = self.image
    else:
      if description is None: description = self.description
      image = self.image.copy()
    # Build the look-up table.
    xlut = np.linspace(0, 1, nlut, dtype = imgtype)
    ylut = imgtype(stretch_function(xlut, params))
    slut = (ylut[1:]-ylut[:-1])/(xlut[1:]-xlut[:-1]) # Slopes.
    if channels in ["V", "L"]:
      channel = self.value() if channels == "V" else self.luminance()
      clipped = np.clip(channel, 0, 1)
      corrected = lookup(clipped, xlut, ylut, slut, nlut)
      image[:] = np.where(abs(channel) > self.CUTOFF, failsafe_divide(image*corrected, channel), 0)
    else:
      for channel, letter in ((0, "R"), (1, "G"), (2, "B")):
        if letter in channels:
          clipped = np.clip(image[channel], 0, 1)
          image[channel] = lookup(clipped, xlut, ylut, slut, nlut)
    return None if inplace else self.newImage(self, image, description)  

  def color_balance(self, red = 1, green = 1, blue = 1, inplace = True, description = None):
    """Multiply the red channel by 'red', the green channel by 'green', and the blue channel by 'blue'.
       Also set new description 'description' (same as the original if None). Update the object if 'inplace'
       is True or return a new instance if 'inplace' is False."""
    if red < 0: raise ValueError("Error, red must be >= 0.")
    if green < 0: raise ValueError("Error, green must be >= 0.")
    if blue < 0: raise ValueError("Error, blue must be >= 0.")
    if inplace:
      if description is not None: self.description = description
      image = self.image
    else:
      if description is None: description = self.description
      image = self.image.copy()
    if red   != 1: image[0] *= red
    if green != 1: image[1] *= green
    if blue  != 1: image[2] *= blue
    return None if inplace else self.newImage(self, image, description)

  def sharpen(self, inplace = True, description = None):
    """Apply a sharpening convolution filter and  set new description 'description'
       (same as the original if None). Update the object if 'inplace' is True or
       return a new instance if 'inplace' is False."""
    if inplace:
      if description is not None: self.description = description
      image = self.image
    else:
      if description is None: description = self.description
      image = self.image.copy()
    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]], dtype = imgtype)
    for channel in range(3):
      image[channel] = convolve2d(image[channel], kernel, mode = "same", boundary = "fill", fillvalue = 0)
    return None if inplace else self.newImage(self, image, description)

  def remove_hot_pixels(self, ratio = 2, channels = "L", inplace = True, description = None):
    """Remove hot pixels in channels 'channels'. 'channels' can be "V" (value), "L" (luminance) or any
       combination of "R" (red) "G" (green), and "B" (blue). All pixels in a channel whose level is greater
       than 'ratio' times the average of their 8 nearest neighbors are replaced by this average.
       Also set new description 'description' (same as the original if None). Update the object if 'inplace'
       is True or return a new instance if 'inplace' is False."""
    if ratio <= 0: raise ValueError("Error, ratio must be > 0.")
    if inplace:
      if description is not None: self.description = description
      image = self.image
    else:
      if description is None: description = self.description
      image = self.image.copy()
    kernel = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype = imgtype)
    if channels in ["V", "L"]:
      channel = self.value() if channels == "V" else self.luminance()
      nnn = convolve2d(np.ones_like(channel), kernel, mode = "same", boundary = "fill", fillvalue = 0)
      avg = convolve2d(channel, kernel, mode = "same", boundary = "fill", fillvalue = 0)/nnn
      mask = (channel > ratio*avg)
      for channel in range(3):
        avg = convolve2d(image[channel], kernel, mode = "same", boundary = "fill", fillvalue = 0)/nnn
        image[channel] = np.where(mask, avg, image[channel])
    else:
      nnn = convolve2d(np.ones_like(image[0]), kernel, mode = "same", boundary = "fill", fillvalue = 0)
      for channel, letter in ((0, "R"), (1, "G"), (2, "B")):
        if letter in channels:
          avg = convolve2d(image[channel], kernel, mode = "same", boundary = "fill", fillvalue = 0)/nnn
          image[channel] = np.where(image[channel] > ratio*avg, avg, image[channel])
    return None if inplace else self.newImage(self, image, description)

  def resize(self, width, height, resample = LANCZOS, inplace = True, description = None):
    """Resize image to width 'width' and height 'height' using resampling method 'resample'
       (either NEAREST, BILINEAR, BICUBIC, LANCZOS, BOX or HAMMING). Also set new description
       'description' (same as the original if None). Update the object if 'inplace' is True
       or return a new instance if 'inplace' is False."""
    if width < 1 or width > 32768: raise ValueError("Error, width must be >= 1 and <= 32768 pixels.")
    if height < 1 or height > 32768: raise ValueError("Error, height must be >= 1 and <= 32768 pixels.")
    if width*height > 2**26: raise ValueError("Error, can not resize to > 64 Mpixels.")
    if not resample in [NEAREST, BILINEAR, BICUBIC, LANCZOS, BOX, HAMMING]: raise ValueError("Error, invalid resampling method.")
    image = np.empty((3, height, width), dtype = imgtype)
    for channel in range(3): # Resize each channel using PIL.
      PILchannel = PILImage.fromarray(np.float32(self.image[channel]), "F").resize((width, height), resample) # Convert to np.float32 while resizing.
      image[channel] = np.asarray(PILchannel, dtype = imgtype)
    if inplace:
      self.image = image
      if description is not None: self.description = description
      return None
    else:
      if description is None: description = self.description
      return self.newImage(self, image, description)

  def rescale(self, scale, resample = LANCZOS, inplace = True, description = None):
    """Rescale image by a factor 'scale' using resampling method 'resample' (either NEAREST,
       BILINEAR, BICUBIC, LANCZOS, BOX or HAMMING). Also set new description 'description'
       (same as the original if None). Update the object if 'inplace' is True or return a new
       instance if 'inplace' is False."""
    if scale <= 0 or scale > 16: raise ValueError("Error, scale must be > 0 and <= 16.")
    width, height = self.size()
    newwidth, newheight = int(round(scale*width)), int(round(scale*height))
    return self.resize(newwidth, newheight, resample, inplace, description)
