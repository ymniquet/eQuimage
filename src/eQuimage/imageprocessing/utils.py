# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.3.0 / 2024.02.17

"""Image processing utils."""

import numpy as np

def failsafe_divide(A, B):
  """Return A/B, ignoring errors (division by zero, ...)."""
  status = np.seterr(all = "ignore")
  C = np.divide(A, B)
  np.seterr(divide = status["divide"], over = status["over"], under = status["under"], invalid = status["invalid"])
  return C

def scale_pixels(image, source, target, cutoff = 1.e-12):
  """Scale all pixels of the image 'image' by the ratio target/source.
     Wherever abs(source) < cutoff, set all channels to target."""
  return np.where(abs(source) > cutoff, failsafe_divide(image*target, source), target)

def lookup(x, xlut, ylut, slut, nlut):
  """Return y = f(x) by linearly interpolating the values ylut = f(xlut) of an evenly spaced look-up table with nlut elements.
     slut = (ylut[1:]-ylut[:-1])/(xlut[1:]-xlut[:-1]) are the slopes used for linear interpolation between successive elements."""
  l = np.clip(np.int32(np.floor((x-xlut[0])*(nlut-1)/(xlut[-1]-xlut[0]))), 0, nlut-2)
  return slut[l]*(x-xlut[l])+ylut[l]
