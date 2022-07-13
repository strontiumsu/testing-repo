# -*- coding: utf-8 -*-
"""
Created on Tue Feb 15 21:19:34 2022

@author: sr
"""



from artiq.experiment import *
import numpy as np    
from Detection import *
from MOTcoils import* 
from ZotinoRampClass import *
from Beamline461Class import*
from Beamline689Class import*
from HCDL import* 

class Red_MOT_TOF(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.setattr_device("ttl5")

        self.setattr_device("ttl7")
        self.Detect=Detection(self)
        self.MC=MOTcoils(self)
        self.BB=Beamline461(self)
        self.BR=Beamline689(self)
        #self.Zot = ZotinoRamp(self)
        
        # MOTdriver parameters
        self.setattr_argument("Red_pulse_duration",NumberValue(200.0*1e-3,min=0.0*1e-3,max=300.0*1e-3,scale = 1e-3,
                      unit="ms"),"MOT coil driver")
        
        self.setattr_argument("Bottom_current_amplitude",NumberValue(0.0,min=0.0,max=5.00,
                      unit="A"),"MOT coil driver")
        
        self.setattr_argument("Bottom_delay",NumberValue(0.0,min=0.0,max=100*1e-3,scale = 1e-3,
                      unit="ms"),"MOT coil driver")
        
        self.setattr_argument("Red_current_amplitude",NumberValue(0.0,min=0.0,max=9.00,
                      unit="A"),"MOT coil driver")
       
        self.setattr_argument("Detection_pulse_time",NumberValue(1.0*1e-3,min=0.0,max=10.00*1e-3,scale = 1e-3,
                      unit="ms"),"Detection")
        
        self.setattr_argument("Delay_duration",
            Scannable(default=[RangeScan(0.0*1e-3, 500.0*1e-3, 20, randomize=False),NoScan(0.0)],scale=1e-3,
                      unit="ms"),"Loading")
        
        self.setattr_argument("Background_subtract",BooleanValue(False),"Loading")
            
        if not hasattr(self.Delay_duration,'sequence'):
            self.x=np.array([0,0])
        else:
            self.x=self.Delay_duration.sequence
        self.y=np.full(len(self.x), np.nan) # Prepare result array
    
        
    def prepare(self):  
        
        # Prepare MOT pulse shape
        self.MC.Blackman_pulse_profile()
        #self.Zot.Linear_ramp_profile()
        # Set AOM attenuations
        self.BB.set_atten()
        self.BR.set_atten()
       
        # Initialize camera
        self.Detect.camera_init()
        self.Detect.disarm()

        
    @kernel    
    def run(self):
        
        # general inicialization
        self.core.reset()
        self.MC.init_DAC()
        self.BB.init_aoms()
        self.BR.init_aoms()
        
        # delay(10*ms)
        # self.ttl5.off() # set red mot light to single frequency
        # delay(10*ms)
        # self.ttl7.on()  # turn off red mot 
        #delay(10*ms)
        
        Lin_ramp_time = 80*ms

        # Prepare datasets
        
        # Camera output datasets
        self.Detect.prep_datasets(self.y)
        self.set_dataset("time_delay", self.x, broadcast=True)
        
        delay(100*ms)
        self.BB.MOT2D_off()  # turn off 2D MOT beam
        delay(1*ms)
        self.BB.Zeeman_off()
        delay(1*ms)
       
        # Main loop
        for ii in range(len(self.x)):
            self.Detect.arm()
            
            delay(800*ms)
            
            #bot = 2*(self.x[ii]/self.x[len(self.x)-1])*self.Bottom_current_amplitude
            
            self.BR.reinit_Red_MOT_aom(self.BR.Red_MOT_Urukul_attenuation, self.BR.Red_MOT_AOM_frequency) # switch to detection frequency
            self.ttl5.on()
            self.BR.Red_MOT_aom_off() # turn off red MOT beam
            delay(1*ms)
            self.BB.MOT2D_off()  # turn off 2D MOT beam
            delay(1*ms)
            self.BB.Zeeman_off()
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
                
                #self.ttl7.on()
                #delay(5*ms)
            ############################

            #prepare for detection image
            self.Detect.arm()
            delay(300*ms)

            self.BB.reinit_MOT3DDP_aom(self.BB.MOT3DDP_iatten, self.BB.f_MOT3D_load)  # Set 3D MOT frequency for loading
            delay(1*ms)

            
            self.MC.Blackman_ramp_up()
            delay(1*ms)
            self.BB.Zeeman_on()
            delay(1*ms)
            self.BB.MOT2D_on() # Turn on atom beam
            delay(1*ms)
            self.BB.MOT_on()
            delay(1*ms)
            self.BR.Repumpers_aom_on() # turn on repumpers
            delay(1*ms)
            self.MC.flat()
            
            with parallel:
                self.BB.Zeeman_off()
                self.BB.MOT2D_off() # turn off atom beam
                self.BB.MOT_off() #turn off 3D 
                self.BB.reinit_MOT3DDP_aom(6.0, self.BB.f_MOT3D_detect) # switch to detection frequency
                #self.MC.Blackman_ramp_down_from_to(3.0,0.1)
                self.MC.Set_current(self.Bottom_current_amplitude) #ramp down Blue mot coils  
                self.ttl5.off()
                self.BR.Red_MOT_aom_on() # turn on red MOT beam
            

            delay(self.Bottom_delay)
            self.BR.Repumpers_aom_off() # turn off repumpers
            self.MC.Linear_ramp(self.Bottom_current_amplitude,self.Red_current_amplitude,Lin_ramp_time,30)
            
            
            #delay(self.x[ii])  # Delay
            #delay(1.5*ms)
            # swith 689 to single frequency
            #self.BR.reinit_Red_MOT_aom(20.0, self.BR.Red_MOT_AOM_frequency) # switch to detection frequency
            #delay(self.Red_pulse_duration)
            
            
            self.BR.Red_MOT_aom_off() # turn off red MOT beam
            self.ttl5.on() # Turn rMOT modulation off
            
            # Switch gradient to zero
            self.MC.Set_current(0.0)
            
            delay(self.x[ii])  # Delay
            
            # IMAGING SEQUENCE
            self.BR.Repumpers_aom_on() # turn off repumpers
            self.Detect.trigger_camera()  # Trigger 
            #delay(1*ms)
            
            self.BB.MOT_on()
            delay(self.Detection_pulse_time)
            self.BB.MOT_off()
            delay(self.Detect.Exposure_Time)
            self.BR.Repumpers_aom_off() # turn off repumpers
            #self.BB.MOT_off()
            #delay(5*ms)
            ###########################
           
            
            self.Detect.acquire()                                # Acquire images
            delay(100*ms)
            self.Detect.transfer_image_background_subtracted(ii)
            delay(100*ms)
            self.Detect.disarm() 
          
            self.mutate_dataset("time_delay",ii,self.x[ii])
            self.mutate_dataset("detection.index",ii,ii)
            
            
            self.Detect.calc_marginal_stats(ii)
           
           
        delay(500*ms)   
        self.MC.Zero_current()  