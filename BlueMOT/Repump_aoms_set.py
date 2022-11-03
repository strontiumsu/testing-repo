# -*- coding: utf-8 -*-
"""
Created on Fri Jun  3 13:00:34 2022

@author: sr
"""
import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from artiq.experiment import *
from Beamline689Class import _Beamline689


class RepumpAomsSet(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.BR=_Beamline689(self)
        self.setattr_device("ttl5")
        self.setattr_device("ttl7")
       
       
        
    def prepare(self):
     
        # Set AOM attenuations
        self.BR.set_atten()
            
         
                  
    @kernel
    def run(self):
        self.core.reset()
        self.BR.init_aoms()  # Initialize AOMs
        