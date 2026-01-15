# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 3.0.0 / 2026.01.15

"""High dynamic range transformations."""

import numpy as np

from .image_utils import blend, clip
from .image_stretch import mts
from . import image_multiscale as multiscale

#####################################
# For inclusion in the Image class. #
#####################################

class MixinImage:
  """To be included in the Image class."""

  def HDRwt1(self, starlet = "cubic", lmin = 1, lmax = 5, rstrength = .1, mstrength = 2., target = "bright", niter = 1, channels = "", maskchannel = ""):
    """HDRWT v1. Experimental."""
    # Check inputs.
    if target not in ["bright", "dark"]: raise ValueError("Error, target must be 'bright' or 'dark'.")
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
    if channels not in ["RGB", "V", "L'", "L", "Ls", "Ln", "L*", "L*ab", "L*uv", "L*sh"]:
      raise ValueError("""Error, channels must be "RGB", "V", "L'", "L", "Ls", "Ln", "L*", "L*ab", "L*uv" or "L*sh".""")
    if channels == "RGB": self.check_color_model("RGB")
    maskchannel = maskchannel.strip()
    if maskchannel == "":
      if self.colormodel in ["RGB", "gray"]:
        maskchannel = "L"
      elif self.colormodel == "HSV":
        maskchannel = "V"
      elif self.colormodel == "HSL":
        maskchannel = "L'"
      elif self.colormodel in ["Lab", "Luv", "Lch", "Lsh"]:
        maskchannel = "L*"
      else:
        raise ValueError(f"Error, unknown color model {self.colormodel}.")
    if maskchannel not in ["V", "L'", "L", "L*"]:
      raise ValueError("""Error, maskchannel must be "V", "L'", "L" or "L*".""")
    print(f"HDRWT on channel(s) {channels} with mask channel {maskchannel}...")
    # HDRWT algorithm.
    image = self.copy()
    # median0 = np.median(image)
    for iiter in range(niter): # HDRWT iterations.
      if niter > 1: print(f"Iteration {iiter+1}/{niter}.")
      for level in range(lmin, lmax+1): # Iterate over wavelet levels.
        print(f"Processing level #{level}: ", end = "")
        # Compute the approximation of the mask channel at that wavelet level.
        lightness = image.get_channel(channel = maskchannel)
        approx = multiscale.slt(lightness, levels = level, starlet = starlet).coeffs[0] if level > 0 else mc
        # Compute the midtone transformation and HDR fusion mask.
        median = np.median(approx)
        if target == "bright":
          mask = np.clip(   approx, 0., 1.)**mstrength
          midtone = max(mts(median, (1.-rstrength)*median), .5)
        else:
          mask = np.clip(1.-approx, 0., 1.)**mstrength
          midtone = min(mts(median, (1.+rstrength)*median), .5)
        print(f"midtone = {midtone:.5f}.")
        # Apply the midtone transformation and blend with the original image.
        stretched = image.midtone_stretch(channels = channels, midtone = midtone, trans = False)
        image = image.blend(stretched, mask)
        # image = image.midtone_stretch(midtone = mts(np.median(image), median0), channels = "L", trans = False)
    return image

  # def HDRwt2(self, starlet = "cubic", lmin = 0, lmax = 3, A = 1., D = 2., gamma = 1., niter = 1, threshold = 0., neutral = 1., decay = 2., channels = ""):
  #   """HDRWT v2. Experimental. Allow for alpha, rthreshold & romega arrays."""
  #   # Check inputs.
  #   channels = channels.strip()
  #   if channels == "":
  #     if self.colormodel == "RGB":
  #       channels = "RGB"
  #     elif self.colormodel == "gray":
  #       channels = "L"
  #     elif self.colormodel == "HSV":
  #       channels = "V"
  #     elif self.colormodel == "HSL":
  #       channels = "L'"
  #     elif self.colormodel in ["Lab", "Luv", "Lch", "Lsh"]:
  #       channels = "L*"
  #     else:
  #       raise ValueError(f"Error, unknown color model {self.colormodel}.")
  #   if channels == "RGB": self.check_color_model("RGB")
  #   if channels not in ["RGB", "V", "L'", "L", "Ls", "Ln", "L*", "L*ab", "L*uv", "L*sh"]:
  #     raise ValueError("""Error, channels must be "RGB", "V", "L'", "L", "Ls", "Ln", "L*", "L*ab", "L*uv" or "L*sh".""")
  #   print(f"HDRWT on channel(s) {channels}...")
  #   # HDRWT algorithm.
  #   image = self.image if channels == "RGB" else self.get_channel(channel = channels)
  #   # median0 = np.median(image)
  #   for iiter in range(niter): # HDRWT iterations.
  #     if niter > 1: print(f"Iteration {iiter+1}/{niter}.")
  #     # Compute wavelet transform.
  #     wt = multiscale.slt(image, levels = lmax+1, starlet = starlet)
  #     # Compress the dynamic range of each wavelet level.
  #     if np.isscalar(A): A = [1.+(A-1.)/decay**level for level in range(lmax+1)]
  #     cwt = wt.enhance_details(A = A, D = D, threshold = threshold, neutral = neutral)
  #     # Blend the compressed wavelet levels with the original ones,
  #     # using the approximation at the next scale as fusion mask.
  #     approx = wt.coeffs[0].copy()
  #     wt.coeffs[0] = cwt.coeffs[0]
  #     for level in range(lmax, lmin-1, -1):
  #       c = wt.coeffs[-(level+1)][0].copy()
  #       wt.coeffs[-(level+1)][0] = blend(c, cwt.coeffs[-(level+1)][0], approx**gamma)
  #       approx += c
  #     # Compute the inverse wavelet transform and renormalize.
  #     image = wt.inverse()
  #     image -= np.min(image)
  #     image /= np.max(image)
  #     # image = np.clip(image, 0., 1.)
  #     # median = np.median(image)
  #     # midtone = mts(median, median0)
  #     # print(median0, median, midtone)
  #     # image = mts(image, midtone)
  #   return self.newImage(image) if channels == "RGB" else self.set_channel(channel = channels, data = image)

  def HDRmt2(self, transform = "cubic", lmin = 0, lmax = 5, alpha = .9, beta = 1., rthreshold = .05, gamma = 1., niter = 1, channels = "", betadecay = 1., compressA = True):
    """HDRMT v2. Experimental."""

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
    if channels not in ["RGB", "V", "L'", "L", "Ls", "Ln", "L*", "L*ab", "L*uv", "L*sh"]:
      raise ValueError("""Error, channels must be "RGB", "V", "L'", "L", "Ls", "Ln", "L*", "L*ab", "L*uv" or "L*sh".""")
    print(f"HDRMT (transform = '{transform}') on channel(s) {channels}...")
    # Compute gains.
    betas = [1.+(beta-1.)/betadecay**level for level in range(lmax+1)]
    # HDRMT algorithm.
    image = self.image if channels == "RGB" else self.get_channel(channel = channels)
    # median0 = np.median(image)
    for iiter in range(niter): # HDRMT iterations.
      if niter > 1: print(f"Iteration {iiter+1}/{niter}.")
      # Compute wavelet/median transform.
      if transform == "median":
        wt = multiscale.mmt(image, levels = lmax+1)
      else:
        wt = multiscale.slt(image, levels = lmax+1, starlet = transform)
      # Compute thresholds.
      if rthreshold > 0.:
        thresholds = [np.percentile(abs(wt.coeffs[level][0]), 100.*rthreshold) for level in range(lmax+1)]
      else:
        thresholds = 0.
      # Scale/compress the dynamic range of each level.
      cwt = wt.enhance_details(alphas = alpha, betas = betas, thresholds = thresholds, alphaA = alpha if compressA else 1.)
      # Blend the compressed levels with the original ones,
      # using the approximation at the next scale as fusion mask.
      approx = wt.coeffs[0].copy()
      wt.coeffs[0] = cwt.coeffs[0]
      for level in range(lmax, lmin-1, -1):
        c = wt.coeffs[-(level+1)][0].copy()
        wt.coeffs[-(level+1)][0] = blend(c, cwt.coeffs[-(level+1)][0], approx**gamma)
        approx += c
      # Compute the inverse wavelet/median transform and renormalize.
      image = wt.inverse()
      image -= np.min(image)
      image /= np.max(image)
      # image = np.clip(image, 0., 1.)
      # median = np.median(image)
      # midtone = mts(median, median0)
      # print(median0, median, midtone)
      # image = mts(image, midtone)
    return self.newImage(image) if channels == "RGB" else self.set_channel(channel = channels, data = image)

  def HDRwt3(self, starlet = "cubic", lmin = 0, lmax = 5, alpha = .9, gamma = 1., niter = 1, channels = ""):
    """HDRWT v3. Experimental."""

    def f(x, alpha):
      absx = abs(x)
      y = alpha*absx-(alpha-1.)*absx**(1.+1./alpha)
      return np.sign(x)*y

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
    if channels not in ["RGB", "V", "L'", "L", "Ls", "Ln", "L*", "L*ab", "L*uv", "L*sh"]:
      raise ValueError("""Error, channels must be "RGB", "V", "L'", "L", "Ls", "Ln", "L*", "L*ab", "L*uv" or "L*sh".""")
    print(f"HDRWT on channel(s) {channels}...")
    # HDRWT algorithm.
    image = self.image if channels == "RGB" else self.get_channel(channel = channels)
    for iiter in range(niter): # HDRWT iterations.
      if niter > 1: print(f"Iteration {iiter+1}/{niter}.")
      # Compute wavelet transform.
      wt = multiscale.slt(image, levels = lmax+1, starlet = starlet)
      # Compress the dynamic range of each wavelet level.
      cwt = wt.copy()
      cwt.coeffs[0] = f(wt.coeffs[0], alpha)
      for level in range(lmax, lmin-1, -1):
        cwt.coeffs[-(level+1)][0] = f(wt.coeffs[-(level+1)][0], alpha)
      # Blend the compressed wavelet levels with the original ones,
      # using the approximation at the next scale as fusion mask.
      approx = wt.coeffs[0].copy()
      wt.coeffs[0] = cwt.coeffs[0]
      for level in range(lmax, lmin-1, -1):
        c = wt.coeffs[-(level+1)][0].copy()
        wt.coeffs[-(level+1)][0] = blend(c, cwt.coeffs[-(level+1)][0], approx**gamma)
        approx += c
      # Compute the inverse wavelet transform and renormalize.
      image = wt.inverse()
      image -= np.min(image)
      image /= np.max(image)
    return self.newImage(image) if channels == "RGB" else self.set_channel(channel = channels, data = image)

  def HDRwt4(self, starlet = "cubic", levels = 5, alpha = 1.5, decay = .5, maskgamma = 1., dimgamma = None, channels = "", maskchannel = ""):
    """HDRWT v4. Experimental."""
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
    if channels not in ["RGB", "V", "L'", "L", "Ls", "Ln", "L*", "L*ab", "L*uv", "L*sh"]:
      raise ValueError("""Error, channels must be "RGB", "V", "L'", "L", "Ls", "Ln", "L*", "L*ab", "L*uv" or "L*sh".""")
    if channels == "RGB": self.check_color_model("RGB")
    maskchannel = maskchannel.strip()
    if maskchannel == "":
      if self.colormodel in ["RGB", "gray"]:
        maskchannel = "L"
      elif self.colormodel == "HSV":
        maskchannel = "V"
      elif self.colormodel == "HSL":
        maskchannel = "L'"
      elif self.colormodel in ["Lab", "Luv", "Lch", "Lsh"]:
        maskchannel = "L*"
      else:
        raise ValueError(f"Error, unknown color model {self.colormodel}.")
    if maskchannel not in ["V", "L'", "L", "L*"]:
      raise ValueError("""Error, maskchannel must be "V", "L'", "L" or "L*".""")
    print(f"HDRWT on channel(s) {channels} with mask channel {maskchannel}...")
    # HDRWT algorithm.
    # Get channel(s).
    image = self.image if channels == "RGB" else self.get_channel(channel = channels)
    median0 = np.median(image)
    # Set mask.
    mask = self.get_channel(channel = maskchannel)**maskgamma
    # Compute wavelet transform.
    wt = multiscale.slt(image, levels = levels, starlet = starlet)
    # Process wavelet levels.
    for level in range(levels):
      f = 1.+(alpha-1.)*mask*(decay**level)
      # f *= 2.
      wt.coeffs[-(level+1)][0] *= f
    # Compute inverse wavelet transform and normalize.
    image = wt.inverse()
    median = np.median(image) or 1.0
    image = clip(image*median0/median, verbose = True)
    # Set channel(s).
    output = self.newImage(image) if channels == "RGB" else self.set_channel(channel = channels, data = image)
    # Dim image.
    gamma = 1.+.2*levels if dimgamma is None else dimgamma
    return output.clip(verbose = True)**gamma

  def HDRmt5(self, transform = "cubic", levels = 5, D = 10., gamma = 1., niter = 1, channels = ""):
    """HDRMT v5. Experimental."""

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
    if channels not in ["RGB", "V", "L'", "L", "Ls", "Ln", "L*", "L*ab", "L*uv", "L*sh"]:
      raise ValueError("""Error, channels must be "RGB", "V", "L'", "L", "Ls", "Ln", "L*", "L*ab", "L*uv" or "L*sh".""")
    print(f"HDRMT (transform = '{transform}') on channel(s) {channels}...")
    # HDRMT algorithm.
    image = self.image if channels == "RGB" else self.get_channel(channel = channels)
    for iiter in range(niter): # HDRMT iterations.
      if niter > 1: print(f"Iteration {iiter+1}/{niter}.")
      # Compute wavelet/median transform.
      if transform == "median":
        wt = multiscale.mmt(image, levels = levels)
      else:
        wt = multiscale.slt(image, levels = levels, starlet = transform)
      approx  = wt.coeffs[0]
      details = image-approx
      # Compress the dynamic range of the approximation.
      median0 = np.median(approx)
      approx = np.asinh(D*approx)/np.asinh(D)
      median  = np.median(approx)
      print(median0, median)
      # approx *= median0/median
      # approx *= median0/median
      # details *= median/median0
      image = approx+1.5*details
      # approx = np.asinh(D*approx)/np.asinh(D)
      # m1 = np.max(  approx+details)
      # m2 = np.max(2*approx+details)
      # alpha = 1.-m1/(m2-m1)
      # print(m1, m2, alpha)
      # image = alpha*approx+details
      # print(np.max(image))
      # Compute the inverse wavelet/median transform and renormalize.
      # image = wt.inverse()
      image -= np.min(image)
      image /= np.max(image)
    return self.newImage(image) if channels == "RGB" else self.set_channel(channel = channels, data = image)
