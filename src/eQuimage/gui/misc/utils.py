# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.5.2 / 2024.06.23
# GUI updated.

"""Tool utils."""

import numpy as np
import matplotlib as mpl
import matplotlib.colors as colors
import matplotlib.ticker as ticker

def histogram_bins(stats, colordepth = 8):
  """Return the number of histogram bins for an image with (luma) stats 'stats' (see imageprocessing.Image.statistics)
     and color depth 'colordepth' (bits/color)."""
  iqr = stats.percentiles[2]-stats.percentiles[0] if stats.percentiles is not None else .25
  nbins = int(stats.npixels**(1./3.)/(2.*iqr))
  nbinsmin = 128
  nbinsmax = min(2**(colordepth-1), 8192)
  return min(max(nbins, nbinsmin), nbinsmax)

def plot_histograms(ax, edges, counts, colors,
                    title = None, xlabel = "Level", ylabel = "Count (a.u.)", ylogscale = False):
  """Plot histograms with bin edges 'edges(nbins)' and bin counts 'counts(nc, nbins)' in axes 'ax',
     where nc is the number of histogram channels and nbins the number of histogram bins.
     Use color 'colors(nc)' for the histogram lines (not displayed if None).
     Set title 'title', x label 'xlabel' and y label 'ylabel' (if not None).
     Use log scale on y axis if 'ylogscale' is True.
     Return a list of nc matplotlib.lines.Line2D histogram lines."""
  centers = (edges[:-1]+edges[1:])/2.
  imin = np.argmin(abs(centers-0.))
  imax = np.argmin(abs(centers-1.))
  cmax = counts[:, imin+1:imax].max()
  rcounts = counts/cmax
  ax.clear()
  histlines = []
  for ic in range(counts.shape[0]):
    histlines.append(ax.plot(centers, rcounts[ic], "-", color = colors[ic])[0] if colors[ic] is not None else None)
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
  ax.axvspan(xmin-1., 0., color = "gray", alpha = .25)
  ax.axvspan(1., xmax+1., color = "gray", alpha = .25)
  if title is not None: ax.set_title(title, weight = "bold")
  return histlines

def update_histograms(ax, histlines, edges, counts, ylogscale = False):
  """Update histogram lines 'histlines(nc)' in axes 'ax' with bin edges 'edges(nbins)' and bin
     counts 'counts(nc, nbins)', where nc is the number of histogram channels and nbins the
     number of histogram bins. Use log scale on y axis if 'ylogscale' is True."""
  centers = (edges[:-1]+edges[1:])/2.
  imin = np.argmin(abs(centers-0.))
  imax = np.argmin(abs(centers-1.))
  cmax = counts[:, imin+1:imax].max()
  rcounts = counts/cmax
  for ic in range(len(histlines)):
    if histlines[ic] is not None:
      histlines[ic].set_xdata(centers)
      histlines[ic].set_ydata(rcounts[ic])
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
  for ic in range(len(histlines)):
    line = histlines[ic]
    if line is None: continue
    if ic == idx:
      line.set_zorder(3)
      line.set_linewidth(lw*1.4142)
    else:
      line.set_zorder(2)
      line.set_linewidth(lw/1.4142)

def transform_histogram(edges, counts, fedges, newedges):
  """Transform histogram defined by bin edges 'edges' and bin counts 'counts'
     by applying a function 'fedges' = f(edges) to the edges then resampling over
     new edges 'newedges'. Return the new counts."""
  nedges = len(edges)
  csum = np.empty(nedges+1, dtype = counts.dtype)
  csum[0] = 0
  np.cumsum(counts, out = csum[1:])
  fcsum = np.interp(newedges, fedges, csum)
  return np.diff(fcsum)

def stats_string(stats):
  """Return string for the channel statistics 'stats' (see imageprocessing.Image.statistics)."""
  median = f"{stats.median:.5f}" if stats.median is not None else "None"
  return f"{stats.name} : min = {stats.minimum:.5f}, max = {stats.maximum:.5f}, med = {median}, {stats.zerocount} ({100.*stats.zerocount/stats.npixels:.2f}%) zeros, {stats.outcount} ({100.*stats.outcount/stats.npixels:.2f}%) out-of-range"

def plot_hsv_wheel(ax):
  """Plot HSV wheel in ploar axes 'ax'."""
  rho = np.linspace(0., 1., 100)
  phi = np.linspace(0., 2.*np.pi, 100)
  RHO, PHI = np.meshgrid(rho, phi)
  h = np.ravel(PHI/(2.*np.pi))
  s = np.ravel(RHO)
  v = np.ones_like(s)
  hsv = np.column_stack((h, s, v))
  rgb = colors.set_hsv_image(hsv)
  ax.scatter(PHI, RHO, c = rgb, zorder = -3)
  ax.set_ylim(0., 1.)
