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
   


class Set_Analog_IO(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("ttl4")
        self.setattr_device("zotino0")
        self.setattr_device("sampler0")
        self.dac_0=self.get_device("zotino0")
        
        
        
        self.setattr_argument("DAC_voltage",NumberValue(0.0,min=-4.0,max=4.00),"DAC")
        #print(self.DAC_voltage)
      
   
           
    @kernel
    def run(self):
             
            self.core.reset()
            self.dac_0.init()
            #self.adc_0.init()
            delay(1*ms)
            #self.dac_0.write_dac(1,self.DAC_voltage)
            self.dac_0.write_dac(1,0.0) #offset voltage
            self.dac_0.write_dac(2,1.2) #ddev voltage
            self.dac_0.load()
            
            d0=-5
            df=-1
            ddev0=10
            ddevf=2
            time=10000*ms
            Npoints=100
            dt = time/Npoints
            for step in range(1, int(Npoints)):            
                self.dac_0.write_dac(1, 0.143*(d0 + (df-d0)/time*step*dt))
                self.dac_0.write_dac(2, -0.0358*(ddev0 + (ddevf-ddev0)/time*step*dt)+1.2)
                self.dac_0.load()
                delay(dt)
           
        

             
       
        
   
                        