# -*- coding: utf-8 -*-
"""
Created on Mon Apr 18 18:11:36 2022

@author: sr
"""
import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from artiq.experiment import *
import numpy as np    
from MOTCoilsClass import _MOTCoils
from Beamline461Class import _Beamline461


class Safety(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.setattr_device('ttl7')
        self.MC=_MOTCoils(self)
        self.BB=_Beamline461(self)
        self.setattr_device("scheduler")

    
    #@kernel    
    def run(self):
        
        while 1:
            self.core.comm.close()
            self.scheduler.pause()
            self.safety_settings()
    
    @kernel        
    def safety_settings(self):
        self.core.reset()
        self.MC.init_DAC()   # Initialize MOT coil DAC
        delay(500*ms)
        self.MC.Zero_current()    
        delay(100*ms)
        self.BB.MOT_off()
        delay(100*ms)
        self.ttl7.off()