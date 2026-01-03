# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 2.0.0 / 2025.12.17
# Doc OK.

"""Stars transformations."""

import os
import shutil
import numpy as np
import scipy.ndimage as ndimg

from . import params
from . import image_masks as masks
from .image_stretch import mts

#####################################
# For inclusion in the Image class. #
#####################################

class MixinImage:
  """To be included in the Image class."""

  def star_mask(self, channel = "L", midtone = "auto", threshold = .9, maxarea = 100., extend = 1.5, smooth = 1., kernel = "disk"):
    """Create a star mask based on a luminance threshold.
  
    Args:
      channel (str, optional): The channel where to look for stars [usually "L" (luma, default) or
        "L*" (lightness)].
      midtone (float, optional): If different from 0.5 (default), apply a midtone stretch to the
        channel before looking for stars. This can help find stars on low contrast, linear RGB 
        images. See :meth:`Image.midtone_stretch() <.midtone_stretch>`; midtone can either be 
        "auto" (for automatic stretch) or a float in ]0, 1[.    
      threshold (float, optional): The star mask is originally computed as a float array with the 
        same size as the image, which is 1 wherever the stretched channel is greater than threshold 
        times the maximum, and 0 otherwise. Default is 0.9.
      maxarea (float, optional): The maximum area of a star (in pixels). Features of the star mask
        whose area is larger than maxarea are discarded. Default is 100.
      extend (float, optional): Once computed, the star features are extended by extend pixels
        (default 1.5).
      smooth (float, optional): Once extended, the star features are smoothed over 2*smooth pixels 
        (default 1). 
      kernel (str, optional): The convolution kernel for smoothing [either "gaussian" for a gaussian
        with standard deviation smooth/4 or "disk" for a constant disk of radius smooth]. 
        See :func:`smooth_mask`.
  
    Returns:
      numpy.ndarray: The star mask.
    """
    # Get channel data.
    data = self.get_channel(channel)
    # Stretch data if needed.
    if midtone == "auto":
      midtone = min(mts(np.median(data), params.starsmed), .5)
      print(f"Midtone = {midtone:.5f}.")
    if midtone != .5: data = mts(data, midtone)
    # Threshold data.
    mask = (data > threshold*np.max(data))
    # Suppress features which are too large to be stars.
    ndiscarded = 0
    label, nfeatures = ndimg.label(mask)
    for i in range(1, nfeatures+1):
      set = (label == i)
      area = np.sum(set)
      if area > maxarea: 
        ndiscarded += 1
        mask[set] = False
    if ndiscarded > 0: print(f"Discarded {ndiscarded} feature(s).")
    # Extend star mask.
    mask = masks.extend_bmask(mask, extend = extend+smooth)
    # Smooth star mask.
    return masks.smooth_mask(mask, radius = smooth, kernel = kernel, mode = "reflect")

  def starnet(self, midtone = .5, starmask = False):
    """Remove the stars from the image with StarNet++.

    See: https://www.starnetastro.com/

    The image is saved as a TIFF file (16 bits integer per channel); the stars are removed from this
    file with StarNet++, and the starless image is finally reloaded in eQuimageLab and returned.

    Warning:
      The command "starnet++" must be in the PATH.

    Args:
      midtone (float, optional): If different from 0.5 (default), apply a midtone stretch to the
        input image before running StarNet++, then apply the inverse stretch to the output starless.
        This can help StarNet++ find stars on low contrast, linear RGB images.
        See :meth:`Image.midtone_stretch() <.midtone_stretch>`; midtone can either be "auto" (for
        automatic stretch) or a float in ]0, 1[.
      starmask (bool, optional): If True, return both the starless image and the star mask.
        If False (default), only return the starless image [the star mask being the difference
        between the original image (self) and the starless].

    Returns:
      Image: The starless image if starmask is False, and both the starless image and star mask if
      starmask is True.
    """
    self.check_color_model("RGB", "gray")
    # We need to cwd to the starnet++ directory to process the image.
    cmdpath = shutil.which("starnet++")
    if cmdpath is None: raise FileNotFoundError("Error, starnet++ executable not found in the PATH.")
    path, cmd = os.path.split(cmdpath)
    # Stretch the input image if needed.
    if midtone == "auto":
      avgmedian = np.mean(np.median(self.image, axis = (-1, -2)))
      midtone = min(mts(avgmedian, params.starsmed), .5)
      print(f"Midtone = {midtone:.5f}.")
    if midtone != .5:
      image = self.midtone_stretch(midtone)
      #print(np.mean(np.median(image.image, axis = (-1, -2))))
    else:
      image = self
    # Run starnet++.
    starless = image.edit_with("starnet++ $FILE$ $FILE$", export = "tiff", depth = 16, editor = "StarNet++", interactive = False, cwd = path)
    # "Unstretch" the starless if needed.
    if midtone != .5:
      starless = starless.midtone_stretch(midtone, inverse = True)
    # Return starless/star masks as appropriate.
    if starmask:
      return starless, self-starless
    else:
      return starless

  def resynthetize_stars_siril(self):
    """Resynthetize stars with Siril.

    This method saves the image as a FITS file (32 bits float per channel) then runs Siril to find
    the stars and resynthetize them with "perfect" Gaussian or Moffat shapes. It returns a synthetic
    star mask that must be blended with the original or starless image. This can be used to correct
    coma and other aberrations.

    Note:
      Star resynthesis works best on the star mask produced by :meth:`Image.starnet() <.starnet>`.

    Warning:
      The command "siril-cli" must be in the PATH.

    Returns:
      Image: The synthetic star mask produced by Siril.
    """
    self.check_color_model("RGB", "gray")
    script = ('requires 1.2.0\n'
              'load "$FILE$"\n'
              'setfindstar -roundness=0.10\n'
              'findstar\n'
              'synthstar\n'
              'save "$FILE$"\n')
    return self.edit_with("siril-cli -s $SCRIPT$", export = "fits", depth = 32, script = script, editor = "Siril", interactive = False)

  def reduce_stars(self, amount, starless = None):
    """Reduce the size of the stars on the image.

    This method makes use of the starless image produced by starnet++ to identify and unstretch
    stars, thus effectively reducing their apparent diameter. It shall be applied to a streched
    (non-linear) image.

    Note:
      Inspired from https://gitlab.com/free-astro/siril-scripts/-/blob/main/processing/DSA-Star_Reduction.py
      by Rich Stevenson - Deep Space Astro.

    See also:
      :meth:`Image.starnet() <.starnet>`

    Args:
      amount (float): The strength of star reduction, expected in ]-1, 1[.
        amount < 0 reduces star size, while amount > 0 increases star size.
      starless (Image, optional): The starless image. If None (default), the starless image is
        computed with StarNet++. The command "starnet++" must then be in the PATH.

    Returns:
      Image: The edited image, with the stars reduced.
    """
    self.check_color_model("RGB", "gray")
    if abs(amount) > .9999: raise ValueError("Error, |amount| must be < .9999.")
    if starless is None: starless = self.starnet(midtone = "auto", starmask = False)
    midtone = (1.-amount)/2.
    fimage    = 1.-    self.midtone_stretch(midtone)
    fstarless = 1.-starless.midtone_stretch(midtone)
    return 1.-(fimage/fstarless)*(1.-starless)
