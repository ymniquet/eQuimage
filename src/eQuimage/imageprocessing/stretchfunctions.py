# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2023.11.27

"""Histogram stretch functions."""

import numpy as np

def midtone_stretch_function(levels, midtone):
  """Return midtone stretch function for the array of levels 'levels' and for midtone parameter 'midtone'.
     The levels MUST be within [0, 1] (clip and remap before if necessary)."""
  return (midtone-1)*levels/((2*midtone-1)*levels-midtone)

def hyperbolic_stretch_function(levels, params):
  """Return hyperbolic stretch function for the array of levels 'levels' and for parameters 'params = (D, b, SYP, SPP, HPP)'.
     The levels MUST be within [0, 1] (clip and remap before if necessary).
     See: https://ghsastro.co.uk/ ."""
  D, b, SYP, SPP, HPP = params
  if abs(D) < 1.e-6: # Identity.
    return np.copy(levels)
  else:
    output = np.empty_like(levels)
    if abs(b) < 1.e-6:
      mask = (levels <= SPP)
      output[mask] = a1+b1*levels[mask]
      mask = (levels >  SPP) & (levels <= SYP)
      output[mask] = a2+b2*np.exp(c2+d2*levels[mask])
      mask = (levels >  SYP) & (levels <= HPP)
      output[mask] = a3+b3*np.exp(c3+d3*levels[mask])
      mask = (levels >  HPP)
      output[mask] = a4+b4*levels[mask]
    elif abs(b+1.) < 1.e-6:
      mask = (levels <= SPP)
      output[mask] = a1+b1*levels[mask]
      mask = (levels >  SPP) & (levels <= SYP)
      output[mask] = a2+b2*np.log(c2+d2*levels[mask])
      mask = (levels >  SYP) & (levels <= HPP)
      output[mask] = a3+b3*np.log(c3+d3*levels[mask])
      mask = (levels >  HPP)
      output[mask] = a4+b4*levels[mask]
    else:
      mask = (levels <= SPP)
      output[mask] = a1+b1*levels[mask]
      mask = (levels >  SPP) & (levels <= SYP)
      output[mask] = a2+b2*(c2+d2*levels[mask])**e2
      mask = (levels >  SYP) & (levels <= HPP)
      output[mask] = a3+b3*(c3+d3*levels[mask])**e3
      mask = (levels >  HPP)
      output[mask] = a4+b4*levels[mask]
    return output
