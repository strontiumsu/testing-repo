# -*- coding: utf-8 -*-
"""
Created on Mon May  8 14:20:59 2023

@author: sr
"""

# make available artiq classes for us
import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from artiq.experiment import EnvExperiment, BooleanValue, kernel

# imports
import numpy as np
from CoolingClass import _Cooling
from CameraClass import _Camera


class FluxMeasurement_exp(EnvExperiment):  
    def build(self):
        self.setattr_device("core")
        self.MOTs = _Cooling(self)
        
        self.setattr_argument('On', BooleanValue(True), "Params")
        
        
    def prepare(self):
        self.MOTs.prepare_aoms()
        
    @kernel
    def run(self):
        # initial devices
        self.core.reset()
        self.MOTs.init_aoms(on=False)
        if self.On: 
            self.MOTs.AOMs_on(['Probe'])
            print('true')
        else: 
            self.MOTs.AOMs_off(['Probe'])
            print('false')

