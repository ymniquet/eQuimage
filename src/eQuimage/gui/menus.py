# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.6.1 / 2024.09.01
# GUI updated.

"""Application menus."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, GObject
from .gtk.customwidgets import Label, HBox, VBox, HButtonBox, Button, CheckButton, RadioButtons, Entry
from .gtk.filechoosers import ImageFileChooserDialog
from .base import InfoDialog, ErrorDialog
from .settings import SettingsWindow
from .tools.blackpoint import BlackPointTool
from .tools.arcsinh import ArcsinhStretchTool
from .tools.hyperbolic import GeneralizedHyperbolicStretchTool
from .tools.midtone import MidtoneStretchTool
from .tools.clahe import CLAHETool
from .tools.colorbalance import ColorBalanceTool
from .tools.colorsaturation import ColorSaturationTool
from .tools.ghscolorsat import GHSColorSaturationTool
from .tools.colornoise import ColorNoiseReductionTool
from .tools.grayscale import GrayScaleConversionTool
from .tools.hotpixels import RemoveHotPixelsTool
from .tools.gaussian import GaussianFilterTool
from .tools.butterworth import ButterworthFilterTool
from .tools.wavelets import WaveletsFilterTool
from .tools.bilateral import BilateralFilterTool
from .tools.nlmeans import NonLocalMeansFilterTool
from .tools.totalvariation import TotalVariationFilterTool
from .tools.unsharp import UnsharpMaskTool
from .tools.thresholdmask import ThresholdMaskTool
from .tools.blend import BlendTool
from .tools.resample import ResampleTool
from .tools.pixelmath import PixelMathTool
from .tools.addframe import AddUnistellarFrame
from .tools.switch import SwitchTool
import os
import tempfile
import threading
import subprocess

XMLMENUS = """
<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <menu id="MainMenu">
    <submenu>
      <attribute name="label">File</attribute>
      <section>
        <item>
          <attribute name="label">Open</attribute>
          <attribute name="action">app.open</attribute>
          <attribute name="accel">&lt;Primary&gt;o</attribute>
        </item>
        <item>
          <attribute name="label">Save</attribute>
          <attribute name="action">app.save</attribute>
          <attribute name="accel">&lt;Primary&gt;s</attribute>
        </item>
        <item>
          <attribute name="label">Close</attribute>
          <attribute name="action">app.close</attribute>
        </item>
      </section>
      <section>
        <item>
          <attribute name="label">Settings</attribute>
          <attribute name="action">app.settings</attribute>
        </item>
      </section>
      <section>
        <item>
          <attribute name="label">Quit</attribute>
          <attribute name="action">app.quit</attribute>
          <attribute name="accel">&lt;Primary&gt;q</attribute>
        </item>
      </section>
    </submenu>
    <submenu>
      <attribute name="label">Stretch</attribute>
      <section>
        <item>
          <attribute name="label">Black point</attribute>
          <attribute name="action">app.blackpoint</attribute>
        </item>
      </section>
      <section>
        <item>
          <attribute name="label">Arcsinh stretch</attribute>
          <attribute name="action">app.asinhstretch</attribute>
        </item>
        <item>
          <attribute name="label">Generalized hyperbolic stretch</attribute>
          <attribute name="action">app.GHstretch</attribute>
        </item>
        <item>
          <attribute name="label">Midtone stretch</attribute>
          <attribute name="action">app.MTstretch</attribute>
        </item>
      </section>
      <section>
        <item>
          <attribute name="label">CLAHE</attribute>
          <attribute name="action">app.CLAHE</attribute>
        </item>
      </section>
    </submenu>
    <submenu>
      <attribute name="label">Colors</attribute>
      <section>
        <item>
          <attribute name="label">Color balance</attribute>
          <attribute name="action">app.colorbalance</attribute>
        </item>
        <item>
          <attribute name="label">Color saturation</attribute>
          <attribute name="action">app.colorsaturation</attribute>
        </item>
        <item>
          <attribute name="label">Color saturation hyperbolic stretch</attribute>
          <attribute name="action">app.GHScolorsat</attribute>
        </item>
        <item>
          <attribute name="label">Color noise reduction</attribute>
          <attribute name="action">app.colornoise</attribute>
        </item>
      </section>
      <section>
        <item>
          <attribute name="label">Negative</attribute>
          <attribute name="action">app.negative</attribute>
        </item>
        <item>
          <attribute name="label">Convert to gray scale</attribute>
          <attribute name="action">app.grayscale</attribute>
        </item>
      </section>
      <section>
        <item>
          <attribute name="label">Convert from lRGB to sRGB</attribute>
          <attribute name="action">app.lRGBtosRGB</attribute>
        </item>
      </section>
    </submenu>
    <submenu>
      <attribute name="label">Filters</attribute>
      <section>
        <item>
          <attribute name="label">Remove hot pixels</attribute>
          <attribute name="action">app.hotpixels</attribute>
        </item>
      </section>
      <section>
        <item>
          <attribute name="label">Gaussian filter</attribute>
          <attribute name="action">app.gaussian</attribute>
        </item>
        <item>
          <attribute name="label">Butterworth filter</attribute>
          <attribute name="action">app.butterworth</attribute>
        </item>
        <item>
          <attribute name="label">Wavelets filter</attribute>
          <attribute name="action">app.wavelets</attribute>
        </item>
        <item>
          <attribute name="label">Non-local means filter</attribute>
          <attribute name="action">app.nlmeans</attribute>
        </item>
        <item>
          <attribute name="label">Bilateral filter</attribute>
          <attribute name="action">app.bilateral</attribute>
        </item>
        <item>
          <attribute name="label">Total variation filter</attribute>
          <attribute name="action">app.totalvariation</attribute>
        </item>
      </section>
      <section>
        <item>
          <attribute name="label">Sharpen (Laplacian)</attribute>
          <attribute name="action">app.sharpen</attribute>
        </item>
        <item>
          <attribute name="label">Unsharp mask</attribute>
          <attribute name="action">app.unsharp</attribute>
        </item>
      </section>
    </submenu>
    <submenu>
      <attribute name="label">Masks</attribute>
      <section>
        <item>
          <attribute name="label">Threshold mask</attribute>
          <attribute name="action">app.thresholdmask</attribute>
        </item>
      </section>
    </submenu>
    <submenu>
      <attribute name="label">Operations</attribute>
      <section>
        <item>
          <attribute name="label">Blend</attribute>
          <attribute name="action">app.blend</attribute>
        </item>
      </section>
      <section>
        <item>
          <attribute name="label">Resample</attribute>
          <attribute name="action">app.resample</attribute>
        </item>
      </section>
      <section>
        <item>
          <attribute name="label">Pixel math</attribute>
          <attribute name="action">app.pixelmath</attribute>
        </item>
      </section>
      <section>
        <item>
          <attribute name="label">Edit with GIMP</attribute>
          <attribute name="action">app.gimp</attribute>
        </item>
      </section>
    </submenu>
    <submenu>
      <attribute name="label">Frames</attribute>
      <section>
        <item>
          <attribute name="label">Remove frame</attribute>
          <attribute name="action">app.removeframe</attribute>
        </item>
        <item>
          <attribute name="label">Restore frame</attribute>
          <attribute name="action">app.restoreframe</attribute>
        </item>
      </section>
      <section>
        <item>
          <attribute name="label">Add frame</attribute>
          <attribute name="action">app.addframe</attribute>
        </item>
      </section>
    </submenu>
    <submenu>
      <attribute name="label">Logs</attribute>
      <section>
        <item>
          <attribute name="label">Undo last operation</attribute>
          <attribute name="action">app.undo</attribute>
          <attribute name="accel">&lt;Primary&gt;z</attribute>
        </item>
        <item>
          <attribute name="label">Redo last operation</attribute>
          <attribute name="action">app.redo</attribute>
          <attribute name="accel">&lt;Primary&gt;r</attribute>
        </item>
      </section>
      <section>
        <item>
          <attribute name="label">Switch to an other image</attribute>
          <attribute name="action">app.switch</attribute>
        </item>
      </section>
      <section>
        <item>
          <attribute name="label">View logs</attribute>
          <attribute name="action">app.viewlogs</attribute>
          <attribute name="accel">&lt;Primary&gt;l</attribute>
        </item>
      </section>
    </submenu>
  </menu>
  <menu id="MainWindowContextMenu">
    <item>
      <attribute name="label">Statistics</attribute>
      <attribute name="action">app.statistics</attribute>
    </item>
    <item>
      <attribute name="label">Light curve</attribute>
      <attribute name="action">app.lightcurve</attribute>
    </item>
  </menu>
</interface>
"""

builder = Gtk.Builder.new_from_string(XMLMENUS, -1)

class Actions:
  """Menu actions class."""

  def __init__(self, app):
    """Set-up menu actions for application 'app'.
       All actions are attached to app for simplicity."""

    def add_action(name, callback, context = {}):
      """Add action with name 'name', callback 'callback', and context modifiers 'context'
         (with respect to the default context {"noimage": False, "activetool": False, "nocancelled": True})."""
      action = Gio.SimpleAction.new(name, None)
      action.connect("activate", callback)
      app.add_action(action)
      actioncontext = {"noimage": False, "activetool": False, "nocancelled": True}
      actioncontext.update(context)
      self.actions.append((action, actioncontext))

    self.app = app
    self.actions = []
    #
    ######################
    # Main menu actions. #
    ######################
    #
    ### File.
    #
    add_action("open", self.load_file, {"noimage": True})
    add_action("save", self.save_file)
    add_action("close", self.close)
    #
    add_action("settings", lambda action, parameter: SettingsWindow(app).open(), {"noimage": True})
    #
    add_action("quit", lambda action, parameter: app.mainwindow.close(), {"noimage": True, "activetool": True})
    #
    ### Stretch.
    #
    add_action("blackpoint", lambda action, parameter: app.run_tool(BlackPointTool, app.stretchotf))
    #
    add_action("asinhstretch", lambda action, parameter: app.run_tool(ArcsinhStretchTool, app.stretchotf))
    add_action("GHstretch", lambda action, parameter: app.run_tool(GeneralizedHyperbolicStretchTool, app.stretchotf))
    add_action("MTstretch", lambda action, parameter: app.run_tool(MidtoneStretchTool, app.stretchotf))
    #
    add_action("CLAHE", lambda action, parameter: app.run_tool(CLAHETool))
    #
    ### Colors.
    #
    add_action("colorbalance", lambda action, parameter: app.run_tool(ColorBalanceTool, app.colorotf))
    add_action("colorsaturation", lambda action, parameter: app.run_tool(ColorSaturationTool, app.colorotf))
    add_action("GHScolorsat", lambda action, parameter: app.run_tool(GHSColorSaturationTool, app.stretchotf))
    add_action("colornoise", lambda action, parameter: app.run_tool(ColorNoiseReductionTool, app.colorotf))
    #
    add_action("negative", lambda action, parameter: app.negative())
    add_action("grayscale", lambda action, parameter: app.run_tool(GrayScaleConversionTool, app.colorotf))
    #
    add_action("lRGBtosRGB", lambda action, parameter: app.lrgb_to_srgb())
    #
    ### Filters.
    #
    add_action("hotpixels", lambda action, parameter: app.run_tool(RemoveHotPixelsTool, app.hotpixelsotf))
    #
    add_action("gaussian", lambda action, parameter: app.run_tool(GaussianFilterTool))
    add_action("butterworth", lambda action, parameter: app.run_tool(ButterworthFilterTool))
    add_action("wavelets", lambda action, parameter: app.run_tool(WaveletsFilterTool))
    add_action("bilateral", lambda action, parameter: app.run_tool(BilateralFilterTool))
    add_action("nlmeans", lambda action, parameter: app.run_tool(NonLocalMeansFilterTool))
    add_action("totalvariation", lambda action, parameter: app.run_tool(TotalVariationFilterTool))
    #
    add_action("sharpen", lambda action, parameter: app.sharpen())
    add_action("unsharp", lambda action, parameter: app.run_tool(UnsharpMaskTool))
    #
    ### Masks.
    #
    add_action("thresholdmask", lambda action, parameter: app.run_tool(ThresholdMaskTool))
    #
    ### Operations.
    #
    add_action("blend", lambda action, parameter: app.run_tool(BlendTool, app.blendotf))
    #
    add_action("resample", lambda action, parameter: app.run_tool(ResampleTool))
    #
    add_action("pixelmath", lambda action, parameter: app.run_tool(PixelMathTool))
    #
    add_action("gimp", lambda action, parameter: self.edit_with_gimp())
    #
    ### Frames.
    #
    add_action("removeframe", lambda action, parameter: app.remove_unistellar_frame())
    add_action("restoreframe", lambda action, parameter: app.restore_unistellar_frame())
    #
    add_action("addframe", lambda action, parameter: app.run_tool(AddUnistellarFrame))
    #
    ### Logs.
    #
    add_action("undo", lambda action, parameter: app.undo())
    add_action("redo", lambda action, parameter: app.redo(), {"noimage": True, "nocancelled": False})
    #
    add_action("switch", lambda action, parameter: app.run_tool(SwitchTool))
    #
    add_action("viewlogs", lambda action, parameter: app.logwindow.open(), {"activetool": True})
    #
    #####################################
    # Main window context menu actions. #
    #####################################
    #
    add_action("statistics", lambda action, parameter: app.mainwindow.show_statistics(), {"noimage": True, "activetool": True})
    add_action("lightcurve", lambda action, parameter: app.mainwindow.show_lightcurve(), {"activetool": True})
    #
    ###
    #
    self.update()

  def update(self):
    """Update menu actions according to the application context."""
    context = self.app.get_context()
    for action, enable in self.actions:
      if not context["image"]:
        enabled = enable["noimage"]
      elif context["activetool"]:
        enabled = enable["activetool"]
      else:
        enabled = True
      if not context["cancelled"]:
        enabled = enabled and enable["nocancelled"]
      action.set_enabled(enabled)

  def load_file(self, *args, **kwargs):
    """Open file dialog and load image file."""
    filename = ImageFileChooserDialog(self.app.mainwindow.window, Gtk.FileChooserAction.OPEN, preview = True)
    if filename is None: return
    try:
      self.app.load_file(filename)
    except Exception as err:
      ErrorDialog(self.app.mainwindow.window, str(err))

  def save_file(self, *args, **kwargs):
    """Open file dialog and save image file."""
    if not self.app.get_context("image"): return
    # Add extra widget to choose the color depth of png and tiff files.
    depthbutton = CheckButton(label = "16 bits color depth (for png and tiff files)")
    filename = ImageFileChooserDialog(self.app.mainwindow.window, Gtk.FileChooserAction.SAVE, path = self.app.get_savename(), extra_widget = depthbutton)
    if filename is None: return
    try:
      self.app.save_file(filename, depth = 16 if depthbutton.get_active() else 8)
    except Exception as err:
      ErrorDialog(self.app.mainwindow.window, str(err))

  def close(self, *args, **kwargs):
    """Close current image."""
    if not self.app.get_context("image"): return
    dialog = Gtk.MessageDialog(transient_for = self.app.mainwindow.window,
                               message_type = Gtk.MessageType.QUESTION,
                               buttons = Gtk.ButtonsType.OK_CANCEL,
                               modal = True)
    dialog.set_markup("Are you sure you want to close this image ?")
    response = dialog.run()
    dialog.destroy()
    if response != Gtk.ResponseType.OK: return True
    self.app.clear()

  def edit_with_gimp(self, *args, **kwargs):
    """Edit image with GIMP."""

    def run(window, depth):
      """Run GIMP in a separate thread."""

      def finalize(image, msg = None, error = False):
        """Finalize run (register image 'image', close window and open info/error dialog with message 'msg')."""
        if image is not None:
          comment = window.comment.get_text().strip()
          if len(comment) > 0: comment = " # "+comment
          self.app.finalize_tool(image, "Edit('GIMP')"+comment)
        close(window)
        if msg is not None:
          Dialog = ErrorDialog if error else InfoDialog
          Dialog(self.app.mainwindow.window, str(msg))
        return False

      try:
        with tempfile.TemporaryDirectory() as tmpdir:
          tmpfile = os.path.join(tmpdir, "eQuimage.tiff")
          # Save image.
          image = self.app.get_image()
          image.save(tmpfile, depth = depth)
          ctime = os.path.getmtime(tmpfile)
          # Run GIMP.
          print("Editing with GIMP...")
          subprocess.run(["gimp", "-n", tmpfile])
          if window.opened: # Cancel operation if the window has been closed in the meantime.
            # Check if the image has been modified by GIMP.
            mtime = os.path.getmtime(tmpfile)
            if mtime != ctime: # If so, load and register the new one...
              print(f"The file {tmpfile} has been modified by GIMP; Reloading in eQuimage...")
              image = self.app.ImageClass()
              image.load(tmpfile)
              if not image.is_valid(): raise RuntimeError("The image returned by GIMP is invalid.")
              GObject.idle_add(finalize, image, None, False)
            else: # Otherwise, open info dialog and cancel operation.
              print(f"The file {tmpfile} has not been modified by GIMP; Cancelling operation...")
              GObject.idle_add(finalize, None, "The image has not been modified by GIMP.\nCancelling operation.", False)
      except Exception as err:
        GObject.idle_add(finalize, None, err, True)

    def edit(window):
      """Start GIMP thread."""
      window.editbutton.set_sensitive(False) # Can only be run once.
      thread = threading.Thread(target = run, args = (window, window.depthbuttons.get_selected()), daemon = False)
      thread.start()

    def close(window, *args, **kwargs):
      """Close tool window."""
      window.destroy()
      window.opened = False

    if not self.app.get_context("image"): return
    window = Gtk.Window(title = "Edit with GIMP",
                        transient_for = self.app.mainwindow.window,
                        modal = True,
                        border_width = 16)
    window.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
    window.opened = True # Embed all data in the window object here.
    window.connect("delete-event", close)
    wbox = VBox()
    window.add(wbox)
    wbox.pack(Label("The image will be saved as a TIFF file with color depth:"))
    window.depthbuttons = RadioButtons((8, "8 bits"), (16, "16 bits"), (32, "32 bits"))
    window.depthbuttons.set_selected(32)
    wbox.pack(window.depthbuttons.hbox(append = " per channel."))
    wbox.pack(Label("and edited with GIMP."))
    wbox.pack(Label("Export under the same name when leaving GIMP."))
    wbox.pack(Label("You can enter a comment for the logs below, <b>before</b> closing GIMP:"))
    window.comment = Entry(text = "", width = 64)
    wbox.pack(window.comment.hbox())
    wbox.pack(Label("<b>The operation will be cancelled if you close this window !</b>"))
    hbox = HButtonBox()
    wbox.pack(hbox)
    window.editbutton = Button(label = "Edit")
    window.editbutton.connect("clicked", lambda button: edit(window)) # Is direct reference to window safe here ?
    hbox.pack(window.editbutton)
    window.cancelbutton = Button(label = "Cancel")
    window.cancelbutton.connect("clicked", lambda button: close(window)) # Is direct reference to window safe here ?
    hbox.pack(window.cancelbutton)
    window.show_all()
