# -*- coding: utf-8 -*-
"""
Created on Tue Feb 15 19:37:10 2022

@author: sr
"""
import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from artiq.experiment import *
import numpy as np    
from MOTCoilsClass import _MOTCoils
from Beamline461Class import _Beamline461
from Beamline689Class import _Beamline689


class Blue_MOT_on_DC_monitor(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.setattr_device("sampler0")
     
        
        self.MC=_MOTCoils(self)
        self.BB=_Beamline461(self)
        self.setattr_device("ttl5")
        self.setattr_device("ttl7")
        self.BR=_Beamline689(self)
        self.setattr_argument("repumper_3P0_on",BooleanValue(True),"Repumpers")
        self.setattr_argument("repumper_3P2_on",BooleanValue(True),"Repumpers")
        self.adc_data=[0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0];
       
        self.alpha=0.1;  # Digital low pass filter 
        self.adc_new=0.0;
        self.adc_f=0.0;
    
    def prepare(self):  
        
        # Prepare MOT pulse shape
        self.MC.Blackman_pulse_profile()
        # Set AOM attenuations
        self.BB.set_atten()
        self.BR.set_atten()
        self.set_dataset("detection.PD_counts",0.0, broadcast=True)
        
        # Initialize camera
        #self.Detect.camera_init()
        #self.Detect.disarm()
        
        
    
    @kernel    
    def run(self):
        
        
        nsamples=20000;
        
        self.core.reset()
        #self.ttl5.off()
        self.sampler0.init()
        self.MC.init_DAC()   # Initialize MOT coil DAC
        self.BB.init_aoms()  # Initialize AOMs
        self.BR.init_aoms()
        self.BB.MOT_on()
        # Main loop
        for i in range(8):                                                     #loops for each sampler channel 
            self.sampler0.set_gain_mu(7-i, 0) 
        self.core.break_realtime()                  #Time break to avoid underflow condition
        print(self.sampler0.get_gains_mu())
        self.core.break_realtime() 
        
        
        
        self.BR.repumper_3P0_off()
        self.BR.repumper_3P2_off()
        
        if self.repumper_3P0_on:
        
                self.BR.repumper_3P0_on()
                
        if self.repumper_3P2_on:
            
                self.BR.repumper_3P2_on()
        
            
         
                 
        self.MC.Blackman_ramp_up()                    # Ramp up MOT coil current
            #self.BB.MOT_on()
            #delay(50*ms)
            
            #ramp down the laser intensity
            #for jj in range(500):
            #    self.BB.set_MOT3DDP_aom_atten(6.0+3*float(jj/500))
            #    delay(1*ms)
        self.MC.flat()
            
        
        self.ttl5.off()
           
        while 1:
         delay(2*ms)
            
         self.sampler0.sample(self.adc_data)
         self.adc_new=self.adc_data[0]*1000
         self.adc_f=self.adc_new*self.alpha+self.adc_f*(1-self.alpha)
         
         self.set_dataset("detection.PD_counts",self.adc_f, broadcast=True) 
         
   
         delay(2*ms)