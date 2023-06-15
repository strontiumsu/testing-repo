# -*- coding: utf-8 -*-
"""
Created on Tue May 16 17:48:23 2023

@author: sr
"""

# make available artiq classes for us
import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from artiq.experiment import EnvExperiment, kernel, ms, delay

# imports
import numpy as np
from CoolingClass import _Cooling


class CoilSwitchTest_exp(EnvExperiment):
   
    def build(self):
        self.setattr_device("core")
        self.MOTs = _Cooling(self)
        
        
    def prepare(self):
        self.MOTs.prepare_coils()
        # 
        # 
    @kernel
    def run(self):
        # initial devices
        self.core.reset()
        delay(100*ms)
        
        
        
        self.MOTs.init_ttls()
        # self.MOTs.init_coils()
        delay(1000*ms)
        self.MOTs.set_current_dir(0)
        
        for i in range(5):
            delay(2000*ms)
            # self.MOTs.set_current_dir(0)
            # delay(2000*ms)
            # self.MOTs.set_current_dir(+1)
            
            
            self.MOTs.Blackman_ramp_up()
            self.MOTs.hold(self.MOTs.bmot_load_duration)
            self.MOTs.Blackman_ramp_down()
            delay(100*ms)
            self.MOTs.set_current_dir(0)
            delay(100*ms)
            
            self.MOTs.Blackman_ramp_up()
            self.MOTs.hold(self.MOTs.bmot_load_duration)
            self.MOTs.set_current(0.0)
            delay(100*ms)
            self.MOTs.set_current_dir(1)
            delay(100*ms)
        

            