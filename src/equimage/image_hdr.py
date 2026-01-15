# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 3.0.0 / 2026.01.15

"""High dynamic range transformations."""

import numpy as np
import scipy.ndimage as ndimg

from . import helpers
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
        mt = multiscale.mmt(image, levels = levels)
      else:
        mt = multiscale.slt(image, levels = levels, starlet = transform)
      # Use approximation as compression/fusion mask.
      mask = mt.coeffs[0].copy()
      # Compress the dynamic range of each level.
      alpham = alpha*np.maximum(mask**beta, 1.e-4) if beta > 0. else alpha # Compress bright more than dark areas.
      for level in range(lmin, levels):
        if verbose:
          p = np.percentile(abs(mt.coeffs[-(level+1)][0]), [1, 99])
          drange1 = p[1]/p[0]
        alphag = gains[level]*alpham
        mt.coeffs[-(level+1)][0] = np.asinh(alphag*mt.coeffs[-(level+1)][0])/np.asinh(alphag)
        if verbose:
          p = np.percentile(abs(mt.coeffs[-(level+1)][0]), [1, 99])
          drange2 = p[1]/p[0]
          print(f"Level #{level}: Dynamical range = {drange1:.3f} -> {drange2:.3f} [{100.*(drange2-drange1)/drange1:.2f}%].")
      # Compute the inverse starlet/median transform.
      image = mt.inverse()
      # Normalize image.
      image -= np.min(image)
      image /= np.max(image)
      median = np.median(image)
      image = mts(image, mts(median, median0))
      if verbose: print(f"Median of renormalized image = {median:.3f}.")
      # Blend original and compressed image using fusion mask.
      if gamma > 0.: image = blend(original, image, mask**gamma)
    return self.newImage(image) if channels == "RGB" else self.set_channel(channel = channels, data = image)

  def HDRMT2(self, transform = "cubic", levels = 6, lmin = 0, alpha = 2.5, gains = 1., beta = 1., gamma = 1., niter = 1, channels = "", verbose = False):
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
        mt = multiscale.mmt(image, levels = levels)
      else:
        mt = multiscale.slt(image, levels = levels, starlet = transform)
      # Use approximation as compression/fusion mask.
      approx = mt.coeffs[0].copy()
      mask = approx.copy()
      # Compress the dynamic range of each level.
      for level in range(levels-1, lmin-1, -1):
        if verbose:
          p = np.percentile(abs(mt.coeffs[-(level+1)][0]), [1, 99])
          drange1 = p[1]/p[0]
        alphal = alpha*gains[level]
        if beta > 0.: alphal *= np.maximum(approx**beta, 1.e-4) # Compress bright more than dark areas.
        # norm = np.percentile(abs(mt.coeffs[-(level+1)][0]), 99)
        norm = np.max(abs(mt.coeffs[-(level+1)][0]))
        approx += mt.coeffs[-(level+1)][0]
        mt.coeffs[-(level+1)][0] = norm*np.asinh(alphal*mt.coeffs[-(level+1)][0]/norm)/np.asinh(alphal)
        if verbose:
          p = np.percentile(abs(mt.coeffs[-(level+1)][0]), [1, 99])
          drange2 = p[1]/p[0]
          print(f"Level #{level}: Dynamical range = {drange1:.3f} -> {drange2:.3f} [{100.*(drange2-drange1)/drange1:.2f}%].")
      # Compute the inverse starlet/median transform.
      image = mt.inverse()
      # Normalize image.
      image -= np.min(image)
      image /= np.max(image)
      median = np.median(image)
      image = mts(image, mts(median, median0))
      if verbose: print(f"Median of renormalized image = {median:.3f}.")
      # Blend original and compressed image using fusion mask.
      if gamma > 0.: image = blend(original, image, mask**gamma)
    return self.newImage(image) if channels == "RGB" else self.set_channel(channel = channels, data = image)

  def HDRMT3(self, transform = "cubic", levels = 6, compression = "tanh", rcscale = 3, strength = (1., 1.414), gain = 1.1, cbscales = (1, 4), cbthreshold = .3, cboost = 2., \
          dnscale = 0, knoise = None, deringing = None, starmask = None, normalize = False, midtone = False, niter = 1, channels = "", verbose = False):
    """HDRMT engine."""

    def deringing_mask(image, threshold = 0.001):
      mini = np.min(image)
      maxi = np.max(image)
      normalized = (image-mini)/max(maxi-mini, helpers.fpepsilon(image.dtype))
      return np.clip(normalized/threshold, 0., 1.)

    def compress_coeffs(c, strength, gain = 1.):
      """Compress multiscale coefficients."""
      if strength > 0.:
        if compression == "tanh":
          return (gain/strength)*np.tanh(strength*c)
        elif compression == "atan":
          return (gain/strength)*np.arctan(strength*c)
        elif compression == "asinh":
          return (gain/strength)*np.asinh(strength*c)
        elif compression == "log":
          return np.sign(c)*(gain/strength)*np.log1p(strength*np.abs(c))
        elif compression == "soft":
          absc = np.abs(c)
          threshold = 1./strength
          return gain*np.where(absc < threshold, c, np.sign(c)*(threshold+np.tanh(strength*(absc-threshold)))/strength)
        else:
          raise ValueError(f"Unknown compression function {compression}.")
      else:
        return c if gain == 1. else gain*c

    def boost_contrast(mt, L, boosts, threshold = .3, sigma = 2.):
      """Boost multi-scale contrast in bright areas."""
      mini = np.min(L)
      maxi = np.max(L)
      normalized = (L-mini)/max(maxi-mini, helpers.fpepsilon(L.dtype))
      mask = np.clip((normalized-threshold)/(1.-threshold), 0., 1.)
      mask = ndimg.gaussian_filter(mask, sigma = sigma)
      for level in range(mt.levels):
        if boosts[level] == 1.: continue
        mt.coeffs[-(level+1)][0] *= 1.+(boosts[level]-1.)*mask

    def denoise(cmt, mt, thresholds):
      """Limit boost of multi-scale coefficients in noisy areas."""
      for level in range(mt.levels):
        threshold = thresholds[level]
        if np.any(threshold > 0.):
          c = helpers.at_least_3D(mt.coeffs[-(level+1)][0])
          cc = helpers.at_least_3D(cmt.coeffs[-(level+1)][0])
          for ic in range(mt.nc):
            mask = np.clip((abs(c[ic])-threshold[ic])/threshold[ic], 0., 1.)
            denoised = mask*cc[ic]+(1.-mask)*c[ic]
            cc[ic] = np.sign(cc[ic])*np.minimum(abs(cc[ic]), abs(denoised))

    # Get channel.
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
    # Check bounds.
    if rcscale is not None: rcscale = min(max(0, rcscale), levels)
    cbscale1, cbscale2 = cbscales if cbscales is not None else (0, levels)
    if cbscale1 is None: cbscale1 = 0
    if cbscale2 is None: cbscale2 = levels
    cbscale1 = min(max(       0, cbscale1), levels)
    cbscale2 = min(max(cbscale1, cbscale2), levels)
    if dnscale is None: dnscale = levels
    dnscale = min(max(0, dnscale), levels)
    if deringing is not None and deringing <= 0.: deringing = None
    # Get compression strengths.
    strengths = np.zeros(levels+1)
    start = rcscale if rcscale is not None else 0
    n = levels-start+1
    if strength is None:
      pass
    elif np.isscalar(strength):
      strengths[start:] = strength
    elif len(strength) == 1:
      strengths[start:] = strength[0]
    elif len(strength) == n:
      strengths[start:] = strength[:]
    elif len(strength) == 2 and n > 2:
      strengths[start:] = np.linspace(strength[0], strength[1], n)
    elif len(strength) == 3 and n > 3:
      strengths[start:-1] = np.linspace(strength[0], strength[1], n-1)
      strengths[-1] = strength[2]
    else:
      raise ValueError("Error, invalid compression strength(s).")
    # Get compression gains.
    gains = np.ones(levels)
    end = rcscale if rcscale is not None else levels
    n = end
    if gain is None:
      pass
    elif np.isscalar(gain):
      gains[:end] = gain
    elif len(gain) == 1:
      gains[:end] = gain[0]
    elif len(gain) == n:
      gains[:end] = gain[:]
    elif len(gain) == 2 and n > 2:
      gains[:end] = np.linspace(gain[0], gain[1], n)
    else:
      raise ValueError("Error, invalid compression gain(s).")
    # Get contrast boosts.
    cboosts = np.ones(levels)
    n = cbscale2-cbscale1+1
    if cboost is None:
      pass
    elif np.isscalar(cboost):
      cbmid = (cbscale1+cbscale2)/2
      for level in range(cbscale1, cbscale2+1):
        cboosts[level] *= 1.+(cboost-1.)*(1.-abs(level-cbmid)/(cbscale2-cbscale1))
    elif len(cboost) == 1:
      cboosts[cbscale1:cbscale2+1] = cboost[0]
    elif len(cboost) == n:
      cboosts[cbscale1:cbscale2+1] = cboost[:]
    elif len(cboost) == 2 and n > 2:
      cboosts[cbscale1:cbscale2+1] = np.linspace(cboost[0], cboost[1], n)
    else:
      raise ValueError("Error, invalid contrast boost(s).")
    if np.all(cboosts == 1.): cboosts = None
    # Get relative noise thresholds.
    knoises = np.zeros(levels)
    end = dnscale+1
    n = end
    if knoise is None:
      pass
    elif np.isscalar(knoise):
      knoises[:end] = knoise
    elif len(knoise) == 1:
      knoises[:end] = knoise[0]
    elif len(knoise) == n:
      knoises[:end] = knoise[:]
    else:
      raise ValueError("Error, invalid relative noise threshold(s).")
    if np.all(knoises == 0.): knoises = None
    # HDRMT algorithm.
    print(f"HDRMT (transform = '{transform}') on channel(s) {channels}...")
    image = self.image if channels == "RGB" else self.get_channel(channel = channels)
    if verbose or normalize:
      mini0 = np.min(image)
      maxi0 = np.max(image)
      if verbose: print(f"Min of original image = {mini0:.5f}.\nMax of original image = {maxi0:.5f}.")
    if verbose or midtone:
      median0 = np.median(image)
      if verbose: print(f"Median of original image = {median0:.3f}.")
    # Create star mask if needed.
    if starmask is None:
      pass
    elif isinstance(starmask, np.ndarray):
      if starmask.shape != self.get_size():
        raise ValueError("Error, the starmask array must be the same width and height as the image.")
    elif isinstance(starmask, str) and starmask == "auto":
        if verbose: print("Creating star mask...")
        _, starmask = eqlab.Image(image).star_masks()
    else:
      raise ValueError("Error, starmask must be None, an array or 'auto'.")
    # Iterate starlet/median transforms.
    for iiter in range(niter):
      if niter > 1: print(f"Iteration {iiter+1}/{niter}.")
      original = image.copy()
      # Create deringing mask if needed.
      deringmask = deringing_mask(original, threshold = deringing) if deringing is not None else None
      # Compute starlet/median transform.
      if transform == "median":
        mt = multiscale.mmt(image, levels = levels)
      else:
        mt = multiscale.slt(image, levels = levels, starlet = transform)
      # Compute noise figures.
      if knoises is not None:
        noisethds, noise = mt.estimate_noise()
        if verbose:
          fmt = mt.nc*" {:.3e}"
          for level in range(levels):
            print(f"Level #{level}: Estimated noise ={fmt.format(*noisethds[level])}.")
          print(f"Estimated total noise ={fmt.format(*noise)}.")
        for level in range(levels):
          noisethds[level] = knoises[level]*noisethds[level]
      # Compress dynamical range.
      cmt = mt.copy()
      cmt.coeffs[0] = compress_coeffs(mt.coeffs[0], strengths[-1])
      for level in range(levels):
        if verbose:
          p = np.percentile(abs(mt.coeffs[-(level+1)][0]), [1, 99])
          crange = p[1]/p[0]
        cmt.coeffs[-(level+1)][0] = compress_coeffs(mt.coeffs[-(level+1)][0], strengths[level], gains[level])
        if verbose:
          p = np.percentile(abs(cmt.coeffs[-(level+1)][0]), [1, 99])
          ccrange = p[1]/p[0]
          print(f"Level #{level}: Dynamical range = {crange:.3f} -> {ccrange:.3f} [{ccrange/crange:.3f}x].")
      # Boost local contrast.
      if cboosts is not None:
        L = image if channels != "RGB" else self.newImage(original).lightness()
        boost_contrast(cmt, L, cboosts, cbthreshold)
      # Denoise multiscale coefficients.
      if knoises is not None:
        denoise(cmt, mt, noisethds)
      # Reconstruct image.
      image = cmt.inverse()
      # Normalize image.
      if verbose or normalize:
        mini = np.min(image)
        maxi = np.max(image)
        if verbose: print(f"Min of compressed image = {mini:.5f}.\nMax of compressed image = {maxi:.5f}.")
        if normalize: image = (image-mini)*(maxi0-mini0)/max(maxi-mini, helpers.fpepsilon(image.dtype))+mini0
      # Apply masks.
      if deringmask is not None: image = eqlab.blend(original, np.clip(image, 0., None), deringmask)
      if starmask is not None: image = eqlab.blend(np.clip(image, None, 1.), original, starmask)
      # Adjust midtone.
      if verbose or midtone:
        median = np.median(image)
        if verbose: print(f"Median of compressed image = {median:.3f}.")
        if midtone: image = mts(image, mts(median, median0))
    return self.newImage(image) if channels == "RGB" else self.set_channel(channel = channels, data = image)
