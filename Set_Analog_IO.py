# -*- coding: utf-8 -*-
"""
Created on Mon May 10 20:48:14 2021

@author: sr
"""

# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 14:09:47 2021

@author: sr
"""

from artiq.experiment import *
import numpy as np
from fit_image import Fit2DGaussParabola
   


class Set_Analog_IO(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("ttl4")
        self.setattr_device("zotino0")
        self.setattr_device("sampler0")
        self.dac_0=self.get_device("zotino0")
        
        
        
        self.setattr_argument("DAC_voltage",NumberValue(0.0,min=-4.0,max=4.00),"DAC")
        print(self.DAC_voltage)
      
   
           
    @kernel
    def run(self):
             
            self.core.reset()
            self.dac_0.init()
            #self.adc_0.init()
            delay(1*ms)
            self.dac_0.write_dac(0,self.DAC_voltage)
            self.dac_0.load()
           
            
                       


             
       
        
   
                        