# -*- coding: utf-8 -*-
"""
Created on Tue Feb 15 21:19:34 2022

@author: sr
"""



from artiq.experiment import *
import numpy as np    
from Detection import *
from MOTcoils import* 
from Beamline461Class import*
from HCDL import* 

class Blue_MOT_lifetime(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.Detect=Detection(self)
        self.MC=MOTcoils(self)
        self.BB=Beamline461(self)
        
        self.setattr_argument("Delay_duration",
            Scannable(default=[NoScan(0.0),RangeScan(0.0*1e-3, 1000.0*1e-3, 20, randomize=False)],scale=1e-3,
                      unit="ms"),"Loading")
        
        if hasattr(self.Delay_duration,'sequence'):
            print(True)
            self.x=self.Delay_duration.sequence
        else:
            self.x=self.Delay_duration
         
        self.y=np.full(len(self.x), np.nan)
        self.t_delay=self.x[0]
        self.freq=self.get_dataset('blue_MOT.f_load')
        self.f_detect=self.get_dataset('blue_MOT.f_detect')
      
            
        
       
            
        
        
    def prepare(self):  
        
        # Prepare MOT pulse shape
        self.MC.Blackman_pulse_profile()
        self.BB.set_atten()
       
        # Initialize camera
        self.Detect.camera_init()
        self.Detect.disarm()
        
        
    
    @kernel    
    def run(self):
        
        self.core.reset()
        self.MC.init_DAC()
        self.BB.init_aoms()
        
        # Prepare datasets
        self.Detect.prep_datasets(self.y)
       
        self.set_dataset("time_delay", self.x, broadcast=True)
       
        
        # Main loop
        for ii in range(len(self.x)):
           self.Detect.arm()
           
           delay(200*ms)
        
           self.t_delay=self.x[ii]
           self.BB.set_MOT3DDP_aom_frequency(self.freq)   # Set loading frequency
           delay(100*ms)
           
           self.MC.Blackman_ramp_up()                     # Ramp up field
           self.MC.flat()
           self.BB.shift_MOT2D_aom_frequency(25.0)        # Detune 2D MOT AOM detuning in MHz. Ideally stopping atom beam
           
           delay(self.t_delay)                            # Delay  
           
           with parallel:
               self.BB.set_MOT3DDP_aom_frequency(self.f_detect) # Switch to detection frequency
               self.Detect.trigger_camera()                     # Trigger camera
           
            
           delay(self.Detect.Exposure_Time)
           self.MC.Blackman_ramp_down()
           delay(200*ms)
           self.Detect.acquire()                                # Acquire images
           
           self.Detect.transfer_image(ii)
                             # Disarm camera   
                  
           
           self.BB.shift_MOT2D_aom_frequency(0.0)               # Shift 2D MOT frequency back to loading frequency
           
           self.Detect.disarm() 
           self.mutate_dataset("time_delay",ii,self.t_delay)
           self.mutate_dataset("index",ii,ii)
         
           
        
        
            #self.Detect.clean_up()