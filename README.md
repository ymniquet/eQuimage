eQuimage is a python tool to postprocess astronomical images from Unistellar telescopes.
Author: Yann-Michel Niquet.

eQuimage requires GTK3, available in all Linux distributions; on Windows, follow https://www.gtk.org/docs/installations/windows/ to install GTK3.

This code has no claim and only offers elementary operations available in many other more advanced softwares (GIMP, PixInsight, etc...). Its main advantages are to highlight the pixels "blackened" or saturated by the treatments (in each R/G/B channel), and to leave the frame of the Unistellar images unprocessed (option only implemented to date for the eQuinox 1 telescope, but feel free to contribute or send me sample images from other telescopes !).

There is no documentation yet, but you should find your way around easily if you have used image processing software before. The python code itself is documented in English.

For more information, see https://astro.ymniquet.fr/eQuimage.

KNOWN BUGS:
  - On windows, the main window (displaying the image) does not always refresh after an operation. Moving the cursor around usually triggers an update.