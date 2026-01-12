# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 2.0.0 / 2025.12.17
# Doc OK.

"""Image statistics & histograms."""

import numpy as np

from . import params
from . import helpers

def parse_channels(channels, errors = True):
  """Parse channel keys.

  Args:
    channels (str): A combination of channel keys:

      - "1", "2", "3" (or equivalently "R", "G", "B" for RGB images):
        The first/second/third channel (all images).
      - "V": The HSV value (RGB, HSV and grayscale images).
      - "S": The HSV saturation (RGB, HSV and grayscale images).
      - "L'": The HSL lightness (RGB, HSL and grayscale images).
      - "S'": The HSL saturation (RGB, HSL and grayscale images).
      - "H": The HSV hue (RGB, HSV and grayscale images).
      - "L": The luma (RGB and grayscale images).
      - "L*": The CIE lightness L* (RGB, grayscale, CIELab and CIELuv images).
      - "c*": The CIE chroma c* (CIELab and CIELuv images).
      - "s*": The CIE saturation s* (CIELuv images).
      - "h*": The CIE hue angle h* (CIELab and CIELuv images).

    errors (bool, optional): If False, discard unknown channel keys;
      If True (default), raise a ValueError.

  Returns:
    list: The list of channel keys.
  """
  keys = []
  prevkey = None
  for key in channels:
    ok = False
    if key in ["1", "2", "3", "R", "G", "B", "L", "V", "S", "H", "c", "s", "h"]:
      keys.append(key)
      ok = True
    elif key == "'":
      if prevkey in ["L", "S"]:
        keys[-1] += key
        ok = True
    elif key == "*":
      if prevkey in ["L", "c", "s", "h"]:
        keys[-1] += key
        ok = True
    elif key == " ":
      ok = True # Skip spaces.
    if not ok and errors: raise ValueError(f"Error, unknown channel '{key}'.")
    prevkey = key
  return keys

#####################################
# For inclusion in the Image class. #
#####################################

class MixinImage:
  """To be included in the Image class."""

  def histograms(self, channels = None, nbins = None, recompute = False):
    """Compute histograms of selected channels of the image.

    The histograms are both returned and embedded in the object as self.hists. Histograms already
    registered in self.hists are not recomputed unless required.

    See also:
      :meth:`params.set_default_hist_bins() <equimage.params.set_default_hist_bins>`,
      :meth:`params.set_max_hist_bins() <equimage.params.set_max_hist_bins>`

    Args:
      channels (str, optional): A combination of keys for the selected channels:

        - "1", "2", "3" (or equivalently "R", "G", "B" for RGB images):
          The first/second/third channel (all images).
        - "V": The HSV value (RGB, HSV and grayscale images).
        - "S": The HSV saturation (RGB, HSV and grayscale images).
        - "L'": The HSL lightness (RGB, HSL and grayscale images).
        - "S'": The HSL saturation (RGB, HSL and grayscale images).
        - "H": The HSV hue (RGB, HSV and grayscale images).
        - "L": The luma (RGB and grayscale images).
        - "L*": The CIE lightness L* (RGB, grayscale, CIELab and CIELuv images).
        - "c*": The CIE chroma c* (CIELab and CIELuv images).
        - "s*": The CIE saturation s* (CIELuv images).
        - "h*": The CIE hue angle h* (CIELab and CIELuv images).

        If it ends with a "+", channels gets appended with the keys already registered in self.hists.
        Default (if None) is "RGBL" for RGB images, "VS" for HSV images, "L'S'" for HSL images,
        "L" for grayscale images, "L*c*" for CIELab and "L*s*" for CIELuv images.
      nbins (int, optional): Number of bins within [0, 1] in the histograms.
        Set to `equimage.params.maxhistbins` if negative, and computed from the image statistics
        using Scott's rule if zero. If None (default), set to `equimage.params.defhistbins`.
      recompute (bool, optional): If False (default), the histograms already registered in self.hists
        are not recomputed (provided they match nbins). If True, all histograms are recomputed.

    Returns:
      dict: hists[key] for key in channels, with:

        - hists[key].name = channel name (provided for convenience).
        - hists[key].nbins = number of bins within [0, 1].
        - hists[key].edges = histogram bins edges.
        - hists[key].counts = histogram bins counts.
        - hists[key].color = suggested line color for histogram plots.
    """
    if channels is None:
      if self.colorspace == "CIELab":
        channels = "L*c*"
      elif self.colorspace == "CIELuv":
        channels = "L*s*"
      elif self.colorspace == "lRGB" or self.colorspace == "sRGB":
        if self.colormodel == "RGB":
          channels = "RGBL"
        elif self.colormodel == "HSV":
          channels = "VS"
        elif self.colormodel == "HSL":
          channels = "V'S'"
        elif self.colormodel == "gray":
          channels = "L"
        else:
          self.color_model_error()
      else:
        self.color_space_error()
    if nbins is None: nbins = params.defhistbins
    if nbins == 0:
      if not recompute and hasattr(self, "hists"): # Retrieve the number of bins from the existing histograms.
        nbins = list(self.hists.values())[0].nbins
      else: # Compute the number of bins using Scott's rule.
        width, height = self.get_size()
        npixels = width*height
        if self.colormodel == "RGB":
          channel = (self.image[0]+self.image[1]+self.image[2])/3.
        elif self.colormodel == "HSV" or self.colormodel == "HSL":
          channel = self.image[2]
        else:
          channel = self.image[0]
        nbins = np.ceil(np.cbrt(npixels)/(3.5*max(np.std(channel), helpers.fpepsilon(self.dtype))))
        nbins = int(min(nbins, params.maxhistbins))
    elif nbins < 0:
      nbins = params.maxhistbins
    nbins = min(max(16, nbins), params.maxhistbins)
    if not hasattr(self, "hists"): self.hists = {} # Register empty histograms in the object, if none already computed.
    if channels and channels[-1] == "+":
      keys = parse_channels(channels[:-1])
      for key in self.hists.keys(): # Add missing keys.
        if not key in keys: keys.append(key)
    else:
      keys = parse_channels(channels)
    hists = {}
    for key in keys:
      if key in hists: # Already selected.
        print(f"Warning, channel '{key}' selected twice or more...")
        continue
      if not recompute and key in self.hists: # Already computed.
        if self.hists[key].nbins == nbins:
          hists[key] = self.hists[key]
          continue
      if key == "1":
        name = "Channel #1"
        color = "red"
        channel = self.image[0]
      elif key == "2":
        name = "Channel #2"
        color = "green"
        if self.get_nc() < 2: raise self.color_model_error()
        channel = self.image[1]
      elif key == "3":
        name = "Channel #3"
        color = "blue"
        if self.get_nc() < 3: raise self.color_model_error()
        channel = self.image[2]
      elif key == "R":
        self.check_color_model("RGB", "gray")
        name = "Red"
        color = "red"
        channel = self.image[0]
      elif key == "G":
        self.check_color_model("RGB", "gray")
        name = "Green"
        color = "green"
        channel = self.image[1] if self.colormodel == "RGB" else self.image[0]
      elif key == "B":
        self.check_color_model("RGB", "gray")
        name = "Blue"
        color = "blue"
        channel = self.image[2] if self.colormodel == "RGB" else self.image[0]
      elif key == "V":
        name = "HSV value"
        color = "darkslategray"
        channel = self.HSV_value()
      elif key == "S":
        name = "HSV saturation"
        color = "orange"
        channel = self.HSV_saturation()
      elif key == "L'":
        name = "HSL lightness"
        color = "darkslategray"
        channel = self.HSL_lightness()
      elif key == "S'":
        name = "HSL saturation"
        color = "orange"
        channel = self.HSL_saturation()
      elif key == "H":
        name = "HSX hue"
        color = "limegreen"
        channel = self.HSX_hue()
      elif key == "L":
        name = "Luma"
        color = "lightslategray"
        channel = self.luma()
      elif key == "L*":
        name = "Lightness"
        color = "lightsteelblue"
        channel = self.lightness()
      elif key == "c*":
        name = "CIE chroma"
        color = "orange"
        channel = self.CIE_chroma()
      elif key == "s*":
        name = "CIE saturation"
        color = "orange"
        channel = self.CIE_saturation()
      elif key == "h*":
        name = "CIE hue"
        color = "limegreen"
        channel = self.CIE_hue()
      else:
        raise ValueError(f"Error, unknown channel '{key}'.")
      mmin = np.floor(np.min(channel)*nbins)
      mmax = np.ceil (np.max(channel)*nbins)
      mbins = max(int(round(mmax-mmin)), 1)
      hists[key] = helpers.Container()
      hists[key].name = name
      hists[key].nbins = nbins
      hists[key].counts, hists[key].edges = np.histogram(channel, bins = mbins, range = (mmin/nbins, mmax/nbins), density = False)
      hists[key].color = color
    self.hists = hists
    return hists

  def statistics(self, channels = None, exclude01 = None, recompute = False):
    """Compute statistics of selected channels of the image.

    The statistics are both returned and embedded in the object as self.stats. Statistics already
    registered in self.stats are not recomputed unless required.

    Args:
      channels (str, optional): A combination of keys for the selected channels:

        - "1", "2", "3" (or equivalently "R", "G", "B" for RGB images):
          The first/second/third channel (all images).
        - "V": The HSV value (RGB, HSV and grayscale images).
        - "S": The HSV saturation (RGB, HSV and grayscale images).
        - "L'": The HSL lightness (RGB, HSL and grayscale images).
        - "S'": The HSL saturation (RGB, HSL and grayscale images).
        - "H": The HSV hue (RGB, HSV and grayscale images).
        - "L": The luma (RGB and grayscale images).
        - "L*": The CIE lightness L* (RGB, grayscale, CIELab and CIELuv images).
        - "c*": The CIE chroma c* (CIELab and CIELuv images).
        - "s*": The CIE saturation s* (CIELuv images).
        - "h*": The CIE hue angle h* (CIELab and CIELuv images).

        If it ends with a "+", channels gets appended with the keys already registered in self.stats.
        Default (if None) is "RGBL" for RGB images, "VS" for HSV images, "L'S'" for HSL images,
        "L" for grayscale images, "L*c*" for CIELab and "L*s*" for CIELuv images.
      exclude01 (bool, optional): If True, exclude pixels <= 0 or >= 1 from the median and percentiles.
        Defaults to `equimage.params.exclude01` if None.
      recompute (bool, optional): If False (default), the statistics already registered in self.stats
        are not recomputed. If True, all statistics are recomputed.

    Returns:
      dict: stats[key] for key in channels, with:

        - stats[key].name = channel name (provided for convenience).
        - stats[key].width = image width (provided for convenience).
        - stats[key].height = image height (provided for convenience).
        - stats[key].npixels = number of image pixels = image width*image height (provided for
          convenience).
        - stats[key].minimum = minimum level.
        - stats[key].maximum = maximum level.
        - stats[key].percentiles = (pr25, pr50, pr75) = the 25th, 50th and 75th percentiles.
        - stats[key].median = pr50 = median level.
        - stats[key].zerocount = number of pixels <= 0.
        - stats[key].outcount = number of pixels > 1 (out-of-range).
        - stats[key].exclude01 = True if pixels >= 0 or <= 1 have been excluded from the median and
          percentiles, False otherwise.
        - stats[key].color = suggested text color for display.
    """
    epsilon = helpers.fpepsilon(self.dtype)
    if channels is None:
      if self.colorspace == "CIELab":
        channels = "L*c*"
      elif self.colorspace == "CIELuv":
        channels = "L*s*"
      elif self.colorspace == "lRGB" or self.colorspace == "sRGB":
        if self.colormodel == "RGB":
          channels = "RGBL"
        elif self.colormodel == "HSV":
          channels = "VS"
        elif self.colormodel == "HSL":
          channels = "V'S'"
        elif self.colormodel == "gray":
          channels = "L"
        else:
          self.color_model_error()
      else:
        self.color_space_error()
    if exclude01 is None: exclude01 = params.exclude01
    if not hasattr(self, "stats"): self.stats = {} # Register empty statistics in the object, if none already computed.
    if channels and channels[-1] == "+":
      keys = parse_channels(channels[:-1])
      for key in self.hists.keys(): # Add missing keys.
        if not key in keys: keys.append(key)
    else:
      keys = parse_channels(channels)
    width, height = self.get_size()
    npixels = width*height
    stats = {}
    for key in keys:
      if key in stats: # Already selected.
        print(f"Warning, channel '{key}' selected twice or more...")
        continue
      if not recompute and key in self.stats: # Already computed.
        if self.stats[key].exclude01 == exclude01:
          stats[key] = self.stats[key]
          continue
      if key == "1":
        name = "Channel #1"
        color = "red"
        channel = self.image[0]
      elif key == "2":
        name = "Channel #2"
        color = "green"
        if self.get_nc() < 2: raise self.color_model_error()
        channel = self.image[1]
      elif key == "3":
        name = "Channel #3"
        color = "blue"
        if self.get_nc() < 3: raise self.color_model_error()
        channel = self.image[2]
      elif key == "R":
        self.check_color_model("RGB", "gray")
        name = "Red"
        color = "red"
        channel = self.image[0]
      elif key == "G":
        self.check_color_model("RGB", "gray")
        name = "Green"
        color = "green"
        channel = self.image[1] if self.colormodel == "RGB" else self.image[0]
      elif key == "B":
        self.check_color_model("RGB", "gray")
        name = "Blue"
        color = "blue"
        channel = self.image[2] if self.colormodel == "RGB" else self.image[0]
      elif key == "V":
        name = "HSV value"
        color = "darkslategray"
        channel = self.HSV_value()
      elif key == "S":
        name = "HSV saturation"
        color = "orange"
        channel = self.HSV_saturation()
      elif key == "L'":
        name = "HSL lightness"
        color = "darkslategray"
        channel = self.HSL_lightness()
      elif key == "S'":
        name = "HSL saturation"
        color = "orange"
        channel = self.HSL_saturation()
      elif key == "H":
        name = "HSX hue"
        color = "limegreen"
        channel = self.HSX_hue()
      elif key == "L":
        name = "Luma"
        color = "lightslategray"
        channel = self.luma()
      elif key == "L*":
        name = "Lightness"
        color = "lightsteelblue"
        channel = self.lightness()
      elif key == "c*":
        name = "CIE chroma"
        color = "orange"
        channel = self.CIE_chroma()
      elif key == "s*":
        name = "CIE saturation"
        color = "orange"
        channel = self.CIE_saturation()
      elif key == "h*":
        name = "CIE hue"
        color = "limegreen"
        channel = self.CIE_hue()
      else:
        raise ValueError(f"Error, unknown channel '{key}'.")
      stats[key] = helpers.Container()
      stats[key].name = name
      stats[key].width = width
      stats[key].height = height
      stats[key].npixels = npixels
      stats[key].minimum = np.min(channel)
      stats[key].maximum = np.max(channel)
      if exclude01:
        mask = (channel >= epsilon) & (channel < 1.)
        stats[key].percentiles = np.percentile(channel[mask], [25., 50., 75.]) if np.any(mask) else None
      else:
        stats[key].percentiles = np.percentile(channel, [25., 50., 75.])
      stats[key].median = stats[key].percentiles[1] if stats[key].percentiles is not None else None
      stats[key].zerocount = np.sum(channel < epsilon)
      stats[key].outcount = np.sum(channel > 1.)
      stats[key].exclude01 = exclude01
      stats[key].color = color
    self.stats = stats
    return stats
