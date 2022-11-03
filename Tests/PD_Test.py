# -*- coding: utf-8 -*-
"""
Created on Tue Oct 25 14:21:57 2022

@author: sr
"""

# -*- coding: utf-8 -*-
"""
Created on Thu Aug 11 14:23:42 2022

@author: sr
"""
import sys
import numpy as np


sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")


from artiq.experiment import EnvExperiment, kernel, ms, delay, parallel, Scannable, RangeScan, NoScan, NumberValue
   

class PD_Test(EnvExperiment):
    def build(self): 
        self.setattr_device("core")
        self.setattr_device("ttl4")
        self.setattr_device("sampler0")
        self.adc_0=self.get_device("sampler0")
        self.setattr_argument("delay",NumberValue(1*1e-3,min=0.0,max=1000.00*1e-3,scale = 1e-3,
                      unit="ms"),"Experiment")

    def prepare(self):
        pass
    
    @kernel     
    def run(self):
        
        # general inicialization
        self.core.reset()    
        delay(500*ms)   
        self.adc_0.init()
        shots = 10
        self.set_dataset('V_std', [0.1 for _ in range(shots)], broadcast=True)
        delay(500*ms)        
        
        CHANNELS = 8
        dat=[0.1 for _ in range(CHANNELS)]
        # Main loop
        samples  = 50
        for ii in range(shots):
            meas = 0.
            delay(0.2*ms)
            self.ttl4.on()
            delay(5*ms)
            self.ttl4.off()
            delay(0.5*ms)
            for jj in range(samples):
                self.adc_0.sample(dat)
                # print(type(dat[0]))
                meas += float(dat[0])
                delay(self.delay)
            self.mutate_dataset('V_std', ii, meas/samples)
            delay(self.delay)
      
               
        
   