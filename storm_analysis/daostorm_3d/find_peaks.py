#!/usr/bin/env python
"""

Finds "all" the peaks in an image.

Hazen 01/14
"""

import numpy

import storm_analysis.sa_library.fitting as fitting
import storm_analysis.sa_library.ia_utilities_c as utilC
import storm_analysis.sa_library.matched_filter_c as matchedFilterC
import storm_analysis.sa_library.dao_fit_c as daoFitC
import storm_analysis.simulator.draw_gaussians_c as dg


class DaostormPeakFinder(fitting.PeakFinder):
    """
    3D-DAOSTORM peak finding (for low SNR data).
    """
    def __init__(self, parameters):
        fitting.PeakFinder.__init__(self, parameters)        
        self.filter_sigma = parameters.getAttr("filter_sigma")
        self.mfilter = None

    def newImage(self, new_image):
        fitting.PeakFinder.newImage(self, new_image)

        # If does not already exist, create a gaussian filter object.
        if self.mfilter is None:
            psf = dg.drawGaussiansXY(new_image.shape,
                                     numpy.array([0.5*new_image.shape[0]]),
                                     numpy.array([0.5*new_image.shape[1]]),
                                     sigma = self.filter_sigma)
            psf = psf/numpy.sum(psf)
            self.mfilter = matchedFilterC.MatchedFilter(psf)

    def peakFinder(self, image):
        
        # Smooth image with gaussian filter.
        smooth_image = self.mfilter.convolve(image)
        
        # Mask the image so that peaks are only found in the AOI.
        masked_image = smooth_image * self.peak_mask
        
        # Identify local maxima in the masked image.
        [new_peaks, self.taken] = utilC.findLocalMaxima(masked_image,
                                                        self.taken,
                                                        self.cur_threshold,
                                                        self.find_max_radius,
                                                        self.margin)

        # Fill in initial values for peak height, background and sigma.
        new_peaks = utilC.initializePeaks(new_peaks,         # The new peaks.
                                          self.image,        # The original image.
                                          self.background,   # The current estimate of the background.
                                          self.sigma,        # The starting sigma value.
                                          self.z_value)      # The starting z value.
        
        return new_peaks
    

class Daostorm2DFixedFitter(fitting.PeakFitter):
    """
    3D-DAOSTORM peak fitting (standard).
    """
    def __init__(self, parameters):
        fitting.PeakFitter.__init__(self, parameters)
        self.mfitter = daoFitC.MultiFitter2DFixed(self.scmos_cal, self.wx_params, self.wy_params, self.min_z, self.max_z)


class Daostorm2DFitter(fitting.PeakFitter):

    def __init__(self, parameters):
        fitting.PeakFitter.__init__(self, parameters)
        self.mfitter = daoFitC.MultiFitter2D(self.scmos_cal, self.wx_params, self.wy_params, self.min_z, self.max_z)
        

class Daostorm3DFitter(fitting.PeakFitter):

    def __init__(self, parameters):
        fitting.PeakFitter.__init__(self, parameters)
        self.mfitter = daoFitC.MultiFitter3D(self.scmos_cal, self.wx_params, self.wy_params, self.min_z, self.max_z)
        
    
class DaostormZFitter(fitting.PeakFitter):
    
    def __init__(self, parameters):
        fitting.PeakFitter.__init__(self, parameters)
        self.mfitter = daoFitC.MultiFitterZ(self.scmos_cal, self.wx_params, self.wy_params, self.min_z, self.max_z)


class DaostormFinderFitter(fitting.PeakFinderFitter):
    """
    Base class to encapsulate 3d-daostorm peak finding and fitting.
    """
    def __init__(self, parameters, peak_finder, peak_fitter):
        fitting.PeakFinderFitter.__init__(self, parameters)
        self.peak_finder = peak_finder
        self.peak_fitter = peak_fitter
        

def initFindAndFit(parameters):
    """
    Return the appropriate type of finder and fitter.
    """

    # Initialize finder.
    if (parameters.getAttr("filter_sigma", -1.0)  > 0.0):
        print("Using matched filter for peak finding.")
        finder = DaostormPeakFinder(parameters)
    else:
        finder = fitting.PeakFinder(parameters)

    # Initialize fitter.
    fitters = {'2dfixed' : Daostorm2DFixedFitter,
               '2d' : Daostorm2DFitter,
               '3d' : Daostorm3DFitter,
               'Z' : DaostormZFitter}
    fitter = fitters[parameters.getAttr("model")](parameters)
    
    return DaostormFinderFitter(parameters, finder, fitter)

#
# The MIT License
#
# Copyright (c) 2016 Zhuang Lab, Harvard University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
