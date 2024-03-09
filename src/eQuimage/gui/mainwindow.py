# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.4.0 / 2024.02.26
# GUI updated.
#
# TODO:
#  - Store tab key in the tab ?

"""Main window."""

import os
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GObject
from .gtk.utils import get_work_area
from .gtk.customwidgets import Label, HBox, VBox, CheckButton, HScale, Notebook
from .base import BaseWindow, BaseToolbar, Container
from .luma import LumaRGBDialog
from .statistics import StatsWindow
from ..imageprocessing import imageprocessing
import numpy as np
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure
from collections import OrderedDict as OD

class MainWindow:
  """Main window class."""

  MAXIMGSIZE = 0.75 # Maximal width/height of the image (as a fraction of the screen resolution).

  SHADOWCOLOR = np.array([[1.], [.5], [0.]], dtype = imageprocessing.IMGTYPE)
  HIGHLIGHTCOLOR = np.array([[1.], [1.], [0.]], dtype = imageprocessing.IMGTYPE)
  DIFFCOLOR = np.array([[1.], [1.], [0.]], dtype = imageprocessing.IMGTYPE)

  __help__ = """[PAGE DOWN]: Next image tab
[PAGE UP]: Previous image tab
[D] : Show image description (if available)
[S]: Statistics (of the zoomed area)
[CTRL+C]: Copy image in a new tab
[CTRL+V]: Paste tab parameters to the tool
[CTRL+X]: Close image tab (if possible)
[CTRL+TAB]: Toggle between main and tool windows""" # Help tootip.

  def __init__(self, app):
    """Bind the window with application 'app'."""
    self.app = app

  def open(self):
    """Open main window."""
    self.window = Gtk.ApplicationWindow(application = self.app, title = "eQuimage v"+self.app.version)
    self.window.connect("delete-event", self.close)
    self.window.connect("key-press-event", self.key_press)
    self.window.connect("key-release-event", self.key_release)
    self.widgets = Container()
    wbox = VBox(spacing = 0)
    self.window.add(wbox)
    fig = Figure()
    ax = fig.add_axes([0., 0., 1., 1.])
    self.canvas = FigureCanvas(fig)
    wbox.pack(self.canvas, expand = True, fill = True)
    self.canvas.size = (-1, -1)
    hbox = HBox(spacing = 0)
    wbox.pack(hbox)
    self.tabs = Notebook(pos = Gtk.PositionType.BOTTOM)
    self.tabs.set_scrollable(True)
    self.tabs.set_show_border(False)
    self.tabs.connect("switch-page", lambda tabs, tab, itab: self.display_tab(itab))
    hbox.pack(self.tabs, expand = True, fill = True)
    label = Label("?")
    label.set_tooltip_text(self.__help__)
    hbox.pack(label, padding = 8)
    hbox = HBox(spacing = 0)
    wbox.pack(hbox)
    hbox.pack("Output range Min:", padding = 4)
    self.widgets.minscale = HScale(0., 0., 1., 0.01, length = 128)
    self.widgets.minscale.connect("value-changed", lambda scale: self.update_output_range("Min"))
    hbox.pack(self.widgets.minscale, expand = True, fill = True, padding = 4)
    self.widgets.spinner = Gtk.Spinner()
    hbox.pack(self.widgets.spinner, padding = 4)
    hbox.pack("Max:", padding = 4)
    self.widgets.maxscale = HScale(1., 0., 1., 0.01, length = 128)
    self.widgets.maxscale.connect("value-changed", lambda scale: self.update_output_range("Max"))
    hbox.pack(self.widgets.maxscale, expand = True, fill = True, padding = 4)
    hbox = HBox(spacing = 0)
    wbox.pack(hbox)
    self.widgets.redbutton = CheckButton(label = "Red")
    self.widgets.redbutton.set_active(True)
    self.widgets.redbutton.connect("toggled", lambda button: self.update_channels("R"))
    hbox.pack(self.widgets.redbutton)
    self.widgets.greenbutton = CheckButton(label = "Green")
    self.widgets.greenbutton.set_active(True)
    self.widgets.greenbutton.connect("toggled", lambda button: self.update_channels("G"))
    hbox.pack(self.widgets.greenbutton)
    self.widgets.bluebutton = CheckButton(label = "Blue")
    self.widgets.bluebutton.set_active(True)
    self.widgets.bluebutton.connect("toggled", lambda button: self.update_channels("B"))
    hbox.pack(self.widgets.bluebutton)
    self.widgets.lumabutton = CheckButton(label = self.rgb_luma_string())
    self.widgets.lumabutton.set_active(False)
    self.widgets.lumabutton.connect("toggled", lambda button: self.update_channels("L"))
    hbox.pack(self.widgets.lumabutton)
    self.widgets.rgblumabutton = Gtk.Button(label = "Set", halign = Gtk.Align.START)
    self.widgets.rgblumabutton.connect("clicked", lambda button: LumaRGBDialog(self.window, self.set_rgb_luma, self.get_rgb_luma()))
    hbox.pack(self.widgets.rgblumabutton, expand = True, fill = True)
    self.widgets.shadowbutton = CheckButton(label = "Shadowed")
    self.widgets.shadowbutton.set_active(False)
    self.widgets.shadowbutton.connect("toggled", lambda button: self.update_modifiers("S"))
    hbox.pack(self.widgets.shadowbutton)
    self.widgets.highlightbutton = CheckButton(label = "Highlighted")
    self.widgets.highlightbutton.set_active(False)
    self.widgets.highlightbutton.connect("toggled", lambda button: self.update_modifiers("H"))
    hbox.pack(self.widgets.highlightbutton)
    self.widgets.diffbutton = CheckButton(label = "Differences")
    self.widgets.diffbutton.set_active(False)
    self.widgets.diffbutton.connect("toggled", lambda button: self.update_modifiers("D"))
    hbox.pack(self.widgets.diffbutton)
    self.widgets.toolbar = BaseToolbar(self.canvas, fig)
    wbox.pack(self.widgets.toolbar)
    self.set_copy_paste_callbacks(None, None)
    self.set_rgb_luma_callback(None)
    self.set_guide_lines(None)
    self.descpopup = None
    self.statswindow = StatsWindow(self.app)
    self.reset_images()
    self.window.show_all()

  def close(self, *args, **kwargs):
    """Quit application."""
    dialog = Gtk.MessageDialog(transient_for = self.window,
                               message_type = Gtk.MessageType.QUESTION,
                               buttons = Gtk.ButtonsType.OK_CANCEL,
                               modal = True)
    dialog.set_markup("Are you sure you want to quit ?")
    response = dialog.run()
    dialog.destroy()
    if response != Gtk.ResponseType.OK: return True
    print("Exiting eQuimage...")
    self.app.quit()

  # Update tabs.

  def get_current_tab(self):
    """Return current tab."""
    return self.tabs.get_current_page()

  def set_current_tab(self, tab):
    """Set current tab 'tab'."""
    if self.get_current_tab() != tab: self.tabs.set_current_page(tab)

  def display_tab(self, tab):
    """Display image of tab 'tab'."""
    keys = list(self.images.keys())
    self.draw_image(keys[tab])

  def update_tab_label(self, tab, label):
    """Update the label 'label' of tab 'tab'."""
    self.tabs.set_tab_label(self.tabs.get_nth_page(tab), Label(label))

  def get_keys(self):
    """Return the list of image keys."""
    return list(self.images.keys())

  def get_current_key(self):
    """Return key of current tab."""
    tab = self.get_current_tab()
    if tab < 0: return None
    keys = list(self.images.keys())
    return keys[tab]

  def set_current_key(self, key):
    """Set current key 'key'."""
    try:
      tab = list(self.images.keys()).index(key)
    except KeyError:
      raise KeyError(f"There is no image with key '{key}'.")
      return
    self.set_current_tab(tab)

  def update_key_label(self, key, label):
    """Update the tab label 'label' of key 'key'."""
    try:
      tab = list(self.images.keys()).index(key)
    except KeyError:
      raise KeyError(f"There is no image with key '{key}'.")
      return
    self.update_tab_label(tab, label)

  # Update displayed channels.

  def update_channels(self, toggled):
    """Update channels buttons."""
    if toggled == "L":
      luma = self.widgets.lumabutton.get_active()
      self.widgets.redbutton.set_active_block(not luma)
      self.widgets.greenbutton.set_active_block(not luma)
      self.widgets.bluebutton.set_active_block(not luma)
    else:
      red = self.widgets.redbutton.get_active()
      green = self.widgets.greenbutton.get_active()
      blue = self.widgets.bluebutton.get_active()
      self.widgets.lumabutton.set_active_block(not (red or green or blue))
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
    modifiers = self.widgets.shadowbutton.get_active() or self.widgets.highlightbutton.get_active() or self.widgets.diffbutton.get_active()
    self.widgets.minscale.set_sensitive(not modifiers)
    self.widgets.maxscale.set_sensitive(not modifiers)
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

  def set_canvas_size(self, width, height):
    """Set canvas size for a target figure width 'width' and height 'height'."""
    swidth, sheight = get_work_area(self.window)
    cwidth, cheight = self.MAXIMGSIZE*swidth, self.MAXIMGSIZE*swidth*height/width
    if cheight > self.MAXIMGSIZE*sheight:
      cwidth, cheight = self.MAXIMGSIZE*sheight*width/height, self.MAXIMGSIZE*sheight
    if self.canvas.size != (cwidth, cheight):
      self.canvas.size = (cwidth, cheight)
      self.canvas.set_size_request(cwidth, cheight)
      self.window.resize(1, 1)

  def draw_image(self, key):
    """Apply modifiers and draw image with key 'key'."""
    if key is None: return
    try:
      image = self.images[key]
    except KeyError:
      raise KeyError(f"There is no image with key '{key}'.")
      return
    shadow = self.widgets.shadowbutton.get_active()
    highlight = self.widgets.highlightbutton.get_active()
    diff = self.widgets.diffbutton.get_active()
    modifiers = shadow or highlight or diff
    luma = self.widgets.lumabutton.get_active()
    if luma:
      image = np.repeat(image.lum[np.newaxis], 3, axis = 0)
      channels = np.array([True, False, False])
      if modifiers: reference = np.repeat(self.reference.lum[np.newaxis], 3, axis = 0)
    else:
      image = image.get_image().copy()
      channels = np.array([self.widgets.redbutton.get_active(), self.widgets.greenbutton.get_active(), self.widgets.bluebutton.get_active()])
      image[~channels] = 0.
      if modifiers: reference = self.reference.get_image()
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

  # Manage the dictionary of images displayed in the tabs.

  def reset_images(self):
    """Reset main window images."""
    self.images = None
    self.currentimage = None
    nimages = self.app.get_nbr_images()
    if nimages > 0:
      self.set_canvas_size(*self.app.get_image_size())
      if nimages > 3:
        self.set_images(OD(Image = self.app.get_image(-1), Original = self.app.get_image(1)), reference = "Original")
      elif nimages > 0:
        self.set_images(OD(Original = self.app.get_image(1)), reference = "Original")
    else:
      self.set_canvas_size(800, 600)
      try:
        splash = imageprocessing.load_image(os.path.join(self.app.get_packagepath(), "images", "splash.png"), {"tag": "Welcome"})
      except:
        splash = imageprocessing.black_image(800, 600, {"tag": "Welcome"})
      self.set_images(OD(Splash = splash))

  def set_images(self, images, reference = None):
    """Set main window images and reference."""
    self.tabs.block_all_signals()
    for tab in range(self.tabs.get_n_pages()): self.tabs.remove_page(-1)
    self.images = OD()
    for key, image in images.items():
      #self.images[key] = image.clone()
      self.images[key] = image.ref()
      self.images[key].lum = self.images[key].luma()
    if reference is None:
      self.reference = self.images[key]
    else:
      try:
        self.reference = self.images[reference]
      except KeyError:
        raise KeyError(f"There is no image with key '{reference}'.")
        self.reference = self.images[key]
    self.reference.meta["deletable"] = False # Can't delete the reference image.
    for key, image in self.images.items():
      label = self.images[key].meta.get("tag", key)
      if key == reference: label += " (\u2022)"
      self.tabs.append_page(Gtk.Alignment(), Label(label)) # Append a zero size dummy child.
    self.widgets.redbutton.set_active_block(True)
    self.widgets.greenbutton.set_active_block(True)
    self.widgets.bluebutton.set_active_block(True)
    self.widgets.lumabutton.set_active_block(False)
    self.widgets.shadowbutton.set_active_block(False)
    self.widgets.highlightbutton.set_active_block(False)
    self.widgets.diffbutton.set_active_block(False)
    self.widgets.minscale.set_sensitive(True)
    self.widgets.maxscale.set_sensitive(True)
    self.widgets.shadowbutton.set_sensitive(True)
    self.widgets.highlightbutton.set_sensitive(True)
    self.widgets.diffbutton.set_sensitive(len(self.images) > 1)
    self.tabs.unblock_all_signals()
    self.tabs.set_current_page(0)
    self.window.show_all()

  def append_image(self, key, image):
    """Append a new tab for image 'image' with key 'key'.
       This can be done only once set_images has been called."""
    if self.images is None:
      raise RuntimeError("The method 'set_images' must be called before 'append_image'.")
      return
    if key in self.images.keys():
      raise KeyError(f"The key '{key}' is already registered.")
      return
    self.tabs.block_all_signals()
    #self.images[key] = image.clone()
    self.images[key] = image.ref()
    self.images[key].lum = self.images[key].luma()
    label = self.images[key].meta.get("tag", key)
    self.tabs.append_page(Gtk.Alignment(), Label(label)) # Append a zero size dummy child.
    self.tabs.unblock_all_signals()
    self.window.show_all()

  def update_image(self, key, image):
    """Update main window image with key 'key'."""
    try:
      #self.images[key] = image.clone()
      self.images[key] = image.ref()
      self.images[key].lum = self.images[key].luma()
      if self.get_current_key() == key: self.draw_image(key)
    except KeyError:
      raise KeyError(f"There is no image with key '{key}'.")

  def delete_image(self, key, force = False):
    """Delete image with key 'key' if image.meta["deletable"] is False or 'force' is True."""
    try:
      image = self.images[key]
    except KeyError:
      raise KeyError(f"There is no image with key '{key}'.")
      return
    deletable = image.meta.get("deletable", False)
    if not deletable and not force: return
    self.tabs.block_all_signals()
    tab = list(self.images.keys()).index(key)
    del self.images[key]
    self.tabs.remove_page(tab)
    self.draw_image(self.get_current_key())
    self.tabs.unblock_all_signals()
    self.window.show_all()

  def get_nbr_images(self):
    """Return the number of image tabs."""
    return self.tabs.get_n_pages()

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

  # Show image description.

  def show_description(self):
    """Open image description popup."""
    if self.descpopup is not None: return
    key = self.get_current_key()
    description = self.images[key].meta.get("description", None)
    if description is None: return
    self.descpopup = Gtk.Window(Gtk.WindowType.POPUP, transient_for = self.window)
    self.descpopup.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
    self.descpopup.set_size_request(480, -1)
    label = Label(description, margin = 8)
    label.set_line_wrap(True)
    self.descpopup.add(label)
    self.descpopup.resize(1, 1)
    self.descpopup.show_all()

  def hide_description(self):
    """Close image description popup."""
    try:
      self.descpopup.destroy()
    except:
      pass
    self.descpopup = None

  # Show image statistics.

  def show_statistics(self):
    """Open image statistics window."""
    key = self.get_current_key()
    if key is None: return
    image = self.images[key]
    ax = self.canvas.figure.axes[0]
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    cropped = image.crop(np.ceil(xlim[0]), np.ceil(xlim[1]), np.ceil(ylim[1]), np.ceil(ylim[0]), inplace = False)
    self.statswindow.open(cropped)

  # Copy/paste callbacks.

  def set_copy_paste_callbacks(self, copy, paste):
    """Call 'copy(key, image)' (if not None) upon Ctrl+C, and 'paste(key, image)' (if not None) upon Ctrl+V,
       where 'image' is the image with key 'key'."""
    self.copy_callback = copy
    self.paste_callback = paste

  # Manage key press/release events.

  def key_press(self, widget, event):
    """Callback for key press in the main window."""
    ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
    alt = event.state & Gdk.ModifierType.MOD1_MASK
    if alt: return
    keyname = Gdk.keyval_name(event.keyval).upper()
    #print(keyname)
    if ctrl:
      key = self.get_current_key()
      if key is None: return
      if keyname == "C" and self.copy_callback is not None:
        self.copy_callback(key, self.images[key])
      elif keyname == "V" and self.paste_callback is not None:
        self.paste_callback(key, self.images[key])
      elif keyname == "X":
        self.delete_image(key)
      elif keyname == "TAB":
        if self.app.toolwindow.opened: self.app.toolwindow.window.present()
    else:
      if keyname == "PAGE_UP":
        self.previous_image()
      elif keyname == "PAGE_DOWN":
        self.next_image()
      elif keyname == "D":
        self.show_description()
      elif keyname == "S":
        self.show_statistics()

  def key_release(self, widget, event):
    """Callback for key release in the main window."""
    keyname = Gdk.keyval_name(event.keyval).upper()
    if keyname == "D":
      self.hide_description()

  # Update luma RGB components.

  def get_rgb_luma(self):
    """Get luma RGB components."""
    return imageprocessing.get_rgb_luma()

  def rgb_luma_string(self, rgbluma = None):
    """Return luma RGB components 'rgbluma' as a string.
       If 'rgbluma' is None, get the current luma RGB components from self.get_rgb_luma()."""
    if rgbluma is None: rgbluma = self.get_rgb_luma()
    return f"Luma = {rgbluma[0]:.2f}R+{rgbluma[1]:.2f}G+{rgbluma[2]:.2f}B"

  def set_rgb_luma_callback(self, callback):
    """Call 'callback(rgbluma)' (if not None) upon update of the luma RGB components rgbluma."""
    self.rgb_luma_callback = callback

  def set_rgb_luma(self, rgbluma):
    """Set luma RGB components 'rgbluma'."""
    imageprocessing.set_rgb_luma(rgbluma)
    self.widgets.lumabutton.set_label(self.rgb_luma_string(rgbluma))
    for key in self.images.keys():
      self.images[key].lum = self.images[key].luma()
    if self.widgets.lumabutton.get_active(): self.draw_image(self.get_current_key())
    if self.rgb_luma_callback is not None: self.rgb_luma_callback(rgbluma)

  def lock_rgb_luma(self):
    """Lock luma RGB components (disable Set button)."""
    self.widgets.rgblumabutton.set_sensitive(False)

  def unlock_rgb_luma(self):
    """Unlock luma RGB components (enable Set button)."""
    self.widgets.rgblumabutton.set_sensitive(True)

  # Guide lines.

  def set_guide_lines(self, plot_guide_lines, redraw = True):
    """Remove any existing guidelines and set new ones defined by the method 'plot_guide_lines'.
       If not None, plot_guide_lines(ax) shall plot the guidelines in axes 'ax' and collect them in ax.guidelines.
       The main window canvas is redrawn if 'redraw' if True."""
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
    self.widgets.spinner.start()
    #self.widgets.toolbar.set_message("Updating...")
    self.window.get_root_window().set_cursor(Gdk.Cursor(Gdk.CursorType.WATCH))

  def set_idle(self):
    """Show the main window as idle."""
    self.widgets.spinner.stop()
    #self.widgets.toolbar.set_message("")
    self.window.get_root_window().set_cursor(Gdk.Cursor(Gdk.CursorType.ARROW))
