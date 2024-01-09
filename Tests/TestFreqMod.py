    # -*- coding: utf-8 -*-
"""
Created on Mon Oct  2 12:17:42 2023

@author: sr
"""

from artiq.experiment import *
import numpy as np

import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from ThreePhotonClass import _ThreePhoton

class TestFreqMod(EnvExperiment):
    
    def build(self):
        # required initializations
        
        self.setattr_device("core")
        self.setattr_device("scheduler")
        

        # import classes for experiment control
        self.ThPh = _ThreePhoton(self)
        self.setattr_argument("pulse_time", NumberValue(1.0*1e-3,min=0.0*1e-3,max=100.00*1e-3,scale=1e-3,
                      unit="ms"),"parameters")
       
        
    def prepare(self):
        self.ThPh.prepare_aoms()
        
        

    @kernel
    def run(self):
        # runs before experiment take place
        self.core.reset()
        self.ThPh.init_aoms(on=False)  # initializes whiling keeping them off

        for _ in range(100):
            self.ThPh.threePhoton_pulse(self.pulse_time) #drive 3P0
            delay(100*ms)
        
        
        # self.MOTs.take_background_image_exp(self.Camera)
        # 