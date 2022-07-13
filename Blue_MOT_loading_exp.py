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
from Beamline689Class import*
from DipoleTrapClass import*
from HCDL import* 

class Blue_MOT_loading(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.setattr_device("sampler0")
        
        
        self.Detect=Detection(self)
        self.MC=MOTcoils(self)
        self.BB=Beamline461(self)
        self.BR=Beamline689(self)
        self.Dipole=DipoleTrap(self)
        
        self.setattr_argument("Delay_duration",
            Scannable(default=[RangeScan(0.0*1e-3, 500.0*1e-3, 20, randomize=False),NoScan(0.0)],scale=1e-3,
                      unit="ms"),"Loading")
        
        self.setattr_argument("Background_subtract",BooleanValue(False),"Loading")
        
        self.setattr_argument("Detection_pulse_time",NumberValue(1.0*1e-3,min=0.0,max=10.00*1e-3,scale = 1e-3,
                      unit="ms"),"Detection")
            
        self.setattr_argument("Detection_attenuation",NumberValue(6.0,min=0.0,max=30.0,scale = 1,
                      unit="dBm"),"Detection")
        
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
        self.Dipole.set_atten()
       
        # Initialize camera
        self.Detect.camera_init()
        #self.Detect.disarm()
      
    @kernel    
    def run(self):
        
        self.core.reset()
        self.sampler0.init()                                                            
        self.MC.init_DAC()
        self.BB.init_aoms()
        self.BR.init_aoms()
        self.Dipole.init_aoms()

        
        #self.MC.Set_current(self.MC.Current_amplitude)
        
        # Prepare datasets
        
        # Camera output datasets
        self.Detect.prep_datasets(self.y)
        self.set_dataset("time_delay", self.x, broadcast=True)
        self.set_dataset("PDsignal", self.y, broadcast=True)
        
        # Main loop
        for ii in range(len(self.x)):
           self.Detect.arm()
           
           delay(300*ms)
           
           self.sampler0.set_gain_mu(0, 0) #sets each channel's gain to 0db
           smp = [0]*8       #creates floating point variable
          
           self.BR.Repumpers_aom_on() # turn on repumpers
           self.BB.MOT2D_off()                  # Turn of 2D MOT
           delay(1*ms)
           self.BB.reinit_MOT3DDP_aom(self.Detection_attenuation, self.BB.f_MOT3D_detect) # switch to detection frequency   
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
           delay(500*ms)
           
           self.BB.reinit_MOT3DDP_aom(self.BB.MOT3DDP_iatten, self.BB.f_MOT3D_load) # switch to detection frequency
           self.MC.Blackman_ramp_up()
           self.BB.MOT2D_on()                # Turn on atom beam
           self.BB.MOT_on()
           
           delay(self.x[ii])                                     # Delay duration 
           self.Detect.arm()
           
           delay(1*ms)
           with parallel:
               self.BB.MOT2D_off()
               self.Detect.trigger_camera()                               # Trigger camera
               self.BB.reinit_MOT3DDP_aom(self.Detection_attenuation, self.BB.f_MOT3D_detect) # switch to detection frequency
           delay(self.Detection_pulse_time/2)
           self.sampler0.sample_mu(smp)
           delay(self.Detection_pulse_time/2)
           self.BB.MOT_off()
           delay(self.Detect.Exposure_Time)
           delay(5*ms)
           
           self.Detect.acquire()                                # Acquire images
           delay(100*ms)
           self.MC.Blackman_ramp_down()
           self.Detect.transfer_image_background_subtracted(ii)
           delay(500*ms)
                             # Disarm camera   
                  
           self.BR.Repumpers_aom_off() # turn off repumpers
           self.Detect.disarm() 
          
           self.mutate_dataset("time_delay",ii,self.x[ii])
           self.mutate_dataset("detection.index",ii,ii)
           self.mutate_dataset("PDsignal",ii,smp[0])
           
        
        delay(200*ms)   
        self.MC.Zero_current()  
        
            #self.Detect.clean_up()