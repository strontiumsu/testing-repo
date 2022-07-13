# -*- coding: utf-8 -*-
"""
Created on Thu Jun  9 16:04:32 2022

@author: sr
"""

from artiq.experiment import *
import numpy as np    
from Detection import *
from MOTcoils import* 
from Beamline461Class import*
from Beamline689Class import*
from HCDL import* 

class Blue_MOT_temp_689scan(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.Detect=Detection(self)
        self.MC=MOTcoils(self)
        self.BB=Beamline461(self)
        self.BR=Beamline689(self)
        
        self.setattr_argument("Delay_duration",
            Scannable(default=[RangeScan(0.0*1e-3, 500.0*1e-3, 20, randomize=False),NoScan(0.0)],scale=1e-3,
                      unit="ms"),"Loading")
        
        self.setattr_argument("Background_subtract",BooleanValue(False),"Loading")
        
        self.setattr_argument("Detection_pulse_time",NumberValue(1.0*1e-3,min=0.0,max=10.00*1e-3,scale = 1e-3,
                      unit="ms"),"Detection")
            
        # if not hasattr(self.Delay_duration,'sequence'):
        #     self.x=np.array([0,0])
        # else:
        #     self.x=self.Delay_duration.sequence
        self.x = self.BR.Red_MOT_AOM_frequency.sequence
        self.y=np.full(len(self.x), np.nan) # Prepare result array
      
      
    def prepare(self):  
        
        # Prepare MOT pulse shape
        self.MC.Blackman_pulse_profile()
        # Set AOM attenuations
        self.BB.set_atten()
        self.BR.set_atten()
       
        # Initialize camera
        self.Detect.camera_init()
        #self.Detect.disarm()
      
    @kernel    
    def run(self):
        
        self.core.reset()
        self.MC.init_DAC()
        self.BB.init_aoms()
        
        #self.MC.Set_current(self.MC.Current_amplitude)
        
        # Prepare datasets
        
        # Camera output datasets
        self.Detect.prep_datasets(self.y)
        self.set_dataset("frequency689", self.x, broadcast=True)
        
        # Main loop
        for ii in range(len(self.x)):
           self.Detect.arm()
           
           delay(500*ms)
          

           self.BB.MOT2D_off()                  # Turn of 2D MOT
           delay(1*ms)
           self.BR.Hp688_aom_off()                  # Turn off 688
           delay(1*ms)
           self.BR.Repumpers_aom_off()                  # Turn off repumo
           delay(1*ms)
           self.BR.Red_MOT_aom_off()                  # Turn off 689
           
           self.BB.set_MOT3DDP_aom_frequency(self.BB.f_MOT3D_detect)  # Set 3D MOT frequency for detection   
           self.BB.MOT_off()
           delay(200*ms)
           
           if self.Background_subtract:
                self.Detect.trigger_camera()    # Trigger camera 
                self.BB.MOT_on()
                delay(self.Detection_pulse_time)
                self.BB.MOT_off()
                delay(self.Detect.Exposure_Time)
                self.Detect.acquire()     # Acquire images
                self.Detect.transfer_background_image(ii)
                self.Detect.arm()
           delay(300*ms)
           
           self.BB.set_MOT3DDP_aom_frequency(self.BB.f_MOT3D_load)  # Set 3D MOT frequency for detection
           self.MC.Blackman_ramp_up()
           self.BB.MOT2D_on()                # Turn on atom beam
           self.BB.MOT_on()
           self.BR.Repumpers_aom_on()
           self.MC.flat()
           
           
           with parallel:
               self.BB.MOT2D_off()
               self.BB.MOT_off()
               self.MC.Zero_current()
               self.BB.set_MOT3DDP_aom_frequency(self.BB.f_MOT3D_detect)  # Set 3D MOT frequency for detection
               self.BR.Repumpers_aom_off()
               #send to dark states
           self.BR.Hp688_aom_on()
           self.BR.Red_MOT_aom_on()
           delay(1*ms)
           self.BR.Hp688_aom_off()
           self.BR.Red_MOT_aom_off()
           
           
           #delay(self.x[ii])                                     # Delay duration 
           
           
           self.Detect.trigger_camera()                               # Trigger camera
           self.BB.MOT_on()
           delay(self.Detection_pulse_time)
           self.BB.MOT_off()
           delay(self.Detect.Exposure_Time)
           self.Detect.acquire()                                # Acquire images
           
           self.Detect.transfer_image_background_subtracted(ii)
                             # Disarm camera   
                  
           #self.Detect.print_bg_image_array()
           #self.Detect.print_image_array()
           #self.Detect.print_bg_subtracted_image_array()
           # Shift 2D MOT frequency back to loading frequency
           
           self.Detect.disarm() 
          
           self.mutate_dataset("frequency689",ii,self.x[ii])
           self.mutate_dataset("detection.index",ii,ii)
    
         
        delay(500*ms)   
        self.MC.Zero_current()  
        
    
    
