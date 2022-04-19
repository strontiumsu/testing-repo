# -*- coding: utf-8 -*-
"""
Created on Thu Apr 14 17:27:17 2022

@author: sr
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Feb 15 19:37:10 2022
@author: sr
"""


from artiq.experiment import *
import numpy as np    
from Detection import *
from MOTcoils import* 
from Beamline461Class import*


class Blue_MOT_opt_old(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.Detect=Detection(self)
        self.MC=MOTcoils(self)
        self.BB=Beamline461(self)
    
        
        
        self.setattr_argument("Detection_frequency",
            Scannable(default=[NoScan(97*1e6), RangeScan(90*1e6, 115*1e6, 10, randomize=False)],scale=1e6,
                      unit="MHz"),"3D MOT optimization")
        
        self.setattr_argument("Detection_duration",NumberValue(10*1e-3,min=0*1e-3,max=200*1e-3,scale=1e-3,unit='ms'),"3D MOT optimization")
       

        if hasattr(self.Detection_frequency,'sequence') and not hasattr(self.BB.MOT3DDP_AOM_frequency,'sequence'):
            self.x=self.Detection_frequency.sequence
            self.f_detect=self.x[0]
            self.f_MOT=self.BB.MOT3DDP_AOM_frequency.value
            self.f_detect_scan=True
            self.f_MOT_scan=False
        elif not hasattr(self.Detection_frequency,'sequence') and hasattr(self.BB.MOT3DDP_AOM_frequency,'sequence'):  
            
            self.x=self.BB.MOT3DDP_AOM_frequency.sequence
            self.f_MOT=self.x[0]
            self.f_detect=self.Detection_frequency.value
            self.f_detect_scan=False
            self.f_MOT_scan=True
        else: 
            print('PICK ONLY ONE VARIABLE TO SCAN!')
    
    def prepare(self):  
        
        # Prepare MOT pulse shape
        self.MC.Blackman_pulse_profile()
        # Set AOM attenuations
        self.BB.set_atten()
        # Initialize camera
        self.Detect.camera_init()
        self.Detect.disarm()
        
        
    
    @kernel    
    def run(self):
        
        self.core.reset()
        self.MC.init_DAC()   # Initialize MOT coil DAC
        self.BB.init_aoms()  # Initialize AOMs

        self.Detect.prep_datasets(self.x)  # Prepare imaging datasets
        
        # Main loop
        for ii in range(len(self.x)):
           if self.f_detect_scan:
                self.f_detect=self.x[ii]
                
           else:    
                self.f_MOT=self.x[ii]
           
           self.set_dataset("frequency", self.x, broadcast=True)     

           self.Detect.arm()  # Arm camera
           delay(500*ms)      # Delay due to switching between FPGA and host computer
           self.BB.set_MOT3DDP_aom_frequency(self.f_MOT) # Set 3D MOT detuning
           #print(self.f_MOT)
           self.MC.Blackman_ramp_up()                    # Ramp up MOT coil current
           self.MC.flat()                                   
           
           with parallel:
               with sequential:
                   self.BB.set_MOT3DDP_aom_frequency(self.f_detect)
                   #print(self.f_detect)
                   #self.BB.pulse_3D_MOT(self.Detection_duration)
               self.Detect.trigger_camera()            
           
           self.MC.Blackman_ramp_down()
           self.Detect.acquire()
           self.Detect.transfer_image(ii)
           self.Detect.disarm()
           self.mutate_dataset("frequency",ii,self.x[ii])
        
        delay(500*ms)
        self.MC.Zero_current()    
        #self.Detect.clean_up()