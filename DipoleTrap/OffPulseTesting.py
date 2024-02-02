# -*- coding: utf-8 -*-
"""
Created on Wed Oct  4 10:14:24 2023

@author: E.Porter
"""


import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")


from artiq.experiment import *
import numpy as np

from BraggClass import _Bragg

class OffPulseTesting(EnvExperiment):


    def build(self):
        self.setattr_device("core")
        self.bragg=_Bragg(self)
        
        self.setattr_argument("off_time",
                      NumberValue(0.0*1e-3,min=0.0,max=200.00*1e-3,scale = 1e-3,
                       unit="ms"))
        
        self.setattr_argument(f"off_atten", NumberValue(5, min=1.0, max=30))
        self.setattr_argument(f"off_scale", NumberValue(0.5, min=0.0, max=0.9))

    def prepare(self):
        self.bragg.prepare_aoms()

    @kernel
    def run(self):
        self.core.reset()
        self.bragg.init_aoms(on=True)
        delay(500*ms)
        
        
        self.bragg.set_AOM_attens([("Dipole",self.off_atten ), ("Homodyne",self.off_atten)])
        self.bragg.set_AOM_scales([("Dipole",self.off_scale ), ("Homodyne",self.off_scale)])
        
        
        delay(self.off_time)
        
        self.bragg.set_AOM_attens([("Dipole",4.0 ), ("Homodyne",3.0)])  
        self.bragg.set_AOM_scales([("Dipole",0.8 ), ("Homodyne",0.8)])  


