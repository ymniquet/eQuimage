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

  def HDRMTe(self, transform = "cubic", levels = 6, compression = "tanh", minscale = 4, strength = (1., 1.414, 2.), gain = 1., boostscales = (0, 3), boost = 2., boostthd = .1, \
             noisescale = None, noisethd = None, deringing = None, starmask = None, normalize = True, midtone = True, niter = 1, channels = "", verbose = False):
    """HDRMT engine. Under development."""
    # TODO : Further boost dark lanes.

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
        return c.copy() if gain == 1. else gain*c

    def boost_contrast(cmt, Lmt, boosts, threshold = .3):
      """Boost multi-scale contrast in bright areas."""
      L = Lmt.coeffs[0].copy()
      for level in range(cmt.levels-1, -1, -1):
        boost = boosts[level]
        if boost != 1.: 
          mask = np.clip((L-threshold)/(1.-threshold), 0., 1.)
          cmt.coeffs[-(level+1)][0] *= 1.+(boost-1.)*mask
        L += Lmt.coeffs[-(level+1)][0]
        
    def denoise(cmt, mt, thresholds):
      """Limit boost of multi-scale coefficients in noisy areas."""
      for level in range(cmt.levels):
        threshold = thresholds[level]
        if threshold > 0.:
          c = mt.coeffs[-(level+1)][0]
          cc = cmt.coeffs[-(level+1)][0]
          mask = np.clip((abs(c)-threshold)/threshold, 0., 1.)
          denoised = mask*cc+(1.-mask)*c
          cmt.coeffs[-(level+1)][0] = np.sign(cc)*np.minimum(abs(cc), abs(denoised))
          
    def pretty_print(label, data):
      n = len(data)
      fmt = "["+(n-1)*"{:.3f} "+"{:.3f}]"
      print(label+" = "+fmt.format(*data))
      
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
    print(f"HDRMT (transform = '{transform}') on channel(s) {channels}...")
    # Check bounds.
    if minscale is not None: minscale = min(max(0, minscale), levels)
    minboost, maxboost = boostscales if boostscales is not None else (0, levels)
    if minboost is None: minboost = 0
    if maxboost is None: maxboost = levels
    minboost = min(max(       0, minboost), levels)
    maxboost = min(max(minboost, maxboost), levels)
    if noisescale is None: noisescale = levels
    noisescale = min(max(0, noisescale), levels)
    if deringing is not None and deringing <= 0.: deringing = None
    # Get compression strengths.
    strengths = np.zeros(levels+1)
    start = minscale if minscale is not None else 0
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
    if verbose: pretty_print("Compression strengths", strengths)
    # Get compression gains.
    gains = np.ones(levels)
    end = minscale if minscale is not None else levels
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
    if verbose: pretty_print("Compression gains", gains)
    # Get contrast boosts.
    boosts = np.ones(levels)
    n = maxboost-minboost+1
    if boost is None:
      pass
    elif np.isscalar(boost):
      midboost = (minboost+maxboost)/2
      for level in range(minboost, maxboost+1):
        boosts[level] *= 1.+(boost-1.)*(1.-abs(level-midboost)/(maxboost-minboost))
    elif len(boost) == 1:
      boosts[minboost:maxboost+1] = boost[0]
    elif len(boost) == n:
      boosts[minboost:maxboost+1] = boost[:]
    elif len(boost) == 2 and n > 2:
      boosts[minboost:maxboost+1] = np.linspace(boost[0], boost[1], n)
    else:
      raise ValueError("Error, invalid contrast boost(s).")
    if np.all(boosts == 1.): 
      boosts = None
    elif verbose: 
      pretty_print("Contrast boosts", gains)
    # Get noise thresholds.
    noisethds = np.zeros(levels)
    end = noisescale+1
    n = end
    if noisethd is None:
      pass
    elif np.isscalar(noisethd):
      noisethds[:end] = noisethd
    elif len(noisethd) == 1:
      noisethds[:end] = noisethd[0]
    elif len(noisethd) == n:
      noisethds[:end] = noisethd[:]
    else:
      raise ValueError("Error, invalid noise threshold(s).")
    if np.all(noisethds == 0.): 
      noisethds = None
    elif verbose:
      pretty_print("Noise thresholds", noisethds)      
    # HDRMT algorithm.
    image = self.image if channels == "RGB" else self.get_channel(channel = channels)
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
      if verbose: print("Computing multiscale transform...")
      if transform == "median":
        mt = multiscale.mmt(image, levels = levels)
      else:
        mt = multiscale.slt(image, levels = levels, starlet = transform)
      # Compress dynamical range.
      if verbose: print("Compressing large scales...")
      cmt = mt.copy()
      cmt.coeffs[0] = compress_coeffs(mt.coeffs[0], strengths[-1])
      if verbose:
        c = mt.coeffs[0]
        p = np.percentile(c[c > 0.], [1, 99])
        crange = p[1]/p[0]          
        c = cmt.coeffs[0]
        p = np.percentile(c[c > 0.], [1, 99])
        ccrange = p[1]/p[0]
        print(f"Approximation: Dynamical range = {crange:.3f} -> {ccrange:.3f} [{ccrange/crange:.3f}x].")        
      for level in range(levels-1, -1, -1):
        cmt.coeffs[-(level+1)][0] = compress_coeffs(mt.coeffs[-(level+1)][0], strengths[level], gains[level])
        if verbose:
          absc = abs(mt.coeffs[-(level+1)][0])
          p = np.percentile(absc[absc > 0.], [1, 99])
          crange = p[1]/p[0]          
          absc = abs(cmt.coeffs[-(level+1)][0])
          p = np.percentile(absc[absc > 0.], [1, 99])
          ccrange = p[1]/p[0]
          print(f"Scale #{level}: Dynamical range = {crange:.3f} -> {ccrange:.3f} [{ccrange/crange:.3f}x].")
      # Boost local contrast.
      if boosts is not None: 
        if verbose: print("Boosting contrast in bright areas...")
        boost_contrast(cmt, mt, boosts, boostthd)
      # Denoise multiscale coefficients.
      if noisethds is not None: 
        if verbose: print("Denoising small scales...")
        denoise(cmt, mt, noisethds)
      # Reconstruct image.
      if verbose: print("Reconstructing image...")
      image = cmt.inverse()
      if verbose:
        print(f"Reconstructed image minimum = {np.min(image):.5f}.")
        print(f"Reconstructed image maximum = {np.max(image):.5f}.")
      # Apply deringing mask.
      if deringmask is not None: 
        if verbose: print("Applying deringing mask...")
        image = eqlab.blend(original, np.clip(image, 0., None), deringmask)
      # Normalize image.
      if normalize:
        if verbose: print("Normalizing image...")
        image = np.tanh(image) # Remap into [-1, 1].
        mini = np.min(image)
        maxi = np.max(image)
        image = (image-mini)/max(maxi-mini, helpers.fpepsilon(image.dtype))
      # Apply star mask.
      if starmask is not None: 
        if verbose: print("Applying star mask...")
        image = eqlab.blend(np.clip(image, None, 1.), original, starmask)
      # Adjust midtone.
      if verbose or midtone:
        median = np.median(image)
        if verbose: print(f"Median of transformed image = {median:.3f}.")
        if midtone: 
          if verbose: print("Correcting midtone...")
          image = mts(image, mts(median, median0))
    return self.newImage(image) if channels == "RGB" else self.set_channel(channel = channels, data = image)
