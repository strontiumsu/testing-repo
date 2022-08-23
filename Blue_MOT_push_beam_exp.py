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
from HCDL import* 

class Blue_MOT_push_beam(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.setattr_device("ttl5")
 
        self.Detect=Detection(self)
        self.MC=MOTcoils(self)
        self.BB=Beamline461(self)
        self.BR=Beamline689(self)
        
        self.setattr_argument("Push_pulse_time",
            Scannable(default=[RangeScan(0.0*1e-6, 1000.0*1e-6, 20, randomize=False),NoScan(0.0)],scale=1e-6,
                      unit="us"),"Detection")
        
        self.setattr_argument("Background_subtract",BooleanValue(False),"Loading")
        
        self.setattr_argument("Detection_pulse_time",NumberValue(1.0*1e-3,min=0.0,max=10.00*1e-3,scale = 1e-3,
                      unit="ms"),"Detection")
            
        self.setattr_argument("Detection_attenuation",NumberValue(6.0,min=0.0,max=30.0,scale = 1,
                      unit="dBm"),"Detection")
        
        if not hasattr(self.Push_pulse_time,'sequence'):
            self.x=np.array([0,0])
        else:
            self.x=self.Push_pulse_time.sequence

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

        self.BR.repumper_3P0_on()
        self.BR.repumper_3P2_on()
        self.ttl5.on() # turn off red MOT beam
        # Camera output datasets
        self.Detect.prep_datasets(self.y)
        self.set_dataset("time_delay", self.x, broadcast=True)
        
        # Main loop
        for ii in range(len(self.x)):
           # prepare scanned probe frequency
           # fnew = self.BB.Probe_AOM_frequency + ii/len(self.x)*4.
           # delay(1*ms)
           # # self.BB.set_Probe_aom_frequency(fnew)
           # self.BB.reinit_Probe_aom(15.0,fnew*1e6)
           # delay(50*ms)
            
            
            
           self.Detect.arm()
           
           delay(300*ms)
          
           delay(1*ms)
           self.BB.MOT2D_off()  # turn off 2D MOT beam
           delay(1*ms)
           self.BB.Zeeman_off()
           delay(1*ms)
           self.BB.Probe_AOM_off()
           delay(1*ms)
            
            
           # BACKGROUND IMAGE SEQUENCE
           if self.Background_subtract:
               self.BB.reinit_MOT3DDP_aom(6.0, self.BB.f_MOT3D_detect)  # Set 3D MOT frequency for imaging
               delay(10*ms)
               #self.ttl7.off() #turn on red beam for background image
               #delay(5*ms)
            
               self.Detect.trigger_camera()    # Trigger camera
               #delay(1*ms)
               self.BB.MOT_on() #turn on mot for background image
               delay(self.Detection_pulse_time)
               self.BB.MOT_off()
            
               delay(self.Detect.Exposure_Time)
               self.Detect.acquire()     # Acquire images
               delay(100*ms)
               self.Detect.transfer_background_image(ii)
               delay(300*ms)
           ############################

           #prepare for detection image
           self.Detect.arm()
           delay(300*ms)

           self.BB.reinit_MOT3DDP_aom(self.BB.MOT3DDP_iatten, self.BB.f_MOT3D_load)  # Set 3D MOT frequency for loading
           delay(1*ms)

           #delay(1*ms)
           #self.BR.repumpers_on() # turn on repumpers
           delay(1*ms)
           self.MC.Blackman_ramp_up()
           delay(1*ms)
           self.BB.Zeeman_on()
           delay(1*ms)
           self.BB.MOT2D_on() # Turn on atom beam
           delay(1*ms)
           self.BB.MOT_on()
           delay(1*ms)
           #self.ttl5.off() # turn on red MOT beam
            
           delay(1*ms)
           self.MC.flat()
           
           with parallel:
                self.BB.Zeeman_off()
                self.BB.MOT2D_off() # turn off atom beam
                self.BB.MOT_off() #turn off 3D 
                self.BB.reinit_MOT3DDP_aom(6.0, self.BB.f_MOT3D_detect) # switch to detection frequency
                #self.ttl5.on() # turn off red MOT beam
            
           
           self.BB.Probe_AOM_on()
           delay(self.x[ii])  # Delay
           self.BB.Probe_AOM_off()
           
           #delay(.1*ms)
            
           # IMAGING SEQUENCE
           self.Detect.trigger_camera()  # Trigger 

           self.BB.MOT_on()
           delay(self.Detection_pulse_time)
           self.BB.MOT_off()
           delay(self.Detect.Exposure_Time)
           #self.BB.MOT_off()
           #delay(5*ms)
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
