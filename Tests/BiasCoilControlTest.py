# -*- coding: utf-8 -*-
"""
Created on Fri May 26 10:57:03 2023

@author: sr
"""

from artiq.experiment import *
import numpy as np
   


class BiasCoilControl(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("zotino0")
        self.dac_0=self.get_device("zotino0")

        

        self.setattr_argument("DAC_channel5_voltage",NumberValue(0.0,min=-4.0,max=4.00),"DAC")
        self.setattr_argument("DAC_channel6_voltage",NumberValue(0.0,min=-4.0,max=4.00),"DAC")
        self.setattr_argument("DAC_channel7_voltage",NumberValue(0.0,min=-4.0,max=4.00),"DAC")
        ### ADD more arguments
        
      
   
           
    @kernel
    def run(self):
        self.core.reset()
        
        self.dac_0.init()

        delay(1*ms)
        self.dac_0.write_dac(5,self.DAC_channel5_voltage)
        self.dac_0.write_dac(6,self.DAC_channel6_voltage)
        self.dac_0.write_dac(7,self.DAC_channel7_voltage)
        
        
        
        self.dac_0.load()