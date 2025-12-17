#!/usr/bin/env python

# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.3.1 / 2025.03.26

# Calculation of the standard deviation of a white Gaussian noise at each starlet level.

import numpy as np
import matplotlib.pyplot as plt
import equimage

starlet = "cubic"
levels = 8

if starlet == "linear":
  kernel_size = 3
elif starlet == "cubic":
  kernel_size = 5
else:
  raise ValueError(f"Unknown starlet {starlet}.")

size = kernel_size*2**levels
c = size//2

image = np.zeros((size, size))
image[c, c] = 1.

print(f"Starlet = {starlet}.")

wt = equimage.slt(image, levels = levels, starlet = starlet, mode = "zero")

sigmas = []
for level in range(levels):
  sigma = float(np.sqrt(np.sum(wt.coeffs[-(level+1)][0]**2)))
  sigmas.append(sigma)
  print(f"Sigma level #{level} = {sigma}.")

print("Sigmas from this script:")
print(sigmas)

print("Sigmas from WaveletTransform.noise_scale_factors(numerical = True):")
print(wt.noise_scale_factors(numerical = True, samples = 10))

plt.matshow(np.log10(wt.coeffs[0]+1.e-12))
plt.show()
