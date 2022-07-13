# -*- coding: utf-8 -*-
"""
Created on Wed Apr 27 22:20:32 2022

@author: sr
"""

# -*- coding: utf-8 -*-



from artiq.experiment import *
import numpy as np    
from DetectionClass import *
from MOTcoils import* 


class Camera_test(EnvExperiment):
    
    
    def build(self): 
        self.setattr_device("core")
        self.Detect=DetectionNew(self)
        self.MC=MOTcoils(self)
        
        self.setattr_argument("Delay_duration",
            Scannable(default=[RangeScan(0.0*1e-3, 500.0*1e-3, 20, randomize=False),NoScan(0.0)],scale=1e-3,
                      unit="ms"),"Loading")
        
        self.setattr_argument("Background_subtract",BooleanValue(False),"Loading")
            
        if not hasattr(self.Delay_duration,'sequence'):
            self.x=np.array([0,0])
        else:
            self.x=self.Delay_duration.sequence
        self.y=np.full(len(self.x), np.nan) # Prepare result array
        #self.Detect.cam.disarm()
      
    def prepare(self):  
        
        # Prepare MOT pulse shape
        self.MC.Blackman_pulse_profile()
       
        # Initialize camera
        self.Detect.camera_init()
        self.Detect.disarm()
        
    @kernel    
    def run(self):
        
        self.core.reset()
        self.MC.init_DAC()
        
        #self.MC.Set_current(self.MC.Current_amplitude)
        
        # Prepare datasets
        
        # Camera output datasets
        self.Detect.prep_datasets(self.y)
        self.set_dataset("time_delay", self.x, broadcast=True)
        
        if self.Background_subtract:
                self.Detect.arm()
                delay(500*ms)
                self.Detect.trigger_camera()    # Trigger camera
                delay(self.Detect.Exposure_Time)
                self.Detect.acquire()     # Acquire images
                #self.Detect.transfer_background_image(ii)
        
        # # Main loop
        # for ii in range(len(self.x)):
           
        #    if self.Background_subtract:
        #         self.Detect.arm()
        #         delay(500*ms)
        #         self.Detect.trigger_camera()    # Trigger camera
        #         delay(self.Detect.Exposure_Time)
        #         self.Detect.acquire()     # Acquire images
        #         self.Detect.transfer_background_image(ii)
        #    delay(300*ms)
        #    self.MC.Blackman_ramp_up()

           
        #    delay(self.x[ii])                                     # Delay duration 
        #    self.Detect.arm()

        #    self.Detect.trigger_camera()                               # Trigger camera
               
        #    delay(self.Detect.Exposure_Time)
        #    delay(200*ms)
        #    self.Detect.acquire()                                # Acquire images
           
        #    self.Detect.transfer_image_background_subtracted(ii)
        #                      # Disarm camera   
                  
        #    #self.Detect.print_bg_image_array()
        #    #self.Detect.print_image_array()
        #    #self.Detect.print_bg_subtracted_image_array()
        #    # Shift 2D MOT frequency back to loading frequency
           
        #    self.Detect.disarm() 
          
        #    self.mutate_dataset("time_delay",ii,self.x[ii])
        #    self.mutate_dataset("detection.index",ii,ii)
        
       
        
        # delay(200*ms)   
        # self.MC.Zero_current()  