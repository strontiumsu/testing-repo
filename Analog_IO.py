# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 14:09:47 2021

@author: sr
"""

from artiq.experiment import *
import numpy as np
from fit_image import Fit2DGaussParabola
   


class Analog_IO(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("ttl4")
        self.setattr_device("zotino0")
        self.setattr_device("sampler0")
        self.dac_0=self.get_device("zotino0")
        self.adc_0=self.get_device("sampler0")
        
        
        self.setattr_argument("DAC_voltage",
            Scannable(default=[NoScan(0.5), RangeScan(-4.0, 4.0, 10, randomize=False)],scale=1.0,
                      unit="V"),"DAC")
        self.setattr_argument("Repetitions",NumberValue(1,ndecimals=0,min=0,step=1,type='int'),"Experiment")
        self.reps=self.Repetitions
       # self.adc_data=[0.1 for ii in range(self.reps*len(self.DAC_voltage.sequence))]

    def prepare(self):
        self.adc_data=[0.1 for ii in range(self.reps*len(self.DAC_voltage.sequence))]
         
    @kernel
    def run(self):
             
            self.core.reset()
            print(self.adc_0.get_gains_mu())
            delay(200*ms)
            print(self.adc_0.get_gains_mu())
            delay(200*ms)
            self.dac_0.init()
            self.adc_0.init()


            delay(1*ms)
            dat=[0.1,0.5]
            jj=0
            for n in range(self.reps):
                    delay(0.2*ms)
                    self.ttl4.on()
                    delay(0.2*ms)
                    self.ttl4.off()
                    delay(0.5*ms)
                    for v in self.DAC_voltage.sequence:
                          
                    
                             delay(0.5*ms)
                             self.dac_0.write_dac(0,v)
                             self.dac_0.load()
                             delay(0.75*ms)
                             self.adc_0.sample(dat)
                            
                             self.adc_data[jj]=dat[1]
                             jj=jj+1
                             delay(0.1*ms)
                             
            delay(5*ms)                 
            self.set_dataset("set_DAC_voltage", self.DAC_voltage.sequence, broadcast=True)
            self.set_dataset("measured_DAC_voltage", self.adc_data, broadcast=True)
            
            self.dac_0.write_dac(0,0.0)
            self.dac_0.load()
            
                       


             
       
        
   
                        