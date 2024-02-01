# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 1.3.0 / 2024.01.29

"""Main menu."""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio
from .gtk.customwidgets import CheckButton
from .gtk.filechoosers import ImageChooserDialog
from .base import ErrorDialog
from .settings import SettingsWindow
from .arcsinh import ArcsinhStretchTool
from .hyperbolic import GeneralizedHyperbolicStretchTool
from .midtone import MidtoneStretchTool
from .colorbalance import ColorBalanceTool
from .colorsaturation import ColorSaturationTool
from .ghscolorsat import GHSColorSaturationTool
from .colornoise import ColorNoiseReductionTool
from .hotpixels import RemoveHotPixelsTool
from .wavelets import WaveletsFilterTool
from .blend import BlendTool
from .addframe import AddUnistellarFrame

class MainMenu:
  """Main menu class."""

  __XMLMENU__ = """
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
          <attribute name="label">Arcsinh stretch</attribute>
          <attribute name="action">app.arcsinhstretch</attribute>
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
    </submenu>
    <submenu>
      <attribute name="label">Filters</attribute>
      <section>
        <item>
          <attribute name="label">Remove hot pixels</attribute>
          <attribute name="action">app.hotpixels</attribute>
        </item>
        <item>
          <attribute name="label">Sharpen</attribute>
          <attribute name="action">app.sharpen</attribute>
        </item>
        <item>
          <attribute name="label">Wavelets filter</attribute>
          <attribute name="action">app.wavelets</attribute>
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
          <attribute name="label">Cancel last operation</attribute>
          <attribute name="action">app.cancel</attribute>
          <attribute name="accel">&lt;Primary&gt;z</attribute>
        </item>
        <item>
          <attribute name="label">Redo last cancelled operation</attribute>
          <attribute name="action">app.redo</attribute>
          <attribute name="accel">&lt;Primary&gt;r</attribute>
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
</interface>
"""

  def __init__(self, app):
    """Build the main menu for app 'app'."""
    self.app = app
    self.actions = []
    #
    ### File.
    #
    action = Gio.SimpleAction.new("open", None)
    action.connect("activate", self.load_file)
    app.add_action(action)
    self.actions.append((action, {"noimage": True, "nooperations": True, "activetool": False, "noframe": True, "nocancelled": True}))
    #
    action = Gio.SimpleAction.new("save", None)
    action.connect("activate", self.save_file)
    app.add_action(action)
    self.actions.append((action, {"noimage": False, "nooperations": False, "activetool": False, "noframe": True, "nocancelled": True}))
    #
    action = Gio.SimpleAction.new("close", None)
    action.connect("activate", self.close)
    app.add_action(action)
    self.actions.append((action, {"noimage": False, "nooperations": True, "activetool": False, "noframe": True, "nocancelled": True}))
    #
    action = Gio.SimpleAction.new("settings", None)
    action.connect("activate", lambda action, parameter: SettingsWindow(app).open())
    app.add_action(action)
    self.actions.append((action, {"noimage": True, "nooperations": True, "activetool": False, "noframe": True, "nocancelled": True}))
    #
    action = Gio.SimpleAction.new("quit", None)
    action.connect("activate", lambda action, parameter: app.mainwindow.close())
    app.add_action(action)
    self.actions.append((action, {"noimage": True, "nooperations": True, "activetool": True, "noframe": True, "nocancelled": True}))
    #
    ### Stretch.
    #
    action = Gio.SimpleAction.new("arcsinhstretch", None)
    action.connect("activate", lambda action, parameter: app.run_tool(ArcsinhStretchTool, app.stretchotf))
    app.add_action(action)
    self.actions.append((action, {"noimage": False, "nooperations": True, "activetool": False, "noframe": True, "nocancelled": True}))
    #
    action = Gio.SimpleAction.new("GHstretch", None)
    action.connect("activate", lambda action, parameter: app.run_tool(GeneralizedHyperbolicStretchTool, app.stretchotf))
    app.add_action(action)
    self.actions.append((action, {"noimage": False, "nooperations": True, "activetool": False, "noframe": True, "nocancelled": True}))
    #
    action = Gio.SimpleAction.new("MTstretch", None)
    action.connect("activate", lambda action, parameter: app.run_tool(MidtoneStretchTool, app.stretchotf))
    app.add_action(action)
    self.actions.append((action, {"noimage": False, "nooperations": True, "activetool": False, "noframe": True, "nocancelled": True}))
    #
    ### Colors.
    #
    action = Gio.SimpleAction.new("colorbalance", None)
    action.connect("activate", lambda action, parameter: app.run_tool(ColorBalanceTool, app.colorotf))
    app.add_action(action)
    self.actions.append((action, {"noimage": False, "nooperations": True, "activetool": False, "noframe": True, "nocancelled": True}))
    #
    action = Gio.SimpleAction.new("colorsaturation", None)
    action.connect("activate", lambda action, parameter: app.run_tool(ColorSaturationTool, app.colorotf))
    app.add_action(action)
    self.actions.append((action, {"noimage": False, "nooperations": True, "activetool": False, "noframe": True, "nocancelled": True}))
    #
    action = Gio.SimpleAction.new("GHScolorsat", None)
    action.connect("activate", lambda action, parameter: app.run_tool(GHSColorSaturationTool, app.stretchotf))
    app.add_action(action)
    self.actions.append((action, {"noimage": False, "nooperations": True, "activetool": False, "noframe": True, "nocancelled": True}))
    #
    action = Gio.SimpleAction.new("colornoise", None)
    action.connect("activate", lambda action, parameter: app.run_tool(ColorNoiseReductionTool, app.colorotf))
    app.add_action(action)
    self.actions.append((action, {"noimage": False, "nooperations": True, "activetool": False, "noframe": True, "nocancelled": True}))
    #
    action = Gio.SimpleAction.new("negative", None)
    action.connect("activate", lambda action, parameter: app.negative())
    app.add_action(action)
    self.actions.append((action, {"noimage": False, "nooperations": True, "activetool": False, "noframe": True, "nocancelled": True}))
    #
    action = Gio.SimpleAction.new("grayscale", None)
    action.connect("activate", lambda action, parameter: app.gray_scale())
    app.add_action(action)
    self.actions.append((action, {"noimage": False, "nooperations": True, "activetool": False, "noframe": True, "nocancelled": True}))
    #
    ### Filters.
    #
    action = Gio.SimpleAction.new("hotpixels", None)
    action.connect("activate", lambda action, parameter: app.run_tool(RemoveHotPixelsTool, app.hotpixelsotf))
    app.add_action(action)
    self.actions.append((action, {"noimage": False, "nooperations": True, "activetool": False, "noframe": True, "nocancelled": True}))
    #
    action = Gio.SimpleAction.new("sharpen", None)
    action.connect("activate", lambda action, parameter: app.sharpen())
    app.add_action(action)
    self.actions.append((action, {"noimage": False, "nooperations": True, "activetool": False, "noframe": True, "nocancelled": True}))
    #
    action = Gio.SimpleAction.new("wavelets", None)
    action.connect("activate", lambda action, parameter: app.run_tool(WaveletsFilterTool))
    app.add_action(action)
    self.actions.append((action, {"noimage": False, "nooperations": True, "activetool": False, "noframe": True, "nocancelled": True}))
    #
    ### Operations.
    #
    action = Gio.SimpleAction.new("blend", None)
    action.connect("activate", lambda action, parameter: app.run_tool(BlendTool, app.blendotf))
    app.add_action(action)
    self.actions.append((action, {"noimage": False, "nooperations": True, "activetool": False, "noframe": True, "nocancelled": True}))
    #
    ### Frames.
    #
    action = Gio.SimpleAction.new("removeframe", None)
    action.connect("activate", lambda action, parameter: app.remove_unistellar_frame())
    app.add_action(action)
    self.actions.append((action, {"noimage": False, "nooperations": True, "activetool": False, "noframe": False, "nocancelled": True}))
    #
    action = Gio.SimpleAction.new("restoreframe", None)
    action.connect("activate", lambda action, parameter: app.restore_unistellar_frame())
    app.add_action(action)
    self.actions.append((action, {"noimage": False, "nooperations": True, "activetool": False, "noframe": False, "nocancelled": True}))
    #
    action = Gio.SimpleAction.new("addframe", None)
    action.connect("activate", lambda action, parameter: app.run_tool(AddUnistellarFrame))
    app.add_action(action)
    self.actions.append((action, {"noimage": False, "nooperations": True, "activetool": False, "noframe": True, "nocancelled": True}))
    #
    ### Logs.
    #
    action = Gio.SimpleAction.new("cancel", None)
    action.connect("activate", lambda action, parameter: app.cancel_last_operation())
    app.add_action(action)
    self.actions.append((action, {"noimage": False, "nooperations": False, "activetool": False, "noframe": True, "nocancelled": True}))
    #
    action = Gio.SimpleAction.new("redo", None)
    action.connect("activate", lambda action, parameter: app.redo_last_cancelled())
    app.add_action(action)
    self.actions.append((action, {"noimage": True, "nooperations": True, "activetool": False, "noframe": True, "nocancelled": False}))
    #
    action = Gio.SimpleAction.new("viewlogs", None)
    action.connect("activate", lambda action, parameter: app.logwindow.open())
    app.add_action(action)
    self.actions.append((action, {"noimage": False, "nooperations": True, "activetool": True, "noframe": True, "nocancelled": True}))
    #
    ###
    #
    builder = Gtk.Builder.new_from_string(self.__XMLMENU__, -1)
    app.set_menubar(builder.get_object("MainMenu"))
    self.update()

  def update(self, present = True):
    """Update main menu."""
    context = self.app.get_context()
    for action, enable in self.actions:
      if not context["image"]:
        enabled = enable["noimage"]
      elif context["activetool"]:
        enabled = enable["activetool"]
      else:
        enabled = True
      if not context["frame"]:
        enabled = enabled and enable["noframe"]
      if not context["operations"]:
        enabled = enabled and enable["nooperations"]
      if not context["cancelled"]:
        enabled = enabled and enable["nocancelled"]
      action.set_enabled(enabled)

  def load_file(self, *args, **kwargs):
    """Open file dialog and load image file."""
    filename = ImageChooserDialog(self.app.mainwindow.window, Gtk.FileChooserAction.OPEN, preview = True)
    if filename is None: return
    try:
      self.app.load_file(filename)
    except Exception as err:
      ErrorDialog(self.app.mainwindow.window, str(err))

  def save_file(self, *args, **kwargs):
    """Open file dialog and save image file."""
    if not self.app.get_context("image"): return
    # Add extra widget to choose the color depth of png and tiff files.
    #widget = Gtk.HBox(spacing = 8)
    #widget.pack_start(Gtk.Label(label = "Color depth (for png and tiff files):"), False, False, 0)
    #button8 = RadioButton.new_with_label_from_widget(None, "8 bits")
    #widget.pack_start(button8, False, False, 0)
    #button16 = RadioButton.new_with_label_from_widget(button8, "16 bits")
    #widget.pack_start(button16, False, False, 0)
    depthbutton = CheckButton(label = "16 bits color depth (for png and tiff files)")
    #filename = ImageChooserDialog(self.app.mainwindow.window, Gtk.FileChooserAction.SAVE, path = self.app.get_savename(), extra_widget = widget)
    filename = ImageChooserDialog(self.app.mainwindow.window, Gtk.FileChooserAction.SAVE, path = self.app.get_savename(), extra_widget = depthbutton)
    if filename is None: return
    try:
      #self.app.save_file(filename, depth = 8 if button8.get_active() else 16)
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
