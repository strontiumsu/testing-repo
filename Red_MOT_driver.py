# -*- coding: utf-8 -*-
"""
Created on Wed Mar 30 16:42:52 2022

@author: sr
"""

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
from HCDL import* 

class Red_MOT_driver(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.MC=MOTcoils(self)
        self.Zot = ZotinoRampClass(self)
        self.BB=Beamline461Class(self)
        
        # MOTdriver parameters
        self.setattr_argument("Red_pulse_duration",NumberValue(200.0*1e-3,min=0.0*1e-3,max=300.0*1e-3,scale = 1e-3,
                      unit="ms"),"MOT_driver")
        
        self.setattr_argument("Bottom_current_amplitude",NumberValue(0.0,min=0.0,max=3.00,
                      unit="A"),"MOT_driver")
        
        self.setattr_argument("Bottom_delay",NumberValue(0.0,min=0.0,max=100*1e-3,scale = 1e-3,
                      unit="ms"),"MOT_driver")
        
        self.setattr_argument("Red_current_amplitude",NumberValue(0.0,min=0.0,max=3.00,
                      unit="A"),"MOT_driver")
       
        self.setattr_argument("Lin_ramp_time",NumberValue(100.0*1e-3,min=0,max=1000.00*1e-3,scale = 1e-3,
                      unit="ms"),"MOT_driver")

        
    def prepare(self):  
        
        # Prepare MOT pulse shape
        self.MC.Blackman_pulse_profile()
       
        
    @kernel    
    def run(self):
        
        self.core.reset()
        self.MC.init_DAC()
        
        # Prepare datasets
        
        
        # Main loop
        for ii in range(10):

           self.MC.Blackman_ramp_up()
           self.MC.flat()
           with parallel:
               #turn off 3D Mot
               self.BB.MOT_off()
               
               #turn on broadband red
               self.Zot.Linear_ramp()
               
               #ramp down Blue mot coils
               self.MC.Blackman_ramp_down_from_to(self.MC.A,self.Bottom_current_amplitude)
           
           delay(self.Bottom_delay)
           self.MC.Linear_ramp(self.Bottom_current_amplitude,self.Red_current_amplitude,self.Lin_ramp_time)
           delay(5*ms)
           self.Zot.zero_dac()
           delay(5*ms)
           delay(self.Red_pulse_duration)
           self.MC.Blackman_ramp_down_from_to(self.Red_current_amplitude,0.0)
           delay(250*ms) 
           
        self.MC.Zero_current()  
    