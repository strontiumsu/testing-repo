# -*- coding: utf-8 -*-
"""
Created on Thu Jul  6 16:08:56 2023

@author: E. Porter
"""

import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")


from artiq.experiment import *
import numpy as np

from BraggClass import _Bragg

class RingDown_exp(EnvExperiment):
    
    def build(self):
        
        self.setattr_device("core")
        self.setattr_device('scheduler')
        self.bragg=_Bragg(self)
        
    def prepare(self):
        self.bragg.prepare_aoms()

    @kernel
    def run(self):
        self.core.reset()
        delay(500*ms)
        self.bragg.init_aoms(on=False)
        delay(1000*ms)
        
        self.bragg.AOMs_on(["Dipole"])
        delay(40000*ms)
        self.bragg.AOMs_off(["Dipole"])
        
        