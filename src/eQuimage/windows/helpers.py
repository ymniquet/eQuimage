# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2023.11.27

"""Tool helpers."""

import numpy as np
import matplotlib as mpl
import matplotlib.ticker as ticker

def plot_histograms(ax, histograms, colors = ("red", "green", "blue", "gray", "black"),
                    title = None, xlabel = "Level", ylabel = "Count (a.u.)", ylogscale = False):
  """Plot histograms 'histograms = (edges, counts)' on axes 'ax', where edges(nbins) are the bin edges and
     counts(5, nbins) are the bin counts for the red, green, blue, value and luminance channels.
     Use 'colors' = (red, green, blue, value, luminance) for the corresponding line (not displayed if None).
     Set title 'title', x label 'xlabel' and y label 'ylabel'. Use log scale on y-axis if 'ylogscale' is True.
     Return a list of handles on the histogram lines."""
  edges, hists = histograms
  centers = (edges[:-1]+edges[1:])/2.
  imin = np.argmin(abs(centers-0.))
  imax = np.argmin(abs(centers-1.))
  hists = hists/hists[:, imin+1:imax].max()
  ax.clear()
  histlines = []
  histlines.append(ax.plot(centers, hists[0], "-", color = colors[0])[0] if colors[0] is not None else None)
  histlines.append(ax.plot(centers, hists[1], "-", color = colors[1])[0] if colors[1] is not None else None)
  histlines.append(ax.plot(centers, hists[2], "-", color = colors[2])[0] if colors[2] is not None else None)
  histlines.append(ax.plot(centers, hists[3], "-", color = colors[3])[0] if colors[3] is not None else None)
  histlines.append(ax.plot(centers, hists[4], "-", color = colors[4])[0] if colors[4] is not None else None)
  xmin = min(0., centers[ 0])
  xmax = max(1., centers[-1])
  ax.set_xlim(xmin, xmax)
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
  ax.axvspan(xmin-1., 0., color = "gray", alpha = 0.25)
  ax.axvspan(1., xmax+1., color = "gray", alpha = 0.25)
  if title is not None: ax.set_title(title, weight = "bold")
  return histlines

def highlight_histogram(histlines, idx, lw = mpl.rcParams["lines.linewidth"]):
  """Highlight histogram line 'histlines[idx]' by making it twice thicker and bringing it to front.Z
     'lw' is the default linewidth."""
  for i in range(5):
    line = histlines[i]
    if line is None: continue
    if i == idx:
      line.set_linewidth(2*lw)
      line.set_zorder(3)
    else:
      line.set_linewidth(lw)
      line.set_zorder(2)

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
