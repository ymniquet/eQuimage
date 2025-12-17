#!/usr/bin/env python

# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.3.1 / 2025.03.26

# Plot of a HSV wheel.

import colorsys
from pylab import *

fig = figure(facecolor = "black")
ax = fig.add_subplot(projection = "polar", facecolor = "black")

rho = linspace(0., 1., 256)
phi = linspace(pi/2., pi/2.+2.*pi, 361)

RHO, PHI = meshgrid(rho, phi)

h = flip((PHI-PHI.min())/(PHI.max()-PHI.min()))
s = RHO
v = ones_like(RHO)

h, s, v = h.flatten().tolist(), s.flatten().tolist(), v.flatten().tolist()
c = [colorsys.hsv_to_rgb(*x) for x in zip(h, s, v)]
c = array(c)

ax.scatter(PHI, RHO, c = c)
ax.set_xticks(pi/6.+linspace(0., 5., 6)*pi/3.)
ax.set_xticklabels(["1/6", "0", "5/6", "2/3", "1/2", "1/3"], color = "white")
ax.set_yticks([.2, .4, .6, .8])
ax.set_yticklabels([])

savefig("../src/equimage/images/HSVwheel.png", dpi = 200)

show()
