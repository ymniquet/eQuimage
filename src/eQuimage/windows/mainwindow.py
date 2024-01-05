# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.2.0 / 2024.01.05

"""Main window."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GObject
from .gtk.utils import get_work_area
from .gtk.signals import Signals
from .gtk.customwidgets import CheckButton, HScale, Notebook
from .base import BaseWindow, BaseToolbar, Container
from .luminance import LuminanceRGBDialog
from .statistics import StatWindow
from ..imageprocessing import imageprocessing
import numpy as np
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure
from collections import OrderedDict as OD

class MainWindow(BaseWindow):
  """Main window class."""

  MAXIMGSIZE = 0.8 # Maximal width/height of the image (as a fraction of the screen resolution).

  SHADOWCOLOR = np.array([[1.], [.5], [0.]], dtype = imageprocessing.IMGTYPE)
  HIGHLIGHTCOLOR = np.array([[1.], [1.], [0.]], dtype = imageprocessing.IMGTYPE)
  DIFFCOLOR = np.array([[1.], [1.], [0.]], dtype = imageprocessing.IMGTYPE)

  def open(self):
    """Open main window."""
    if self.opened: return
    if not self.app.get_nbr_images(): return
    self.opened = True
    self.window = Gtk.Window(title = self.app.get_basename())
    self.window.connect("delete-event", self.close)
    self.window.connect("key-press-event", self.keypress)
    self.widgets = Container()
    wbox = Gtk.VBox()
    self.window.add(wbox)
    hbox = Gtk.HBox()
    wbox.pack_start(hbox, False, False, 0)
    self.tabs = Notebook()
    self.tabs.set_tab_pos(Gtk.PositionType.TOP)
    self.tabs.set_scrollable(True)
    self.tabs.set_show_border(False)
    self.tabs.connect("switch-page", lambda tabs, tab, itab: self.update_tab(itab))
    hbox.pack_start(self.tabs, True, True, 0)
    label = Gtk.Label("?", halign = Gtk.Align.END)
    label.set_tooltip_text("[N], [TAB]: Next image tab\n[P]: Previous image tab\n[S]: Image statistics")
    hbox.pack_start(label, False, False, 8)
    fig = Figure()
    ax = fig.add_axes([0., 0., 1., 1.])
    fwidth, fheight = self.app.get_image_size()
    swidth, sheight = get_work_area(self.window)
    cwidth, cheight = self.MAXIMGSIZE*swidth, self.MAXIMGSIZE*swidth*fheight/fwidth
    if cheight > self.MAXIMGSIZE*sheight:
      cwidth, cheight = self.MAXIMGSIZE*sheight*fwidth/fheight, self.MAXIMGSIZE*sheight
    self.canvas = FigureCanvas(fig)
    self.canvas.set_size_request(cwidth, cheight)
    wbox.pack_start(self.canvas, True, True, 0)
    hbox = Gtk.HBox()
    wbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Output range Min:"), False, False, 4)
    self.widgets.minscale = HScale(0., 0., 1., 0.01, length = 128)
    self.widgets.minscale.connect("value-changed", lambda scale: self.update_output_range("Min"))
    hbox.pack_start(self.widgets.minscale, True, True, 4)
    hbox.pack_start(Gtk.Label(label = "Max:"), False, False, 4)
    self.widgets.maxscale = HScale(1., 0., 1., 0.01, length = 128)
    self.widgets.maxscale.connect("value-changed", lambda scale: self.update_output_range("Max"))
    hbox.pack_start(self.widgets.maxscale, True, True, 4)
    hbox = Gtk.HBox()
    wbox.pack_start(hbox, False, False, 0)
    self.widgets.redbutton = CheckButton(label = "Red")
    self.widgets.redbutton.set_active(True)
    self.widgets.redbutton.connect("toggled", lambda button: self.update_channels("R"))
    hbox.pack_start(self.widgets.redbutton, False, False, 0)
    self.widgets.greenbutton = CheckButton(label = "Green")
    self.widgets.greenbutton.set_active(True)
    self.widgets.greenbutton.connect("toggled", lambda button: self.update_channels("G"))
    hbox.pack_start(self.widgets.greenbutton, False, False, 0)
    self.widgets.bluebutton = CheckButton(label = "Blue")
    self.widgets.bluebutton.set_active(True)
    self.widgets.bluebutton.connect("toggled", lambda button: self.update_channels("B"))
    hbox.pack_start(self.widgets.bluebutton, False, False, 0)
    self.widgets.lumbutton = CheckButton(label = self.rgb_luminance_string())
    self.widgets.lumbutton.set_active(False)
    self.widgets.lumbutton.connect("toggled", lambda button: self.update_channels("L"))
    hbox.pack_start(self.widgets.lumbutton, False, False, 0)
    self.widgets.rgblumbutton = Gtk.Button(label = "Set", halign = Gtk.Align.START)
    self.widgets.rgblumbutton.connect("clicked", lambda button: LuminanceRGBDialog(self.window, self.set_rgb_luminance, self.get_rgb_luminance()))
    hbox.pack_start(self.widgets.rgblumbutton, True, True, 0)
    #hbox.pack_start(self.widgets.rgblumbutton, False, False, 0)
    #self.widgets.spinner = Gtk.Spinner()
    #hbox.pack_start(self.widgets.spinner, True, True, 0)
    self.widgets.shadowbutton = CheckButton(label = "Shadowed")
    self.widgets.shadowbutton.set_active(False)
    self.widgets.shadowbutton.connect("toggled", lambda button: self.update_modifiers("S"))
    hbox.pack_start(self.widgets.shadowbutton, False, False, 0)
    self.widgets.highlightbutton = CheckButton(label = "Highlighted")
    self.widgets.highlightbutton.set_active(False)
    self.widgets.highlightbutton.connect("toggled", lambda button: self.update_modifiers("H"))
    hbox.pack_start(self.widgets.highlightbutton, False, False, 0)
    self.widgets.diffbutton = CheckButton(label = "Differences")
    self.widgets.diffbutton.set_active(False)
    self.widgets.diffbutton.connect("toggled", lambda button: self.update_modifiers("D"))
    hbox.pack_start(self.widgets.diffbutton, False, False, 0)
    self.widgets.toolbar = BaseToolbar(self.canvas, fig)
    wbox.pack_start(self.widgets.toolbar, False, False, 0)
    self.set_rgb_luminance_callback(None)
    self.set_guide_lines(None)
    self.statwindow = StatWindow(self.app)
    self.reset_images()

  def destroy(self, *args, **kwargs):
    """Destroy main window."""
    if not self.opened: return None
    self.window.destroy()
    self.opened = False
    del self.tabs
    del self.canvas
    del self.widgets
    del self.images

  def close(self, *args, **kwargs):
    """Clear the app and close main window."""
    if not self.opened: return None
    dialog = Gtk.MessageDialog(transient_for = self.window,
                               message_type = Gtk.MessageType.QUESTION,
                               buttons = Gtk.ButtonsType.OK_CANCEL,
                               modal = True)
    dialog.set_markup("Are you sure you want to close this image ?")
    response = dialog.run()
    dialog.destroy()
    if response != Gtk.ResponseType.OK: return True
    self.app.clear()

  # Update tabs.

  def get_current_key(self):
    """Return the key associated to the current tab."""
    tab = self.tabs.get_current_page()
    if tab < 0: return None
    keys = list(self.images.keys())
    return keys[tab]

  def update_tab(self, tab):
    """Update image tab."""
    keys = list(self.images.keys())
    self.draw_image(keys[tab])

  # Update displayed channels.

  def update_channels(self, toggled):
    """Update channels buttons."""
    if toggled == "L":
      luminance = self.widgets.lumbutton.get_active()
      self.widgets.redbutton.set_active_block(not luminance)
      self.widgets.greenbutton.set_active_block(not luminance)
      self.widgets.bluebutton.set_active_block(not luminance)
    else:
      red = self.widgets.redbutton.get_active()
      green = self.widgets.greenbutton.get_active()
      blue = self.widgets.bluebutton.get_active()
      self.widgets.lumbutton.set_active_block(not (red or green or blue))
    self.draw_image(self.get_current_key())

  # Update image modifiers (shadow, highlight, difference).

  def update_modifiers(self, toggled):
    """Update image modifiers."""
    if toggled == "D":
      if self.widgets.diffbutton.get_active():
        self.widgets.shadowbutton.set_active_block(False)
        self.widgets.highlightbutton.set_active_block(False)
    else:
      self.widgets.diffbutton.set_active_block(False)
    modifier = self.widgets.shadowbutton.get_active() or self.widgets.highlightbutton.get_active() or self.widgets.diffbutton.get_active()      
    self.widgets.minscale.set_sensitive(not modifier)
    self.widgets.maxscale.set_sensitive(not modifier)    
    self.draw_image(self.get_current_key())

  # Update output range.

  def update_output_range(self, updated):
    """Update output range."""
    vmin = self.widgets.minscale.get_value()
    vmax = self.widgets.maxscale.get_value()
    if vmax-vmin < 0.01:
      if updated == "Max":
        vmin = max(0., vmax-0.01)
        vmax = vmin+0.01
      else:
        vmax = min(vmin+0.01, 1.)
        vmin = vmax-0.01
      self.widgets.minscale.set_value_block(vmin)
      self.widgets.maxscale.set_value_block(vmax)
    self.refresh_image()

  # Image modifiers (shadow, highlight, difference).

  def difference(self, image, reference, channels):
    """Highlight differences between 'image' and 'reference' with DIFFCOLOR color."""
    diff = image.copy()
    mask = np.any(image[channels] != reference[channels], axis = 0)
    diff[:, mask] = self.DIFFCOLOR
    return diff

  def shadow_highlight(self, image, reference, channels, shadow = True, highlight = True):
    """If shadow is True,
         show pixels black on 'image' and     on 'reference' with color 0.5*SHADOWCOLOR,
         and  pixels black on 'image' but not on 'reference' with color     SHADOWCOLOR,
       If higlight is True,
         show pixels with at least one channel >= 1 on 'image' and     on  'reference' with color 0.5*HIGHLIGHTCOLOR,
         and  pixels with at least one channel >= 1 on 'image' but not on  'reference' with color     HIGHLIGHTCOLOR."""
    swhl = image.copy()
    if shadow:
      imgmask = np.all(image[channels] < imageprocessing.IMGTOL, axis = 0)
      if image.shape == reference.shape:
        refmask = np.all(reference[channels] < imageprocessing.IMGTOL, axis = 0)
        swhl[:, imgmask &  refmask] = 0.5*self.SHADOWCOLOR
        swhl[:, imgmask & ~refmask] =     self.SHADOWCOLOR
      else:
        swhl[:, imgmask] = self.SHADOWCOLOR
    if highlight:
      imgmask = np.any(image[channels] > 1.-imageprocessing.IMGTOL, axis = 0)
      if image.shape == reference.shape:
        refmask = np.any(reference[channels] > 1.-imageprocessing.IMGTOL, axis = 0)
        swhl[:, imgmask &  refmask] = 0.5*self.HIGHLIGHTCOLOR
        swhl[:, imgmask & ~refmask] =     self.HIGHLIGHTCOLOR
      else:
        swhl[:, imgmask] = self.HIGHLIGHTCOLOR
    return swhl

  # Draw or refresh the image displayed in the main window.

  def draw_image(self, key):
    """Apply modifiers and draw image with key 'key'."""
    if key is None: return
    try:
      image = self.images[key]
    except KeyError:
      raise KeyError("There is no image with key '{key}'.")
      return
    shadow = self.widgets.shadowbutton.get_active()
    highlight = self.widgets.highlightbutton.get_active()
    diff = self.widgets.diffbutton.get_active()
    modifiers = shadow or highlight or diff
    luminance = self.widgets.lumbutton.get_active()
    if luminance:
      image = np.repeat(image._luminance[np.newaxis], 3, axis = 0)
      channels = np.array([True, False, False])
      if modifiers: reference = np.repeat(self.reference._luminance[np.newaxis], 3, axis = 0)
    else:
      image = image.image.copy()
      channels = np.array([self.widgets.redbutton.get_active(), self.widgets.greenbutton.get_active(), self.widgets.bluebutton.get_active()])
      image[~channels] = 0.
      if modifiers: reference = self.reference.image
    if modifiers:
      if diff:
        if image.shape == reference.shape: image = self.difference(image, reference, channels)
      elif shadow or highlight:
        image = self.shadow_highlight(image, reference, channels, shadow, highlight)
    self.refresh_image(image)

  def refresh_image(self, image = None):
    """Draw (if 'image' is not None) or refresh the current image."""
    update = self.currentimage is not None # Is this an update or fresh draw ?
    if image is not None:
      currentshape = self.currentimage.shape if update else None
      self.currentimage = np.clip(np.moveaxis(image, 0, -1), 0., 1.)
      update = update and self.currentimage.shape == currentshape
    if self.currentimage is None: return # Nothing to draw !
    vmin = self.widgets.minscale.get_value() if self.widgets.minscale.get_sensitive() else 0.
    vmax = self.widgets.maxscale.get_value() if self.widgets.maxscale.get_sensitive() else 1.
    if vmin > 0. or vmax < 1.:
      ranged = np.where((self.currentimage >= vmin) & (self.currentimage <= vmax), self.currentimage, 0.)
    else:
      ranged = self.currentimage
    ax = self.canvas.figure.axes[0]
    if update:
      ax.imshown.set_data(ranged) # Update image (preserves zoom, ...).
    else:
      ax.clear() # Draw image.
      ax.imshown = ax.imshow(ranged, aspect = "equal")
      ax.axis("off")
      if self.plot_guide_lines is not None: self.plot_guide_lines(ax)
    self.canvas.draw_idle()
    self.window.queue_draw()
    self.set_idle()

  # Show image statistics.

  def show_statistics(self):
    """Open image statistics window."""
    if not self.opened: return
    key = self.get_current_key()
    if key is None: return
    try:
      image = self.images[key]
    except KeyError:
      raise KeyError("There is no image with key '{key}'.")
      return
    width, height = image.size()
    ax = self.canvas.figure.axes[0]
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    xmin = max(int(np.ceil(xlim[0])), 0)
    xmax = min(int(np.ceil(xlim[1])), width)
    ymin = max(int(np.ceil(ylim[1])), 0)
    ymax = min(int(np.ceil(ylim[0])), height)
    #print(xmin, xmax, ymin, ymax)
    cropped = imageprocessing.Image(image.image[:, ymin:ymax, xmin:xmax], "")
    self.statwindow.open(cropped)

  # Manage the dictionary of images displayed in the tabs.

  def reset_images(self):
    """Reset main window images."""
    if not self.opened: return
    self.images = None
    self.currentimage = None
    nimages = self.app.get_nbr_images()
    if nimages > 3:
      self.set_images(OD(Image = self.app.get_image(-1), Original = self.app.get_image(0)), reference = "Original")
    elif nimages > 0:
      self.set_images(OD(Original = self.app.get_image(0)), reference = "Original")

  def set_images(self, images, reference = None):
    """Set main window images and reference."""
    if not self.opened: return
    self.tabs.block_all_signals()
    for tab in range(self.tabs.get_n_pages()): self.tabs.remove_page(-1)
    self.images = OD()
    for key, image in images.items():
      self.images[key] = image.clone()
      self.images[key]._luminance = self.images[key].luminance()
    if reference is None:
      self.reference = self.images[key]
    else:
      try:
        self.reference = self.images[reference]
      except KeyError:
        raise KeyError("There is no image with key '{reference}'.")
        self.reference = self.images[key]
    self.reference.description += " (\u2022)"
    for key, image in self.images.items():
      self.tabs.append_page(Gtk.Alignment(), Gtk.Label(label = self.images[key].description)) # Append a zero size dummy child.
    self.widgets.redbutton.set_active_block(True)
    self.widgets.greenbutton.set_active_block(True)
    self.widgets.bluebutton.set_active_block(True)
    self.widgets.lumbutton.set_active_block(False)
    self.widgets.shadowbutton.set_active_block(False)
    self.widgets.highlightbutton.set_active_block(False)
    self.widgets.diffbutton.set_active_block(False)
    self.widgets.shadowbutton.set_sensitive(True)
    self.widgets.highlightbutton.set_sensitive(True)
    self.widgets.diffbutton.set_sensitive(len(self.images) > 1)
    self.tabs.unblock_all_signals()
    self.tabs.set_current_page(0)
    self.window.show_all()

  def update_image(self, key, image):
    """Update main window image with key 'key'."""
    if not self.opened: return
    try:
      self.images[key] = image.clone()
      self.images[key]._luminance = self.images[key].luminance()
      if self.get_current_key() == key: self.draw_image(key)
    except KeyError:
      raise KeyError("There is no image with key '{key}'.")

  def next_image(self, *args, **kwargs):
    """Show next image."""
    if self.images is None: return
    tab = (self.tabs.get_current_page()+1)%self.tabs.get_n_pages()
    self.tabs.set_current_page(tab)

  def previous_image(self, *args, **kwargs):
    """Show previous image."""
    if self.images is None: return
    tab = (self.tabs.get_current_page()-1)%self.tabs.get_n_pages()
    self.tabs.set_current_page(tab)

  # Manage key press events.

  def keypress(self, widget, event):
    """Callback for key press in the main window."""
    keyname = Gdk.keyval_name(event.keyval).upper()
    #print(keyname)
    if keyname == "P":
      self.previous_image()
    elif keyname in ["N", "TAB"]:
      self.next_image()
    elif keyname == "S":
      self.show_statistics()

  # Update luminance RGB components.

  def get_rgb_luminance(self):
    """Get luminance RGB components."""
    return imageprocessing.get_rgb_luminance()

  def rgb_luminance_string(self, rgblum = None):
    """Return luminance RGB components 'rgblum' as a string.
       If 'rgblum' is None, get the current luminance RGB components from self.get_rgb_luminance()."""
    if rgblum is None: rgblum = self.get_rgb_luminance()
    return f"Luminance = {rgblum[0]:.2f}R+{rgblum[1]:.2f}G+{rgblum[2]:.2f}B"

  def set_rgb_luminance_callback(self, callback):
    """Call 'callback(rgblum)' upon update of the luminance RGB components rgblum."""
    self.rgb_luminance_callback = callback

  def set_rgb_luminance(self, rgblum):
    """Set luminance RGB components 'rgblum'."""
    imageprocessing.set_rgb_luminance(rgblum)
    if not self.opened: return
    self.widgets.lumbutton.set_label(self.rgb_luminance_string(rgblum))
    for key in self.images.keys():
      self.images[key]._luminance = self.images[key].luminance()
    if self.widgets.lumbutton.get_active(): self.draw_image(self.get_current_key())
    if self.rgb_luminance_callback is not None: self.rgb_luminance_callback(rgblum)

  def lock_rgb_luminance(self):
    """Lock luminance RGB components (disable Set button)."""
    if not self.opened: return
    self.widgets.rgblumbutton.set_sensitive(False)

  def unlock_rgb_luminance(self):
    """Unlock luminance RGB components (enable Set button)."""
    if not self.opened: return
    self.widgets.rgblumbutton.set_sensitive(True)

  # Guide lines.

  def set_guide_lines(self, plot_guide_lines, redraw = True):
    """Remove any existing guidelines and set new ones defined by the method 'plot_guide_lines'.
       If not None, plot_guide_lines(ax) shall plot the guidelines in axes 'ax' and collect them in ax.guidelines.
       The main window canvas is redrawn if 'redraw' if True."""
    if not self.opened: return
    ax = self.canvas.figure.axes[0]
    try:
      for guideline in ax.guidelines: guideline.remove()
      del(ax.guidelines)
    except:
      pass
    self.plot_guide_lines = plot_guide_lines
    if self.plot_guide_lines is not None: self.plot_guide_lines(ax)
    if redraw:
      self.canvas.draw_idle()
      self.window.queue_draw()

  # Show activity.

  def set_busy(self):
    """Show the main window as busy."""
    if not self.opened: return
    #self.widgets.spinner.start()
    self.widgets.toolbar.set_message("Updating...")
    #self.window.get_root_window().set_cursor(Gdk.Cursor(Gdk.CursorType.WATCH))

  def set_idle(self):
    """Show the main window as idle."""
    if not self.opened: return
    #self.widgets.spinner.stop()
    self.widgets.toolbar.set_message("")
    #self.window.get_root_window().set_cursor(Gdk.Cursor(Gdk.CursorType.ARROW))
