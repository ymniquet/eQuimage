# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2024.01.14

"""Image processing tools for Unistellar telescopes."""

import numpy as np
import matplotlib.pyplot as plt
from .imageprocessing import Image

Unistellar_warned_about_frames = False

class UnistellarImage(Image):
  """Image class for the Unistellar telescopes. Handles the Unistellar frame."""

  # type: Telescope & image type.
  # width: Framed image width.
  # height: Framed image height.
  # radius: Frame radius.
  # margin: Frame margin (between the frame & image).
  # cropradius: Crop radius (crop image at that radius to remove the frame).
  # threshold: Minimal HSV value of the frame.

  telescopes = [{"type": "eQuinox 1", "width": 2240, "height": 2240, "radius": 1050, "margin": 64, "cropradius": 996, "threshold": 24/255},
                {"type": "eQuinox 1 (Planets)", "width": 1120, "height": 1120, "radius": 525, "margin": 32, "cropradius": 498, "threshold": 24/255}]

  def __init__(self, *args, **kwargs):
    """Initialize object."""
    self.telescope = "unknown"
    super().__init__(*args, **kwargs)

  def check_frame(self):
    """Check if the image has an Unistellar frame.
       Return True if so, False otherwise."""
    global Unistellar_warned_about_frames
    if not Unistellar_warned_about_frames:
      print("#########################################################################")
      print("# WARNING: Frame detection is presently based on the size of the image. #")
      print("#          This will (hopefully) be made more robust later.             #")
      print("#########################################################################")
      Unistellar_warned_about_frames = True
    self.telescope = None
    for telescope in self.telescopes:
      if self.image.shape == (3, telescope["height"], telescope["width"]):
        self.telescope = telescope.copy()
        break
    return self.telescope is not None

  def draw_crop_boundary(self, ax = None, color = "yellow", linestyle = "--", linewidth = 1.):
    """Draw the Unistellar frame crop boundary in axes 'ax' (gca() if None) with linestyle 'linestyle', linewidth 'linewidth' and color 'color'."""
    if self.telescope == "unknown": self.check_frame()
    if self.telescope is None: return
    width = self.telescope["width"]
    height = self.telescope["height"]
    radius = self.telescope["cropradius"]
    if ax is None: ax = plt.gca()
    ax.add_patch(plt.Circle((width/2, height/2), radius, linestyle = linestyle, linewidth = linewidth, color = color, fill = False))

  def get_frame_type(self):
    """Return Unistellar frame type."""
    if self.telescope == "unknown": self.check_frame()
    return None if self.telescope is None else self.telescope["type"]

  def get_frame_radius(self):
    """Return Unistellar frame radius."""
    if self.telescope == "unknown": self.check_frame()
    return None if self.telescope is None else self.telescope["radius"]

  def get_frame_margin(self):
    """Return Unistellar frame margin."""
    if self.telescope == "unknown": self.check_frame()
    return None if self.telescope is None else self.telescope["margin"]

  def get_frame_crop_radius(self):
    """Return Unistellar frame crop radius."""
    if self.telescope == "unknown": self.check_frame()
    return None if self.telescope is None else self.telescope["cropradius"]

  def get_frame(self):
    """Return the Unistellar frame as an image."""
    if self.telescope == "unknown": self.check_frame()
    if self.telescope is None: raise ValueError("Not a framed Unistellar image.")
    width = self.telescope["width"]
    height = self.telescope["height"]
    radius = self.telescope["cropradius"]
    threshold = self.telescope["threshold"]
    x = np.arange(0, width)-(width-1)/2
    y = np.arange(0, height)-(height-1)/2
    X, Y = np.meshgrid(x, y, sparse = True)
    outer = (X**2+Y**2 > radius**2)
    mask = outer & (self.value() >= threshold)
    frame = np.zeros_like(self.image)
    frame[:, mask] = self.image[:, mask]
    return Image(frame, "Frame of '"+self.description+"'")

  def remove_frame(self, frame, description = None, inplace = True):
    """Remove the Unistellar frame from the image and set new description 'description' (same as the original if None).
       Update the object if 'inplace' is True or return a new instance if 'inplace' is False."""
    if description is None: description = self.description
    image = self.image if inplace else self.image.copy()
    image = np.where(frame.value() > 0, 0, image)
    return None if inplace else self.newImage(self, image, description)

  def add_frame(self, frame, description = None, inplace = True):
    """Add the Unistellar frame 'frame' to the image and set new description 'description' (same as the original if None).
       Update the object if 'inplace' is True or return a new instance if 'inplace' is False."""
    if description is None: description = self.description
    image = self.image if inplace else self.image.copy()
    image = np.where(frame.value() > 0, frame.image, self.image)
    return None if inplace else self.newImage(self, image, description)
