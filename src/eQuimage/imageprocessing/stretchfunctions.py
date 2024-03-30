# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.4.0 / 2024.03.30

"""Histogram stretch functions."""

import numpy as np

def midtone_stretch_function(x_, params):
  """Return the midtone stretch function f(x_) for parameters 'params' = (shadow, midtone, highlight, low, high)."""
  shadow, midtone, highlight, low, high = params
  midtone = (midtone-shadow)/(highlight-shadow)
  x = np.clip(x_, shadow, highlight)
  x = np.interp(x, (shadow, highlight), (0., 1.))
  y = (midtone-1.)*x/((2.*midtone-1.)*x-midtone)
  return np.interp(y, (low, high), (0., 1.))

def blackpoint_stretch_function(x_, params):
  """Return the linear black point stretch function f(x_) for parameters 'params' = (shadow, )."""
  shadow, = params
  x = np.clip(x_, shadow, 1.)
  return np.interp(x, (shadow, 1.), (0., 1.))

def arcsinh_stretch_function(x_, params):
  """Return the arcsinh stretch function f(x_) for parameters 'params' = (shadow, stretch)."""
  shadow, stretch = params
  x = np.clip(x_, shadow, 1.)
  x = np.interp(x, (shadow, 1.), (0., 1.))
  if abs(stretch) < 1.e-6: # Identity.
    return x
  else:
    return np.arcsinh(stretch*x)/np.arcsinh(stretch)

def ghyperbolic_stretch_function(x_, params):
  """Return the generalized hyperbolic stretch function f(x_) for parameters 'params' = (log(D+1), B, SYP, SPP, HPP, inverse).
     See: https://ghsastro.co.uk/.
     Code adapted from https://github.com/mikec1485/GHS/blob/main/src/scripts/GeneralisedHyperbolicStretch/lib/GHSStretch.js."""
  logD1, B, SYP, SPP, HPP, inverse = params
  D = np.exp(logD1)-1.
  x = np.clip(x_, 0., 1.)
  if abs(D) < 1.e-6: # Identity.
    return x
  else:
    y = np.empty_like(x)
    if abs(B) < 1.e-6:
      qs = np.exp(-D*(SYP-SPP))
      q0 = qs-D*SPP*np.exp(-D*(SYP-SPP))
      qh = 2.-np.exp(-D*(HPP-SYP))
      q1 = qh+D*(1.-HPP)*np.exp(-D*(HPP-SYP))
      q  = 1./(q1-q0)
      # Coefficient for x < SPP.
      b1 = D*np.exp(-D*(SYP-SPP))*q
      # Coefficients for SPP <= x < SYP.
      a2 = -q0*q
      b2 = q
      c2 = -D*SYP
      d2 = D
      # Coefficients for SYP <= x < HPP.
      a3 = (2.-q0)*q
      b3 = -q
      c3 = D*SYP
      d3 = -D
      # Coefficients for x >= HPP.
      a4 = (qh-q0-D*HPP*np.exp(-D*(HPP-SYP)))*q
      b4 = D*np.exp(-D*(HPP-SYP))*q
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
        SPT =    b1*SPP
        SYT = a2+b2*np.exp(c2+d2*SYP)
        HPT = a4+b4*HPP
        mask = (x <  SPT)
        y[mask] = x[mask]/b1
        mask = (x >= SPT) & (x < SYT)
        y[mask] = (np.log((x[mask]-a2)/b2)-c2)/d2
        mask = (x >= SYT) & (x < HPT)
        y[mask] = (np.log((x[mask]-a3)/b3)-c3)/d3
        mask = (x >= HPT)
        y[mask] = (x[mask]-a4)/b4
    elif abs(B+1.) < 1.e-6:
      qs = -np.log(1.+D*(SYP-SPP))
      q0 = qs-D*SPP/(1.+D*(SYP-SPP))
      qh = np.log(1.+D*(HPP-SYP))
      q1 = qh+D*(1.-HPP)/(1.+D*(HPP-SYP))
      q  = 1./(q1-q0)
      # Coefficient for x < SPP.
      b1 = D/(1.+D*(SYP-SPP))*q
      # Coefficients for SPP <= x < SYP.
      a2 = -q0*q
      b2 = -q
      c2 = 1.+D*SYP
      d2 = -D
      # Coefficients for SYP <= x < HPP.
      a3 = -q0*q
      b3 = q
      c3 = 1.-D*SYP
      d3 = D
      # Coefficients for x >= HPP.
      a4 = (qh-q0-D*HPP/(1.+D*(HPP-SYP)))*q
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
        SYT = a2+b2*np.log(c2+d2*SYP)
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
      if B < 0.:
        B  = -B
        qs = (1.-(1.+D*B*(SYP-SPP))**((B-1.)/B))/(B-1.)
        q0 = qs-D*SPP*(1.+D*B*(SYP-SPP))**(-1./B)
        qh = ((1.+D*B*(HPP-SYP))**((B-1.)/B)-1.)/(B-1.)
        q1 = qh+D*(1.-HPP)*(1.+D*B*(HPP-SYP))**(-1./B)
        q  = 1./(q1-q0)
        # Coefficient for x < SPP.
        b1 = D*(1.+D*B*(SYP-SPP))**(-1./B)*q
        # Coefficients for SPP <= x < SYP.
        a2 = (1./(B-1.)-q0)*q
        b2 = -q/(B-1.)
        c2 = 1.+D*B*SYP
        d2 = -D*B
        e2 = (B-1.)/B
        # Coefficients for SYP <= x < HPP.
        a3 = (-1./(B-1.)-q0)*q
        b3 = q/(B-1.)
        c3 = 1.-D*B*SYP
        d3 = D*B
        e3 = (B-1.)/B
        # Coefficients for x >= HPP.
        a4 = (qh-q0-D*HPP*(1.+D*B*(HPP-SYP))**(-1./B))*q
        b4 = D*(1.+D*B*(HPP-SYP))**(-1./B)*q
      else:
        qs = (1.+D*B*(SYP-SPP))**(-1./B)
        q0 = qs-D*SPP*(1.+D*B*(SYP-SPP))**(-(1.+B)/B)
        qh = 2.-(1.+D*B*(HPP-SYP))**(-1./B)
        q1 = qh+D*(1.-HPP)*(1.+D*B*(HPP-SYP))**(-(1.+B)/B)
        q  = 1./(q1-q0)
        # Coefficient for x < SPP.
        b1 = D*(1.+D*B*(SYP-SPP))**(-(1.+B)/B)*q
        # Coefficients for SPP <= x < SYP.
        a2 = -q0*q
        b2 = q
        c2 = 1.+D*B*SYP
        d2 = -D*B
        e2 = -1./B
        # Coefficients for SYP <= x < HPP.
        a3 = (2.-q0)*q
        b3 = -q
        c3 = 1.-D*B*SYP
        d3 = D*B
        e3 = -1./B
        # Coefficients for x >= HPP.
        a4 = (qh-q0-D*HPP*(1.+D*B*(HPP-SYP))**(-(B+1.)/B))*q
        b4 = D*(1.+D*B*(HPP-SYP))**(-(B+1.)/B)*q
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
        SYT = a2+b2*(c2+d2*SYP)**e2
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
