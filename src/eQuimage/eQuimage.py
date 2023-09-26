#!/usr/bin/python

# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 2023.08

# TO DO:
#  - Remove hot pixels on super-resolution images ?

import os
os.environ["LANGUAGE"] = "en"
import sys
import inspect
packagepath = os.path.dirname(inspect.getabsfile(inspect.currentframe()))
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Gio
from .gtkhelpers import get_work_area, ErrorDialog, SpinButton, HScale, BaseToolbar
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
plt.style.use(packagepath+"/eQuimage.mplstyle")
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backend_tools import ToolBase
import matplotlib.ticker as ticker
from . import imageprocessing
from .Unistellar_images import UnistellarImage as Image
from collections import OrderedDict as OD

class Container:
  """Empty class as a container."""
  pass

class eQuimageApp(Gtk.Application):
  """The eQuimage application."""

  PLOTFRAME = False # Plot Unistellar frame boundary ?

  def __init__(self, *args, **kwargs):
    """Initialize the eQuimage application."""
    super().__init__(*args, flags = Gio.ApplicationFlags.HANDLES_OPEN, **kwargs)
    self.initialize()

  def do_activate(self):
    """Open the main menu on activation."""
    self.mainmenu.open()

  def do_open(self, files, nfiles, hint):
    """Open command line file on startup."""
    if nfiles > 1:
      print("Syntax : eQuimage [image_file] where [image_file] is the image to be opened.")
      self.quit()
    self.activate()
    self.load_file(files[0].get_path())

  ####################################
  # Subclasses for specific windows. #
  ####################################

  ##### Luminance RGB dialog. #####

  class LuminanceRGBDialog(Gtk.Window):
    """Luminance RGB dialog."""

    # Here we store the data, widgets & methods of this simple dialog directly in the window object.

    def __init__(self, parent, callback, rgblum):
      """Open a luminance RGB dialog for parent window 'parent', with initial
         RGB components 'rgblum'. When the apply button is pressed, close the
         dialog and call 'callback(rgblum)', where rgblum are the updated RGB
         components of the luminance."""
      super().__init__(title = "Luminance RGB",
                       transient_for = parent,
                       modal = True,
                       border_width = 16)
      vbox = Gtk.VBox()
      vbox = Gtk.VBox(spacing = 16)
      self.add(vbox)
      hbox = Gtk.HBox(spacing = 8)
      vbox.pack_start(hbox, False, False, 0)
      hbox.pack_start(Gtk.Label(label = "Red:"), False, False, 0)
      self.redspin = SpinButton(rgblum[0], 0., 1., 0.01)
      hbox.pack_start(self.redspin, False, False, 0)
      hbox.pack_start(Gtk.Label(label = 8*" "+"Green:"), False, False, 0)
      self.greenspin = SpinButton(rgblum[1], 0., 1., 0.01)
      hbox.pack_start(self.greenspin, False, False, 0)
      hbox.pack_start(Gtk.Label(label = 8*" "+"Blue:"), False, False, 0)
      self.bluespin = SpinButton(rgblum[2], 0., 1., 0.01)
      hbox.pack_start(self.bluespin, False, False, 0)
      hbox = Gtk.HButtonBox(homogeneous = True, spacing = 16, halign = Gtk.Align.START)
      vbox.pack_start(hbox, False, False, 0)
      applybutton = Gtk.Button(label = "Apply")
      applybutton.connect("clicked", self.apply)
      hbox.pack_start(applybutton, False, False, 0)
      cancelbutton = Gtk.Button(label = "Cancel")
      cancelbutton.connect("clicked", lambda button: self.destroy())
      hbox.pack_start(cancelbutton, False, False, 0)
      self.callback = callback
      self.show_all()

    def apply(self, *args, **kwargs):
      """Apply luminance RGB settings."""
      red = self.redspin.get_value()
      green = self.greenspin.get_value()
      blue = self.bluespin.get_value()
      total = red+green+blue
      if total <= 0.: return
      rgblum = (red/total, green/total, blue/total)
      self.callback(rgblum)
      self.destroy()

  ##### Generic application window. #####

  class BaseWindow:
    """Generic window."""

    def __init__(self, app):
      """Bind the window with application 'app'."""
      self.app = app
      self.opened = False

  ##### Main menu. ######

  class MainMenu(BaseWindow):
    """Main menu class."""

    def open(self):
      """Open main menu window."""
      if self.opened: return
      self.opened = True
      self.window = Gtk.ApplicationWindow(application = self.app, title = "eQuimage", border_width = 8)
      self.window.connect("delete-event", self.close)
      vbox = Gtk.VBox(spacing = 8, halign = Gtk.Align.START)
      self.window.add(vbox)
      frame = Gtk.Frame(label = " File management ")
      frame.set_label_align(0.025, 0.5)
      vbox.pack_start(frame, False, False, 0)
      vbbox = Gtk.VBox(homogeneous = True, margin = 8)
      frame.add(vbbox)
      self.buttons = {}
      self.buttons["Open"] = Gtk.Button(label = "Open")
      self.buttons["Open"].context = {"noimage": True, "nooperations": True, "activetool": False, "noframe": True}
      self.buttons["Open"].connect("clicked", self.load_file)
      vbbox.pack_start(self.buttons["Open"], False, False, 0)
      self.buttons["Save"] = Gtk.Button(label = "Save")
      self.buttons["Save"].context = {"noimage": False, "nooperations": False, "activetool": False, "noframe": True}
      self.buttons["Save"].connect("clicked", self.save_file)
      vbbox.pack_start(self.buttons["Save"], False, False, 0)
      self.buttons["Close"] = Gtk.Button(label = "Close")
      self.buttons["Close"].context = {"noimage": False, "nooperations": True, "activetool": True, "noframe": True}
      self.buttons["Close"].connect("clicked", lambda button: self.app.clear())
      vbbox.pack_start(self.buttons["Close"], False, False, 0)
      self.buttons["Quit"] = Gtk.Button(label = "Quit")
      self.buttons["Quit"].context = {"noimage": True, "nooperations": True, "activetool": True, "noframe": True}
      self.buttons["Quit"].connect("clicked", self.close)
      vbbox.pack_start(self.buttons["Quit"], False, False, 0)
      frame = Gtk.Frame(label = " Image transformations ")
      frame.set_label_align(0.025, 0.5)
      vbox.pack_start(frame, False, False, 0)
      vbbox = Gtk.VBox(homogeneous = True, margin = 8)
      frame.add(vbbox)
      self.buttons["Hotpixels"] = Gtk.Button(label = "Remove hot pixels")
      self.buttons["Hotpixels"].context = {"noimage": False, "nooperations": True, "activetool": False, "noframe": True}
      self.buttons["Hotpixels"].connect("clicked", lambda button: self.app.run_tool(self.app.RemoveHotPixelsTool))
      vbbox.pack_start(self.buttons["Hotpixels"], False, False, 0)
      self.buttons["Sharpen"] = Gtk.Button(label = "Sharpen")
      self.buttons["Sharpen"].context = {"noimage": False, "nooperations": True, "activetool": False, "noframe": True}
      self.buttons["Sharpen"].connect("clicked", lambda button: self.app.sharpen())
      vbbox.pack_start(self.buttons["Sharpen"], False, False, 0)
      self.buttons["Colors"] = Gtk.Button(label = "Balance colors")
      self.buttons["Colors"].context = {"noimage": False, "nooperations": True, "activetool": False, "noframe": True}
      self.buttons["Colors"].connect("clicked", lambda button: self.app.run_tool(self.app.ColorBalanceTool))
      vbbox.pack_start(self.buttons["Colors"], False, False, 0)
      self.buttons["Stretch"] = Gtk.Button(label = "Stretch (Shadow/Midtone/Highlight)")
      self.buttons["Stretch"].context = {"noimage": False, "nooperations": True, "activetool": False, "noframe": True}
      self.buttons["Stretch"].connect("clicked", lambda button: self.app.run_tool(self.app.StretchTool))
      vbbox.pack_start(self.buttons["Stretch"], False, False, 0)
      self.buttons["Grayscale"] = Gtk.Button(label = "Convert to gray scale")
      self.buttons["Grayscale"].context = {"noimage": False, "nooperations": True, "activetool": False, "noframe": True}
      self.buttons["Grayscale"].connect("clicked", lambda button: self.app.gray_scale())
      vbbox.pack_start(self.buttons["Grayscale"], False, False, 0)
      self.buttons["Cancel"] = Gtk.Button(label = "Cancel last operation")
      self.buttons["Cancel"].context = {"noimage": False, "nooperations": False, "activetool": False, "noframe": True}
      self.buttons["Cancel"].connect("clicked", lambda button: self.app.cancel_last_operation())
      vbbox.pack_start(self.buttons["Cancel"], False, False, 0)
      self.buttons["Logs"] = Gtk.Button(label = "View logs")
      self.buttons["Logs"].context = {"noimage": False, "nooperations": True, "activetool": True, "noframe": True}
      self.buttons["Logs"].connect("clicked", lambda button: self.app.logwindow.open())
      vbbox.pack_start(self.buttons["Logs"], False, False, 0)
      frame = Gtk.Frame(label = " Unistellar frame ")
      frame.set_label_align(0.025, 0.5)
      vbox.pack_start(frame, False, False, 0)
      hbbox = Gtk.HBox(margin = 8, spacing = 8, homogeneous = True)
      frame.add(hbbox)
      self.buttons["Removeframe"] = Gtk.Button(label = "Remove frame")
      self.buttons["Removeframe"].context = {"noimage": False, "nooperations": True, "activetool": False, "noframe": False}
      self.buttons["Removeframe"].connect("clicked", lambda button: self.app.remove_unistellar_frame())
      hbbox.pack_start(self.buttons["Removeframe"], True, True, 0)
      self.buttons["Restoreframe"] = Gtk.Button(label = "Restore frame")
      self.buttons["Restoreframe"].context = {"noimage": False, "nooperations": True, "activetool": False, "noframe": False}
      self.buttons["Restoreframe"].connect("clicked", lambda button: self.app.restore_unistellar_frame())
      hbbox.pack_start(self.buttons["Restoreframe"], True, True, 0)
      self.window.show_all()
      self.update()

    def close(self, *args, **kwargs):
      """Close main menu window (force if kwargs["force"] = True)."""
      if not self.opened: return None
      force = kwargs["force"] if "force" in kwargs.keys() else False
      if not force:
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

    def update(self, present = True):
      """Update main menu window (and present if 'present' is True)."""
      if not self.opened: return
      context = self.app.get_context()
      for button in self.buttons.values():
        if not context["image"]:
          sensitive = button.context["noimage"]
        elif context["activetool"]:
          sensitive = button.context["activetool"]
        else:
          sensitive = True
        if not context["frame"]:
          sensitive = sensitive and button.context["noframe"]
        if not context["operations"]:
          sensitive = sensitive and button.context["nooperations"]
        button.set_sensitive(sensitive)
      if present: self.window.present()

    def load_file(self, *args, **kwargs):
      """Open file dialog and load image file."""
      if not self.opened: return
      dialog = Gtk.FileChooserDialog(title = "Open",
                                     transient_for = self.window,
                                     action = Gtk.FileChooserAction.OPEN)
      dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                         Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
      response = dialog.run()
      filename = dialog.get_filename()
      dialog.destroy()
      if response != Gtk.ResponseType.OK: return
      try:
        self.app.load_file(filename)
      except Exception as err:
        ErrorDialog(self.window, str(err))
        self.app.clear()

    def save_file(self, *args, **kwargs):
      """Open file dialog and save image file."""
      if not self.opened: return
      if not self.app.get_context("image"): return
      dialog = Gtk.FileChooserDialog(title = "Save as",
                                     transient_for = self.window,
                                     action = Gtk.FileChooserAction.SAVE)
      dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                         Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
      filename = self.app.get_savename()
      dialog.set_filename(filename)
      dialog.set_current_name(os.path.basename(filename))
      response = dialog.run()
      filename = dialog.get_filename()
      dialog.destroy()
      if response != Gtk.ResponseType.OK: return
      try:
        self.app.save_file(filename)
      except Exception as err:
        ErrorDialog(self.window, str(err))

  ##### Main window. ######

  class MainWindow(BaseWindow):
    """Main window class."""

    MAXIMGSIZE = 0.8 # Maximal width/height of the image (as a fraction of the screen resolution).

    SHADOWCOLOR = np.array([[1.], [.5], [0.]])
    HIGHLIGHTCOLOR = np.array([[1.], [1.], [0.]])
    DIFFCOLOR = np.array([[1.], [1.], [0.]])

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
      shhl = image.copy()
      if shadow:
        imgmask = np.all(image[channels] <= 0., axis = 0)
        refmask = np.all(reference[channels] <= 0., axis = 0)
        shhl[:, imgmask &  refmask] =     self.SHADOWCOLOR
        shhl[:, imgmask & ~refmask] = 0.5*self.SHADOWCOLOR
      if highlight:
        mask = np.any((image[channels] >= 1.) & (reference[channels] < 1.), axis = 0)
        shhl[:, mask] = self.HIGHLIGHTCOLOR
      return shhl

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
      if self.app.PLOTFRAME and self.app.hasframe and key == "Original":
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

    def keypress(self, widget, event):
      """Callback for key press in the main window."""
      keyname = Gdk.keyval_name(event.keyval).upper()
      if keyname == "P":
        self.previous_image()
      elif keyname == "N":
        self.next_image()

    def get_rgb_luminance(self):
      """Get luminance RGB components."""
      return imageprocessing.get_rgb_luminance()

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

    def rgb_luminance_string(self, rgblum = None):
      """Return luminance RGB components 'rgblum' as a string.
         If 'rgblum' is None, get the current luminance RGB components from self.get_rgb_luminance()."""
      if rgblum is None: rgblum = self.get_rgb_luminance()
      return f"Luminance = {rgblum[0]:.2f}R+{rgblum[1]:.2f}G+{rgblum[2]:.2f}B"

    def lock_rgb_luminance(self):
      """Lock luminance RGB components (disable Set button)."""
      if not self.opened: return
      self.widgets.rgblumbutton.set_sensitive(False)

    def unlock_rgb_luminance(self):
      """Unlock luminance RGB components (enable Set button)."""
      if not self.opened: return
      self.widgets.rgblumbutton.set_sensitive(True)

  ##### Log window. ######

  class LogWindow(BaseWindow):
    """Log window class."""

    def open(self):
      if self.opened: return
      if not self.app.get_nbr_images(): return
      self.opened = True
      self.window = Gtk.Window(title = f"Logs for {self.app.get_basename()}", border_width = 16)
      self.window.connect("delete-event", self.close)
      self.window.set_size_request(480, 360)
      vbox = Gtk.VBox(spacing = 8)
      self.window.add(vbox)
      textview = Gtk.TextView()
      textview.set_editable(False)
      textview.set_cursor_visible(False)
      textview.set_wrap_mode(True)
      textview.set_justification(Gtk.Justification.LEFT)
      vbox.pack_start(textview, True, True, 0)
      self.textbuffer = textview.get_buffer()
      hbox = Gtk.HButtonBox(homogeneous = True, spacing = 16, halign = Gtk.Align.START)
      vbox.pack_start(hbox, False, False, 0)
      copybutton = Gtk.Button(label = "Copy")
      copybutton.connect("clicked", self.copy_to_clipboard)
      hbox.pack_start(copybutton, False, False, 0)
      closebutton = Gtk.Button(label = "Close")
      closebutton.connect("clicked", self.close)
      hbox.pack_start(closebutton, False, False, 0)
      self.update()
      self.window.show_all()

    def close(self, *args, **kwargs):
      """Close log window."""
      if not self.opened: return
      self.window.destroy()
      self.opened = False
      del self.textbuffer

    def update(self):
      """Update log window."""
      if not self.opened: return
      self.textbuffer.set_text(self.app.logs())

    def copy_to_clipboard(self, *args, **kwargs):
      """Copy the content of the log window to the clipboard."""
      if not self.opened: return
      clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
      clipboard.set_text(self.textbuffer.get_text(self.textbuffer.get_start_iter(), self.textbuffer.get_end_iter(), False), -1)

  ##### Base tool window. ######

  class BaseToolWindow(BaseWindow):
    """Base tool window class."""

    def __init__(self, app):
      """Bind window with app 'app'."""
      super().__init__(app)
      self.operation = None

    def open(self, image, title):
      """Open tool window with title 'title' for image 'image'."""
      if self.opened: return
      self.opened = True
      self.image = image.clone(description = "Image")
      self.image.stats = None
      self.reference = image.clone(description = "Reference")
      self.reference.stats = None
      self.operation = None
      self.window = Gtk.Window(title = title,
                               transient_for = self.app.mainmenu.window,
                               border_width = 16)
      self.window.connect("delete-event", self.close)
      self.widgets = Container()

    def close(self, *args, **kwargs):
      """Close tool window."""
      if not self.opened: return
      self.app.mainwindow.set_rgb_luminance_callback(None)
      self.window.destroy()
      self.opened = False
      self.app.finalize_tool(self.image, self.operation)
      del self.widgets
      del self.image
      del self.reference

    def apply_cancel_reset_close_buttons(self):
      """Return a Gtk.HButtonBox with Apply/Cancel/Reset/Close buttons
         connected to self.apply, self.cancel, self.reset and self.close methods."""
      hbox = Gtk.HButtonBox(homogeneous = True, spacing = 16, halign = Gtk.Align.START)
      self.widgets.applybutton = Gtk.Button(label = "Apply")
      self.widgets.applybutton.connect("clicked", self.apply)
      hbox.pack_start(self.widgets.applybutton, False, False, 0)
      self.widgets.cancelbutton = Gtk.Button(label = "Cancel")
      self.widgets.cancelbutton.connect("clicked", self.cancel)
      self.widgets.cancelbutton.set_sensitive(False)
      hbox.pack_start(self.widgets.cancelbutton, False, False, 0)
      self.widgets.resetbutton = Gtk.Button(label = "Reset")
      self.widgets.resetbutton.connect("clicked", self.reset)
      hbox.pack_start(self.widgets.resetbutton, False, False, 0)
      self.widgets.closebutton = Gtk.Button(label = "Close")
      self.widgets.closebutton.connect("clicked", self.close)
      hbox.pack_start(self.widgets.closebutton, False, False, 0)
      return hbox

  ##### Remove hot pixels tool window. ######

  class RemoveHotPixelsTool(BaseToolWindow):

    initratio = 2.

    def open(self, image):
      """Open tool window for image 'image'."""
      if self.opened: return
      if not self.app.mainwindow.opened: return
      super().open(image, "Remove hot pixels")
      vbox = Gtk.VBox(spacing = 16)
      self.window.add(vbox)
      hbox = Gtk.HBox(spacing = 8)
      vbox.pack_start(hbox, False, False, 0)
      hbox.pack_start(Gtk.Label(label = "Channel(s):"), False, False, 0)
      self.widgets.rgbbutton = Gtk.RadioButton.new_with_label_from_widget(None, "RGB")
      hbox.pack_start(self.widgets.rgbbutton, False, False, 0)
      self.widgets.lumbutton = Gtk.RadioButton.new_with_label_from_widget(self.widgets.rgbbutton, "Luminance")
      hbox.pack_start(self.widgets.lumbutton, False, False, 0)
      hbox = Gtk.HBox(spacing = 8)
      vbox.pack_start(hbox, False, False, 0)
      hbox.pack_start(Gtk.Label(label = "Ratio:"), False, False, 0)
      self.widgets.ratiospin = SpinButton(self.initratio, 1., 10., 0.01)
      hbox.pack_start(self.widgets.ratiospin, False, False, 0)
      vbox.pack_start(self.apply_cancel_reset_close_buttons(), False, False, 0)
      self.app.mainwindow.set_images(OD(Image = self.image, Reference = self.reference), reference = "Reference")
      self.resetparams = ("RGB", self.initratio)
      self.window.show_all()

    def reset(self, *args, **kwargs):
      """Reset tool."""
      channels, ratio = self.resetparams
      if channels == "RGB":
        self.widgets.rgbbutton.set_active(True)
      else:
        self.widgets.lumbutton.set_active(True)
      self.widgets.ratiospin.set_value(ratio)

    def apply(self, *args, **kwargs):
      """Apply tool."""
      ratio = self.widgets.ratiospin.get_value()
      if self.widgets.rgbbutton.get_active():
        channels = "RGB"
        self.operation = f"RemoveHotPixels(RGB, ratio = {ratio:.2f})"
      else:
        channels = "L"
        red, green, blue = imageprocessing.get_rgb_luminance()
        self.operation = f"RemoveHotPixels(L({red:.2f}, {green:.2f}, {blue:.2f}), ratio = {ratio:.2f})"
      self.image.copy_from(self.reference)
      print(f"Removing hot pixels on {channels} channel(s)...")
      self.image.remove_hot_pixels(ratio, channels = channels)
      self.app.mainwindow.update_image("Image", self.image)
      self.resetparams = (channels, ratio)
      self.widgets.cancelbutton.set_sensitive(True)

    def cancel(self, *args, **kwargs):
      """Cancel tool."""
      if self.operation is None: return
      self.image.copy_from(self.reference)
      self.app.mainwindow.update_image("Image", self.image)
      self.widgets.ratiospin.set_value(self.initratio)
      self.operation = None
      self.resetparams = ("RGB" if self.widgets.rgbbutton.get_active() else "L", self.initratio)
      self.widgets.cancelbutton.set_sensitive(False)

  ##### Color balance tool window. ######

  class ColorBalanceTool(BaseToolWindow):
    """Color balance tool."""

    def open(self, image):
      """Open tool window for image 'image'."""
      if self.opened: return
      if not self.app.mainwindow.opened: return
      super().open(image, "Color balance")
      vbox = Gtk.VBox(spacing = 16)
      self.window.add(vbox)
      hbox = Gtk.HBox(spacing = 8)
      vbox.pack_start(hbox, False, False, 0)
      hbox.pack_start(Gtk.Label(label = "Red:"), False, False, 0)
      self.widgets.redspin = SpinButton(1., 0., 2., 0.01)
      hbox.pack_start(self.widgets.redspin, False, False, 0)
      hbox.pack_start(Gtk.Label(label = 8*" "+"Green:"), False, False, 0)
      self.widgets.greenspin = SpinButton(1., 0., 2., 0.01)
      hbox.pack_start(self.widgets.greenspin, False, False, 0)
      hbox.pack_start(Gtk.Label(label = 8*" "+"Blue:"), False, False, 0)
      self.widgets.bluespin = SpinButton(1., 0., 2., 0.01)
      hbox.pack_start(self.widgets.bluespin, False, False, 0)
      vbox.pack_start(self.apply_cancel_reset_close_buttons(), False, False, 0)
      self.app.mainwindow.set_images(OD(Image = self.image, Reference = self.reference), reference = "Reference")
      self.resetparams = (1., 1., 1.)
      self.window.show_all()

    def reset(self, *args, **kwargs):
      """Reset tool."""
      red, green, blue = self.resetparams
      self.widgets.redspin.set_value(red)
      self.widgets.greenspin.set_value(green)
      self.widgets.bluespin.set_value(blue)

    def apply(self, *args, **kwargs):
      """Apply tool."""
      red = self.widgets.redspin.get_value()
      green = self.widgets.greenspin.get_value()
      blue = self.widgets.bluespin.get_value()
      print("Balancing colors...")
      self.image.copy_from(self.reference)
      self.image.color_balance(red, green, blue)
      self.app.mainwindow.update_image("Image", self.image)
      self.operation = f"ColorBalance(R = {red:.2f}, G = {green:.2f}, B = {blue:.2f})"
      self.resetparams = (red, green, blue)
      self.widgets.cancelbutton.set_sensitive(True)

    def cancel(self, *args, **kwargs):
      """Cancel tool."""
      if self.operation is None: return
      self.image.copy_from(self.reference)
      self.app.mainwindow.update_image("Image", self.image)
      self.widgets.redspin.set_value(1.)
      self.widgets.greenspin.set_value(1.)
      self.widgets.bluespin.set_value(1.)
      self.operation = None
      self.resetparams = (1., 1., 1.)
      self.widgets.cancelbutton.set_sensitive(False)

  ##### Stretch tool window. #####

  class StretchTool(BaseToolWindow):
    """Stretch tool."""

    def open(self, image):
      """Open tool window for image 'image'."""
      if self.opened: return
      if not self.app.mainwindow.opened: return
      super().open(image, "Stretch (Shadow/Midtone/Highlight)")
      self.suspendcallbacks = True
      self.window.connect("key-press-event", self.keypress)
      vbox = Gtk.VBox(spacing = 16)
      self.window.add(vbox)
      fbox = Gtk.VBox(spacing = 0)
      vbox.pack_start(fbox, True, True, 0)
      self.widgets.fig = Figure(figsize = (10., 6.), layout = "constrained")
      canvas = FigureCanvas(self.widgets.fig)
      canvas.set_size_request(800, 480)
      fbox.pack_start(canvas, True, True, 0)
      toolbar = BaseToolbar(canvas, self.widgets.fig)
      fbox.pack_start(toolbar, False, False, 0)
      grid = Gtk.Grid(column_spacing = 8)
      vbox.pack_start(grid, True, True, 0)
      reflabel = Gtk.Label(label = "[Reference]", halign = Gtk.Align.START)
      grid.add(reflabel)
      self.widgets.refstats = Gtk.Label(label = "", halign = Gtk.Align.START)
      grid.attach_next_to(self.widgets.refstats, reflabel, Gtk.PositionType.RIGHT, 1, 1)
      imglabel = Gtk.Label(label = "[Image]", halign = Gtk.Align.START)
      grid.attach_next_to(imglabel, reflabel, Gtk.PositionType.BOTTOM, 1, 1)
      self.widgets.imgstats = Gtk.Label(label = "", halign = Gtk.Align.START)
      grid.attach_next_to(self.widgets.imgstats, imglabel, Gtk.PositionType.RIGHT, 1, 1)
      hbox = Gtk.HBox(spacing = 8)
      vbox.pack_start(hbox, False, False, 0)
      self.widgets.linkbutton = Gtk.CheckButton(label = "Link RGB channels")
      self.widgets.linkbutton.set_active(True)
      self.widgets.linkbutton.connect("toggled", lambda button: self.update(suspend = self.suspendcallbacks))
      hbox.pack_start(self.widgets.linkbutton, True, True, 0)
      self.widgets.lrgbtabs = Gtk.Notebook()
      self.widgets.lrgbtabs.set_tab_pos(Gtk.PositionType.TOP)
      self.widgets.lrgbtabs.connect("switch-page", lambda tabs, tab, itab: self.update(tab = itab, suspend = self.suspendcallbacks))
      vbox.pack_start(self.widgets.lrgbtabs, False, False, 0)
      self.channelkeys = []
      self.resetparams = {}
      self.currentparams = {}
      self.widgets.channels = {}
      for key, name, color, lcolor in (("R", "Red", (1., 0., 0.), (1., 0., 0.)),
                                       ("G", "Green", (0., 1., 0.), (0., 1., 0.)),
                                       ("B", "Blue", (0., 0., 1.), (0., 0., 1.)),
                                       ("V", "HSV value = max(RGB)", (0., 0., 0.), (1., 1., 1.)),
                                       ("L", "Luminance", (0.5, 0.5, 0.5), (1., 1., 1.))):
        self.channelkeys.append(key)
        self.resetparams[key] = (0., 0.5, 1., 0., 1.)
        self.currentparams[key] = (0., 0.5, 1., 0., 1.)
        self.widgets.channels[key] = Container()
        channel = self.widgets.channels[key]
        channel.color = np.array(color)
        channel.lcolor = np.array(lcolor)
        tbox = Gtk.VBox(spacing = 16, margin = 16)
        hbox = Gtk.HBox(spacing = 8)
        tbox.pack_start(hbox, False, False, 0)
        hbox.pack_start(Gtk.Label(label = "Shadow:"), False, False, 0)
        channel.shadowspin = SpinButton(0., 0., 0.25, 0.001, digits = 3)
        channel.shadowspin.connect("value-changed", lambda button: self.update(updated = "shadow", suspend = self.suspendcallbacks))
        hbox.pack_start(channel.shadowspin, False, False, 0)
        hbox.pack_start(Gtk.Label(label = 8*" "+"Midtone:"), False, False, 0)
        channel.midtonespin = SpinButton(0.5, 0., 1., 0.01, digits = 3)
        channel.midtonespin.connect("value-changed", lambda button: self.update(updated = "midtone", suspend = self.suspendcallbacks))
        hbox.pack_start(channel.midtonespin, False, False, 0)
        hbox.pack_start(Gtk.Label(label = 8*" "+"Hichlight:"), False, False, 0)
        channel.highlightspin = SpinButton(1., 0., 1., 0.01, digits = 3)
        channel.highlightspin.connect("value-changed", lambda button: self.update(updated = "highlight", suspend = self.suspendcallbacks))
        hbox.pack_start(channel.highlightspin, False, False, 0)
        hbox = Gtk.HBox(spacing = 8)
        tbox.pack_start(hbox, False, False, 0)
        hbox.pack_start(Gtk.Label(label = "Low range:"), False, False, 0)
        channel.lowspin = SpinButton(0., -10., 0., 0.01, digits = 3)
        channel.lowspin.connect("value-changed", lambda button: self.update(updated = "low", suspend = self.suspendcallbacks))
        hbox.pack_start(channel.lowspin, False, False, 0)
        hbox.pack_start(Gtk.Label(label = 8*" "+"High range:"), False, False, 0)
        channel.highspin = SpinButton(1., 1., 10., 0.01, digits = 3)
        channel.highspin.connect("value-changed", lambda button: self.update(updated = "high", suspend = self.suspendcallbacks))
        hbox.pack_start(channel.highspin, False, False, 0)
        self.widgets.lrgbtabs.append_page(tbox, Gtk.Label(label = name))
      vbox.pack_start(self.apply_cancel_reset_close_buttons(), False, False, 0)
      self.widgets.logscale = False
      self.widgets.fig.refhistax = self.widgets.fig.add_subplot(211)
      self.plot_reference_histogram()
      self.widgets.fig.imghistax = self.widgets.fig.add_subplot(212)
      self.plot_image_histogram()
      self.app.mainwindow.set_images(OD(Image = self.image, Reference = self.reference), reference = "Reference")
      self.app.mainwindow.set_rgb_luminance_callback(self.update_rgb_luminance)
      self.window.show_all()
      self.suspendcallbacks = False
      self.widgets.lrgbtabs.set_current_page(3)

    def reset(self, *args, **kwargs):
      """Reset tool."""
      suspendcallbacks = self.suspendcallbacks
      self.suspendcallbacks = True
      unlinkrgb = False
      redparams = self.resetparams["R"]
      for key in self.channelkeys:
        channel = self.widgets.channels[key]
        if key in ("R", "G", "B"):
          unlinkrgb = unlinkrgb or (self.resetparams[key] != redparams)
        shadow, midtone, highlight, low, high = self.resetparams[key]
        channel.shadowspin.set_value(shadow)
        channel.midtonespin.set_value(midtone)
        channel.highlightspin.set_value(highlight)
        channel.lowspin.set_value(low)
        channel.highspin.set_value(high)
      if unlinkrgb: self.widgets.linkbutton.set_active(False)
      self.suspendcallbacks = suspendcallbacks
      self.update()

    def apply(self, *args, **kwargs):
      """Apply tool."""
      self.image.copy_from(self.reference)
      self.operation = "Stretch("
      for key in self.channelkeys:
        channel = self.widgets.channels[key]
        shadow = channel.shadowspin.get_value()
        midtone = channel.midtonespin.get_value()
        highlight = channel.highlightspin.get_value()
        low = channel.lowspin.get_value()
        high = channel.highspin.get_value()
        if key != "L":
          self.operation += f"{key} : (shadow = {shadow:.3f}, midtone = {midtone:.3f}, highlight = {highlight:.3f}, low = {low:.3f}, high = {high:.3f}), "
        else:
          red, green, blue = imageprocessing.get_rgb_luminance()
          self.operation += f"L({red:.2f}, {green:.2f}, {blue:.2f}) : (shadow = {shadow:.3f}, midtone = {midtone:.3f}, highlight = {highlight:.3f}, low = {low:.3f}, high = {high:.3f}))"
        self.resetparams[key] = (shadow, midtone, highlight, low, high)
        if shadow == 0. and midtone == 0.5 and highlight == 1. and low == 0. and high == 1.: continue
        print(f"Stretching {key} channel...")
        self.image.clip_shadows_highlights(shadow, highlight, channels = key)
        self.image.midtone_correction((midtone-shadow)/(highlight-shadow), channels = key)
        self.image.set_dynamic_range((low, high), (0., 1.), channels = key)
      self.app.mainwindow.update_image("Image", self.image)
      self.plot_image_histogram()
      self.widgets.cancelbutton.set_sensitive(True)

    def cancel(self, *args, **kwargs):
      """Cancel tool."""
      if self.operation is None: return
      suspendcallbacks = self.suspendcallbacks
      self.suspendcallbacks = True
      self.image.copy_from(self.reference)
      self.app.mainwindow.update_image("Image", self.image)
      self.plot_image_histogram()
      self.operation = None
      for key in self.channelkeys:
        channel = self.widgets.channels[key]
        channel.shadowspin.set_value(0.)
        channel.midtonespin.set_value(0.5)
        channel.highlightspin.set_value(1.)
        channel.lowspin.set_value(0.)
        channel.highspin.set_value(1.)
        self.resetparams[key] = (0., 0.5, 1., 0., 1.)
      self.suspendcallbacks = suspendcallbacks
      self.update()
      self.widgets.cancelbutton.set_sensitive(False)

    def display_stats(self, key):
      """Display reference and image stats for channel 'key'."""
      channel = {"R": "Red", "G": "Green", "B": "Blue", "V": "Value", "L": "Luminance"}[key]
      npixels = self.reference.image[0].size
      if self.reference.stats is not None:
        minimum, maximum, median, zerocount, oorcount = self.reference.stats[key]
        string = f"{channel} : min = {minimum:.3f}, max = {maximum:.3f}, med = {median:.3f}, {zerocount} ({100.*zerocount/npixels:.2f}%) zeros, {oorcount} ({100.*oorcount/npixels:.2f}%) out-of-range"
        self.widgets.refstats.set_label(string)
      if self.image.stats is not None:
        minimum, maximum, median, zerocount, oorcount = self.image.stats[key]
        string = f"{channel} : min = {minimum:.3f}, max = {maximum:.3f}, med = {median:.3f}, {zerocount} ({100.*zerocount/npixels:.2f}%) zeros, {oorcount} ({100.*oorcount/npixels:.2f}%) out-of-range"
        self.widgets.imgstats.set_label(string)

    def transfer_function(self, shadow, midtone, highlight, low, high, maxlum = 2.):
      """Return (t, f(t)) on a grid 0 < t < 'maxlum', where f is the transfer function for
        'shadow', 'midtone', 'highlight', 'low', and 'high' parameters."""
      t = np.linspace(0., maxlum, int(256*maxlum))
      clipped = np.clip(t, shadow, highlight)
      expanded = np.interp(clipped, (shadow, highlight), (0., 1.))
      corrected = imageprocessing.midtone_transfer_function(expanded, (midtone-shadow)/(highlight-shadow))
      ft = np.interp(corrected, (low, high), (0., 1.))
      return t, ft

    def plot_histogram(self, ax, image, title = None, xlabel = "Level", ylabel = "Count (a.u.)", ylogscale = False):
      """Plot histogram for image 'image' on axes 'ax' with title 'title', x label 'xlabel' and y label 'ylabel'.
         Use log scale on y-axis if ylogscale is True."""
      edges, hists = image.histograms(nbins = 128)
      centers = (edges[:-1]+edges[1:])/2.
      hists /= hists[:, 1:].max()
      ax.clear()
      ax.plot(centers, hists[0], "-", color = self.widgets.channels["R"].color)
      ax.plot(centers, hists[1], "-", color = self.widgets.channels["G"].color)
      ax.plot(centers, hists[2], "-", color = self.widgets.channels["B"].color)
      ax.plot(centers, hists[3], "-", color = self.widgets.channels["V"].color)
      ax.plot(centers, hists[4], "-", color = self.widgets.channels["L"].color)
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
      ax.axvspan(1., 10., color = "gray", alpha = 0.25)
      if title is not None: ax.set_title(title)

    def plot_reference_histogram(self):
      """Plot reference histogram."""
      suspendcallbacks = self.suspendcallbacks
      self.suspendcallbacks = True
      ax = self.widgets.fig.refhistax
      ax.clear()
      self.plot_histogram(ax, self.reference, title = "[Reference]", xlabel = None, ylabel = "Count (a.u.)/Transf. func.", ylogscale = self.widgets.logscale)
      tab = self.widgets.lrgbtabs.get_current_page()
      key = self.channelkeys[tab]
      channel = self.widgets.channels[key]
      shadow = channel.shadowspin.get_value()
      midtone = channel.midtonespin.get_value()
      highlight = channel.highlightspin.get_value()
      low = channel.lowspin.get_value()
      high = channel.highspin.get_value()
      color = channel.color
      lcolor = channel.lcolor
      self.widgets.shadowline = ax.axvline(shadow, color = 0.1*lcolor, linestyle = "-.")
      self.widgets.midtoneline = ax.axvline(midtone, color = 0.5*lcolor, linestyle = "-.")
      self.widgets.highlightline = ax.axvline(highlight, color = 0.9*lcolor, linestyle = "-.")
      t, ft = self.transfer_function(shadow, midtone, highlight, low, high)
      self.widgets.tfplot, = ax.plot(t, ft, linestyle = ":", color = color)
      self.widgets.fig.canvas.draw_idle()
      self.reference.stats = self.reference.statistics()
      self.display_stats(key)
      self.suspendcallbacks = suspendcallbacks

    def plot_image_histogram(self):
      """Plot image histogram."""
      suspendcallbacks = self.suspendcallbacks
      self.suspendcallbacks = True
      ax = self.widgets.fig.imghistax
      ax.clear()
      self.plot_histogram(ax, self.image, title = "[Image]", ylogscale = self.widgets.logscale)
      self.widgets.fig.canvas.draw_idle()
      self.image.stats = self.image.statistics()
      tab = self.widgets.lrgbtabs.get_current_page()
      key = self.channelkeys[tab]
      self.display_stats(key)
      self.suspendcallbacks = suspendcallbacks

    def update(self, *args, **kwargs):
      """Update histograms."""
      if "suspend" in kwargs.keys():
        if kwargs["suspend"]: return
      self.suspendcallbacks = True
      if "tab" in kwargs.keys():
        tab = kwargs["tab"]
        key = self.channelkeys[tab]
        self.display_stats(key)
      else:
        tab = self.widgets.lrgbtabs.get_current_page()
        key = self.channelkeys[tab]
      updated = kwargs["updated"] if "updated" in kwargs.keys() else None
      channel = self.widgets.channels[key]
      color = channel.color
      lcolor = channel.lcolor
      shadow = channel.shadowspin.get_value()
      midtone = channel.midtonespin.get_value()
      highlight = channel.highlightspin.get_value()
      low = channel.lowspin.get_value()
      high = channel.highspin.get_value()
      if highlight < shadow+0.05:
        highlight = shadow+0.05
        channel.highlightspin.set_value(highlight)
      if updated in ["shadow", "highlight"]:
        shadow_, midtone_, highlight_, low_, high_ = self.currentparams[key]
        midtone_ = (midtone_-shadow_)/(highlight_-shadow_)
        midtone = shadow+midtone_*(highlight-shadow)
        channel.midtonespin.set_value(midtone)
      if midtone <= shadow:
        midtone = shadow+0.001
        channel.midtonespin.set_value(midtone)
      if midtone >= highlight:
        midtone = highlight-0.001
        channel.midtonespin.set_value(midtone)
      self.currentparams[key] = (shadow, midtone, highlight, low, high)
      self.widgets.shadowline.set_color(0.1*lcolor)
      self.widgets.shadowline.set_xdata([shadow, shadow])
      self.widgets.midtoneline.set_color(0.5*lcolor)
      self.widgets.midtoneline.set_xdata([midtone, midtone])
      self.widgets.highlightline.set_color(0.9*lcolor)
      self.widgets.highlightline.set_xdata([highlight, highlight])
      self.widgets.tfplot.set_color(color)
      t, ft = self.transfer_function(shadow, midtone, highlight, low, high)
      self.widgets.tfplot.set_xdata(t)
      self.widgets.tfplot.set_ydata(ft)
      self.widgets.fig.canvas.draw_idle()
      if self.widgets.linkbutton.get_active() and key in ("R", "G", "B"):
        for rgbkey in ("R", "G", "B"):
          rgbchannel = self.widgets.channels[rgbkey]
          rgbchannel.shadowspin.set_value(shadow)
          rgbchannel.midtonespin.set_value(midtone)
          rgbchannel.highlightspin.set_value(highlight)
          rgbchannel.lowspin.set_value(low)
          rgbchannel.highspin.set_value(high)
          self.currentparams[rgbkey] = (shadow, midtone, highlight, low, high)
      self.suspendcallbacks = False

    def keypress(self, widget, event):
      """Callback for key press in the stretch tool window."""
      keyname = Gdk.keyval_name(event.keyval).upper()
      if keyname == "L":
        self.widgets.logscale = not self.widgets.logscale
        self.plot_reference_histogram()
        self.plot_image_histogram()

    def update_rgb_luminance(self, rgblum):
      """Update luminance rgb components."""
      self.plot_reference_histogram()
      self.plot_image_histogram()

  ###############################
  # Application data & methods. #
  ###############################

  def initialize(self):
    """Initialize the eQuimage object."""
    self.mainmenu = self.MainMenu(self)
    self.mainwindow = self.MainWindow(self)
    self.toolwindow = self.BaseToolWindow(self)
    self.logwindow = self.LogWindow(self)
    self.filename = None
    self.hasframe = False
    self.clear()

  def clear(self):
    """Close file (if any) and clear the eQuimage object data."""
    if self.filename is not None: print(f"Closing {self.filename}...")
    self.mainwindow.close(force = True, clear = False)
    self.logwindow.close()
    self.toolwindow.close()
    if self.hasframe: del self.frame
    self.hasframe = False
    self.filename = None
    self.pathname = None
    self.basename = None
    self.savename = None
    self.images = []
    self.operations = []
    self.width = 0
    self.height = 0
    self.exif = None
    self.mainmenu.update()

  def get_context(self, key = None):
    """Return the application context:
         - get_context("image") = True if an image is loaded.
         - get_context("operations") = True if operations have been performed on the image.
         - get_context("activetool") = True if a tool is active.
         - get_context("frame") = True if the image has a frame.
         - get_context() returns all above keys as a dictionnary."""
    context = {"image": len(self.images) > 0, "operations": len(self.operations) > 0, "activetool": self.toolwindow.opened, "frame": self.hasframe}
    return context[key] if key is not None else context

  def get_filename(self):
    """Return image file name."""
    return self.filename

  def get_basename(self):
    """Return image base name."""
    return self.basename

  def get_pathname(self):
    """Return image path name."""
    return self.pathname

  def get_savename(self):
    """Return image save name."""
    return self.savename

  def get_image_size(self):
    """Return width and height of the images."""
    return self.width, self.height

  def push_image(self, image):
    """Push a clone of image 'image' on top of the images stack."""
    self.images.append(image.clone())

  def pop_image(self):
    """Pop and return image from the top of the images stack."""
    return self.images.pop()

  def get_nbr_images(self):
    """Return the number of images in the images stack."""
    return len(self.images)

  def get_image(self, index):
    """Return image with index 'index' from the images stack."""
    return self.images[index]

  def load_file(self, filename):
    """Load image file 'filename'."""
    print(f"Loading file {filename}...")
    image = Image()
    self.exif = image.load(filename, description = "Original")
    self.clear()
    self.filename = filename
    self.pathname = os.path.dirname(filename)
    self.basename = os.path.basename(filename)
    root, ext = os.path.splitext(filename)
    self.savename = root+"-post"+ext
    self.width, self.height = image.size()
    self.hasframe = image.check_frame()
    if self.hasframe:
      print(f"Image has a frame type '{image.get_frame_type()}'.")
      self.frame = image.get_frame()
    self.push_image(image)
    self.mainwindow.open()
    self.mainmenu.update()

  def save_file(self, filename = None):
    """Save image file 'filename' (defaults to self.savename if None)."""
    if not self.images: return
    if filename is None: filename = self.savename
    if self.images[-1].is_gray_scale():
      print(f"Saving file {filename} as gray scale...")
      self.images[-1].save_gray_scale(filename, exif = self.exif)
    else:
      print(f"Saving file {filename} as RGBA...")
      self.images[-1].save(filename, exif = self.exif)
    root, ext = os.path.splitext(filename)
    with open(root+".log", "w") as f: f.write(self.logs())
    self.savename = filename

  def push_operation(self, image, operation = "Unknown"):
    """Push operation 'operation' on image 'image' on top of the operations and images stacks."""
    self.push_image(image)
    self.operations.append((operation, self.images[-1]))

  def pop_operation(self):
    """Pop and return last (operation, image) from the top of the operations stack.
       The images stack is truncated accordingly."""
    operation, image = self.operations.pop()
    index = self.images.index(image)
    self.images = self.images[:index]
    return operation, image

  def get_nbr_operations(self):
    """Return the number of operations in the operations stack."""
    return len(self.operations)

  def logs(self):
    """Return logs from the operations stack."""
    text = ""
    for operation, image in self.operations:
      text += operation+"\n"
    return text

  def run_tool(self, ToolClass):
    """Run tool 'ToolClass'."""
    if not self.mainwindow.opened: return
    if self.toolwindow.opened: return
    self.toolwindow = ToolClass(self)
    self.toolwindow.open(self.images[-1])
    self.mainmenu.update(present = False)
    self.toolwindow.window.present()

  def finalize_tool(self, image, operation):
    """Finalize tool: push ('image', 'operation') on the operations and images stacks (if operation is not None)
       and refresh main menu, main window, and log window."""
    if operation is not None:
      image.set_description("Image")
      self.push_operation(image, operation)
    self.mainwindow.reset_images()
    self.logwindow.update()
    self.mainmenu.update()

  def cancel_last_operation(self):
    """Cancel last operation."""
    if not self.mainwindow.opened: return
    if self.toolwindow.opened: return
    if not self.operations: return
    print("Cancelling last operation...")
    self.pop_operation()
    self.mainwindow.reset_images()
    self.logwindow.update()
    self.mainmenu.update()

  def sharpen(self):
    """Sharpen image."""
    if not self.mainwindow.opened: return
    if self.toolwindow.opened: return
    print("Sharpening image...")
    self.finalize_tool(self.images[-1].sharpen(inplace = False), f"Sharpen()")

  def gray_scale(self):
    """Convert image to gray scale."""
    if not self.mainwindow.opened: return
    if self.toolwindow.opened: return
    print("Converting to gray scale...")
    red, green, blue = imageprocessing.get_rgb_luminance()
    self.finalize_tool(self.images[-1].gray_scale(inplace = False), f"GrayScale({red:.2f}, {green:.2f}, {blue:.2f})")

  def remove_unistellar_frame(self):
    """Remove Unistellar frame."""
    if not self.mainwindow.opened: return
    if self.toolwindow.opened: return
    if not self.hasframe: return
    print("Removing Unistellar frame...")
    self.finalize_tool(self.images[-1].remove_frame(self.frame, inplace = False), "RemoveUnistellarFrame()")

  def restore_unistellar_frame(self):
    """Restore Unistellar frame."""
    if not self.mainwindow.opened: return
    if self.toolwindow.opened: return
    if not self.hasframe: return
    print("Restoring Unistellar frame...")
    self.finalize_tool(self.images[-1].add_frame(self.frame, inplace = False), "RestoreUnistellarFrame()")

#

def run():
  """Run eQuimage."""
  application = eQuimageApp()
  application.run(sys.argv)

#

if __name__ == "__main__": run()
