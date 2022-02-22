# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 14:09:47 2021

@author: sr
"""

from artiq.experiment import *
import numpy as np
from fit_image import Fit2DGaussParabola
   


class MOT_DC(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("ttl5")
        self.setattr_device("zotino0")
        self.dac_0=self.get_device("zotino0")
    
        # 3D MOT coil DC set
        
        self.setattr_argument("Current_amplitude",NumberValue(0.0,min=-4.0,max=20.00,
                      unit="A"),"MOT_driver")
       
        
        

    def prepare(self):
       self.A=self.Current_amplitude        
         
                  
    @kernel
    def run(self):
            self.core.reset()
            self.dac_0.init()
            
            delay(10*ms)
                          
            self.dac_0.write_dac(0,self.A)
            self.dac_0.load()        
              


            
            
    
            
            
        

         

                     