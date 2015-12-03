"""
Functions for visualizing flow cytometry data.

"""

import numpy as np
import scipy.ndimage.filters
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.font_manager import FontProperties

# Use default colors from palettable if available
try:
    import palettable
except ImportError, e:
    cmap_default = plt.get_cmap(matplotlib.rcParams['image.cmap'])
else:
    cmap_default = palettable.colorbrewer.diverging.Spectral_8_r.mpl_colormap

savefig_dpi = 250

##############################################################################
# SIMPLE PLOTS
##############################################################################
#
# The following functions produce simple plots independently of any other 
# function.
#
##############################################################################

def hist1d(data_list,
           channel=0,
           log=False,
           div=1,
           bins=None,
           histtype='stepfilled',
           normed=False,
           xlabel=None,
           ylabel=None,
           xlim=None,
           ylim=None,
           title=None,
           legend=False,
           legend_loc='best',
           legend_fontsize='medium',
           legend_labels=None,
           facecolor=None,
           edgecolor=None,
           savefig=None,
           **kwargs):
    """
    Plot one 1D histogram from one or more flow cytometry data sets.

    This function does not create a new figure or axis, so it can be called
    directly to plot in a previously created axis if desired. If `savefig`
    is not specified, the plot is maintained in the current axis when the
    function returns. This allows for further modifications to the axis by
    direct calls to, for example, ``plt.xlabel``, ``plt.title``, etc.
    However, if `savefig` is specified, the figure is closed after being
    saved. In this case, parameters `xlabel`, `ylabel`, `xlim`, `ylim`,
    `title`, and the legend-related parameters of this function are the
    only way to modify the axis.

    Parameters
    ----------
    data_list : FCSData or numpy array or list of FCSData or numpy array
        Flow cytometry data to plot.
    channel : int or str, optional
        Channel from where to take the events to plot. If ndim == 1,
        channel is ignored. String channel specifications are only
        supported for data types which support string-based indexing
        (e.g. FCSData).
    log : bool, optional
        Flag specifying whether the x axis should be in log scale.
    div : int or float, optional
        Downscaling factor for the default number of bins. If `bins` is not
        specified, the default set of bins extracted from
        ``data_list[i].domain`` contains ``n`` bins, and ``div != 1``,
        `hist1d` will actually use ``n/div`` bins, covering the same range
        as ``data_list[i].domain``. `div` is ignored if `bins` is
        specified.
    bins : array_like, optional
        bins argument to pass to plt.hist. If not specified, `hist1d`
        attempts to extract bins from ``data_list[i].domain``.
    histtype : {'bar', 'barstacked', 'step', 'stepfilled'}, str, optional
        Histogram type. Directly passed to ``plt.hist``.
    normed : bool, optional
        Flag indicating whether to normalize the histogram such that the
        area under the curve is equal to one.
    savefig : str, optional
        The name of the file to save the figure to. If None, do not save.

    Other parameters
    ----------------
    xlabel : str, optional
        Label to use on the x axis. If None, attempts to extract channel
        name from last data object.
    ylabel : str, optional
        Label to use on the y axis. If None and ``normed==True``, use
        'Probability'. If None and `normed==False``, use 'Counts'.
    xlim : tuple, optional
        Limits for the x axis. If not specified and `bins` exists, use
        the lowest and highest values of `bins`.
    ylim : tuple, optional
        Limits for the y axis.
    title : str, optional
        Plot title.
    legend : bool, optional
        Flag specifying whether to include a legend. If `legend` is True,
        the legend labels will be taken from `legend_labels` if present,
        else they will be taken from ``str(data_list[i])``.
    legend_loc : str, optional
        Location of the legend.
    legend_fontsize : int or str, optional
        Font size for the legend.
    legend_labels : list, optional
        Labels to use for the legend.
    facecolor : matplotlib color or list of matplotlib colors, optional
        The histogram's facecolor. It can be a list with the same length as
        `data_list`. If `edgecolor` and `facecolor` are not specified, and
        ``histtype == 'stepfilled'``, the facecolor will be taken from the
        module-level variable `cmap_default`.
    edgecolor : matplotlib color or list of matplotlib colors, optional
        The histogram's edgecolor. It can be a list with the same length as
        `data_list`. If `edgecolor` and `facecolor` are not specified, and
        ``histtype == 'step'``, the edgecolor will be taken from the
        module-level variable `cmap_default`.
    kwargs : dict, optional
        Additional parameters passed directly to matploblib's ``hist``.

    Notes
    -----
    `hist1d` calls matplotlib's ``hist`` function for each object in
    `data_list`. `hist_type`, the type of histogram to draw, is directly
    passed to ``plt.hist``. Additional keyword arguments provided to
    `hist1d` are passed directly to ``plt.hist``.

    """
    # Convert to list if necessary
    if not isinstance(data_list, list):
        data_list = [data_list]

    # Default colors
    if histtype == 'stepfilled' and edgecolor is None and facecolor is None:
        facecolor = [cmap_default(i)
                     for i in np.linspace(0, 1, len(data_list))]
    elif histtype == 'step' and edgecolor is None and facecolor is None:
        edgecolor = [cmap_default(i)
                     for i in np.linspace(0, 1, len(data_list))]

    # Convert colors to lists if necessary
    if not isinstance(edgecolor, list):
        edgecolor = [edgecolor]*len(data_list)
    if not isinstance(facecolor, list):
        facecolor = [facecolor]*len(data_list)

    # Iterate through data_list
    for i, data in enumerate(data_list):
        # Extract channel
        if data.ndim > 1:
            y = data[:, channel]
        else:
            y = data
        # If bins are not specified, try to get bins from data object
        if (bins is None and hasattr(y, 'hist_bin_edges')
                and y.hist_bin_edges(0) is not None):
            # Get bin information
            bd = y.hist_bin_edges(0)
            # Get bin scaled indices
            xd = np.linspace(0, 1, len(bd))
            xs = np.linspace(0, 1, (len(bd) - 1)/div + 1)
            # Generate sub-sampled bins
            bins = np.interp(xs, xd, bd)

        # Actually plot
        if bins is not None:
            n, edges, patches = plt.hist(y,
                                         bins,
                                         histtype=histtype,
                                         normed=normed,
                                         edgecolor=edgecolor[i],
                                         facecolor=facecolor[i],
                                         **kwargs)
        else:
            n, edges, patches = plt.hist(y,
                                         histtype=histtype,
                                         normed=normed,
                                         edgecolor=edgecolor[i],
                                         facecolor=facecolor[i],
                                         **kwargs)
        if log == True:
            plt.gca().set_xscale('log')

    ###
    # Final configuration
    ###

    # x and y labels
    if xlabel is not None:
        # Highest priority is user-provided label
        plt.xlabel(xlabel)
    elif hasattr(y, 'channels'):
        # Attempt to use channel name
        plt.xlabel(y.channels[0])

    if ylabel is not None:
        # Highest priority is user-provided label
        plt.ylabel(ylabel)
    elif normed:
        plt.ylabel('Probability')
    else:
        # Default is "Counts"
        plt.ylabel('Counts')

    # x and y limits
    if xlim is not None:
        # Highest priority is user-provided limits
        plt.xlim(xlim)
    elif bins is not None:
        # Use bins if specified
        plt.xlim((edges[0], edges[-1]))

    if ylim is not None:
        plt.ylim(ylim)

    # title and legend
    if title is not None:
        plt.title(title)

    if legend:
        if legend_labels is None:
            legend_labels = [str(data) for data in data_list]
        plt.legend(legend_labels,
                   loc=legend_loc,
                   prop={'size': legend_fontsize})

    # Save if necessary
    if savefig is not None:
        plt.tight_layout()
        plt.savefig(savefig, dpi=savefig_dpi)
        plt.close()

def density2d(data, 
              channels=[0,1],
              log=False,
              div=1,
              bins=None,
              smooth=True,
              sigma=10.0,
              mode='mesh',
              colorbar=False,
              normed=False,
              xlabel=None,
              ylabel=None,
              title=None,
              savefig=None,
              **kwargs):
    """
    Plot a 2D density plot from two channels of a flow cytometry data set.

    `density2d` has two plotting modes which are selected using the `mode`
    argument. With ``mode=='mesh'``, this function plots the data as a true
    2D histogram, in which a plane is divided into bins and the color of
    each bin is directly related to the number of elements therein. With
    ``mode=='scatter'``, this function also calculates a 2D histogram,
    but it plots a 2D scatter plot in which each dot corresponds to a bin,
    colored according to the number elements therein. The most important
    difference is that the ``scatter`` mode does not color regions
    corresponding to empty bins. This allows for easy identification of
    regions with low number of events. For both modes, the calculated
    histogram can be smoothed using a Gaussian kernel by specifying
    ``smooth=True``. The width of the kernel is, in this case, given by
    `sigma`.

    This function does not create a new figure or axis, so it can be called
    directly to plot in a previously created axis if desired. If `savefig`
    is not specified, the plot is maintained in the current axis when the
    function returns. This allows for further modifications to the axis by
    direct calls to, for example, ``plt.xlabel``, ``plt.title``, etc.
    However, if `savefig` is specified, the figure is closed after being
    saved. In this case, parameters `xlabel`, `ylabel`, `xlim`, `ylim`,
    `title`, and the legend-related parameters of this function are the
    only way to modify the axis.

    Parameters
    ----------
    data : FCSData or numpy array
        Flow cytometry data to plot.
    channels : list of int, list of str, optional
        Two channels to use for the plot.
    log : bool, optional
        Flag specifying whether the axes should be in log scale.
    div : int or float, optional
        Downscaling factor for the default number of bins. If `bins` is not
        specified, the default set of bins extracted from `data` contains
        ``n*m`` bins, and ``div != 1``, `density2d` will actually use
        ``n/div * m/div`` bins that cover the same range as the default
        bins. `div` is ignored if `bins` is specified.
    bins : array_like, optional
        bins argument to pass to plt.hist. If not specified, attempts to 
        extract bins from `data`.
    smooth : bool, optional
        Flag indicating whether to apply Gaussian smoothing to the
        histogram.
    mode : {'mesh', 'scatter'}, str, optional
        Plotting mode. 'mesh' produces a 2D-histogram whereas 'scatter'
        produces a scatterplot colored by histogram bin value.
    colorbar : bool, optional
        Flag indicating whether to add a colorbar to the plot.
    normed : bool, optional
        Flag indicating whether to plot a normed histogram (probability
        mass function instead of a counts-based histogram).
    savefig : str, optional
        The name of the file to save the figure to. If None, do not save.

    Other parameters
    ----------------
    sigma : float, optional
        The sigma parameter for the Gaussian kernel to use when smoothing.
    xlabel : str, optional
        Label to use on the x axis. If None, attempts to extract channel
        name from `data`.
    ylabel : str, optional
        Label to use on the y axis. If None, attempts to extract channel
        name from `data`.
    title : str, optional
        Plot title.
    kwargs : dict, optional
        Additional parameters passed directly to the underlying matplotlib
        functions: ``plt.scatter`` if ``mode==scatter``, and
        ``plt.pcolormesh`` if ``mode==mesh``.

    """
    # Extract channels to plot
    if len(channels) != 2:
        raise ValueError('two channels need to be specified')
    data_plot = data[:, channels]

    # If bins are not specified, try to get bins from data object
    if (bins is None and hasattr(data_plot, 'hist_bin_edges')
            and data_plot.hist_bin_edges(0) is not None
            and data_plot.hist_bin_edges(1) is not None):
        # Get bin information
        bdx = data_plot.hist_bin_edges(0)
        bdy = data_plot.hist_bin_edges(1)
        # Get bin scaled indices
        xdx = np.linspace(0, 1, len(bdx))
        xsx = np.linspace(0, 1, (len(bdx) - 1)/div + 1)
        xdy = np.linspace(0, 1, len(bdy))
        xsy = np.linspace(0, 1, (len(bdy) - 1)/div + 1)
        # Generate sub-sampled bins
        bins = np.array([np.interp(xsx, xdx, bdx), 
                            np.interp(xsy, xdy, bdy)])

    # If colormap is not specified, use the default of this module
    if 'cmap' not in kwargs:
        kwargs['cmap'] = cmap_default

    # Calculate histogram
    if bins is not None:
        H,xe,ye = np.histogram2d(data_plot[:,0], data_plot[:,1], bins=bins)
    else:
        H,xe,ye = np.histogram2d(data_plot[:,0], data_plot[:,1])

    # Smooth    
    if smooth:
        sH = scipy.ndimage.filters.gaussian_filter(
            H,
            sigma=sigma,
            order=0,
            mode='constant',
            cval=0.0)
    else:
        sH = None

    # Normalize
    if normed:
        H = H / np.sum(H)
        sH = sH / np.sum(sH) if sH is not None else None

    ###
    # Plot
    ###

    # numpy histograms are organized such that the 1st dimension (eg. FSC) =
    # rows (1st index) and the 2nd dimension (eg. SSC) = columns (2nd index).
    # Visualized as is, this results in x-axis = SSC and y-axis = FSC, which
    # is not what we're used to. Transpose the histogram array to fix the
    # axes.
    H = H.T
    sH = sH.T if sH is not None else None

    if mode == 'scatter':
        Hind = np.ravel(H)
        xc = (xe[:-1] + xe[1:]) / 2.0   # x-axis bin centers
        yc = (ye[:-1] + ye[1:]) / 2.0   # y-axis bin centers
        xv, yv = np.meshgrid(xc, yc)
        x = np.ravel(xv)[Hind != 0]
        y = np.ravel(yv)[Hind != 0]
        z = np.ravel(H if sH is None else sH)[Hind != 0]
        plt.scatter(x, y, s=1, edgecolor='none', c=z, **kwargs)
    elif mode == 'mesh':
        plt.pcolormesh(xe, ye, H if sH is None else sH, **kwargs)
    else:
        raise ValueError("mode {} not recognized".format(mode))

    if colorbar:
        cbar = plt.colorbar()
        if normed:
            cbar.ax.set_ylabel('Probability')
        else:
            cbar.ax.set_ylabel('Counts')
    # Reset axis and log if necessary
    if log:
        plt.gca().set_xscale('log')
        plt.gca().set_yscale('log')
        a = list(plt.axis())
        a[0] = 10**(np.ceil(np.log10(xe[0])))
        a[1] = 10**(np.ceil(np.log10(xe[-1])))
        a[2] = 10**(np.ceil(np.log10(ye[0])))
        a[3] = 10**(np.ceil(np.log10(ye[-1])))
        plt.axis(a)
    else:
        a = list(plt.axis())
        a[0] = np.ceil(xe[0])
        a[1] = np.ceil(xe[-1])
        a[2] = np.ceil(ye[0])
        a[3] = np.ceil(ye[-1])
        plt.axis(a)

    # x and y labels
    if xlabel is not None:
        # Highest priority is user-provided label
        plt.xlabel(xlabel)
    elif hasattr(data_plot, 'channels'):
        # Attempt to use channel name
        plt.xlabel(data_plot.channels[0])

    if ylabel is not None:
        # Highest priority is user-provided label
        plt.ylabel(ylabel)
    elif hasattr(data_plot, 'channels'):
        # Attempt to use channel name
        plt.ylabel(data_plot.channels[1])

    # title
    if title is not None:
        plt.title(title)

    # Save if necessary
    if savefig is not None:
        plt.tight_layout()
        plt.savefig(savefig, dpi=savefig_dpi)
        plt.close()

def scatter2d(data_list, 
              channels=[0,1],
              xlabel=None,
              ylabel=None,
              xlim=None,
              ylim=None,
              savefig=None,
              **kwargs):
    """
    Plot 2D scatter plot from one or more FCSData objects or numpy arrays.

    This function does not create a new figure or axis, so it can be called
    directly to plot in a previously created axis if desired. If `savefig`
    is not specified, the plot is maintained in the current axis when the
    function returns. This allows for further modifications to the axis by
    direct calls to, for example, ``plt.xlabel``, ``plt.title``, etc.
    However, if `savefig` is specified, the figure is closed after being
    saved. In this case, the default values for ``xlabel`` and ``ylabel``
    will be used.

    Parameters
    ----------
    data_list : array or FCSData or list of array or list of FCSData
        Flow cytometry data to plot.
    channels : list of int, list of str
        Two channels to use for the plot.
    savefig : str, optional
        The name of the file to save the figure to. If None, do not save.

    Other parameters
    ----------------
    xlabel : str, optional
        Label to use on the x axis. If None, attempts to extract channel
        name from last data object.
    ylabel : str, optional
        Label to use on the y axis. If None, attempts to extract channel
        name from last data object.
    xlim : tuple, optional
        Limits for the x axis. If None, attempts to extract limits from the
        domain of the last data object.
    ylim : tuple, optional
        Limits for the y axis. If None, attempts to extract limits from the
        domain of the last data object.
    kwargs : dict, optional
        Additional parameters passed directly to matploblib's ``scatter``.
        `color` can be specified as a list, with an element for each data
        object. If the keyword argument `color` is not provided, elements
        from `data_list` are plotted with colors taken from the default
        colormap.

    Notes
    -----
    `scatter2d` calls matplotlib's ``scatter`` function for each object in
    data_list. Additional keyword arguments provided to `scatter2d` are
    passed directly to ``plt.scatter``.

    """
    # Check appropriate number of channels
    if len(channels) != 2:
        raise ValueError('two channels need to be specified')

    # Convert to list if necessary
    if not isinstance(data_list, list):
        data_list = [data_list]

    # Convert color to list, if necessary
    if 'color' in kwargs and not isinstance(kwargs['color'], list):
        kwargs['color'] = [kwargs['color']]*len(data_list)

    # Default colors
    if 'color' not in kwargs:
        kwargs['color'] = [cmap_default(i)
                           for i in np.linspace(0, 1, len(data_list))]

    # Iterate through data_list
    for i, data in enumerate(data_list):
        # Get channels to plot
        data_plot = data[:, channels]
        # Get kwargs
        kwargsi = kwargs.copy()
        if 'color' in kwargsi:
            kwargsi['color'] = kwargs['color'][i]
        # Make scatter plot
        plt.scatter(data_plot[:,0],
                    data_plot[:,1],
                    s=5,
                    alpha=0.25,
                    **kwargsi)

    # Set labels if specified, else try to extract channel names
    if xlabel is not None:
        plt.xlabel(xlabel)
    elif hasattr(data_plot, 'channels'):
        plt.xlabel(data_plot.channels[0])
    if ylabel is not None:
        plt.ylabel(ylabel)
    elif hasattr(data_plot, 'channels'):
        plt.ylabel(data_plot.channels[1])

    # Set plot limits if specified, else extract range from domain
    if xlim is not None:
        plt.xlim(xlim)
    elif hasattr(data_plot, 'domain') and data_plot.domain(0) is not None:
        plt.xlim(data_plot.domain(0)[0], data_plot.domain(0)[-1])
    if ylim is not None:
        plt.ylim(ylim)
    elif hasattr(data_plot, 'domain') and data_plot.domain(1) is not None:
        plt.ylim(data_plot.domain(1)[0], data_plot.domain(1)[-1])

    # Save if necessary
    if savefig is not None:
        plt.tight_layout()
        plt.savefig(savefig, dpi=savefig_dpi)
        plt.close()

def scatter3d(data_list, 
              channels=[0,1,2],
              xlabel=None,
              ylabel=None,
              zlabel=None,
              xlim=None,
              ylim=None,
              zlim=None,
              savefig=None,
              **kwargs):
    """
    Plot 3D scatter plot from one or more FCSData objects or numpy arrays.

    This function does not create a new figure or axis, so it can be called
    directly to plot in a previously created axis if desired. If `savefig`
    is not specified, the plot is maintained in the current axis when the
    function returns. This allows for further modifications to the axis by
    direct calls to, for example, ``plt.xlabel``, ``plt.title``, etc.
    However, if `savefig` is specified, the figure is closed after being
    saved. In this case, the default values for ``xlabel`` and ``ylabel``
    will be used.

    Parameters
    ----------
    data_list : array or FCSData or list of array or list of FCSData
        Flow cytometry data to plot.
    channels : list of int, list of str
        Three channels to use for the plot.
    savefig : str, optional
        The name of the file to save the figure to. If None, do not save.

    Other parameters
    ----------------
    xlabel : str, optional
        Label to use on the x axis. If None, attempts to extract channel
        name from last data object.
    ylabel : str, optional
        Label to use on the y axis. If None, attempts to extract channel
        name from last data object.
    zlabel : str, optional
        Label to use on the z axis. If None, attempts to extract channel
        name from last data object.
    xlim : tuple, optional
        Limits for the x axis. If None, attempts to extract limits from the
        domain of the last data object.
    ylim : tuple, optional
        Limits for the y axis. If None, attempts to extract limits from the
        domain of the last data object.
    zlim : tuple, optional
        Limits for the z axis. If None, attempts to extract limits from the
        domain of the last data object.
    kwargs : dict, optional
        Additional parameters passed directly to matploblib's ``scatter``.
        `color` can be specified as a list, with an element for each data
        object. If the keyword argument `color` is not provided, elements
        from `data_list` are plotted with colors taken from the default
        colormap.

    Notes
    -----
    `scatter3d` uses matplotlib's ``scatter`` with a 3D projection.
    Additional keyword arguments provided to `scatter3d` are passed
    directly to ``scatter``.

    """
    # Check appropriate number of channels
    if len(channels) != 3:
        raise ValueError('three channels need to be specified')

    # Convert to list if necessary
    if not isinstance(data_list, list):
        data_list = [data_list]

    # Convert color to list, if necessary
    if 'color' in kwargs and not isinstance(kwargs['color'], list):
        kwargs['color'] = [kwargs['color']]*len(data_list)

    # Default colors
    if 'color' not in kwargs:
        kwargs['color'] = [cmap_default(i)
                           for i in np.linspace(0, 1, len(data_list))]

    # Make 3d axis if necessary
    ax_3d = plt.gca(projection='3d')

    # Iterate through data_list
    for i, data in enumerate(data_list):
        # Get channels to plot
        data_plot = data[:, channels]
        # Get kwargs
        kwargsi = kwargs.copy()
        if 'color' in kwargsi:
            kwargsi['color'] = kwargs['color'][i]
            kwargsi['c'] = kwargs['color'][i]
        # Make scatter plot
        ax_3d.scatter(data_plot[:,0],
                      data_plot[:,1],
                      data_plot[:,2],
                      marker='o',
                      alpha=0.1,
                      **kwargsi)

    # Remove tick marks
    ax_3d.xaxis.set_ticklabels([])
    ax_3d.yaxis.set_ticklabels([])
    ax_3d.zaxis.set_ticklabels([])

    # Set labels if specified, else try to extract channel names
    if xlabel is not None:
        ax_3d.set_xlabel(xlabel)
    elif hasattr(data_plot, 'channels'):
        ax_3d.set_xlabel(data_plot.channels[0])
    if ylabel is not None:
        ax_3d.set_ylabel(ylabel)
    elif hasattr(data_plot, 'channels'):
        ax_3d.set_ylabel(data_plot.channels[1])
    if zlabel is not None:
        ax_3d.set_zlabel(zlabel)
    elif hasattr(data_plot, 'channels'):
        ax_3d.set_zlabel(data_plot.channels[2])

    # Set plot limits if specified, else extract range from domain
    if xlim is not None:
        ax_3d.set_xlim(xlim)
    elif hasattr(data_plot, 'domain') and data_plot.domain(0) is not None:
        ax_3d.set_xlim(data_plot.domain(0)[0], data_plot.domain(0)[-1])
    if ylim is not None:
        ax_3d.set_ylim(ylim)
    elif hasattr(data_plot, 'domain') and data_plot.domain(1) is not None:
        ax_3d.set_ylim(data_plot.domain(1)[0], data_plot.domain(1)[-1])
    if zlim is not None:
        ax_3d.set_zlim(zlim)
    elif hasattr(data_plot, 'domain') and data_plot.domain(2) is not None:
        ax_3d.set_zlim(data_plot.domain(2)[0], data_plot.domain(2)[-1])

    # Save if necessary
    if savefig is not None:
        plt.tight_layout()
        plt.savefig(savefig, dpi=savefig_dpi)
        plt.close()

##############################################################################
# COMPLEX PLOTS
##############################################################################
#
# The functions below produce plots by composing the results of the functions 
# defined above.
#
##############################################################################

def density_and_hist(data,
                     gated_data=None,
                     gate_contour=None,
                     density_channels=None,
                     density_params={},
                     hist_channels=None,
                     hist_params={},
                     figsize=None,
                     savefig=None):
    """
    Make a combined density/histogram plot of a FCSData object.

    This function calls `hist1d` and `density2d` to plot a density diagram
    and a number of histograms in different subplots of the same plot using
    one single function call. Setting `density_channels` to None will not
    produce a density diagram, and setting `hist_channels` to None will not
    produce any histograms. Setting both to None will raise an error.
    Additional parameters can be provided to `density2d` and `hist1d` by
    using `density_params` and `hist_params`.

    If `gated_data` is provided, this function will plot the histograms
    corresponding to `gated_data` on top of `data`'s histograms, with some
    transparency on `data`. In addition, a legend will be added with the
    labels 'Ungated' and 'Gated'. If `gate_contour` is provided and it
    contains a valid list of 2D curves, these will be plotted on top of the
    density plot.

    This function creates a new figure and a set of axes. If `savefig` is
    not specified, the plot is maintained in the newly created figure when
    the function returns. However, if `savefig` is specified, the figure
    is closed after being saved.

    Parameters
    ----------
    data : FCSData object
        Flow cytometry data object to plot.
    gated_data : FCSData object, optional
        Flow cytometry data object. If `gated_data` is specified, the
        histograms of `data` are plotted with an alpha value of 0.5, and
        the histograms of `gated_data` are plotted on top of those with
        an alpha value of 1.0.
    gate_contour : list, optional
        List of Nx2 curves, representing a gate contour to be plotted in
        the density diagram.
    density_channels : list
        Two channels to use for the density plot. If `density_channels` is
        None, do not plot a density plot.
    density_params : dict, optional
        Parameters to pass to `density2d`.
    hist_channels : list
        Channels to use for each histogram. If `hist_channels` is None,
        do not plot histograms.
    hist_params : list, optional
        List of dictionaries with the parameters to pass to each call of
        `hist1d`.
    savefig : str, optional
        The name of the file to save the figure to. If None, do not save.

    Other parameters
    ----------------
    figsize : tuple, optional
        Figure size. If None, calculate a default based on the number of
        subplots.

    Raises
    ------
    ValueError
        If both `density_channels` and `hist_channels` are None.

    """
    # Check number of plots
    if density_channels is None and hist_channels is None:
        raise ValueError("density_channels and hist_channels cannot be both "
            "None")
    # Change hist_channels to iterable if necessary
    if not hasattr(hist_channels, "__iter__"):
        hist_channels = [hist_channels]
    if isinstance(hist_params, dict):
        hist_params = [hist_params]*len(hist_channels)

    plot_density = not(density_channels is None)
    n_plots = plot_density + len(hist_channels)

    # Calculate plot size if necessary
    if figsize is None:
        height = 0.315 + 2.935*n_plots
        figsize = (6, height)

    # Create plot
    plt.figure(figsize=figsize)

    # Density plot
    if plot_density:
        plt.subplot(n_plots, 1, 1)
        # Plot density diagram
        density2d(data, channels=density_channels, **density_params)
        # Plot gate contour
        if gate_contour is not None:
            for g in gate_contour:
                plt.plot(g[:,0], g[:,1], color='k', linewidth=1.25)
        # Add title
        if 'title' not in density_params:
            if gated_data is not None:
                ret = gated_data.shape[0]*100./data.shape[0]
                title = "{} ({:.1f}% retained)".format(str(data), ret)
            else:
                title = str(data)
            plt.title(title)

    # Colors
    n_colors = n_plots - 1
    colors = [cmap_default(i) for i in np.linspace(0, 1, n_colors)]
    # Histogram
    for i, hist_channel in enumerate(hist_channels):
        # Define subplot
        plt.subplot(n_plots, 1, plot_density + i + 1)
        # Default colors
        hist_params_i = hist_params[i].copy()
        if 'facecolor' not in hist_params_i:
            hist_params_i['facecolor'] = colors[i]
        # Plots
        if gated_data is not None:
            hist1d(data,
                   channel=hist_channel,
                   alpha=0.5,
                   **hist_params_i)
            hist1d(gated_data,
                   channel=hist_channel,
                   alpha=1.0,
                   **hist_params_i)
            plt.legend(['Ungated', 'Gated'], loc='best', fontsize='medium')
        else:
            hist1d(data, channel=hist_channel, **hist_params_i)
    
    # Save if necessary
    if savefig is not None:
        plt.tight_layout()
        plt.savefig(savefig, dpi=savefig_dpi)
        plt.close()

def scatter3d_and_projections(data_list,
                              channels=[0,1,2],
                              xlabel=None,
                              ylabel=None,
                              zlabel=None,
                              xlim=None,
                              ylim=None,
                              zlim=None,
                              figsize=None,
                              savefig=None,
                              **kwargs):
    """
    Plot a 3D scatter plot and 2D projections from FCSData objects.

    `scatter3d_and_projections` creates a 3D scatter plot and three 2D
    projected scatter plots in four different axes for each FCSData object
    in `data_list`, in the same figure.

    This function creates a new figure and a set of axes. If `savefig` is
    not specified, the plot is maintained in the newly created figure when
    the function returns. However, if `savefig` is specified, the figure
    is closed after being saved.

    Parameters
    ----------
    data_list : FCSData object, or list of FCSData objects
        Flow cytometry data to plot.
    channels : list of int, list of str
        Three channels to use for the plot.
    savefig : str, optional
        The name of the file to save the figure to. If None, do not save.

    Other parameters
    ----------------
    xlabel : str, optional
        Label to use on the x axis. If None, attempts to extract channel
        name from last data object.
    ylabel : str, optional
        Label to use on the y axis. If None, attempts to extract channel
        name from last data object.
    zlabel : str, optional
        Label to use on the z axis. If None, attempts to extract channel
        name from last data object.
    xlim : tuple, optional
        Limits for the x axis. If None, attempts to extract limits from the
        domain of the last data object.
    ylim : tuple, optional
        Limits for the y axis. If None, attempts to extract limits from the
        domain of the last data object.
    zlim : tuple, optional
        Limits for the z axis. If None, attempts to extract limits from the
        domain of the last data object.
    figsize : tuple, optional
        Figure size. If None, use matplotlib's default.
    kwargs : dict, optional
        Additional parameters passed directly to matploblib's ``scatter``.
        `color` can be specified as a list, with an element for each data
        object. If the keyword argument `color` is not provided, elements
        from `data_list` are plotted with colors taken from the default
        colormap.

    Notes
    -----
    `scatter3d_and_projections` uses matplotlib's ``scatter``, with the 3D
    scatter plot using a 3D projection. Additional keyword arguments
    provided to `scatter3d_and_projections` are passed directly to
    ``scatter``.

    """
    # Check appropriate number of channels
    if len(channels) != 3:
        raise ValueError('three channels need to be specified')

    # Create figure
    plt.figure(figsize=figsize)

    # Axis 1: channel 0 vs channel 2
    plt.subplot(221)
    scatter2d(data_list,
              channels=[channels[0], channels[2]],
              xlabel=xlabel,
              ylabel=zlabel,
              xlim=xlim,
              ylim=zlim,
              **kwargs)

    # Axis 2: 3d plot
    ax_3d = plt.gcf().add_subplot(222, projection='3d')
    scatter3d(data_list,
              channels=channels,
              xlabel=xlabel,
              ylabel=ylabel,
              zlabel=zlabel,
              xlim=xlim,
              ylim=ylim,
              zlim=zlim,
              **kwargs)

    # Axis 3: channel 0 vs channel 1
    plt.subplot(223)
    scatter2d(data_list,
              channels=[channels[0], channels[1]],
              xlabel=xlabel,
              ylabel=ylabel,
              xlim=xlim,
              ylim=ylim,
              **kwargs)

    # Axis 4: channel 2 vs channel 1
    plt.subplot(224)
    scatter2d(data_list,
              channels=[channels[2], channels[1]],
              xlabel=zlabel,
              ylabel=ylabel,
              xlim=zlim,
              ylim=ylim,
              **kwargs)

    # Save if necessary
    if savefig is not None:
        plt.tight_layout()
        plt.savefig(savefig, dpi=savefig_dpi)
        plt.close()