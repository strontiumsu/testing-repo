# -*- coding: utf-8 -*-
"""
Created on Mon Feb 21 18:04:50 2022

@author: sr
"""

from artiq.experiment import *
import numpy as np    
from Detection import *
from MOTcoils import* 
from Beamline461 import*
import scipy.optimize
import matplotlib as plt


class CurveFit(EnvExperiment):
       
    def parabola(x, a, b, c):
        return a*x**2 + b*x + c
        
    def parabolaFit(self,xdata,ydata): 
        fit_params, pcov = scipy.optimize.curve_fit(self.parabola, xdata, ydata)
        
        for param, fit_param in zip(params, fit_params):
            print(param, fit_param)
            y_fit = self.parabola(x, *fit_params)
            plt.plot(xdata, y_fit, label='fit')  
            plt.legend(loc='lower right')  
            plt.show()