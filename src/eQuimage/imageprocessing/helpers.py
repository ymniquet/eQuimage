# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2023.11.27

"""Image processing helpers."""

import numpy as np

def midtone_transfer_function(tone, midtone):
  """Midtone transfer function for tone 'tone' and midtone 'midtone'."""
  return (midtone-1)*tone/((2*midtone-1)*tone-midtone)

def failsafe_divide(A, B):
  """Return A/B, ignoring errors (division by zero, ...)."""
  status = np.seterr(all = "ignore")
  C = np.divide(A, B)
  np.seterr(divide = status["divide"], over = status["over"], under = status["under"], invalid = status["invalid"])
  return C