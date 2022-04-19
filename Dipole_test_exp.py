# -*- coding: utf-8 -*-
"""
Created on Tue Mar 15 19:12:48 2022

@author: sr
"""

from artiq.experiment import *
import numpy as np    
from DipoleTrapClass import*

class Dipole_test(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.Dipole=DipoleTrap(self)
        
        # self.setattr_argument("Delay_duration",
        #     Scannable(default=[RangeScan(0.0*1e-3, 200.0*1e-3, 20, randomize=False),NoScan(0.0)],scale=1e-3,
        #               unit="ms"),"Loading")
        
        # self.setattr_argument("Background_subtract",BooleanValue(False),"Loading")
            
        # if not hasattr(self.Delay_duration,'sequence'):
        #     self.x=np.array([0,0])
        # else:
        #     self.x=self.Delay_duration.sequence
        # self.y=np.full(len(self.x), np.nan) # Prepare result array
        
    def prepare(self):  

        # Set AOM attenuations
        self.Dipole.set_atten()

        
    @kernel    
    def run(self):
        
        self.core.reset()
        self.Dipole.init_aoms()
