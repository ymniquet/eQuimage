# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
# Author: Yann-Michel Niquet (contact@ymniquet.fr).
# Version: 3.0.0 / 2026.03.10
# Doc OK.

"""Interface with scikit-image."""

import numpy as np
import skimage as skim

#####################################
# For inclusion in the Image class. #
#####################################

class MixinImage:
  """To be included in the Image class."""

  ###########
  # Filter. #
  ###########

  def gaussian_filter(self, sigma, mode = "reflect", channels = ""):
    """Convolve (blur) selected channels of the image with a gaussian.

    Args:
      sigma (float): The standard deviation of the gaussian (pixels).
      mode (str, optional): How to extend the image across its boundaries:

        - "reflect" (default): the image is reflected about the edge of the last pixel (abcd → dcba|abcd|dcba).
        - "mirror": the image is reflected about the center of the last pixel (abcd → dcb|abcd|cba).
        - "nearest": the image is padded with the value of the last pixel (abcd → aaaa|abcd|dddd).
        - "zero": the image is padded with zeros (abcd → 0000|abcd|0000).

      channels (str, optional): The selected channels (default "" = all channels).
        See :meth:`Image.apply_channels() <.apply_channels>` or https://astro.ymniquet.fr/codes/equimagelab/docs/channels.html.

    Returns:
      Image: The processed image.

    See also:
      :func:`skimage.filters.gaussian`
    """
    if mode == "zero": mode = "constant" # Translate modes.
    return self.apply_channels(lambda channel: skim.filters.gaussian(channel, channel_axis = 0, sigma = sigma, mode = mode, cval = 0.), channels)

  def butterworth_filter(self, cutoff, order = 2, padding = 0, channels = ""):
    """Apply a Butterworth low-pass filter to selected channels of the image.

    The Butterworh filter reads in the frequency domain:

    .. math::
      H(f) = 1/(1+(f/f_c)^{2n})

    where :math:`n` is the order of the filter and :math:`f_c` is the cut-off frequency.
    The data are Fast-Fourier Transformed back and forth to apply the filter.

    Args:
      cutoff (float): The normalized cutoff frequency in [0, 1]. Namely, fc = (1-cutoff)fs/2 with fs
        the FFT sampling frequency.
      order (int, optional): The order of the filter (default 2).
      padding (int, optional): Number of pixels to pad the image with (default 0; increase if the
        filter leaves visible artifacts on the edges).
      channels (str, optional): The selected channels (default "" = all channels).
        See :meth:`Image.apply_channels() <.apply_channels>` or https://astro.ymniquet.fr/codes/equimagelab/docs/channels.html.

    Returns:
      Image: The processed image.

    See also:
      :func:`skimage.filters.butterworth`
    """
    return self.apply_channels(lambda channel: skim.filters.butterworth(channel, channel_axis = 0, cutoff_frequency_ratio = (1.-cutoff)/2.,
                               order = order, npad = padding, squared_butterworth = True), channels)

  def unsharp_mask(self, sigma, strength, channels = ""):
    r"""Apply an unsharp mask to selected channels of the image.

    Given a channel :math:`C_{in}`, returns

    .. math::
      C_{out} = C_{in}+\mathrm{strength}[C_{in}-\mathrm{BLUR}(C_{in})]

    where BLUR(:math:`C_{in}`) is the convolution of :math:`C_{in}` with a gaussian of standard
    deviation sigma. As BLUR(:math:`C_{in}`) is a low-pass filter, :math:`C_{in}`-BLUR(:math:`C_{in}`)
    is a high-pass filter whose output is admixed in the original image. This enhances details; the
    larger the mixing strength, the sharper the image, at the expense of noise and fidelity.

    Args:
      sigma (float): The standard deviation of the gaussian (pixels).
      strength (float): The mixing strength.
      channels (str, optional): The selected channels (default "" = all channels).
        See :meth:`Image.apply_channels() <.apply_channels>` or https://astro.ymniquet.fr/codes/equimagelab/docs/channels.html.

    Returns:
      Image: The processed image.

    See also:
      :func:`skimage.filters.unsharp_mask`
    """
    return self.apply_channels(lambda channel: skim.filters.unsharp_mask(channel, channel_axis = 0, radius = radius, amount = strength), channels)

  ############
  # Denoise. #
  ############

  def estimate_noise(self):
    """Estimate the rms noise of the image, averaged over all channels.

    Returns:
      float: The rms noise of the image, averaged over the channels.

    See also:
      :func:`skimage.restoration.estimate_sigma`

    To do:
      Estimate the noise in arbitrary channels.
    """
    return skim.restoration.estimate_sigma(self.image, channel_axis = 0, average_sigmas = True)

  def wavelets_filter(self, sigma, wavelet = "coif4", mode = "soft", method = "BayesShrink", shifts = 0, channels = "L"):
    """Wavelets filter for denoising selected channels of the image.

    Performs a wavelets transform on the selected channels and filters the wavelets to reduce noise.

    Args:
      sigma (float): The estimated noise standard deviation used to compute the wavelets filter
        threshold. The larger sigma, the smoother the output image.
      wavelet (str, optional): The wavelets used to decompose the image (default "coif4").
        Can be any of the orthogonal wavelets of `pywavelets.wavelist`. Recommended wavelets are:

          - Daubechies wavelets ("db1"..."db8"),
          - Symlets ("sym2"..."sym8"),
          - Coiflets ("coif1"..."coif8").

      mode (str, optional): Denoising method [either "soft" (default) or "hard"].
      method (str, optional): Thresholding method [either "BayesShrink" (default) or "VisuShrink"].
        Separate thresholds are applied to the wavelets bands for "BayesShrink", whereas a single
        threshold is applied for "VisuShrink" (best in principle for Gaussian noise, but may appear
        overly smooth).
      shifts (int, optional): Number of spin cycles (default 0). The wavelets transform is not
        shift-invariant. To mimic a shift-invariant transform as best as possible, the output image
        is an average of the original image shifted shifts times in each direction, filtered, then
        shifted back to the original position.
      channels (str, optional): The selected channels (default "L" = luma).
        See :meth:`Image.apply_channels() <.apply_channels>` or https://astro.ymniquet.fr/codes/equimagelab/docs/channels.html.

    Returns:
      Image: The processed image.

    See also:
      :func:`skimage.restoration.denoise_wavelet`,
      :func:`skimage.restoration.cycle_spin`
    """
    kwargs = dict(channel_axis = -1, sigma = sigma, wavelet = wavelet, wavelet_levels = None, mode = mode,
                  method = method, convert2ycbcr = False, rescale_sigma = True)
    return self.apply_channels(lambda channel: skim.restoration.cycle_spin(channel, channel_axis = 0, max_shifts = shifts,
                               func = skim.restoration.denoise_wavelet, func_kw = kwargs, num_workers = None), channels)

  def bilateral_filter(self, sigma_space, sigma_color = .1, mode = "reflect", channels = ""):
    r"""Bilateral filter for denoising selected channels of the image.

    The bilateral filter convolves the selected channel(s) :math:`C_{in}` with a gaussian :math:`g_s`
    of standard deviation sigma_space weighted by a gaussian :math:`g_c` in color space (with standard
    deviation sigma_color):

    .. math::
      C_{out}(\mathbf{r}) \propto \sum_{\mathbf{r}'} C_{in}(\mathbf{r}') g_s(|\mathbf{r}-\mathbf{r}'|) g_c(|C_{in}(\mathbf{r})-C_{in}(\mathbf{r}')|)

    Therefore, the bilateral filter averages the neighboring pixels whose colors are sufficiently similar.
    The bilateral filter may tend to produce cartoon-like (piecewise-constant) images.

    Args:
      sigma_space (float): The standard deviation of the gaussian in real space (pixels).
      sigma_color (float, optional): The standard deviation of the gaussian in color space (default 0.1).
      mode (str, optional): How to extend the image across its boundaries:

        - "reflect" (default): the image is reflected about the edge of the last pixel (abcd → dcba|abcd|dcba).
        - "mirror": the image is reflected about the center of the last pixel (abcd → dcb|abcd|cba).
        - "nearest": the image is padded with the value of the last pixel (abcd → aaaa|abcd|dddd).
        - "zero": the image is padded with zeros (abcd → 0000|abcd|0000).

      channels (str, optional): The selected channels (default "" = all channels).
        See :meth:`Image.apply_channels() <.apply_channels>` or https://astro.ymniquet.fr/codes/equimagelab/docs/channels.html.

    Returns:
      Image: The processed image.

    See also:
      :func:`skimage.restoration.denoise_bilateral`
    """
    if mode == "mirror": # Translate modes.
      mode = "symmetric"
    elif mode == "nearest":
      mode = "edge"
    elif mode == "zero":
      mode = "constant"
    return self.apply_channels(lambda channel: skim.restoration.denoise_bilateral(channel, channel_axis = 0, sigma_spatial = sigma_space,
                               sigma_color = sigma_color, mode = mode, cval = 0.), channels)

  def total_variation(self, weight = .1, algorithm = "Chambolle", channels = ""):
    r"""Total variation denoising of selected channels of the image.

    Given a noisy channel :math:`C_{in}`, the total variation filter finds an image :math:`C_{out}`
    with less total variation than :math:`C_{in}` under the constraint that :math:`C_{out}` remains
    similar to :math:`C_{in}`. This can be expressed as the Rudin–Osher–Fatemi (ROF) minimization
    problem:

    .. math::
      \text{Minimize} \sum_{\mathbf{r}} |\nabla C_{out}(\mathbf{r})| + (\lambda/2)[C_{out}(\mathbf{r})-C_{in}(\mathbf{r})]^2

    where the weight :math:`1/\lambda` controls denoising (the larger the weight, the stronger the
    denoising at the expense of image fidelity). The minimization can either be performed with the
    Chambolle or split Bregman algorithm. Total variation denoising tends to produce cartoon-like
    (piecewise-constant) images.

    Args:
      weight (float, optional): The weight 1/lambda (default 0.1).
      algorithm (str, optional): Either "Chambolle" (default) for the Chambolle algorithm
                                 or "Bregman" for the split Bregman algorithm.
      channels (str, optional): The selected channels (default "" = all channels).
        See :meth:`Image.apply_channels() <.apply_channels>` or https://astro.ymniquet.fr/codes/equimagelab/docs/channels.html.

    Returns:
      Image: The processed image.

    See also:
      :func:`skimage.restoration.denoise_tv_chambolle`,
      :func:`skimage.restoration.denoise_tv_bregman`
    """
    if algorithm == "Chambolle":
      return self.apply_channels(lambda channel: skim.restoration.denoise_tv_chambolle(channel, channel_axis = 0, weight = weight), channels)
    elif algorithm == "Bregman":
      return self.apply_channels(lambda channel: skim.restoration.denoise_tv_bregman(channel, channel_axis = 0, weight = 1./(2.*weight)), channels)
    else:
      raise ValueError(f"Error, unknown algorithm '{algorithm}' (must be 'Chambolle' or 'Bregman').")

  def non_local_means(self, size = 7, dist = 11, h = .01, sigma = 0., fast = True, channels = ""):
    r"""Non-local means filter for denoising selected channels of the image.

    Given a channel :math:`C_{in}`, returns

    .. math::
      C_{out}(\mathbf{r}) \propto \sum_{\mathbf{r}'} f(\mathbf{r},\mathbf{r}') C_{in}(\mathbf{r}')

    where:

    .. math::
      f(\mathbf{r},\mathbf{r}') = \exp[-(M(\mathbf{r})-M(\mathbf{r}'))^2/h^2]\text{ for }|\mathbf{r}-\mathbf{r}'| < d

    and :math:`M(\mathbf{r})` is an average of :math:`C_{in}` in a patch around :math:`\mathbf{r}`.
    Therefore, the non-local means filter averages the neighboring pixels whose patches (texture) are
    sufficiently similar. The non-local means filter can restore textures that would be blurred by
    other denoising algorithms such as the bilateral and total variation filters.

    Args:
      size (int, optional): The size of the (square) patch used to compute M(r) (default 7).
      dist (int, optional): The maximal distance d between the patches (default 11).
      h (float, optional): The cut-off in gray levels (default 0.01; the filter is applied to all
        channels independently).
      sigma (float, optional): The standard deviation of the noise (if known), subtracted out when
        computing f(r, r'). This can lead to a modest improvement in image quality (keep default 0
        if unknown).
      fast (bool, optional): If true (default), the pixels within the patch are averaged uniformly.
        If false, they are weighted by a gaussian (better yet slower).
      channels (str, optional): The selected channels (default "" = all channels).
        See :meth:`Image.apply_channels() <.apply_channels>` or https://astro.ymniquet.fr/codes/equimagelab/docs/channels.html.

    Returns:
      Image: The processed image.

    See also:
      :func:`skimage.restoration.denoise_nl_means`
    """
    return self.apply_channels(lambda channel: skim.restoration.denoise_nl_means(channel, channel_axis = 0, patch_size = size,
                               patch_distance = dist, h = h, sigma = sigma, fast_mode = fast), channels)

  #############
  # Contrast. #
  #############

  def CLAHE(self, size = None, clip = .01, nbins = 256, channels = ""):
    """Contrast Limited Adaptive Histogram Equalization (CLAHE) of selected channels of the image.

    See https://en.wikipedia.org/wiki/Adaptive_histogram_equalization.

    Args:
      size (int, optional): The size of the tiles (in pixels) used to sample local histograms, given
        as a single integer or as pair of integers (width, height of the tiles). If None (default),
        the tile size defaults to 1/8 of the image width and height.
      clip (float, optional): The clip limit used to control contrast enhancement (default 0.01).
      nbins (int, optional): The number of bins in the local histograms (default 256).
      channels (str, optional): The selected channels (default "" = all channels).
        See :meth:`Image.apply_channels() <.apply_channels>` or https://astro.ymniquet.fr/codes/equimagelab/docs/channels.html.
        CLAHE works best for the "V", "L" and "L*" channels.

    Returns:
      Image: The processed image.

    See also:
      :func:`skimage.exposure.equalize_adapthist`
    """
    clipped = self.clip_channels(channels) # Clip relevant channels before CLAHE to avoid artifacts.
    return clipped.apply_channels(lambda channel: skim.exposure.equalize_adapthist(channel, kernel_size = size, clip_limit = clip, nbins = nbins),
                                  channels, multi = False)
