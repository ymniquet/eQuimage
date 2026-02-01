# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 3.0.0 / 2026.01.15
# Doc OK.

"""Histogram stretch.

The following symbols are imported in the equimage/equimagelab namespaces for convenience:
  "hms", "mts", "ghs", "Dharmonic_through".
"""

__all__ = ["hms", "mts", "ghs", "Dharmonic_through"]

import copy
import numpy as np
import scipy.interpolate as spint
from scipy.interpolate import Akima1DInterpolator

from . import stretchfunctions as stf

######################
# Stretch functions. #
######################

def hms(image, D):
  """Apply a harmonic stretch function to the input image.

  The harmonic stretch function defined as

    f(x) = (D+1)*x/(D*x+1)

  is a rational interpolation from f(0) = 0 to f(1) = 1 with f'(0) = D+1.

  Args:
    image (numpy.ndarray): The input image.
    D (float): The stretch parameter (expected > -1).

  Returns:
    numpy.ndarray: The stretched image.
  """
  return stf.harmonic_stretch_function(image, D, False)

def mts(image, midtone):
  """Apply a midtone stretch function to the input image.

  The midtone stretch function defined as

    f(x) = (midtone-1)*x/((2*midtone-1)*x-midtone)

  is a rational interpolation from f(0) = 0 to f(1) = 1 with f(midtone) = 0.5.
  It is nothing else than the harmonic stretch function with D = 1/midtone-2.

  See also:
    :func:`hms`

  Args:
    image (numpy.ndarray): The input image.
    midtone (float): The midtone level (expected in ]0, 1[).

  Returns:
    numpy.ndarray: The stretched image.
  """
  return stf.midtone_stretch_function(image, midtone, False)

def ghs(image, lnD1, b, SYP, SPP = 0., HPP = 1.):
  """Apply a generalized hyperbolic stretch function to the input image.

  For details about generalized hyperbolic stretches, see: https://ghsastro.co.uk/.

  Args:
    image (numpy.ndarray): The input image.
    logD1 (float): The global stretch parameter ln(D+1) (must be >= 0).
    b (float): The local stretch parameter.
    SYP (float): The symmetry point (expected in [0, 1]).
    SPP (float, optional): The shadow protection point (default 0; expected in [0, SYP]).
    HPP (float, optional): The highlight protection point (default 1; expected in [SYP, 1]).
    inverse (bool): Return the inverse transformation function if True.

  Returns:
    numpy.ndarray: The stretched image.
  """
  return stf.ghyperbolic_stretch_function(image, lnD1, b, SYP, SPP, HPP, False)

######################################
# Harmonic stretch parametrizations. #
######################################

def Dharmonic_through(x, y):
  """Return the stretch parameter D such that f(x) = y, with f the harmonic stretch function.

  The harmonic stretch function defined as

    f(x) = (D+1)*x/(D*x+1)

  is a rational interpolation from f(0) = 0 to f(1) = 1 with f'(0) = D+1.

  This function provides an alternative parametrization of f.
  It returns D such that f(x) = y.

  See also:
    :func:`hms`

  Args:
    x (float): The target input level (expected in ]0, 1[).
    y (float): The target output level (expected in ]0, 1[).

  Returns:
    float: The stretch parameter D such that f(x) = y.
  """
  return (y-x)/(x*(1.-y))

#####################################
# For inclusion in the Image class. #
#####################################

class MixinImage:
  """To be included in the Image class."""

  #####################
  # Simple stretches. #
  #####################

  def set_black_point(self, shadow, channels = "", trans = True):
    """Set the black (shadow) level in selected channels of the image.

    The selected channels are clipped below shadow and linearly stretched to map [shadow, 1]
    onto [0, 1]. The output, stretched image channels therefore fit in the [0, infty[ range.

    Args:
      shadow (float): The black (shadow) level (expected < 1).
      channels (str, optional): The selected channels (default "" = all channels).
        See :meth:`Image.apply_channels() <.apply_channels>` or https://astro.ymniquet.fr/codes/equimagelab/docs/channels.html.
      trans (bool, optional): If True (default), embed the transormation in the output image as
        output.trans (see :meth:`Image.apply_channels() <.apply_channels>`).

    Returns:
      Image: The processed image.
    """
    if shadow > .9999: raise ValuerError("Error, shadow must be <= 0.9999.")
    output = self.apply_channels(lambda channel: stf.shadow_stretch_function(channel, shadow), channels, trans = trans)
    if trans: output.trans.xticks = [shadow]
    return output

  def set_shadow_highlight(self, shadow, highlight, channels = "", trans = True):
    """Set shadow and highlight levels in selected channels of the image.

    The selected channels are clipped below shadow and above highlight and linearly stretched
    to map [shadow, highlight] onto [0, 1]. The output, stretched channels therefore fit in
    the [0, 1] range.

    Args:
      shadow (float): The shadow level (expected < 1).
      highlight (float): The highlight level (expected > shadow).
      channels (str, optional): The selected channels (default "" = all channels).
        See :meth:`Image.apply_channels() <.apply_channels>` or https://astro.ymniquet.fr/codes/equimagelab/docs/channels.html.
      trans (bool, optional): If True (default), embed the transormation in the output image as
        output.trans (see :meth:`Image.apply_channels() <.apply_channels>`).

    Returns:
      Image: The processed image.
    """
    if shadow > .9999: raise ValuerError("Error, shadow must be <= 0.9999.")
    if highlight-shadow < .0001: raise ValuerError("Error, highlight-shadow must be >= 0.0001.")
    output = self.apply_channels(lambda channel: stf.shadow_highlight_stretch_function(channel, shadow, highlight), channels, trans = trans)
    if trans: output.trans.xticks = [shadow, highlight]
    return output

  def set_dynamic_range(self, fr, to, channels = "", trans = True):
    """Set the dynamic range of selected channels of the image.

    The selected channels are linearly stretched to map [fr[0], fr[1]] onto [to[0], to[1]],
    and clipped outside the [to[0], to[1]] range.

    Args:
      fr (a tuple or list of two floats such that fr[1] > fr[0]): The input range.
      to (a tuple or list of two floats such that 1 >= to[1] > to[0] >= 0): The output range.
      channels (str, optional): The selected channels (default "" = all channels).
        See :meth:`Image.apply_channels() <.apply_channels>` or https://astro.ymniquet.fr/codes/equimagelab/docs/channels.html.
      trans (bool, optional): If True (default), embed the transormation in the output image as
        output.trans (see :meth:`Image.apply_channels() <.apply_channels>`).

    Returns:
      Image: The processed image.
    """
    if to[0] < 0.: raise ValueError("Error, to[0] must be >= 0 !")
    if to[1] > 1.: raise ValueError("Error, to[1] must be <= 1 !")
    if fr[1]-fr[0] < 0.0001: raise ValueError("Error, fr[1]-fr[0] must be >= 0.0001 !")
    if to[1]-to[0] < 0.0001: raise ValueError("Error, to[1]-to[0] must be >= 0.0001 !")
    return self.apply_channels(lambda channel: stf.dynamic_range_stretch_function(channel, fr, to), channels, trans = trans)

  def harmonic_stretch(self, D, inverse = False, channels = "", trans = True):
    """Apply a harmonic stretch to selected channels of the image.

    The harmonic stretch function defined as

      f(x) = (D+1)*x/(D*x+1)

    is a rational interpolation from f(0) = 0 to f(1) = 1 with f'(0) = D+1.

    See also:
      :meth:`Image.gharmonic_stretch() <.gharmonic_stretch>`

    Args:
      D (float): The stretch parameter (expected > -1).
      inverse (bool, optional): Return the inverse transformation if True (default False).
      channels (str, optional): The selected channels (default "" = all channels).
        See :meth:`Image.apply_channels() <.apply_channels>` or https://astro.ymniquet.fr/codes/equimagelab/docs/channels.html.
      trans (bool, optional): If True (default), embed the transormation in the output image as
        output.trans (see :meth:`Image.apply_channels() <.apply_channels>`).

    Returns:
      Image: The stretched image.
    """
    if D < -.9999: raise ValueError("Error, D must be >= -.9999")
    return self.apply_channels(lambda channel: stf.harmonic_stretch_function(channel, D, inverse), channels, trans = trans)

  def gharmonic_stretch(self, D, SYP = 0., SPP = 0., HPP = 1., inverse = False, channels = "", trans = True):
    """Apply a generalized harmonic stretch to selected channels of the image.

    The generalized harmonic stretch function f is defined as:

      - f(x) = b1*x when x <= SPP,
      - f(x) = a2+b2/(1-D*(x-SYP)) when SPP <= x <= SYP,
      - f(x) = a3+b3/(1+D*(x-SYP)) when SYP <= x <= HPP,
      - f(x) = a4+b4*x when x >= HPP.

    The coefficients a and b are computed so that f is continuous and derivable.
    SYP is the "symmetry point"; SPP is the "shadow protection point" and HPP is the "highlight
    protection point". They can be tuned to preserve contrast in the low and high brightness
    areas, respectively.

    f(x) falls back to the "usual" harmonic stretch function

      f(x) = (D+1)*x/(D*x+1)

    when SPP = SYP = 0 and HPP = 1 (the defaults).

    Moreover, the generalized hyperbolic stretch function for local stretch parameter b = 1 is the
    generalized harmonic stretch function.

    For details about generalized hyperbolic stretches, see: https://ghsastro.co.uk/.

    See also:
      :meth:`Image.harmonic_stretch() <.harmonic_stretch>`,
      :meth:`Image.ghyperbolic_stretch() <.ghyperbolic_stretch>`

    Note:
      Code adapted from https://github.com/mikec1485/GHS/blob/main/src/scripts/GeneralisedHyperbolicStretch/lib/GHSStretch.js
      (published by Mike Cranfield under GNU GPL license).

    Args:
      D (float): The stretch parameter (must be >= 0).
      SYP (float): The symmetry point (expected in [0, 1]).
      SPP (float, optional): The shadow protection point (default 0, must be <= SYP).
      HPP (float, optional): The highlight protection point (default 1, must be >= SYP).
      inverse (bool, optional): Return the inverse transformation if True (default False).
      channels (str, optional): The selected channels (default "" = all channels).
        See :meth:`Image.apply_channels() <.apply_channels>` or https://astro.ymniquet.fr/codes/equimagelab/docs/channels.html.
      trans (bool, optional): If True (default), embed the transormation in the output image as
        output.trans (see :meth:`Image.apply_channels() <.apply_channels>`).

    Returns:
      Image: The stretched image.
    """
    if D < 0.: raise ValueError("Error, D must be >= 0.")
    if SPP > SYP:
      SPP = SYP
      print("Warning, changed SPP = SYP !")
    if HPP < SYP:
      HPP = SYP
      print("Warning, changed HPP = SYP !")
    output = self.apply_channels(lambda channel: stf.gharmonic_stretch_function(channel, D, SYP, SPP, HPP, inverse), channels, trans = trans)
    if trans: output.trans.xticks = [SPP, SYP, HPP]
    return output

  def midtone_stretch(self, midtone, inverse = False, channels = "", trans = True):
    """Apply a midtone stretch to selected channels of the image.

    The midtone stretch function defined as

      f(x) = (midtone-1)*x/((2*midtone-1)*x-midtone)

    is a rational interpolation from f(0) = 0 to f(1) = 1 with f(midtone) = 0.5.
    It is nothing else than the harmonic stretch function with D = 1/midtone-2.

    See also:
      :meth:`Image.harmonic_stretch() <.harmonic_stretch>`

    Args:
      midtone (float): The midtone level (expected in ]0, 1[).
      inverse (bool, optional): Return the inverse transformation if True (default False).
      channels (str, optional): The selected channels (default "" = all channels).
        See :meth:`Image.apply_channels() <.apply_channels>` or https://astro.ymniquet.fr/codes/equimagelab/docs/channels.html.
      trans (bool, optional): If True (default), embed the transormation in the output image as
        output.trans (see :meth:`Image.apply_channels() <.apply_channels>`).

    Returns:
      Image: The stretched image.
    """
    if midtone < .0001 or midtone >= .9999: raise ValueError("Error, midtone must be >= 0.0001 and <= 0.9999.")
    output = self.apply_channels(lambda channel: stf.midtone_stretch_function(channel, midtone, inverse), channels, trans = trans)
    if trans: output.trans.xticks = [midtone]
    return output

  def midtone_transfer(self, midtone, shadow = 0., highlight = 1., low = 0., high = 1., channels = "", trans = True):
    """Apply the shadow/midtone/highlight/low/high levels transfer function to selected channels of the image.

    This method:

      1) Clips the input data in the [shadow, highlight] range and maps [shadow, highlight]
         onto [0, 1].
      2) Applies the midtone stretch function f(x) = (m-1)*x/((2*m-1)*x-m),
         with m = (midtone-shadow)/(highlight-shadow) the remapped midtone.
      3) Maps [low, high] onto [0, 1] and clips the output data outside the [0, 1] range.

    See also:
      :meth:`Image.midtone_stretch() <.midtone_stretch>`

    Args:
      midtone (float): The input midtone level (expected in ]0, 1[).
      shadow (float, optional): The input shadow level (default 0; expected < midtone).
      highlight (float, optional): The input highlight level (default 1; expected > midtone).
      low (float, optional): The "low" output level (default 0; expected <= 0).
      high (float, optional): The "high" output level (default 1; expected >= 1).
      channels (str, optional): The selected channels (default "" = all channels).
        See :meth:`Image.apply_channels() <.apply_channels>` or https://astro.ymniquet.fr/codes/equimagelab/docs/channels.html.
      trans (bool, optional): If True (default), embed the transormation in the output image as
        output.trans (see :meth:`Image.apply_channels() <.apply_channels>`).

    Returns:
      Image: The stretched image.
    """
    if midtone < .0001 or midtone > .9999: raise ValueError("Error, midtone must be >= 0.0001 and <= 0.9999.")
    if midtone-shadow < .0001: raise ValueError("Error, midtone-shadow must be >= 0.0001.")
    if highlight-midtone < .0001: raise ValueError("Error, highlight-midtone must be >= 0.0001.")
    if low > 0.:
      low = 0.
      print("Warning, changed low = 0.")
    if high < 1.:
      high = 1.
      print("Warning, changed high = 1.")
    output = self.apply_channels(lambda channel: stf.midtone_transfer_function(channel, shadow, midtone, highlight, low, high), channels, trans = trans)
    if trans: output.trans.xticks = [shadow, midtone, highlight]
    return output

  def garcsinh_stretch(self, D, SYP = 0., SPP = 0., HPP = 1., inverse = False, channels = "", trans = True):
    """Apply a generalized arcsinh stretch to selected channels of the image.

    The generalized arcsinh stretch function f is defined as:

      - f(x) = b1*x when x <= SPP,
      - f(x) = a2+b2*arcsinh(-D*(x-SYP)) when SPP <= x <= SYP,
      - f(x) = a3+b3*arcsinh( D*(x-SYP)) when SYP <= x <= HPP,
      - f(x) = a4+b4*x when x >= HPP.

    The coefficients a and b are computed so that f is continuous and derivable.
    SYP is the "symmetry point"; SPP is the "shadow protection point" and HPP is the "highlight
    protection point". They can be tuned to preserve contrast in the low and high brightness
    areas, respectively.

    f(x) falls back to the "standard" arcsinh stretch function

      f(x) = arcsinh(D*x)/arcsinh(D)

    when SPP = SYP = 0 and HPP = 1 (the defaults).

    For details about generalized hyperbolic stretches, see: https://ghsastro.co.uk/.

    Note:
      Code adapted from https://github.com/mikec1485/GHS/blob/main/src/scripts/GeneralisedHyperbolicStretch/lib/GHSStretch.js
      (published by Mike Cranfield under GNU GPL license).

    Args:
      D (float): The stretch parameter (must be >= 0).
      SYP (float): The symmetry point (expected in [0, 1]).
      SPP (float, optional): The shadow protection point (default 0, must be <= SYP).
      HPP (float, optional): The highlight protection point (default 1, must be >= SYP).
      inverse (bool, optional): Return the inverse transformation if True (default False).
      channels (str, optional): The selected channels (default "" = all channels).
        See :meth:`Image.apply_channels() <.apply_channels>` or https://astro.ymniquet.fr/codes/equimagelab/docs/channels.html.
      trans (bool, optional): If True (default), embed the transormation in the output image as
        output.trans (see :meth:`Image.apply_channels() <.apply_channels>`).

    Returns:
      Image: The stretched image.
    """
    if D < 0.: raise ValueError("Error, D must be >= 0.")
    if SPP > SYP:
      SPP = SYP
      print("Warning, changed SPP = SYP !")
    if HPP < SYP:
      HPP = SYP
      print("Warning, changed HPP = SYP !")
    output = self.apply_channels(lambda channel: stf.garcsinh_stretch_function(channel, D, SYP, SPP, HPP, inverse), channels, trans = trans)
    if trans: output.trans.xticks = [SPP, SYP, HPP]
    return output

  def ghyperbolic_stretch(self, lnD1, b, SYP, SPP = 0., HPP = 1., inverse = False, channels = "", trans = True):
    """Apply a generalized hyperbolic stretch to selected channels of the image.

    For details about generalized hyperbolic stretches, see: https://ghsastro.co.uk/.

    Args:
      logD1 (float): The global stretch parameter ln(D+1) (must be >= 0).
      b (float): The local stretch parameter.
      SYP (float): The symmetry point (expected in [0, 1]).
      SPP (float, optional): The shadow protection point (default 0, must be <= SYP).
      HPP (float, optional): The highlight protection point (default 1, must be >= SYP).
      inverse (bool, optional): Return the inverse transformation if True (default False).
      channels (str, optional): The selected channels (default "" = all channels).
        See :meth:`Image.apply_channels() <.apply_channels>` or https://astro.ymniquet.fr/codes/equimagelab/docs/channels.html.
      trans (bool, optional): If True (default), embed the transormation in the output image as
        output.trans (see :meth:`Image.apply_channels() <.apply_channels>`).

    Returns:
      numpy.ndarray: The stretched image.
    """
    if lnD1 < 0.: raise ValueError("Error, lnD1 must be >= 0.")
    if SPP > SYP:
      SPP = SYP
      print("Warning, changed SPP = SYP !")
    if HPP < SYP:
      HPP = SYP
      print("Warning, changed HPP = SYP !")
    output = self.apply_channels(lambda channel: stf.ghyperbolic_stretch_function(channel, lnD1, b, SYP, SPP, HPP, inverse), channels, trans = trans)
    if trans: output.trans.xticks = [SPP, SYP, HPP]
    return output

  def gpowerlaw_stretch(self, D, SYP, SPP = 0., HPP = 1., inverse = False, channels = "", trans = True):
    """Apply a generalized power law stretch to selected channels of the image.

    The generalized power law stretch function f is defined as:

      - f(x) = b1*x when x <= SPP,
      - f(x) = a2+b2*(1+(x-SYP))**(D+1) when SPP <= x <= SYP,
      - f(x) = a3+b3*(1-(x-SYP))**(D+1) when SYP <= x <= HPP,
      - f(x) = a4+b4*x when x >= HPP.

    The coefficients a and b are computed so that f is continuous and derivable.
    SYP is the "symmetry point"; SPP is the "shadow protection point" and HPP is the "highlight
    protection point". They can be tuned to preserve contrast in the low and high brightness
    areas, respectively.

    For details about generalized hyperbolic stretches, see: https://ghsastro.co.uk/.

    Args:
      D (float): The stretch parameter (must be >= 0).
      SYP (float): The symmetry point (expected in [0, 1]).
      SPP (float, optional): The shadow protection point (default 0, must be <= SYP).
      HPP (float, optional): The highlight protection point (default 1, must be >= SYP).
      inverse (bool, optional): Return the inverse transformation if True (default False).
      channels (str, optional): The selected channels (default "" = all channels).
        See :meth:`Image.apply_channels() <.apply_channels>` or https://astro.ymniquet.fr/codes/equimagelab/docs/channels.html.
      trans (bool, optional): If True (default), embed the transormation in the output image as
        output.trans (see :meth:`Image.apply_channels() <.apply_channels>`).

    Returns:
      numpy.ndarray: The stretched image.
    """
    if D < 0.: raise ValueError("Error, D must be >= 0.")
    if SPP > SYP:
      SPP = SYP
      print("Warning, changed SPP = SYP !")
    if HPP < SYP:
      HPP = SYP
      print("Warning, changed HPP = SYP !")
    output = self.apply_channels(lambda channel: stf.gpowerlaw_stretch_function(channel, D, SYP, SPP, HPP, inverse), channels, trans = trans)
    if trans: output.trans.xticks = [SPP, SYP, HPP]
    return output

  def gamma_stretch(self, gamma, channels = "", trans = True):
    """Apply a gamma stretch to selected channels of the image.

    The gamma stretch function is defined as:

      f(x) = x**gamma

    This method clips the selected channels below 0 before stretching.

    Args:
      gamma (float): The stretch exponent (must be > 0).
      channels (str, optional): The selected channels (default "" = all channels).
        See :meth:`Image.apply_channels() <.apply_channels>` or https://astro.ymniquet.fr/codes/equimagelab/docs/channels.html.
      trans (bool, optional): If True (default), embed the transormation in the output image as
        output.trans (see :meth:`Image.apply_channels() <.apply_channels>`).

    Returns:
      Image: The stretched image.
    """
    if gamma <= 0.: raise ValueError("Error, gamma must be > 0.")
    return self.apply_channels(lambda channel: stf.gamma_stretch_function(channel, gamma), channels, trans = trans)

  def curve_stretch(self, f, channels = "", trans = True):
    """Apply a curve stretch, defined by an arbitrary function f, to selected channels of the image.

    f may be, e.g., an explicit function or a spline interpolator. It must be defined over the whole
    range spanned by the channel(s).

    Note:
      This is practically a wrapper for :meth:`Image.apply_channels() <.apply_channels>`.

    Args:
      f (function): The function f(numpy.ndarray) → numpy.ndarray applied to the selected channels.
      channels (str, optional): The selected channels (default "" = all channels).
        See :meth:`Image.apply_channels() <.apply_channels>` or https://astro.ymniquet.fr/codes/equimagelab/docs/channels.html.
      trans (bool, optional): If True (default), embed the transormation in the output image as
        output.trans (see :meth:`Image.apply_channels() <.apply_channels>`).

    Returns:
      Image: The stretched image.
    """
    return self.apply_channels(f, channels, trans = trans)

  def spline_stretch(self, x, y, spline = "akima", channels = "", trans = True):
    """Apply a spline curve stretch to selected channels of the image.

    The spline must be defined over the whole range spanned by the channel(s).

    Args:
      x, y (numpy.ndarray): A sampling of the function y = f(x) interpolated by the spline.
      spline (int or str, optional): The spline type. Either an integer (the order) for a B-spline,
        or the string "akima" (for an Akima spline, default).
      channels (str, optional): The selected channels (default "" = all channels).
        See :meth:`Image.apply_channels() <.apply_channels>` or https://astro.ymniquet.fr/codes/equimagelab/docs/channels.html.
      trans (bool, optional): If True (default), embed the transormation in the output image as
        output.trans (see :meth:`Image.apply_channels() <.apply_channels>`).

    Returns:
      Image: The stretched image.
    """
    if isinstance(spline, int):
      tck = spint.splrep(x, y, k = spline)
      def fspline(x): spint.splev(x, tck)
    elif spline == "akima":
      fspline = Akima1DInterpolator(x, y)
    else:
      raise ValueError(f"Error, unknown spline '{spline}'.")
    output = self.apply_channels(fspline, channels = channels, trans = trans)
    if trans:
      output.trans.xm = x
      output.trans.ym = y
    return output

  ######################
  # Complex stretches. #
  ######################

  def statistical_stretch(self, median, boost = 0., maxiter = 5, accuracy = .001, channels = "", trans = True):
    """Statistical stretch of selected channels of the image.

    This method:

      1) Applies (a series) of harmonic stretches to the selected channels in order to bring the
         average median of these channels to the target level.
      2) Optionally, boosts contrast above the target median with a specially designed curve stretch.

    It is recommended to set the black point of the image before statistical stretch.

    Note:
      This is a Python implementation of the statistical stretch algorithm of Seti Astro,
      published by Franklin Marek under the CC BY-NC 4.0 license (http://creativecommons.org/licenses/by-nc/4.0/).
      See: https://www.setiastro.com/statistical-stretch.

    Hint:
      You can apply the harmonic stretches and the final contrast boost separately by calling this
      method twice with the same target median, first with boost = 0, then with boost > 0. As the
      average median of the image already matches the target median, no harmonic stretch will be
      applied on second call.

    See also:
      :meth:`Image.set_black_point() <.set_black_point>`,
      :meth:`Image.harmonic_stretch() <.harmonic_stretch>`

    Args:
      median (float): The target median (expected in ]0, 1[).
      boost (float, optional): The contrast boost (expected >= 0; default 0 = no boost).
      maxiter (int, optional): The maximum number of harmonic stretches applied to reach the target
        median (default 5). For a single channel, the algorithm shall actually converge in a single
        iteration.
      accuracy (float, optional): The target accuracy of the median (default 0.001).
      channels (str, optional): The selected channels (default "" = auto).
        See :meth:`Image.apply_channels() <.apply_channels>` or https://astro.ymniquet.fr/codes/equimagelab/docs/channels.html.
      trans (bool, optional): If True (default), embed the transormation in the output image as
        output.trans (see :meth:`Image.apply_channels() <.apply_channels>`).

    Returns:
      Image: The stretched image.
    """

    def compute_medians(image, channels):
      """Compute the medians of the channels of the input image, returned as a dictionary."""
      if channels == "V":
        medians = {"V": np.median(image.HSV_value())}
      elif channels == "S":
        medians = {"S": np.median(image.HSV_saturation())}
      elif channels == "L'":
        medians = {"L'": np.median(image.HSL_lightness())}
      elif channels == "S'":
        medians = {"S'": np.median(image.HSL_saturation())}
      elif channels in ["L", "Ls", "Lb", "Ln"]:
        medians = {"L": np.median(image.luma())}
      elif channels in ["L*", "L*/ab", "L*/uv", "L*/sh"]:
        medians = {"L*": np.median(image.lightness())}
      else:
        medians = {}
        nc = self.get_nc()
        for c in channels:
          if c.isdigit():
            ic = int(c)-1
            if ic < 0 or ic >= nc: raise ValueError(f"Error, invalid channel '{c}'.")
          elif c in "RGB":
            self.check_color_model("RGB")
            ic = "RGB".index(c)
          elif c == " ": # Skip spaces.
            continue
          else:
            raise ValueError(f"Syntax errror in the channels string '{channels}'.")
          if medians.get(c, None) is not None:
            print(f"Warning, channel '{c}' selected twice or more...")
            continue
          medians[c] = np.median(image.image[ic])
      return medians

    def print_medians(medians):
      """Print the input dictionary of medians."""
      spacer = ""
      for key, median in medians.items():
        print(f"{spacer}Median({key}) = {median:.5f}", end = "")
        spacer = "; "
      print()

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
    # Iterate harmonic stretches until the average median of the channels matches the target median.
    # This shall actually converge in one iteration for a single channel image.
    niter = 0
    output = self
    ctrans = None
    while True:
      print(f"Iteration #{niter}:")
      medians = compute_medians(output, channels) # Compute the medians of the channels.
      print_medians(medians)
      avgmedian = np.mean(list(medians.values())) # Compute the average median.
      if len(medians) > 1: print(f"Average median = {avgmedian:.5f}.")
      converged = (abs(avgmedian-median) < accuracy) # Check convergence.
      if converged or niter >= maxiter: break
      niter += 1
      # Compute the effective stretch parameter D such that f(avgmedian) = median, with f the harmonic stretch function.
      D = Dharmonic_through(avgmedian, median)
      output = output.harmonic_stretch(D, channels = channels, trans = trans and ctrans is None) # Harmonic stretch.
      if trans: # Cumulative transformation.
        if ctrans is None:
          ctrans = copy.copy(output.trans)
          ctrans.xticks = [avgmedian]
        else:
          ctrans.y = stf.harmonic_stretch_function(ctrans.y, D, False)
    if converged:
      print(f"Converged in {niter} iteration(s).")
    else:
      print(f"Warning, did not converge within {maxiter} iteration(s).")
    if boost > 0.: # Boost contrast above the average median.
      print("Boosting constrast above the average median...")
      x = [0., .5*avgmedian, avgmedian, .25+.75*avgmedian, .75+.25*avgmedian, 1.]
      y = [x[0], x[1], x[2], x[3]**(1.-boost), (x[4]**(1.-boost))**(1.-boost), x[5]]
      fboost = Akima1DInterpolator(x, y) # Akima spline.
      clipped = output.clip_channels(channels = channels, trans = trans and ctrans is None) # Clip channels.
      nclipped = np.sum(np.any(clipped.image != output.image, axis = 0))
      if nclipped > 0: print(f"Clipped {nclipped} pixel(s).")
      if trans: # Cumulative transformation.
        if ctrans is None:
          ctrans = copy.copy(clipped.trans)
          ctrans.xticks = [avgmedian]
        else:
          ctrans.y = np.clip(ctrans.y, 0., 1.)
      output = clipped.curve_stretch(fboost, channels = channels, trans = False) # Curve stretch.
      if trans: # Cumulative transformation.
        ctrans.y = fboost(ctrans.y)
    if ctrans is not None: output.trans = ctrans
    return output

  def masked_stretch(self, median, niter, gamma = 1., clip = 0., channels = "", maskchannel = ""):
    r"""Apply a series of masked midtone stretches to selected channels of the image.

    Given a target median, this method applies a series of niter "small" midtone stretches to bring
    the median of the selected channels of the image close to the target. Each of these midtone
    stretches is blended with the previous one using the lightness (or any proxy for it, such as the
    luma) as a mask:

      image_0 = self

      mask_n = [1-lightness(image_n)]**gamma

      image_{n+1} = mask_n*mts(image_n, midtone)+(1-mask_n)*image_n

    The method returns image_{niter}. mts is the midtone stretch function, and the midtone parameter
    is estimated so that median(image_{niter}) is close to the target [yet median(image_{niter})
    will not exactly match the target as the solution is only approximate]. The larger the number
    of iterations, the closer the midtone to 0.5, thus the smoother the stretches. Moreover, the
    features that are or have become bright get little further stretched thanks to the mask.
    This prevents, e.g., stars from overblowing as in a conventional, single hard stretch.

    See also:
      :meth:`Image.midtone_stretch() <.midtone_stretch>`

    Args:
      median (float): The target median (expected in ]0, 1[).
      maxiter (int): The number of iterations (midtone stretches). The larger niter, the smoother
        the unitary stretches.
      gamma (float, optional): The power law transformation applied to the lightness (see above
        equations). The larger gamma, the better preserved the bright features, but the lower the
        contrast in the dark features. Default is 1.
      clip (float, optional): Clip the lightness below that value. Pixels whose lightness is smaller 
        than clip are thus fully stretched (not blended). Default is 0.
      channels (str, optional): The selected channels (default "" = auto).
        See :meth:`Image.apply_channels() <.apply_channels>` or https://astro.ymniquet.fr/codes/equimagelab/docs/channels.html.
      maskchannel (str, optional): The lightness channel (default "" = auto).
        Can be "V", "L'", "L" or "L*".

    Returns:
      Image: The stretched image.
    """

    def estimate_median(median, midtone, niter):
      """Returns the expected median of the image after niter midtone transformations.
      On input, 'median' is the median of the original image. This function does not, however,
      account for the effects of the mask."""
      for iiter in range(niter):
        median = mts(median, midtone)
      return median

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
    if channels not in ["RGB", "V", "L'", "L", "Ls", "Ln", "L*", "L*/ab", "L*/uv", "L*/sh"]:
      raise ValueError("""Error, channels must be "RGB", "V", "L'", "L", "Ls", "Ln", "L*", "L*/ab", "L*/uv" or "L*/sh".""")
    if channels == "RGB": self.check_color_model("RGB")
    channels_ = "L" if channels in ["Ls", "Ln"] else channels
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
    print(f"Masked stretch on channel(s) {channels} with mask channel {maskchannel}...")
    # Compute the midtone by dichotomy.
    target = median # Rename the target median.
    median0 = np.median(self if channels == "RGB" else self.get_channel(channel = channels))
    midtone1 = .25 ; median1 = estimate_median(median0, midtone1, niter)
    midtone2 = .75 ; median2 = estimate_median(median0, midtone2, niter)
    if (median1-target)*(median2-target) > 0.: # No solution within the [.25, .75] range.
      raise ValueError("Error, the target median is too far from the original median of the image. Increase niter.")
    midtone = (midtone1+midtone2)/2.
    median = estimate_median(median0, midtone, niter)
    while abs(median-target) > .001:
      if (median1-target)*(median-target) < 0.:
        midtone2, median2 = midtone, median
      else:
        midtone1, median1 = midtone, median
      midtone = (midtone1+midtone2)/2.
      median = estimate_median(median0, midtone, niter)
    print(f"Midtone = {midtone:.5f}.")
    # Apply niter masked midtone stretches to the image.
    output = self
    for iiter in range(niter):
      lightness = output.get_channel(channel = maskchannel)
      mask = np.clip((1.-lightness)/(1.-clip), 0., 1.)**gamma
      output = output.blend(output.midtone_stretch(channels = channels_, midtone = midtone), mask)
    # Protect highlights if appropriate.
    if channels == "Ls":
      output = output.protect_highlights_saturation()
    elif channels == "Ln":
      maximum = np.max(output.image)
      if maximum > 1.: output.image /= maximum
    # compute final median.
    median = np.median(output if channels == "RGB" else output.get_channel(channel = channels))
    print(f"Final median = {median:.5f}.")
    return output
