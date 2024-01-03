# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2023.11.27

"""Tool helpers."""

import numpy as np
import matplotlib.ticker as ticker

def plot_histograms(ax, histograms, colors = ("red", "green", "blue", "gray", "black"),
                    title = None, xlabel = "Level", ylabel = "Count (a.u.)", ylogscale = False):
  """Plot red/green/blue/value/luminance histograms 'histograms' on axes 'ax'.
     Use 'colors' = (red, green, blue, value, luminance) for the corresponding line (not displayed if None).
     Set title 'title', x label 'xlabel' and y label 'ylabel'.
     Use log scale on y-axis if 'ylogscale' is True."""
  edges, hists = histograms
  centers = (edges[:-1]+edges[1:])/2.
  hists = hists/hists[:, 1:].max()
  ax.clear()
  if colors[0] is not None: ax.plot(centers, hists[0], "-", color = colors[0])
  if colors[1] is not None: ax.plot(centers, hists[1], "-", color = colors[1])
  if colors[2] is not None: ax.plot(centers, hists[2], "-", color = colors[2])
  if colors[3] is not None: ax.plot(centers, hists[3], "-", color = colors[3])
  if colors[4] is not None: ax.plot(centers, hists[4], "-", color = colors[4])
  xmax = max(1., centers[-1])
  ax.set_xlim(0., xmax)
  if xlabel is not None: ax.set_xlabel(xlabel)
  ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(5))
  if ylogscale:
    ax.set_yscale("log")
    ax.set_ylim(np.min(hists[hists > 0.]), 1.)
  else:
    ax.set_yscale("linear")
    ax.set_ylim(0., 1.)
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(5))
  if ylabel is not None: ax.set_ylabel(ylabel)
  ax.axvspan(1., xmax+1., color = "gray", alpha = 0.25)
  if title is not None: ax.set_title(title, weight = "bold")

def stats_string(image, key):
  """Return string with the statistics of channel 'key' of image 'image' (see imageprocessing.Image.statistics).
     The statistics must be embedded in the image as image.stats."""
  try:
    stats = image.stats[key]
    npixels = image.image[0].size
    channel = {"R": "Red", "G": "Green", "B": "Blue", "V": "Value", "L": "Luminance"}[key]
    median = f"{stats.median:.3f}" if stats.median is not None else "None"
    return f"{channel} : min = {stats.minimum:.3f}, max = {stats.maximum:.3f}, med = {median}, {stats.zerocount} ({100.*stats.zerocount/npixels:.2f}%) zeros, {stats.outcount} ({100.*stats.outcount/npixels:.2f}%) out-of-range"
  except:
    return ""
