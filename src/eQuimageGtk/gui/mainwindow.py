# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.7.0 / 2025.05.11
# GUI updated.

"""Main window."""

import os
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GObject
from .gtk.utils import get_work_area
from .gtk.customwidgets import Align, Label, HBox, VBox, Button, CheckButton, HScale, Notebook
from .gtk.keyboard import decode_key
from . import menus
from .base import BaseWindow, FigureCanvas, BaseToolbar, Container
from .luma import LumaRGBDialog
from .statistics import StatsWindow
from .lightcurve import LightCurveWindow
from ..imageprocessing import imageprocessing
import numpy as np
from matplotlib.figure import Figure
from collections import OrderedDict as OD

class MainWindow:
  """Main window class."""

  MAXIMGSIZE = .75 # Maximal width/height of the image (as a fraction of the screen resolution).

  SHADOWCOLOR = np.array([[1.], [.5], [0.]], dtype = imageprocessing.IMGTYPE)
  HIGHLIGHTCOLOR = np.array([[1.], [1.], [0.]], dtype = imageprocessing.IMGTYPE)
  DIFFCOLOR = np.array([[1.], [1.], [0.]], dtype = imageprocessing.IMGTYPE)

  _HELP_ = """[PAGE DOWN]: Next image tab
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
    self.canvas.size = (-1, -1)
    wbox.pack(self.canvas, expand = True, fill = True)
    hbox = HBox(spacing = 0)
    wbox.pack(hbox)
    self.tabs = Notebook(pos = Gtk.PositionType.BOTTOM)
    self.tabs.set_scrollable(True)
    self.tabs.set_show_border(False)
    self.tabs.connect("switch-page", lambda tabs, tab, itab: self.display_tab(itab))
    hbox.pack(self.tabs, expand = True, fill = True)
    label = Label("[?]")
    label.set_tooltip_text(self._HELP_)
    hbox.pack(label, padding = 8)
    hbox = HBox(spacing = 0)
    wbox.pack(hbox)
    hbox.pack("Output range Min:", padding = 4)
    self.widgets.minscale = HScale(0., 0., 1., .01, digits = 2, length = 128)
    self.widgets.minscale.connect("value-changed", lambda scale: self.update_output_range("Min"))
    hbox.pack(self.widgets.minscale, expand = True, fill = True, padding = 4)
    self.widgets.spinner = Gtk.Spinner()
    hbox.pack(self.widgets.spinner, padding = 4)
    hbox.pack("Max:", padding = 4)
    self.widgets.maxscale = HScale(1., 0., 1., .01, digits = 2, length = 128)
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
    self.widgets.rgblumabutton = Button(label = "Set", halign = Align.START)
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
    class MainToolbar(BaseToolbar): home = self.home # Work around matplotlib toolbar limitations.
    self.widgets.toolbar = MainToolbar(self.canvas, fig)
    wbox.pack(self.widgets.toolbar)
    self.set_copy_paste_callbacks(None, None)
    self.set_rgb_luma_callback(None)
    self.set_guide_lines(None)
    self.popup = None
    # Add context menu for statistics & light curve to the canvas.
    self.statswindow = StatsWindow(self.app)
    self.lightwindow = LightCurveWindow(self.app)
    self.contextmenu = Gtk.Menu().new_from_model(menus.builder.get_object("MainWindowContextMenu"))
    self.contextmenu.attach_to_widget(self.window)
    self.canvas.connect("button-press-event", self.button_press)
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

  # Images/tabs associations.

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

  def get_key_tab(self, tab):
    """Return the image key of tab 'tab'."""
    return list(self.images.keys())[tab]

  def get_tab_key(self, key):
    """Return the tab of image 'key'."""
    try:
      return list(self.images.keys()).index(key)
    except KeyError:
      raise KeyError(f"There is no image with key '{key}'.")

  def get_current_key(self):
    """Return the image key of the current tab."""
    tab = self.get_current_tab()
    return self.get_key_tab(tab) if tab >= 0 else None

  def set_current_key(self, key):
    """Set current tab with image 'key'."""
    tab = self.get_tab_key(key)
    if tab is not None: self.set_current_tab(tab)

  def update_key_label(self, key, label):
    """Update the tab label 'label' of image 'key'."""
    tab = self.get_tab_key(key)
    if tab is not None: self.update_tab_label(tab, label)

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
    if vmax-vmin < .01:
      if updated == "Max":
        vmin = max(0., vmax-.01)
        vmax = vmin+.01
      else:
        vmax = min(vmin+.01, 1.)
        vmin = vmax-.01
      self.widgets.minscale.set_value_block(vmin)
      self.widgets.maxscale.set_value_block(vmax)
    self.refresh_image()

  # Image modifiers (shadow, highlight, difference).

  def difference(self, image, reference, channels):
    """Highlight differences between 'image' and 'reference' with color DIFFCOLOR."""
    if reference is None: return
    if reference.shape != image.shape: return
    mask = np.any(image[channels] != reference[channels], axis = 0)
    image[:, mask] = self.DIFFCOLOR

  def shadow_highlight(self, image, reference, channels, shadow = True, highlight = True):
    """If shadow is True,
         show pixels black on 'image' and     on 'reference' with color .5*SHADOWCOLOR,
         and  pixels black on 'image' but not on 'reference' with color     SHADOWCOLOR,
       If higlight is True,
         show pixels with at least one channel >= 1 on 'image' and     on  'reference' with color .5*HIGHLIGHTCOLOR,
         and  pixels with at least one channel >= 1 on 'image' but not on  'reference' with color     HIGHLIGHTCOLOR."""
    if shadow:
      shadowmask = np.all(image[channels] < imageprocessing.IMGTOL, axis = 0)
    if highlight:
      hlightmask = np.any(image[channels] > 1.-imageprocessing.IMGTOL, axis = 0)
    if shadow:
      image[:, shadowmask] = self.SHADOWCOLOR
      if reference is not None:
        if reference.shape == image.shape:
          refmask = np.all(reference[channels] < imageprocessing.IMGTOL, axis = 0)
          image[:, shadowmask & refmask] = .5*self.SHADOWCOLOR
    if highlight:
      image[:, hlightmask] = self.HIGHLIGHTCOLOR
      if reference is not None:
        if reference.shape == image.shape:
          refmask = np.any(reference[channels] > 1.-imageprocessing.IMGTOL, axis = 0)
          image[:, hlightmask & refmask] = .5*self.HIGHLIGHTCOLOR

  # Draw or refresh the image displayed in the main window.

  def set_canvas_size(self, width, height):
    """Set canvas size for a figure width 'width' and height 'height'."""
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
    reference = None
    shadow = self.widgets.shadowbutton.get_active()
    highlight = self.widgets.highlightbutton.get_active()
    diff = self.widgets.diffbutton.get_active()
    modifiers = shadow or highlight or diff
    luma = self.widgets.lumabutton.get_active()
    if luma:
      image = np.repeat(image._luma_[np.newaxis], 3, axis = 0)
      channels = np.array([True, False, False])
      if modifiers and self.refkey is not None:
        reference = np.repeat(self.images[self.refkey]._luma_[np.newaxis], 3, axis = 0)
    else:
      image = image.get_image_copy()
      channels = np.array([self.widgets.redbutton.get_active(), self.widgets.greenbutton.get_active(), self.widgets.bluebutton.get_active()])
      image[~channels] = 0.
      if modifiers and self.refkey is not None:
        reference = self.images[self.refkey].get_image()
    if modifiers:
      if diff:
        self.difference(image, reference, channels)
      else:
        self.shadow_highlight(image, reference, channels, shadow, highlight)
    self.refresh_image(image)
    self.set_idle()

  def refresh_image(self, image = None, redraw = False):
    """Draw 'image' (if not None) or refresh the current image.
       Reset the axes and redraw the whole canvas if 'redraw' is True."""
    update = not redraw # Is this an update or fresh plot ?
    update = update and self.currentimage is not None
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

  def home(self, *args, **kwargs):
    """Replacement callback for matplotlib toolbar home button.
       Matplotlib toolbar home button resets the axes to their original span even if the image
       has been resampled and changed size in between. Therefore, resampled images appear cropped.
       This replacement callback handles image size changes properly by redrawing the canvas completely."""
    self.refresh_image(redraw = True)

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
    self.close_key_windows()
    self.tabs.block_all_signals()
    for tab in range(self.tabs.get_n_pages()): self.tabs.remove_page(-1)
    self.images = OD()
    for key, image in images.items():
      self.images[key] = image.ref()
      self.images[key]._luma_ = self.images[key].luma()
    self.refkey = None
    if reference is not None:
      if reference not in self.images.keys():
        raise KeyError(f"There is no image with key '{reference}'.")
      self.refkey = reference
    for key, image in self.images.items():
      label = self.images[key].meta.get("tag", key)
      if key == self.refkey: label += " (\u2022)"
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
    self.widgets.diffbutton.set_sensitive(self.refkey is not None and len(self.images) > 1)
    self.tabs.unblock_all_signals()
    self.tabs.set_current_page(0)
    self.window.show_all()

  def append_image(self, key, image):
    """Append a new tab for image 'image' with key 'key'.
       This can be done only once set_images has been called."""
    if self.images is None:
      raise RuntimeError("The method 'set_images' must be called before 'append_image'.")
    if key in self.images.keys():
      raise KeyError(f"The key '{key}' is already registered.")
    self.tabs.block_all_signals()
    self.images[key] = image.ref()
    self.images[key]._luma_ = self.images[key].luma()
    label = self.images[key].meta.get("tag", key)
    self.tabs.append_page(Gtk.Alignment(), Label(label)) # Append a zero size dummy child.
    self.tabs.unblock_all_signals()
    self.widgets.diffbutton.set_sensitive(self.refkey is not None)
    self.window.show_all()

  def update_image(self, key, image, create = False):
    """Update image with key 'key'.
       A new tab is appended if 'key' does not exist and 'create' is True. Otherwise, a KeyError exception is raised."""
    if key in self.images.keys():
      self.close_key_windows(key)
      self.images[key] = image.ref()
      self.images[key]._luma_ = self.images[key].luma()
      currentkey = self.get_current_key()
      redraw = (currentkey == key)
      if self.refkey == key:
        shadow = self.widgets.shadowbutton.get_active()
        highlight = self.widgets.highlightbutton.get_active()
        diff = self.widgets.diffbutton.get_active()
        redraw = redraw or shadow or highlight or diff
      if redraw: self.draw_image(currentkey)
    else:
      if create:
        self.append_image(key, image)
      else:
        raise KeyError(f"There is no image with key '{key}'.")

  def delete_image(self, key, force = False, failsafe = False):
    """Delete image with key 'key' if image.meta["deletable"] is False or 'force' is True.
       A KeyError exception is raised if image 'key' does not exist unless 'failsafe' is True."""
    try:
      image = self.images[key]
    except KeyError:
      if not failsafe: raise KeyError(f"There is no image with key '{key}'.")
      return
    deletable = image.meta.get("deletable", False)
    if not deletable and not force: return
    self.close_key_windows(key)
    if self.refkey == key:
      self.widgets.diffbutton.set_active_block(False)
      self.refkey = None
    self.tabs.block_all_signals()
    tab = list(self.images.keys()).index(key)
    del self.images[key]
    self.tabs.remove_page(tab)
    self.draw_image(self.get_current_key())
    self.tabs.unblock_all_signals()
    self.widgets.diffbutton.set_sensitive(self.refkey is not None and len(self.images) > 1)
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
    if self.popup is not None: return
    key = self.get_current_key()
    description = self.images[key].meta.get("description", None)
    if description is None: return
    self.popup = Gtk.Window(Gtk.WindowType.POPUP, transient_for = self.window)
    self.popup.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
    self.popup.set_size_request(480, -1)
    label = Label(description, margin = 8)
    label.set_line_wrap(True)
    self.popup.add(label)
    self.popup.resize(1, 1)
    self.popup.show_all()

  def hide_description(self):
    """Close image description popup."""
    try:
      self.popup.destroy()
    except:
      pass
    self.popup = None

  # Show image statistics & light curve.

  def show_statistics(self):
    """Open image statistics window."""
    key = self.get_current_key()
    if key is None: return
    image = self.images[key]
    ax = self.canvas.figure.axes[0]
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    cropped = image.crop(np.ceil(xlim[0]), np.ceil(xlim[1]), np.ceil(ylim[1]), np.ceil(ylim[0]), inplace = False)
    self.statswindow.open(cropped, key, image.meta.get("tag", key))

  def show_lightcurve(self):
    """Open light curve window."""
    key = self.get_current_key()
    if key is None: return
    image = self.images[key]
    self.lightwindow.open(image, key, image.meta.get("tag", key))

  def close_key_windows(self, key = None):
    """Close statistics and light curve windows opened for key 'key' (any if None)."""
    self.statswindow.close(key = key)
    self.lightwindow.close(key = key)

  # Copy/paste callbacks.

  def set_copy_paste_callbacks(self, copy, paste):
    """Call 'copy(key, image)' (if not None) upon Ctrl+C, and 'paste(key, image)' (if not None) upon Ctrl+V,
       where 'image' is the image with key 'key'."""
    self.copy_callback = copy
    self.paste_callback = paste

  # Manage key & mouse button press/release events.

  def key_press(self, widget, event):
    """Callback for key press in the main window."""
    kbrd = decode_key(event)
    if kbrd.alt: return
    if kbrd.ctrl:
      key = self.get_current_key()
      if key is None: return
      if kbrd.uname == "C" and self.copy_callback is not None:
        self.copy_callback(key, self.images[key])
      elif kbrd.uname == "V" and self.paste_callback is not None:
        self.paste_callback(key, self.images[key])
      elif kbrd.uname == "X":
        self.delete_image(key)
      elif kbrd.uname == "TAB":
        if self.app.toolwindow.opened: self.app.toolwindow.window.present()
    else:
      if kbrd.uname == "PAGE_UP":
        self.previous_image()
      elif kbrd.uname == "PAGE_DOWN":
        self.next_image()
      elif kbrd.uname == "D":
        self.show_description()
      elif kbrd.uname == "S":
        self.show_statistics()

  def key_release(self, widget, event):
    """Callback for key release in the main window."""
    kbrd = decode_key(event)
    if kbrd.uname == "D":
      self.hide_description()

  def button_press(self, widget, event):
    """Callback for mouse button press in the main window."""
    if self.widgets.toolbar.mode != "": return # Don't mess with toolbar actions.
    if event.button == 3:
      self.contextmenu.popup_at_pointer(event)

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
      self.images[key]._luma_ = self.images[key].luma()
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
    """Remove any existing guidelines and plot new ones with the method 'plot_guide_lines'.
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
