# -*- coding: utf-8 -*-
"""
Created on Fri Jun  3 13:00:34 2022

@author: sr
"""

from artiq.experiment import *
import numpy as np
from fit_image import Fit2DGaussParabola
from Beamline689Class import*  


class AomsRedTest(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.BR=Beamline689(self)
        self.setattr_device("ttl5")
        self.setattr_device("ttl7")
       
       
        
    def prepare(self):
     
        # Set AOM attenuations
        self.BR.set_atten()
            
         
                  
    @kernel
    def run(self):
        self.core.reset()
        self.BR.init_aoms()  # Initialize AOMs
        