# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 2.0.0 / 2025.12.17

"""High dynamic range transformations."""

import numpy as np

from .image_utils import blend
from .image_stretch import mts
from . import image_multiscale as multiscale

#####################################
# For inclusion in the Image class. #
#####################################

class MixinImage:
  """To be included in the Image class."""

  def HDRMT(self, transform = "cubic", levels = 6, lmin = 0, alpha = 2.5, gains = 1., beta = 1., gamma = 1., niter = 1, channels = "", verbose = False):
    """High dynamic range multiscale transform (HDRMT).

    Compress the dynamic range of each level of a multiscale transform in order to reveal details
    in the bright areas of the image.

    Each level #i is compressed by applying an arcsinh stretch to the detail coefficients D_i:

      D_i -> asinh(K*D_i)/asinh(K)

    where K = alpha*gain_i*A**beta. Here alpha is an overall compression strength, gain_i is a
    multiplicative gain for each level, and A are the approximation coefficients of the multiscale
    transform. The larger is beta >= 0, the stronger is the compression in the bright areas of the
    image (with respect to the dark areas).

    The compressed image is next renormalized (in the [0, 1] range) and a midtone stretch is applied
    to match the medians of the compressed and original images. Then the compressed and original
    images are blended together:

      image = (1-A**gamma)*original+(A**gamma)*compressed

    The darker areas of the original image are, therefore, the better preserved the larger gamma >= 0.

    The whole process can be iterated niter times. As this non-linear operation transfers intensities
    across scales, it can be better to iterate a with small alpha than to make a single iteration
    with a large alpha.

    See also:
      :meth:`Image.slt() <.slt>`, :meth:`Image.mmt() <.mmt>`

    Args:
      transform (str, optional): The multiscale transform ["cubic" (default) or "linear" for
        the corresponding starlet transform, "median" for a median transform].
      levels (int, optional): The number of detail levels (default 6).
      lmin (int, optional): The lowest detail level to compress (default 0 = smallest scale).
      alpha (float, optional): The overall compression strength (default 2.5).
      gains (float or numpy.ndarray, optional): The gains in each detail level (default 1).
      beta (float, optional): The beta exponent that controls compression as a function of
        brightness (default 1).
      gamma (float, optional): The gamma exponent that controls the blending between the original
        and compressed image (default 1).
      niter (int, optional): The number of iterations (default 1).
      channels (str, optional): The channel(s) the operation is applied to. Can be "RGB", "V",
        "L'", "L", "Ls", "Ln", "L*", "L*/ab", "L*/uv", "L*/sh"  or "" (auto, default).
        See :meth:`Image.apply_channels() <.apply_channels>` or https://astro.ymniquet.fr/codes/equimagelab/docs/channels.html.
      verbose (bool, optional): Print extra information if True (default False).

     Returns:
      Image: The processed image.
    """
    # Check inputs.
    channels = channels.strip()
    if channels == "":
      if self.colormodel == "RGB":
        channels = "RGB"
      elif self.colormodel == "gray":
        channels = "L"
      elif self.colormodel == "HSV":
        channels = "V"
      elif self.colormodel == "HSL":
        channels = "L'"
      elif self.colormodel in ["Lab", "Luv", "Lch", "Lsh"]:
        channels = "L*"
      else:
        raise ValueError(f"Error, unknown color model {self.colormodel}.")
    if channels == "RGB": self.check_color_model("RGB")
    if channels not in ["RGB", "V", "L'", "L", "Ls", "Ln", "L*", "L*/ab", "L*/uv", "L*/sh"]:
      raise ValueError("""Error, channels must be "RGB", "V", "L'", "L", "Ls", "Ln", "L*", "L*/ab", "L*/uv" or "L*/sh".""")
    print(f"HDRMT (transform = '{transform}') on channel(s) {channels}...")
    if np.isscalar(gains): gains = np.full(levels+1, gains)
    # HDRMT algorithm.
    image = self.image if channels == "RGB" else self.get_channel(channel = channels)
    # Normalize image.
    image -= np.min(image)
    image /= np.max(image)
    median0 = np.median(image)
    if verbose: print(f"Median of original image = {median0:.3f}.")
    # Iterate starlet/median transforms.
    for iiter in range(niter):
      if niter > 1: print(f"Iteration {iiter+1}/{niter}.")
      # Copy image.
      original = image.copy()
      # Compute starlet/median transform.
      if transform == "median":
        wt = multiscale.mmt(image, levels = levels)
      else:
        wt = multiscale.slt(image, levels = levels, starlet = transform)
      # Use approximation as compression/fusion mask.
      mask = wt.coeffs[0].copy()
      # Compress the dynamic range of each level.
      alpham = alpha*np.maximum(mask**beta, 1.e-4) if beta > 0. else alpha # Compress bright more than dark areas.
      for level in range(lmin, levels):
        if verbose:
          p = np.percentile(abs(wt.coeffs[-(level+1)][0]), [2.5, 97.5])
          drange1 = p[1]/p[0]
        alphag = gains[level]*alpham
        wt.coeffs[-(level+1)][0] = np.asinh(alphag*wt.coeffs[-(level+1)][0])/np.asinh(alphag)
        if verbose:
          p = np.percentile(abs(wt.coeffs[-(level+1)][0]), [2.5, 97.5])
          drange2 = p[1]/p[0]
          print(f"Level #{level}: Dynamical range = {drange1:.3f} -> {drange2:.3f} [{100.*(drange2-drange1)/drange1:.2f}%].")
      # Compute the inverse starlet/median transform.
      image = wt.inverse()
      # Normalize image.
      image -= np.min(image)
      image /= np.max(image)
      median = np.median(image)
      image = mts(image, mts(median, median0))
      if verbose: print(f"Median of renormalized image = {median:.3f}.")
      # Blend original and compressed image using fusion mask.
      if gamma > 0.: image = blend(original, image, mask**gamma)
    return self.newImage(image) if channels == "RGB" else self.set_channel(channel = channels, data = image)
