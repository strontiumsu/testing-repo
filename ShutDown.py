# -*- coding: utf-8 -*-
"""
Created on Mon 3/6/23

@author: E. Porter
"""

# make available artiq classes for us
import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from artiq.experiment import EnvExperiment, kernel, ms, NumberValue, delay, parallel, now_mu

# imports
import numpy as np
from CoolingClass import _Cooling
from CameraClass import _Camera


class ShutDown(EnvExperiment):

    
    def build(self):
        self.setattr_device("core")
        self.setattr_device("scheduler")
        self.MOTs = _Cooling(self)
        

        
    def prepare(self):
        # initial datasets for the aoms and mot coils, does not run on core
        self.MOTs.prepare_aoms()
        self.MOTs.prepare_coils()

        

        
    @kernel
    def run(self):
        # initial devices
        self.core.reset()
        self.MOTs.init_coils()
        self.MOTs.init_aoms(on=False)
        delay(100*ms)
        self.MOTs.AOMs_off(self.MOTs.AOMs)
        self.MOTs.set_current(0)
        
        
        