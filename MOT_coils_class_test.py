# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 14:09:47 2021

@author: sr
"""

from artiq.experiment import *
import numpy as np
from fit_image import Fit2DGaussParabola
from MOTcoils import*   


class MOT_coils_class_test(EnvExperiment):

    def build(self):
             
            self.setattr_device("core")
            self.setattr_device("ttl5")
            self.MC=MOTcoils(self)
            
    def prepare(self):
        self.MC.Blackman_pulse_profile()      
         
    @kernel
    def run(self):
            self.core.reset()

            for nn in range(9000):
                
                    with sequential:
                         self.ttl5.on()
                         
                         self.MC.Blackman_ramp_up()
                         self.MC.flat()
                         self.MC.Blackman_ramp_down()
                         
                         self.ttl5.off()
                         
                    self.MC.Zero_current()     
                            
                    
                    


            
            
    
            
            
        

         

                     