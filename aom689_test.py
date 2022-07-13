# -*- coding: utf-8 -*-
"""
Created on Tue Sep 21 11:34:31 2021

@author: sr
"""

# -*- coding: utf-8 -*-
"""
Created on Fri Aug 13 10:37:36 2021

@author: sr
"""

from artiq.experiment import *
import numpy as np
from fit_image import Fit2DGaussParabola
from Beamline689Class import*  


class AOM689Test(EnvExperiment):
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
        