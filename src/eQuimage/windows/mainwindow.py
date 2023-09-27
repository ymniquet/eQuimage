# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 2023.09

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
from .gtk.utils import get_work_area
from .gtk.customwidgets import HScale
from .base import BaseWindow, BaseToolbar, Container
from .luminance import LuminanceRGBDialog
import numpy as np
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure
from collections import OrderedDict as OD
from ..imageprocessing import imageprocessing

"""Main window."""

class MainWindow(BaseWindow):
  """Main window class."""

  MAXIMGSIZE = 0.8 # Maximal width/height of the image (as a fraction of the screen resolution).

  SHADOWCOLOR = np.array([[1.], [.5], [0.]])
  HIGHLIGHTCOLOR = np.array([[1.], [1.], [0.]])
  DIFFCOLOR = np.array([[1.], [1.], [0.]])

  PLOTFRAME = False # Plot Unistellar frame boundary ?

  def open(self):
    """Open main window."""
    if self.opened: return
    if not self.app.get_nbr_images(): return
    self.opened = True
    self.suspendcallbacks = False
    self.set_rgb_luminance_callback(None)
    self.window = Gtk.Window(title = self.app.get_basename())
    self.window.connect("delete-event", self.close)
    self.window.connect("key-press-event", self.keypress)
    self.widgets = Container()
    vbox = Gtk.VBox()
    self.window.add(vbox)
    self.tabs = Gtk.Notebook()
    self.tabs.set_tab_pos(Gtk.PositionType.TOP)
    self.tabs.set_scrollable(True)
    self.tabs.set_show_border(False)
    self.tabs.connect("switch-page", lambda tabs, tab, itab: self.update_tab(itab, self.suspendcallbacks))
    vbox.pack_start(self.tabs, False, False, 0)
    fig = Figure()
    ax = fig.add_axes([0., 0., 1., 1.])
    fwidth, fheight = self.app.get_image_size()
    swidth, sheight = get_work_area(self.window)
    cwidth, cheight = self.MAXIMGSIZE*swidth, self.MAXIMGSIZE*swidth*fheight/fwidth
    if cheight > self.MAXIMGSIZE*sheight:
      cwidth, cheight = self.MAXIMGSIZE*sheight*fwidth/fheight, self.MAXIMGSIZE*sheight
    self.canvas = FigureCanvas(fig)
    self.canvas.set_size_request(cwidth, cheight)
    vbox.pack_start(self.canvas, True, True, 0)
    hbox = Gtk.HBox()
    vbox.pack_start(hbox, False, False, 0)
    hbox.pack_start(Gtk.Label(label = "Output range Min:"), False, False, 4)
    self.widgets.minscale = HScale(0., 0., 1., 0.01, length = 128)
    self.widgets.minscale.connect("value-changed", lambda scale: self.update_output_range("Min", self.suspendcallbacks))
    hbox.pack_start(self.widgets.minscale, True, True, 4)
    hbox.pack_start(Gtk.Label(label = "Max:"), False, False, 4)
    self.widgets.maxscale = HScale(1., 0., 1., 0.01, length = 128)
    self.widgets.maxscale.connect("value-changed", lambda scale: self.update_output_range("Max", self.suspendcallbacks))
    hbox.pack_start(self.widgets.maxscale, True, True, 4)
    hbox = Gtk.HBox()
    vbox.pack_start(hbox, False, False, 0)
    self.widgets.redbutton = Gtk.CheckButton(label = "Red")
    self.widgets.redbutton.set_active(True)
    self.widgets.redbutton.connect("toggled", lambda button: self.update_channels("R", self.suspendcallbacks))
    hbox.pack_start(self.widgets.redbutton, False, False, 0)
    self.widgets.greenbutton = Gtk.CheckButton(label = "Green")
    self.widgets.greenbutton.set_active(True)
    self.widgets.greenbutton.connect("toggled", lambda button: self.update_channels("G", self.suspendcallbacks))
    hbox.pack_start(self.widgets.greenbutton, False, False, 0)
    self.widgets.bluebutton = Gtk.CheckButton(label = "Blue")
    self.widgets.bluebutton.set_active(True)
    self.widgets.bluebutton.connect("toggled", lambda button: self.update_channels("B", self.suspendcallbacks))
    hbox.pack_start(self.widgets.bluebutton, False, False, 0)
    self.widgets.lumbutton = Gtk.CheckButton(label = self.rgb_luminance_string())
    self.widgets.lumbutton.set_active(False)
    self.widgets.lumbutton.connect("toggled", lambda button: self.update_channels("L", self.suspendcallbacks))
    hbox.pack_start(self.widgets.lumbutton, False, False, 0)
    self.widgets.rgblumbutton = Gtk.Button(label = "Set", halign = Gtk.Align.START)
    self.widgets.rgblumbutton.connect("clicked", lambda button: self.app.LuminanceRGBDialog(self.window, self.set_rgb_luminance, self.get_rgb_luminance()))
    hbox.pack_start(self.widgets.rgblumbutton, True, True, 0)
    self.widgets.shadowbutton = Gtk.CheckButton(label = "Shadowed")
    self.widgets.shadowbutton.set_active(False)
    self.widgets.shadowbutton.connect("toggled", lambda button: self.update_modifiers("S", self.suspendcallbacks))
    hbox.pack_start(self.widgets.shadowbutton, False, False, 0)
    self.widgets.highlightbutton = Gtk.CheckButton(label = "Highlighted")
    self.widgets.highlightbutton.set_active(False)
    self.widgets.highlightbutton.connect("toggled", lambda button: self.update_modifiers("H", self.suspendcallbacks))
    hbox.pack_start(self.widgets.highlightbutton, False, False, 0)
    self.widgets.diffbutton = Gtk.CheckButton(label = "Differences")
    self.widgets.diffbutton.set_active(False)
    self.widgets.diffbutton.connect("toggled", lambda button: self.update_modifiers("D", self.suspendcallbacks))
    hbox.pack_start(self.widgets.diffbutton, False, False, 0)
    toolbar = BaseToolbar(self.canvas, fig)
    vbox.pack_start(toolbar, False, False, 0)
    self.reset_images()

  def close(self, *args, **kwargs):
    """Close main window (force if kwargs["force"] = True; don't clear app if kwargs["clear"] = False)."""
    if not self.opened: return None
    force = kwargs["force"] if "force" in kwargs.keys() else False
    if not force:
      dialog = Gtk.MessageDialog(transient_for = self.window,
                                 message_type = Gtk.MessageType.QUESTION,
                                 buttons = Gtk.ButtonsType.OK_CANCEL,
                                 modal = True)
      dialog.set_markup("Are you sure you want to close this image ?")
      response = dialog.run()
      dialog.destroy()
      if response != Gtk.ResponseType.OK: return True
    self.window.destroy()
    self.opened = False
    del self.tabs
    del self.canvas
    del self.widgets
    del self.images
    clear = kwargs["clear"] if "clear" in kwargs.keys() else True
    if clear: self.app.clear()

  # Update tabs.

  def get_current_key(self):
    """Return the key associated to the current tab."""
    tab = self.tabs.get_current_page()
    keys = list(self.images.keys())
    return keys[tab]

  def update_tab(self, tab, suspend):
    """Update image tab."""
    if suspend: return
    keys = list(self.images.keys())
    self.draw_image(keys[tab])

  # Update displayed channels.

  def update_channels(self, toggled, suspend):
    """Update channels buttons."""
    if suspend: return
    self.suspendcallbacks = True
    if toggled == "L":
      luminance = self.widgets.lumbutton.get_active()
      self.widgets.redbutton.set_active(not luminance)
      self.widgets.greenbutton.set_active(not luminance)
      self.widgets.bluebutton.set_active(not luminance)
    else:
      red = self.widgets.redbutton.get_active()
      green = self.widgets.greenbutton.get_active()
      blue = self.widgets.bluebutton.get_active()
      self.widgets.lumbutton.set_active(not (red or green or blue))
    self.suspendcallbacks = False
    self.draw_image(self.get_current_key())

  # Update image modifiers (shadow, highlight, difference).

  def update_modifiers(self, toggled, suspend):
    """Update image modifiers."""
    if suspend: return
    self.suspendcallbacks = True
    if toggled == "D":
      if self.widgets.diffbutton.get_active():
        self.widgets.shadowbutton.set_active(False)
        self.widgets.highlightbutton.set_active(False)
    else:
      self.widgets.diffbutton.set_active(False)
    self.suspendcallbacks = False
    self.draw_image(self.get_current_key())

  # Update output range.

  def update_output_range(self, updated, suspend):
    """Update output range."""
    if suspend: return
    vmin = self.widgets.minscale.get_value()
    vmax = self.widgets.maxscale.get_value()
    if vmax-vmin < 0.01:
      if updated == "Max":
        vmin = max(0., vmax-0.01)
        vmax = vmin+0.01
      else:
        vmax = min(vmin+0.01, 1.)
        vmin = vmax-0.01
      self.suspendcallbacks = True
      self.widgets.minscale.set_value(vmin)
      self.widgets.maxscale.set_value(vmax)
      self.suspendcallbacks = False
    self.refresh_image()

  # Apply image modifiers (shadow, highlight, difference).

  def differences(self, image, reference, channels):
    """Highlight differences between 'image' and 'reference' with DIFFCOLOR color."""
    mask = np.any(image[channels] != reference[channels], axis = 0)
    diff = image.copy()
    diff[:, mask] = self.DIFFCOLOR
    return diff

  def shadows_highlights(self, image, reference, channels, shadow = True, highlight = True):
    """If shadow is True,
         show pixels black on 'image' and     in 'reference' with     SHADOWCOLOR,
         and  pixels black on 'image' but not in 'reference' with 0.5*SHADOWCOLOR,
       If higlight is True,
         show pixels with at least one channel >= 1 on 'image' but not on 'reference' with HIGHLIGHTCOLOR."""
    shdhgh = image.copy()
    if shadow:
      imgmask = np.all(image[channels] <= 0., axis = 0)
      refmask = np.all(reference[channels] <= 0., axis = 0)
      shdhgh[:, imgmask &  refmask] =     self.SHADOWCOLOR
      shdhgh[:, imgmask & ~refmask] = 0.5*self.SHADOWCOLOR
    if highlight:
      mask = np.any((image[channels] >= 1.) & (reference[channels] < 1.), axis = 0)
      shdhgh[:, mask] = self.HIGHLIGHTCOLOR
    return shdhgh

  # Draw or refresh the image displayed in the main window.

  def draw_image(self, key):
    """Draw image with key 'key'."""
    try:
      image = self.images[key]
    except KeyError:
      raise KeyError("There is no image with key '{key}'.")
      return
    shadow = self.widgets.shadowbutton.get_active()
    highlight = self.widgets.highlightbutton.get_active()
    diff = self.widgets.diffbutton.get_active()
    luminance = self.widgets.lumbutton.get_active()
    if luminance:
      image = np.repeat(image.lum[np.newaxis], 3, axis = 0)
      reference = np.repeat(self.reference.lum[np.newaxis], 3, axis = 0)
      channels = np.array([True, False, False])
    else:
      image = image.image.copy()
      reference = self.reference.image
      channels = np.array([self.widgets.redbutton.get_active(), self.widgets.greenbutton.get_active(), self.widgets.bluebutton.get_active()])
      image[~channels] = 0.
    if diff:
      image = self.differences(image, reference, channels)
    elif shadow or highlight:
      image = self.shadows_highlights(image, reference, channels, shadow, highlight)
    self.refresh_image(image)
    if self.PLOTFRAME and self.app.hasframe and key == "Original":
      self.images["Original"].draw_frame_boundary(ax = self.canvas.figure.axes[0])

  def refresh_image(self, image = None):
    """Draw (if 'image' is not None) or refresh the current image."""
    update = self.widgets.currentimage is not None # Is this an update or fresh draw ?
    if image is not None: self.widgets.currentimage = np.clip(np.moveaxis(image, 0, -1), 0., 1.)
    if self.widgets.currentimage is None: return # Nothing to draw !
    vmin = self.widgets.minscale.get_value()
    vmax = self.widgets.maxscale.get_value()
    if vmin > 0. or vmax < 1.:
      ranged = np.where((self.widgets.currentimage >= vmin) & (self.widgets.currentimage <= vmax), self.widgets.currentimage, 0.)
    else:
      ranged = self.widgets.currentimage
    if update:
      self.drawn.set_data(ranged) # Update image (preserves zoom, ...).
    else:
      self.canvas.figure.axes[0].clear() # Draw image.
      self.drawn = self.canvas.figure.axes[0].imshow(ranged)
      self.canvas.figure.axes[0].axis("off")
    self.canvas.draw_idle()

  # Manage the dictionary of images displayed in the different tabs.

  def reset_images(self):
    """Reset main window images."""
    if not self.opened: return
    self.images = None
    self.widgets.currentimage = None
    nimages = self.app.get_nbr_images()
    if nimages > 1:
      self.set_images(OD(Image = self.app.get_image(-1), Original = self.app.get_image(0)), reference = "Original")
    elif nimages > 0:
      self.set_images(OD(Original = self.app.get_image(0)), reference = "Original")

  def set_images(self, images, reference = None):
    """Set main window images and reference."""
    if not self.opened: return
    self.suspendcallbacks = True
    for tab in range(self.tabs.get_n_pages()): self.tabs.remove_page(-1)
    self.images = OD()
    for key, image in images.items():
      self.images[key] = image.clone()
      self.images[key].lum = self.images[key].luminance()
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
    self.widgets.redbutton.set_active(True)
    self.widgets.greenbutton.set_active(True)
    self.widgets.bluebutton.set_active(True)
    self.widgets.lumbutton.set_active(False)
    self.widgets.shadowbutton.set_active(False)
    self.widgets.highlightbutton.set_active(False)
    self.widgets.diffbutton.set_active(False)
    multimages = (len(self.images) > 1)
    self.widgets.shadowbutton.set_sensitive(multimages)
    self.widgets.highlightbutton.set_sensitive(multimages)
    self.widgets.diffbutton.set_sensitive(multimages)
    self.suspendcallbacks = False
    self.window.show_all()
    self.tabs.set_current_page(0)

  def update_image(self, key, image):
    """Update main window image with key 'key'."""
    if not self.opened: return
    try:
      self.images[key] = image.clone()
      self.images[key].lum = self.images[key].luminance()
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
    if keyname == "P":
      self.previous_image()
    elif keyname == "N":
      self.next_image()

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
      self.images[key].lum = self.images[key].luminance()
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
