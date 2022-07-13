# -*- coding: utf-8 -*-
"""
Created on Mon Apr 18 18:11:36 2022

@author: sr
"""

from artiq.experiment import *
import numpy as np    
from MOTcoils import* 


class Safety(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.MC=MOTcoils(self)
    
    @kernel    
    def run(self):

        self.core.reset()
        
        self.ttl5.on()
        self.MC.init_DAC()   # Initialize MOT coil DAC
        delay(500*ms)
        self.MC.Zero_current()    