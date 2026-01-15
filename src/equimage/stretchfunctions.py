# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 3.0.0 / 2026.01.15
# Doc OK.

"""Histogram stretch functions."""

import numpy as np

def shadow_stretch_function(x, shadow):
  """Return the linear shadow stretch function f(x).

  The input data x is clipped below shadow and linearly stretched to map [shadow, 1] onto [0, 1].
  The output, stretched data therefore fits in the [0, infty[ range.

  Args:
    x (numpy.ndarray): The input data.
    shadow (float): The shadow level (expected < 1).

  Returns:
    numpy.ndarray: The stretched data.
  """
  x = np.clip(x, shadow, None)
  return (x-shadow)/(1.-shadow)

def shadow_highlight_stretch_function(x, shadow, highlight):
  """Return the linear shadow/highlight stretch function f(x).

  The input data x is clipped below shadow and above highlight and linearly stretched to map
  [shadow, highlight] onto [0, 1]. The output, stretched data therefore fits in the [0, 1] range.

  Args:
    x (numpy.ndarray): The input data.
    shadow (float): The shadow level (expected < 1).
    highlight (float): The highlight level (expected > shadow).

  Returns:
    numpy.ndarray: The stretched data.
  """
  x = np.clip(x, shadow, highlight)
  return (x-shadow)/(highlight-shadow)

def dynamic_range_stretch_function(x, fr, to):
  """Return the linear dynamic range stretch function f(x).

  The input data x is linearly stretched to map [fr[0], fr[1]] onto [to[0], to[1]], then clipped
  outside the [to[0], to[1]] range.

  Args:
    x (numpy.ndarray): The input data.
    fr (a tuple or list of two floats): The input range.
    to (a tuple or list of two floats): The output range.

  Returns:
    numpy.ndarray: The stretched data.
  """
  return np.interp(x, fr, to)

def harmonic_stretch_function(x, D, inverse):
  """Return the harmonic stretch function f(x).

  The harmonic stretch function defined as

    f(x) = (D+1)*x/(D*x+1)

  is a rational interpolation from f(0) = 0 to f(1) = 1 with f'(0) = D+1.

  See also:
    :func:`gharmonic_stretch_function`

  Args:
    x (numpy.ndarray): The input data.
    D (float): The stretch parameter (expected > -1).
    inverse (bool): Return the inverse stretch function if True.

  Returns:
    numpy.ndarray: The stretched data.
  """
  return x/((D+1.)-D*x) if inverse else (D+1.)*x/(D*x+1.)

def gharmonic_stretch_function(x, D, SYP, SPP, HPP, inverse):
  """Return the generalized harmonic stretch function f(x).

  The generalized harmonic stretch function is defined as:

    - f(x) = b1*x when x <= SPP,
    - f(x) = a2+b2/(1-D*(x-SYP)) when SPP <= x <= SYP,
    - f(x) = a3+b3/(1+D*(x-SYP)) when SYP <= x <= HPP,
    - f(x) = a4+b4*x when x >= HPP.

  The coefficients a and b are computed so that f is continuous and derivable.

  f(x) falls back to the "usual" harmonic stretch function

    f(x) = (D+1)*x/(D*x+1)

  when SPP = SYP = 0 and HPP = 1.

  Moreover, the generalized hyperbolic stretch function for local stretch parameter b = 1 is the
  generalized harmonic stretch function.

  For details about generalized hyperbolic stretches, see: https://ghsastro.co.uk/.

  See also:
    :func:`harmonic_stretch_function`,
    :func:`ghyperbolic_stretch_function`

  Note:
    Code adapted from https://github.com/mikec1485/GHS/blob/main/src/scripts/GeneralisedHyperbolicStretch/lib/GHSStretch.js
    (published by Mike Cranfield under GNU GPL license).

  Args:
    x (numpy.ndarray): The input data.
    D (float): The stretch parameter (expected >= 0).
    SYP (float): The symmetry point (expected in [0, 1]).
    SPP (float): The shadow protection point (expected in [0, SYP]).
    HPP (float): The highlight protection point (expected in [SYP, 1]).
    inverse (bool): Return the inverse stretch function if True.

  Returns:
    numpy.ndarray: The stretched data.
  """
  if abs(D) < 1.e-6: # Identity.
    return x
  else:
    qs = 1./(1.+D*(SYP-SPP))
    q0 = qs-D*SPP/(1.+D*(SYP-SPP))**2
    qh = 2.-1./(1.+D*(HPP-SYP))
    q1 = qh+D*(1.-HPP)/(1.+D*(HPP-SYP))**2
    q  = 1./(q1-q0)
    # Coefficient for x < SPP.
    b1 =  q*D/(1.+D*(SYP-SPP))**2
    # Coefficients for SPP <= x < SYP.
    a2 = -q*q0
    b2 =  q
    # Coefficients for SYP <= x < HPP.
    a3 =  q*(2.-q0)
    b3 = -q
    # Coefficients for x >= HPP.
    a4 =  q*(qh-q0-D*HPP/(1.+D*(HPP-SYP))**2)
    b4 =  q*D/(1.+D*(HPP-SYP))**2
    # Generalized harmonic transformation.
    y = np.empty_like(x)
    if not inverse:
      mask = (x <  SPP)
      y[mask] =    b1*x[mask]
      mask = (x >= SPP) & (x < SYP)
      y[mask] = a2+b2/(1.+D*(SYP-x[mask]))
      mask = (x >= SYP) & (x < HPP)
      y[mask] = a3+b3/(1.+D*(x[mask]-SYP))
      mask = (x >= HPP)
      y[mask] = a4+b4*x[mask]
    else:
      SPT = b1*SPP
      SYT = a2+b2
      HPT = a4+b4*HPP
      mask = (x <  SPT)
      y[mask] = x[mask]/b1
      mask = (x >= SPT) & (x < SYT)
      y[mask] = SYP-(b2/(x[mask]-a2)-1.)/D
      mask = (x >= SYT) & (x < HPT)
      y[mask] = SYP+(b3/(x[mask]-a3)-1.)/D
      mask = (x >= HPT)
      y[mask] = (x[mask]-a4)/b4
    return y

def midtone_stretch_function(x, midtone, inverse):
  """Return the midtone stretch function f(x).

  The midtone stretch function defined as

    f(x) = (midtone-1)*x/((2*midtone-1)*x-midtone)

  is a rational interpolation from f(0) = 0 to f(1) = 1 with f(midtone) = 0.5.
  It is nothing else than the harmonic stretch function with D = 1/midtone-2.

  See also:
    :func:`harmonic_stretch_function`

  Args:
    x (numpy.ndarray): The input data.
    midtone (float): The midtone level (expected in ]0, 1[]).
    inverse (bool): Return the inverse stretch function if True.

  Returns:
    numpy.ndarray: The stretched data.
  """
  return midtone*x/((2.*midtone-1.)*x-midtone+1.) if inverse else (midtone-1.)*x/((2.*midtone-1.)*x-midtone)

def midtone_transfer_function(x, shadow, midtone, highlight, low, high):
  """Return the shadow/midtone/highlight/low/high levels transfer function f(x).

  This function:

    1) Clips the input data in the [shadow, highlight] range and maps [shadow, highlight]
       onto [0, 1].
    2) Applies the midtone stretch function f(x) = (m-1)*x/((2*m-1)*x-m),
       with m = (midtone-shadow)/(highlight-shadow) the remapped midtone.
    3) Maps [low, high] onto [0, 1] and clips the output data outside the [0, 1] range.

  See also:
    :func:`midtone_stretch_function`

  Args:
    x (numpy.ndarray): The input data.
    midtone (float): The input midtone level (expected in ]0, 1[).
    shadow (float): The input shadow level (expected < midtone).
    highlight (float): The input highlight level (expected > midtone).
    low (float): The "low" output level (expected <= 0).
    high (float): The "high" output level (expected >= 1).

  Returns:
    numpy.ndarray: The stretched data.
  """
  midtone = (midtone-shadow)/(highlight-shadow)
  x = np.clip(x, shadow, highlight)
  x = (x-shadow)/(highlight-shadow)
  y = (midtone-1.)*x/((2.*midtone-1.)*x-midtone)
  return np.interp(y, (low, high), (0., 1.))

def arcsinh_stretch_function(x, D):
  """Return the arcsinh stretch function f(x).

  The arcsinh stretch function is defined as:

    f(x) = arcsinh(D*x)/arcsinh(D)

  See also:
    :func:`garcsinh_stretch_function`

  Args:
    x (numpy.ndarray): The input data.
    D (float): The stretch parameter (expected >= 0).

  Returns:
    numpy.ndarray: The stretched data.
  """
  return np.arcsinh(D*x)/np.arcsinh(D) if abs(D) > 1.e-6 else x

def garcsinh_stretch_function(x, D, SYP, SPP, HPP, inverse):
  """Return the generalized arcsinh stretch function f(x).

  This is a generalization of the arcsinh stretch function, defined as:

    - f(x) = b1*x when x <= SPP,
    - f(x) = a2+b2*arcsinh(-D*(x-SYP)) when SPP <= x <= SYP,
    - f(x) = a3+b3*arcsinh( D*(x-SYP)) when SYP <= x <= HPP,
    - f(x) = a4+b4*x when x >= HPP.

  The coefficients a and b are computed so that f is continuous and derivable.

  f(x) falls back to the "usual" arcsinh stretch function

    f(x) = arcsinh(D*x)/arcsinh(D)

  when SPP = SYP = 0 and HPP = 1.

  For details about generalized hyperbolic stretches, see: https://ghsastro.co.uk/.

  See also:
    :func:`arcsinh_stretch_function`

  Note:
    Code adapted from https://github.com/mikec1485/GHS/blob/main/src/scripts/GeneralisedHyperbolicStretch/lib/GHSStretch.js
    (published by Mike Cranfield under GNU GPL license).

  Args:
    x (numpy.ndarray): The input data.
    D (float): The stretch parameter (expected >= 0).
    SYP (float): The symmetry point (expected in [0, 1]).
    SPP (float): The shadow protection point (expected in [0, SYP]).
    HPP (float): The highlight protection point (expected in [SYP, 1]).
    inverse (bool): Return the inverse stretch function if True.

  Returns:
    numpy.ndarray: The stretched data.
  """
  if abs(D) < 1.e-6: # Identity.
    return x
  else:
    qs = -np.arcsinh(D*(SYP-SPP))
    q0 = qs-SPP*D/np.sqrt(1.+(D*(SYP-SPP))**2)
    qh =  np.arcsinh(D*(HPP-SYP))
    q1 = qh+(1.-HPP)*D/np.sqrt(1.+(D*(HPP-SYP))**2)
    q  = 1./(q1-q0)
    # Coefficient for x < SPP.
    b1 =  q*D/np.sqrt(1.+(D*(SYP-SPP))**2)
    # Coefficients for SPP <= x < SYP.
    a2 = -q*q0
    b2 = -q
    # Coefficients for SYP <= x < HPP.
    a3 = -q*q0
    b3 =  q
    # Coefficients for x >= HPP.
    a4 =  q*(qh-q0-HPP*D/np.sqrt(1.+(D*(HPP-SYP))**2))
    b4 =  q*D/np.sqrt(1.+(D*(HPP-SYP))**2)
    # Generalized arcsinh transformation.
    y = np.empty_like(x)
    if not inverse:
      mask = (x <  SPP)
      y[mask] =    b1*x[mask]
      mask = (x >= SPP) & (x < SYP)
      y[mask] = a2+b2*np.arcsinh(D*(SYP-x[mask]))
      mask = (x >= SYP) & (x < HPP)
      y[mask] = a3+b3*np.arcsinh(D*(x[mask]-SYP))
      mask = (x >= HPP)
      y[mask] = a4+b4*x[mask]
    else:
      SPT = b1*SPP
      SYT = a2
      HPT = a4+b4*HPP
      mask = (x <  SPT)
      y[mask] = x[mask]/b1
      mask = (x >= SPT) & (x < SYT)
      y[mask] = SYP-np.sinh((x[mask]-a2)/b2)/D
      mask = (x >= SYT) & (x < HPT)
      y[mask] = SYP+np.sinh((x[mask]-a3)/b3)/D
      mask = (x >= HPT)
      y[mask] = (x[mask]-a4)/b4
    return y

def ghyperbolic_stretch_function(x, logD1, b, SYP, SPP, HPP, inverse):
  """Return the generalized hyperbolic stretch function f(x).

  For details about generalized hyperbolic stretches, see: https://ghsastro.co.uk/.

  Note:
    Code adapted from https://github.com/mikec1485/GHS/blob/main/src/scripts/GeneralisedHyperbolicStretch/lib/GHSStretch.js
    (published by Mike Cranfield under GNU GPL license).

  Args:
    x (numpy.ndarray): The input data.
    logD1 (float): The global stretch parameter ln(D+1) (expected >= 0).
    b (float): The local stretch parameter.
    SYP (float): The symmetry point (expected in [0, 1]).
    SPP (float): The shadow protection point (expected in [0, SYP]).
    HPP (float): The highlight protection point (expected in [SYP, 1]).
    inverse (bool): Return the inverse stretch function if True.

  Returns:
    numpy.ndarray: The stretched data.
  """
  D = np.exp(logD1)-1.
  if abs(D) < 1.e-6: # Identity.
    return x
  else:
    y = np.empty_like(x)
    if abs(b) < 1.e-6:
      qs = np.exp(-D*(SYP-SPP))
      q0 = qs-D*SPP*np.exp(-D*(SYP-SPP))
      qh = 2.-np.exp(-D*(HPP-SYP))
      q1 = qh+D*(1.-HPP)*np.exp(-D*(HPP-SYP))
      q  = 1./(q1-q0)
      # Coefficient for x < SPP.
      b1 = q*D*np.exp(-D*(SYP-SPP))
      # Coefficients for SPP <= x < SYP.
      a2 = -q*q0
      b2 =  q
      c2 = -D*SYP
      d2 =  D
      # Coefficients for SYP <= x < HPP.
      a3 =  q*(2.-q0)
      b3 = -q
      c3 =  D*SYP
      d3 = -D
      # Coefficients for x >= HPP.
      a4 = q*(qh-q0-D*HPP*np.exp(-D*(HPP-SYP)))
      b4 = q*D*np.exp(-D*(HPP-SYP))
      # GHS transformation.
      if not inverse:
        mask = (x <  SPP)
        y[mask] =    b1*x[mask]
        mask = (x >= SPP) & (x < SYP)
        y[mask] = a2+b2*np.exp(c2+d2*x[mask])
        mask = (x >= SYP) & (x < HPP)
        y[mask] = a3+b3*np.exp(c3+d3*x[mask])
        mask = (x >= HPP)
        y[mask] = a4+b4*x[mask]
      else:
        SPT = b1*SPP
        SYT = a2+b2#*np.exp(c2+d2*SYP)
        HPT = a4+b4*HPP
        mask = (x <  SPT)
        y[mask] = x[mask]/b1
        mask = (x >= SPT) & (x < SYT)
        y[mask] = (np.log((x[mask]-a2)/b2)-c2)/d2
        mask = (x >= SYT) & (x < HPT)
        y[mask] = (np.log((x[mask]-a3)/b3)-c3)/d3
        mask = (x >= HPT)
        y[mask] = (x[mask]-a4)/b4
    elif abs(b+1.) < 1.e-6:
      qs = -np.log(1.+D*(SYP-SPP))
      q0 = qs-D*SPP/(1.+D*(SYP-SPP))
      qh =  np.log(1.+D*(HPP-SYP))
      q1 = qh+D*(1.-HPP)/(1.+D*(HPP-SYP))
      q  = 1./(q1-q0)
      # Coefficient for x < SPP.
      b1 = q*D/(1.+D*(SYP-SPP))
      # Coefficients for SPP <= x < SYP.
      a2 = -q*q0
      b2 = -q
      c2 = 1.+D*SYP
      d2 = -D
      # Coefficients for SYP <= x < HPP.
      a3 = -q*q0
      b3 =  q
      c3 = 1.-D*SYP
      d3 =  D
      # Coefficients for x >= HPP.
      a4 = q*(qh-q0-D*HPP/(1.+D*(HPP-SYP)))
      b4 = q*D/(1.+D*(HPP-SYP))
      # GHS transformation.
      if not inverse:
        mask = (x <  SPP)
        y[mask] =    b1*x[mask]
        mask = (x >= SPP) & (x < SYP)
        y[mask] = a2+b2*np.log(c2+d2*x[mask])
        mask = (x >= SYP) & (x < HPP)
        y[mask] = a3+b3*np.log(c3+d3*x[mask])
        mask = (x >= HPP)
        y[mask] = a4+b4*x[mask]
      else:
        SPT =    b1*SPP
        SYT = a2#+b2*np.log(c2+d2*SYP)
        HPT = a4+b4*HPP
        mask = (x <  SPT)
        y[mask] = x[mask]/b1
        mask = (x >= SPT) & (x < SYT)
        y[mask] = (np.exp((x[mask]-a2)/b2)-c2)/d2
        mask = (x >= SYT) & (x < HPT)
        y[mask] = (np.exp((x[mask]-a3)/b3)-c3)/d3
        mask = (x >= HPT)
        y[mask] = (x[mask]-a4)/b4
    else:
      if b < 0.:
        b  = -b
        qs = (1.-(1.+D*b*(SYP-SPP))**((b-1.)/b))/(b-1.)
        q0 = qs-D*SPP*(1.+D*b*(SYP-SPP))**(-1./b)
        qh = ((1.+D*b*(HPP-SYP))**((b-1.)/b)-1.)/(b-1.)
        q1 = qh+D*(1.-HPP)*(1.+D*b*(HPP-SYP))**(-1./b)
        q  = 1./(q1-q0)
        # Coefficient for x < SPP.
        b1 = q*D*(1.+D*b*(SYP-SPP))**(-1./b)
        # Coefficients for SPP <= x < SYP.
        a2 =  q*(1./(b-1.)-q0)
        b2 = -q/(b-1.)
        c2 = 1.+D*b*SYP
        d2 = -D*b
        e2 = (b-1.)/b
        # Coefficients for SYP <= x < HPP.
        a3 = q*(-1./(b-1.)-q0)
        b3 = q/(b-1.)
        c3 = 1.-D*b*SYP
        d3 = D*b
        e3 = (b-1.)/b
        # Coefficients for x >= HPP.
        a4 = q*(qh-q0-D*HPP*(1.+D*b*(HPP-SYP))**(-1./b))
        b4 = q*D*(1.+D*b*(HPP-SYP))**(-1./b)
      else:
        qs = (1.+D*b*(SYP-SPP))**(-1./b)
        q0 = qs-D*SPP*(1.+D*b*(SYP-SPP))**(-(1.+b)/b)
        qh = 2.-(1.+D*b*(HPP-SYP))**(-1./b)
        q1 = qh+D*(1.-HPP)*(1.+D*b*(HPP-SYP))**(-(1.+b)/b)
        q  = 1./(q1-q0)
        # Coefficient for x < SPP.
        b1 = q*D*(1.+D*b*(SYP-SPP))**(-(1.+b)/b)
        # Coefficients for SPP <= x < SYP.
        a2 = -q*q0
        b2 =  q
        c2 = 1.+D*b*SYP
        d2 = -D*b
        e2 = -1./b
        # Coefficients for SYP <= x < HPP.
        a3 =  q*(2.-q0)
        b3 = -q
        c3 = 1.-D*b*SYP
        d3 = D*b
        e3 = -1./b
        # Coefficients for x >= HPP.
        a4 = q*(qh-q0-D*HPP*(1.+D*b*(HPP-SYP))**(-(b+1.)/b))
        b4 = q*D*(1.+D*b*(HPP-SYP))**(-(b+1.)/b)
      # GHS transformation.
      if not inverse:
        mask = (x <  SPP)
        y[mask] =    b1*x[mask]
        mask = (x >= SPP) & (x < SYP)
        y[mask] = a2+b2*(c2+d2*x[mask])**e2
        mask = (x >= SYP) & (x < HPP)
        y[mask] = a3+b3*(c3+d3*x[mask])**e3
        mask = (x >= HPP)
        y[mask] = a4+b4*x[mask]
      else:
        SPT =    b1*SPP
        SYT = a2+b2#*(c2+d2*SYP)**e2
        HPT = a4+b4*HPP
        mask = (x <  SPT)
        y[mask] = x[mask]/b1
        mask = (x >= SPT) & (x < SYT)
        y[mask] = (((x[mask]-a2)/b2)**(1./e2)-c2)/d2
        mask = (x >= SYT) & (x < HPT)
        y[mask] = (((x[mask]-a3)/b3)**(1./e3)-c3)/d3
        mask = (x >= HPT)
        y[mask] = (x[mask]-a4)/b4
    return y

def gpowerlaw_stretch_function(x, D, SYP, SPP, HPP, inverse):
  """Return the generalized power law stretch function f(x).

  The generalized power law stretch function is defined as:

    - f(x) = b1*x when x <= SPP,
    - f(x) = a2+b2*(1+(x-SYP))**(D+1) when SPP <= x <= SYP,
    - f(x) = a3+b3*(1-(x-SYP))**(D+1) when SYP <= x <= HPP,
    - f(x) = a4+b4*x when x >= HPP.

  The coefficients a and b are computed so that f is continuous and derivable.

  For details about generalized hyperbolic stretches, see: https://ghsastro.co.uk/.

  Args:
    x (numpy.ndarray): The input data.
    D (float): The stretch parameter (expected >= 0).
    SYP (float): The symmetry point (expected in [0, 1]).
    SPP (float): The shadow protection point (expected in [0, SYP]).
    HPP (float): The highlight protection point (expected in [SYP, 1]).
    inverse (bool): Return the inverse stretch function if True.

  Returns:
    numpy.ndarray: The stretched data.
  """
  if abs(D) < 1.e-6: # Identity.
    return x
  else:
    qs = (1.-(SYP-SPP))**(D+1.)
    q0 = qs-(D+1.)*SPP*(1.-(SYP-SPP))**D
    qh = 2.-(1.-(HPP-SYP))**(D+1.)
    q1 = qh+(D+1.)*(1.-HPP)*(1.-(HPP-SYP))**D
    q  = 1./(q1-q0)
    # Coefficient for x < SPP.
    b1 =  q*(D+1.)*(1.-(SYP-SPP))**D
    # Coefficients for SPP <= x < SYP.
    a2 = -q*q0
    b2 =  q
    # Coefficients for SYP <= x < HPP.
    a3 =  q*(2.-q0)
    b3 = -q
    # Coefficients for x >= HPP.
    a4 =  q*(qh-q0-(D+1.)*HPP*(1.-(HPP-SYP))**D)
    b4 =  q*(D+1.)*(1.-(HPP-SYP))**D
    # Generalized power law transformation.
    y = np.empty_like(x)
    if not inverse:
      mask = (x <  SPP)
      y[mask] =    b1*x[mask]
      mask = (x >= SPP) & (x < SYP)
      y[mask] = a2+b2*(1.-(SYP-x[mask]))**(D+1.)
      mask = (x >= SYP) & (x < HPP)
      y[mask] = a3+b3*(1.-(x[mask]-SYP))**(D+1.)
      mask = (x >= HPP)
      y[mask] = a4+b4*x[mask]
    else:
      SPT = b1*SPP
      SYT = a2+b2
      HPT = a4+b4*HPP
      mask = (x <  SPT)
      y[mask] = x[mask]/b1
      mask = (x >= SPT) & (x < SYT)
      y[mask] = SYP-1.+((x[mask]-a2)/b2)**(1./(D+1.))
      mask = (x >= SYT) & (x < HPT)
      y[mask] = SYP+1.-((x[mask]-a3)/b3)**(1./(D+1.))
      mask = (x >= HPT)
      y[mask] = (x[mask]-a4)/b4
    return y

def gamma_stretch_function(x, gamma):
  """Return the gamma stretch function f(x).

  The gamma stretch function is defined as:

    f(x) = x**gamma

  This function clips the input data x below 0 before stretching.

  Args:
    x (numpy.ndarray): The input data.
    gamma (float): The stretch exponent (expected > 0).

  Returns:
    numpy.ndarray: The stretched data.
  """
  x = np.clip(x, 0., None)
  return x**gamma
