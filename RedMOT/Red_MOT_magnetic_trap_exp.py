# -*- coding: utf-8 -*-
"""
Created on Wed Aug 31 15:53:27 2022

@author: sr
"""

import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from artiq.experiment import *
import numpy as np    
from DetectionClass import _Detection
from MOTCoilsClass import _MOTCoils
from Beamline461Class import _Beamline461
from Beamline689Class import _Beamline689

class Red_MOT_magnetic_trap(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.setattr_device("ttl5")
        self.setattr_device("ttl6")
        self.setattr_device("ttl7")

        self.Detect=_Detection(self)
        self.MC=_MOTCoils(self)
        self.BB=_Beamline461(self)
        self.BR=_Beamline689(self)
        
        self.setattr_argument("Delay_duration",
            Scannable(default=[RangeScan(0.0*1e-3, 500.0*1e-3, 20, randomize=False),NoScan(0.0)],scale=1e-3,
                      unit="ms"),"Loading")
        
        self.setattr_argument("Background_subtract",BooleanValue(False),"Loading")
        
        self.setattr_argument("Detection_pulse_time",NumberValue(1.0*1e-3,min=0.0,max=10.00*1e-3,scale = 1e-3,
                      unit="ms"),"Detection")
            
        self.setattr_argument("Detection_attenuation",NumberValue(6.0,min=0.0,max=30.0,scale = 1,
                      unit="dBm"),"Detection")
        
        self.setattr_argument("Repump_pulse_time",NumberValue(1.0*1e-3,min=0.0,max=10.00*1e-3,scale = 1e-3,
                      unit="ms"),"Detection")
        
        # MOTdriver parameters
        self.setattr_argument("Red_pulse_duration",NumberValue(25.0*1e-3,min=0.0*1e-3,max=300.0*1e-3,scale = 1e-3,
                      unit="ms"),"MOT coil driver")
        
        self.setattr_argument("Bottom_current_amplitude",NumberValue(0.25,min=0.0,max=5.00,
                      unit="A"),"MOT coil driver")
        
        self.setattr_argument("Bottom_delay",NumberValue(10.0*1e-3,min=0.0,max=100*1e-3,scale = 1e-3,
                      unit="ms"),"MOT coil driver")
        
        self.setattr_argument("Lin_ramp_time",NumberValue(100.0*1e-3,min=0.0,max=200*1e-3,scale = 1e-3,
                      unit="ms"),"MOT coil driver")
        
        self.setattr_argument("Red_current_amplitude",NumberValue(1.25,min=0.0,max=9.00,
                      unit="A"),"MOT coil driver")
        
        self.setattr_argument("Red_mot_stage",BooleanValue(True),"MOT coil driver")
        
        if not hasattr(self.Delay_duration,'sequence'):
            self.x=np.array([0,0])
        else:
            self.x=self.Delay_duration.sequence
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
        self.BR.init_aoms()
        
        # Camera output datasets
        self.Detect.prep_datasets(self.y)
        self.set_dataset("time_delay", self.x, broadcast=True)
        
        Lin_ramp_time = 100*ms
       # Main loop
        for ii in range(len(self.x)):
            
            self.Detect.arm()
            
            delay(800*ms)
            
            delay(1*ms)
            self.BB.MOT2D_off()  # turn off 2D MOT beam
            delay(1*ms)
            self.BB.Zeeman_off()
            delay(1*ms)
            
            
            # BACKGROUND IMAGE SEQUENCE
            if self.Background_subtract:
                self.BB.reinit_MOT3DDP_aom(6.0, self.BB.f_MOT3D_detect)  # Set 3D MOT frequency for imaging
                delay(10*ms)
                self.BR.repumpers_on() # turn on repumpers
                self.Detect.trigger_camera()    # Trigger camera
                self.BB.MOT_on() #turn on mot for background image
                delay(self.Detection_pulse_time)
                self.BB.MOT_off()
                delay(self.Detect.Exposure_Time)
                self.BR.repumpers_off() # turn off repumpers
                self.Detect.acquire()     # Acquire images
                delay(100*ms)
                self.Detect.transfer_background_image(ii)
                delay(300*ms)
                #prepare for detection image
                self.Detect.arm()
                delay(300*ms)
            ###########################
           

            self.BB.reinit_MOT3DDP_aom(self.BB.MOT3DDP_iatten, self.BB.f_MOT3D_load)  # Set 3D MOT frequency for loading
            delay(1*ms)
            self.MC.Blackman_ramp_up()
            delay(1*ms)
            self.BB.Zeeman_on()
            delay(1*ms)
            self.BB.MOT2D_on() # Turn on atom beam
            delay(1*ms)
            self.BB.MOT_on()
            
            self.MC.flat()
            
            if self.Red_mot_stage:
                self.ttl5.off() #turn on red beam
            
            with parallel:
                self.BB.Zeeman_off()
                self.BB.MOT2D_off() # turn off atom beam
                self.BB.MOT_off() #turn off 3D 
                self.BB.reinit_MOT3DDP_aom(6.0, self.BB.f_MOT3D_detect) # switch to detection frequency
             
            self.BR.repumpers_on() # turn on repumpers
            delay(self.x[ii])
            
            if self.Red_mot_stage:
                self.MC.Set_current(self.Bottom_current_amplitude) #ramp down Blue mot coils

                delay(self.Bottom_delay)
                self.MC.Linear_ramp(self.Bottom_current_amplitude,self.Red_current_amplitude,Lin_ramp_time,30)

                with parallel:
                    self.ttl5.on() #turn off modulation channel
                    self.ttl6.on() #switch to single-frequency channel
                delay(self.Red_pulse_duration) #single frequency stage time
                self.ttl6.off() #switch back to mod channel (which is off)
            
            
            # IMAGING SEQUENCE
            #self.BR.repumpers_on() # turn on repumpers
            self.Detect.trigger_camera()  # Trigger 
            self.BB.MOT_on()
            delay(self.Detection_pulse_time)
            self.BB.MOT_off()
            delay(self.Detect.Exposure_Time)
            self.BR.repumpers_off() # turn off repumpers
            ###########################
            self.MC.Set_current(0.0)
            
            self.Detect.acquire()                                # Acquire images
            delay(100*ms)
            self.Detect.transfer_image_background_subtracted(ii)
            delay(100*ms)
            self.Detect.disarm() 
          
            self.mutate_dataset("time_delay",ii,self.x[ii])
            self.mutate_dataset("detection.index",ii,ii)
           
        
        delay(200*ms)   
        self.MC.Zero_current()  
        
            #self.Detect.clean_up()