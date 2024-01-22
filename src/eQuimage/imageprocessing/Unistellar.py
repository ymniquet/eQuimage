# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2024.01.14

"""Image processing tools for Unistellar frames."""

import numpy as np
import matplotlib.pyplot as plt
from .imageprocessing import Image

Unistellar_warned_about_frames = False

class UnistellarImage(Image):
  """Image class for the Unistellar frames. Handles the Unistellar frame."""

  # type: Telescope & image type.
  # width: Framed image width.
  # height: Framed image height.
  # radius: Frame radius.
  # margin: Frame margin (between the frame & image).
  # cropradius: Crop radius (crop image at that radius to remove the frame).
  # threshold: Minimal HSV value of the frame.

  __FRAMES__ = [{"type": "eQuinox 1", "width": 2240, "height": 2240, "radius": 1050, "margin": 64, "cropradius": 996, "threshold": 24/255},
                {"type": "eQuinox 1 (Planets)", "width": 1120, "height": 1120, "radius": 525, "margin": 32, "cropradius": 498, "threshold": 24/255}]

  def check_frame(self):
    """Check if the image has an Unistellar frame.
       Return the dictionary of frame properties if so, None otherwise."""
    global Unistellar_warned_about_frames
    if not Unistellar_warned_about_frames:
      print("#########################################################################")
      print("# WARNING: Frame detection is presently based on the size of the image. #")
      print("#          This will (hopefully) be made more robust later.             #")
      print("#########################################################################")
      Unistellar_warned_about_frames = True
    for framed in self.__FRAMES__:
      if self.rgb.shape == (3, framed["height"], framed["width"]):
        return framed
    return None

  def draw_crop_boundary(self, ax = None, color = "yellow", linestyle = "--", linewidth = 1.):
    """Draw the Unistellar frame crop boundary in axes 'ax' (gca() if None) with linestyle 'linestyle', linewidth 'linewidth' and color 'color'."""
    framed = self.check_frame()
    if not framed: return
    width = framed["width"]
    height = framed["height"]
    radius = framed["cropradius"]
    if ax is None: ax = plt.gca()
    ax.add_patch(plt.Circle((width/2, height/2), radius, linestyle = linestyle, linewidth = linewidth, color = color, fill = False))

  def get_frame(self):
    """Return the Unistellar frame as an image."""
    framed = self.check_frame()
    if not framed: return None
    width = framed["width"]
    height = framed["height"]
    radius = framed["cropradius"]
    threshold = framed["threshold"]
    x = np.arange(0, width)-(width-1)/2
    y = np.arange(0, height)-(height-1)/2
    X, Y = np.meshgrid(x, y, sparse = True)
    outer = (X**2+Y**2 > radius**2)
    mask = outer & (self.value() >= threshold)
    frame = np.zeros_like(self.rgb)
    frame[:, mask] = self.rgb[:, mask]
    return Image(frame, {"description": "Unistellar Frame"})

  def remove_frame(self, frame, inplace = True, meta = "self"):
    """Remove the Unistellar frame from the image and set new meta-data 'meta' (same as the original if meta = "self").
       Update the object if 'inplace' is True or return a new instance if 'inplace' is False."""
    image = np.where(frame.value() > 0., 0., self.rgb)
    if inplace:
      self.rgb = image
      if meta != "self": self.meta = meta
      return None
    else:
      if meta == "self": meta = deepcopy(self.meta)
      return self.newImage(self, image, meta)

  def add_frame(self, frame, inplace = True, meta = "self"):
    """Add the Unistellar frame 'frame' to the image and set new meta-data 'meta' (same as the original if meta = "self").
       Update the object if 'inplace' is True or return a new instance if 'inplace' is False."""
    image = np.where(frame.value() > 0., frame, self.rgb)
    if inplace:
      self.rgb = image
      if meta != "self": self.meta = meta
      return None
    else:
      if meta == "self": meta = deepcopy(self.meta)
      return self.newImage(self, image, meta)
