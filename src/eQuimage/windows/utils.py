# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2024.01.05

"""Tool utils."""

import numpy as np
import matplotlib as mpl
import matplotlib.ticker as ticker

def plot_histograms(ax, edges, counts, colors = ("red", "green", "blue", "gray", "black"),
                    title = None, xlabel = "Level", ylabel = "Count (a.u.)", ylogscale = False):
  """Plot histograms in axes 'ax', with bin edges 'edges(nbins)' and bin counts 'counts(5, nbins)'
     for the red, green, blue, value and luminance channels.
     Use color 'colors(5)' for the corresponding histogram line (not displayed if None).
     Set title 'title', x label 'xlabel' and y label 'ylabel'. Use log scale on y axis if 'ylogscale' is True.
     Return a list of matplotlib.lines.Line2D histogram lines."""
  centers = (edges[:-1]+edges[1:])/2.
  imin = np.argmin(abs(centers-0.))
  imax = np.argmin(abs(centers-1.))
  cmax = counts[:, imin+1:imax].max()
  rcounts = counts/cmax
  ax.clear()
  histlines = []
  for i in range(5):
    histlines.append(ax.plot(centers, rcounts[i], "-", color = colors[i])[0] if colors[i] is not None else None)
  xmin = min(0., centers[ 0])
  xmax = max(1., centers[-1])
  ax.set_xlim(xmin, xmax)
  ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(5))
  if xlabel is not None: ax.set_xlabel(xlabel)
  if ylogscale:
    ax.set_yscale("log")
    #ax.set_ylim(1./cmax, 1.)
    ax.set_ylim(rcounts[counts > 0.].min(), 1.)
  else:
    ax.set_yscale("linear")
    ax.set_ylim(0., 1.)
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(5))
  if ylabel is not None: ax.set_ylabel(ylabel)
  ax.axvspan(xmin-1., 0., color = "gray", alpha = 0.25)
  ax.axvspan(1., xmax+1., color = "gray", alpha = 0.25)
  if title is not None: ax.set_title(title, weight = "bold")
  return histlines

def update_histograms(ax, histlines, edges, counts, ylogscale = False):
  """Update histogram lines 'histlines(5)' in axes 'ax' with bin edges 'edges(nbins)' and bin
     counts 'counts(5, nbins)' for the red, green, blue, value and luminance channels.
     Use log scale on y axis if 'ylogscale' is True."""
  centers = (edges[:-1]+edges[1:])/2.
  imin = np.argmin(abs(centers-0.))
  imax = np.argmin(abs(centers-1.))
  cmax = counts[:, imin+1:imax].max()
  rcounts = counts/cmax
  for i in range(5):
    if histlines[i] is not None:
      histlines[i].set_xdata(centers)
      histlines[i].set_ydata(rcounts[i])
  if ylogscale:
    ax.set_yscale("log")
    #ax.set_ylim(1./cmax, 1.)    
    ax.set_ylim(rcounts[counts > 0.].min(), 1.)
  else:
    ax.set_yscale("linear")
    ax.set_ylim(0., 1.)    
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(5))    

def highlight_histogram(histlines, idx, lw = mpl.rcParams["lines.linewidth"]):
  """Highlight histogram line 'histlines[idx]' by making it twice thicker and bringing it to front. 'lw' is the default linewidth."""
  for i in range(5):
    line = histlines[i]
    if line is None: continue
    if i == idx:
      line.set_zorder(3)
      line.set_linewidth(lw*1.4142)
    else:
      line.set_zorder(2)
      line.set_linewidth(lw/1.4142)

def stats_string(image, key):
  """Return string with the statistics of channel 'key' of image 'image' (see imageprocessing.Image.statistics).
     The statistics may be embedded in the image as image.stats; otherwise, they are computed on the fly."""
  try:
    stats = image.stats[key]
  except:
    stats = image.statistics()[key]
  npixels = image.image[0].size
  channel = {"R": "Red", "G": "Green", "B": "Blue", "V": "Value", "L": "Luminance"}[key]
  median = f"{stats.median:.3f}" if stats.median is not None else "None"
  return f"{channel} : min = {stats.minimum:.3f}, max = {stats.maximum:.3f}, med = {median}, {stats.zerocount} ({100.*stats.zerocount/npixels:.2f}%) zeros, {stats.outcount} ({100.*stats.outcount/npixels:.2f}%) out-of-range"
