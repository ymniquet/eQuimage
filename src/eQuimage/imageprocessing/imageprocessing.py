# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2023.11.27

"""Image processing tools."""

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image as PILImage
from scipy.signal import convolve2d
from .helpers import failsafe_divide, midtone_transfer_function

rgbluminance = (0.3, 0.6, 0.1)

def get_rgb_luminance():
  """Return the RGB components of the luminance channel."""
  return rgbluminance

def set_rgb_luminance(rgb):
  """Set the RGB components 'rgb' of the luminance channel."""
  global rgbluminance
  rgbluminance = tuple(rgb)

class Image:
  """Image class. The RGB components are stored as floats in the range [0., 1.]."""

  CUTOFF = 1.e-12

  def __init__(self, image = None, description = ""):
    """Initialize object with RGB image 'image' and description 'description'."""
    self.image = image
    self.description = description

  @classmethod
  def newImage(cls, self, image = None, description = ""):
    """Return a new instance with RGB image 'image' and description 'description'."""
    return cls(image = image, description = description)

  def load(self, filename, description = None):
    """Load file 'filename' and set description 'description'. Return exif data if available."""
    if description is None: description = self.description
    img = PILImage.open(filename)
    img.load()
    exif = img.getexif()
    data = np.moveaxis(np.asarray(img, dtype = float), -1, 0)
    self.image = data[0:3]/255.
    self.description = description
    return exif

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
    data = np.clip(self.image*255., 0., 255.)
    return np.moveaxis(np.rint(data).astype("uint8"), 0, -1)

  def luminance16(self):
    """Return the luminance as 16 bits signed integers in the range [0, 65535]."""
    data = np.clip(self.luminance()*65535., 0., 65535.)
    return np.rint(data).astype("uint32")

  def draw(self, ax):
    """Draw the image in matplotlib axes 'ax'."""
    ax.imshow(self.rgb8())

  def save(self, filename, exif = None):
    """Save the image in file 'filename' with exif data 'exif' (if not None)."""
    img = PILImage.fromarray(self.rgb8(), "RGB")
    img.save(filename, exif = exif)

  def save_gray_scale(self, filename, exif = None):
    """Save the luminance in file 'filename' with exif data 'exif' (if not None)."""
    img = PILImage.fromarray(self.luminance16(), "I")
    img.save(filename, exif = exif)

  def clone(self, description = None):
    """Return a clone of the image with new description 'description' (same as the original if None)."""
    if description is None: description = self.description
    return self.newImage(self, self.image.copy(), description)

  def copy_from(self, reference):
    """Copy the RGB data from 'reference'."""
    self.image = reference.image.copy()

  def statistics(self):
    """Compute image statistics for channels "R" (red), "G" (green), "B" (blue), "V" (value) and "L" (luminance).
       Return stats[key] for key in ("R", "G", "B", "V", "L"), with:
         - stats[key].minimum = minimum value in channel key.
         - stats[key].maximum = maximum value in channel key.
         - stats[key].median  = median  value in channel key (excluding pixels <= 0).
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
      stats[key].median = np.median(channel[channel > 0.])
      stats[key].zerocount = np.sum(channel <= 0.)
      stats[key].outcount = np.sum(channel > 1.)
    return stats

  def histograms(self, nbins = 256):
    """Return image histograms as a (5, nbins) array (red, green, blue, value and luminance channels).
       'nbins' is the number of bins in each channel."""
    maximum = max(1., self.image.max())
    hists = np.empty((5, nbins))
    for channel in range(3):
      hists[channel], edges = np.histogram(self.image[channel], bins = nbins, range = (0., maximum), density = False)
    hists[3], edges = np.histogram(self.value(), bins = nbins, range = (0., maximum), density = False)
    hists[4], edges = np.histogram(self.luminance(), bins = nbins, range = (0., maximum), density = False)
    return edges, hists

  def is_out_of_range(self):
    """Return True if the image is out-of-range (values < 0 or > 1 in any channel), False otherwise."""
    return np.any(self.image < 0.) or np.any(self.image > 1.)

  def gray_scale(self, inplace = True, description = None):
    """Convert to gray scale and set new description 'description' (same as the original if None).
       Update the object if 'inplace' is True or return a new instance if False."""
    if description is None: description = self.description
    image = self.image if inplace else self.image.copy()
    image[0:3] = self.luminance()
    return None if inplace else self.newImage(self, image, description)

  def is_gray_scale(self):
    """Return True if the image is a gray scale (same RGB channels), False otherwise."""
    return np.all(self.image[0] == self.image[1]) and np.all(self.image[0] == self.image[2])

  def clip_shadows_highlights(self, shadow = None, highlight = None, channels = "V", inplace = True, description = None):
    """Clip channels 'channels' below shadow level 'shadow' and above highlight level 'highglight', and
       remap [shadow, highglight] to [0., 1.]. 'channels' can be "V" (value), "L" (luminance) or any combination of "R" (red),
       "G" (green), and "B" (blue). shadow = min(channel) for each channel if 'shadow' is none, and highglight = max(channel)
       for each channel if 'highglight' is None.  Also set new description 'description' (same as the original if None).
       Update the object if 'inplace' is True or return a new instance if 'inplace' is False."""
    if shadow is not None:
      if shadow < 0.: raise ValueError("Error, shadow must be >= 0.")
    if highlight is not None:
      if highlight <= shadow: raise ValueError("Error, highlight must be > shadow.")
    if description is None: description = self.description
    image = self.image if inplace else self.image.copy()
    if channels in ["V", "L"]:
      channel = self.value() if channels == "V" else self.luminance()
      if shadow is None: shadow = max(channel.min(), 0.)
      if highlight is None: highlight = channel.max()
      clipped = np.clip(channel, shadow, highlight)
      expanded = np.interp(clipped, (shadow, highlight), (0., 1.))
      image[:] = np.where(abs(channel) > self.CUTOFF, failsafe_divide(image*expanded, channel), 0.)
    else:
      for channel, letter in ((0, "R"), (1, "G"), (2, "B")):
        if letter in channels:
          shadow_ = max(image[channel].min(), 0.) if shadow is None else shadow
          highlight_ = image[channel].max() if highlight is None else highlight
          clipped = np.clip(image[channel], shadow_, highlight_)
          image[channel] = np.interp(clipped, (shadow_, highlight_), (0., 1.))
    return None if inplace else self.newImage(self, image, description)

  def set_dynamic_range(self, fr = None, to = (0., 1.), channels = "L", inplace = True, description = None):
    """Remap 'channels' from range 'fr' (a tuple) to range 'to' (a tuple, default (0., 1.)).
       'channels' can be "V" (value), "L" (luminance) or any combination of "R" (red) "G" (green), and "B" (blue).
       fr = (min(channel), max(channel)) for each channel if 'fr' is None. Also set new description 'description'
       (same as the original if None). Update the object if 'inplace' is True or return a new instance
       if 'inplace' is False."""
    if fr is not None:
      if fr[1] <= fr[0]: raise ValueError("Error, fr[1] must be > fr[0].")
    if to[1] <= to[0]: raise ValueError("Error, to[1] must be > to[0].")
    if description is None: description = self.description
    image = self.image if inplace else self.image.copy()
    if channels in ["V", "L"]:
      channel = self.value() if channels == "V" else self.luminance()
      if fr is None: fr = (channel.min(), channel.max())
      expanded = np.maximum(np.interp(channel, fr, to), 0.)
      image[:] = np.where(abs(channel) > self.CUTOFF, failsafe_divide(image*expanded, channel), expanded)
    else:
      for channel, letter in ((0, "R"), (1, "G"), (2, "B")):
        if letter in channels:
          fr_ = (image[channel].min(), image[channel].max()) if fr is None else fr
          image[channel] = np.maximum(np.interp(image[channel], fr_, to), 0.)
    return None if inplace else self.newImage(self, image, description)

  def gamma_correction(self, gamma, channels = "L", inplace = True, description = None):
    """Apply gamma correction with exponent 'gamma' to channels 'channels'.
       'channels' can be "V" (value), "L" (luminance) or any combination of "R" (red) "G" (green), and "B" (blue).
       Also set new description 'description' (same as the original if None). Update the object if 'inplace'
       is True or return a new instance if 'inplace' is False."""
    if gamma <= 0.: raise ValueError("Error, gamma must be >= 0.")
    if description is None: description = self.description
    image = self.image if inplace else self.image.copy()
    if channels in ["V", "L"]:
      channel = self.value() if channels == "V" else self.luminance()
      corrected = channel**gamma
      image[:] = np.where(abs(channel) > self.CUTOFF, failsafe_divide(image*corrected, channel), 0.)
    else:
      for channel, letter in ((0, "R"), (1, "G"), (2, "B")):
        if letter in channels:
          image[channel] = image[channel]**gamma
    return None if inplace else self.newImage(self, image, description)

  def midtone_correction(self, midtone = 0.5, channels = "L", inplace = True, description = None):
    """Apply midtone transfer function with midtone 'midtone' to channels 'channels'.
       'channels' can be "V" (value), "L" (luminance) or any combination of "R" (red) "G" (green), and "B" (blue).
       Also set new description 'description' (same as the original if None). Update the object if  'inplace'
       is True or return a new instance if 'inplace' is False."""
    if midtone <= 0.: raise ValueError("Error, midtone must be >= 0.")
    if description is None: description = self.description
    image = self.image if inplace else self.image.copy()
    if channels in ["V", "L"]:
      channel = self.value() if channels == "V" else self.luminance()
      clipped = np.clip(channel, 0., 1.)
      corrected = midtone_transfer_function(clipped, midtone)
      image[:] = np.where(abs(channel) > self.CUTOFF, failsafe_divide(image*corrected, channel), 0.)
    else:
      for channel, letter in ((0, "R"), (1, "G"), (2, "B")):
        if letter in channels:
          clipped = np.clip(image[channel], 0., 1.)
          image[channel] = midtone_transfer_function(clipped, midtone)
    return None if inplace else self.newImage(self, image, description)

  def color_balance(self, red = 1., green = 1., blue = 1., inplace = True, description = None):
    """Multiply the red channel by 'red', the green channel by 'green', and the blue channel by 'blue'.
       Also set new description 'description' (same as the original if None). Update the object if 'inplace'
       is True or return a new instance if 'inplace' is False."""
    if red < 0.: raise ValueError("Error, red must be >= 0.")
    if green < 0.: raise ValueError("Error, green must be >= 0.")
    if blue < 0.: raise ValueError("Error, blue must be >= 0.")
    if description is None: description = self.description
    image = self.image if inplace else self.image.copy()
    if red   != 1.: image[0] *= red
    if green != 1.: image[1] *= green
    if blue  != 1.: image[2] *= blue
    return None if inplace else self.newImage(self, image, description)

  def sharpen(self, inplace = True, description = None):
    """Apply a sharpening convolution filter and  set new description 'description'
       (same as the original if None). Update the object if 'inplace' is True or
       return a new instance if 'inplace' is False."""
    if description is None: description = self.description
    image = self.image if inplace else self.image.copy()
    kernel = np.array([[-1., -1., -1.], [-1., 9., -1.], [-1., -1., -1.]])
    for channel in range(3):
      image[channel] = convolve2d(image[channel], kernel, mode = "same", boundary = "fill", fillvalue = 0.)
    return None if inplace else self.newImage(self, image, description)

  def remove_hot_pixels(self, ratio = 2., channels = "L", inplace = True, description = None):
    """Remove hot pixels in channels 'channels'. 'channels' can be "V" (value), "L" (luminance) or any
       combination of "R" (red) "G" (green), and "B" (blue). All pixels in a channel whose level is greater
       than 'ratio' times the average of their 8 nearest neighbors are replaced by this average.
       Also set new description 'description' (same as the original if None). Update the object if 'inplace'
       is True or return a new instance if 'inplace' is False."""
    if ratio <= 0.: raise ValueError("Error, ratio must be > 0.")
    if description is None: description = self.description
    image = self.image if inplace else self.image.copy()
    kernel = np.array([[1., 1., 1.], [1., 0., 1.], [1., 1., 1.]])
    if channels in ["V", "L"]:
      channel = self.value() if channels == "V" else self.luminance()
      nnn = convolve2d(np.ones_like(channel), kernel, mode = "same", boundary = "fill", fillvalue = 0.)
      avg = convolve2d(channel, kernel, mode = "same", boundary = "fill", fillvalue = 0.)/nnn
      mask = (channel > ratio*avg)
      for channel in range(3):
        avg = convolve2d(image[channel], kernel, mode = "same", boundary = "fill", fillvalue = 0.)/nnn
        image[channel] = np.where(mask, avg, image[channel])
    else:
      nnn = convolve2d(np.ones_like(image[0]), kernel, mode = "same", boundary = "fill", fillvalue = 0.)
      for channel, letter in ((0, "R"), (1, "G"), (2, "B")):
        if letter in channels:
          avg = convolve2d(image[channel], kernel, mode = "same", boundary = "fill", fillvalue = 0.)/nnn
          image[channel] = np.where(image[channel] > ratio*avg, avg, image[channel])
    return None if inplace else self.newImage(self, image, description)
