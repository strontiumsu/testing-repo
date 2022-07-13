# -*- coding: utf-8 -*-
"""
Created on Wed Apr 13 15:34:33 2022

@author: sr
"""

from artiq.experiment import *
import numpy as np    


class TTL_trigger(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.setattr_device("ttl5")
        
    @kernel    
    def run(self):
        self.core.reset()
        # Main loop
            
        delay(20*ms)
        self.ttl5.on()
        delay(10*ms)
        self.ttl5.off()
        delay(20*ms)