# -*- coding: utf-8 -*-
"""
Created on Mon Feb 14 17:07:25 2022

@author: sr
"""

       
from artiq.experiment import *
import numpy as np    
from HCDL import *

class HCDL_setup(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        
        self.HCDL=HCDL(self)
    
    def prepare(self):  
        self.HCDL.set_atten()
     
    
    @kernel
    def run(self):
        self.core.reset()
        self.HCDL.init_aoms()
        self.HCDL.set_pump_aom_frequency()
        self.HCDL.set_offset_aom_frequency() 
        self.HCDL.set_lock_DP_aom_frequency()
        
        