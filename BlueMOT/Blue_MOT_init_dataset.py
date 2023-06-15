# -*- coding: utf-8 -*-
"""
Created on Thu Feb 17 16:42:49 2022

@author: sr
"""

import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from artiq.experiment import *
import numpy as np    


class Blue_MOT_init_dataset(EnvExperiment):

    def build(self):
         self.setattr_device("core")
         # 3D MOT
         self.setattr_argument("MOT3D_loading_frequency", NumberValue(90*1e6,min=10.0*1e6,max=200.00*1e6,scale=1e6,
                          unit="MHz"),"3D MOT") 
         self.setattr_argument("MOT3D_detection_frequency", NumberValue(100*1e6,min=10.0*1e6,max=200.00*1e6,scale=1e6,
                          unit="MHz"),"3D MOT")
         self.setattr_argument("MOT3D_attenuation", NumberValue(6.0,min=1.0,max=30.0),"3D MOT")
         self.setattr_argument("MOT3D_DDS_amplitude_scale", NumberValue(0.8,min=0.0,max=0.9),"3D MOT")
         
         # 2D MOT
         self.setattr_argument("MOT2D_loading_frequency", NumberValue(105*1e6,min=10.0*1e6,max=200.00*1e6,scale=1e6,
                          unit="MHz"),"2D MOT") 
         self.setattr_argument("MOT2D_attenuation", NumberValue(6.0,min=1.0,max=30.0),"2D MOT")
         self.setattr_argument("MOT2D_DDS_amplitude_scale", NumberValue(0.8,min=0.0,max=0.9),"2D MOT")
         
         # Zeeman
         self.setattr_argument("Zeeman_loading_frequency", NumberValue(350.*1e6,min=325.*1e6,max=370.*1e6,scale=1e6,
                          unit="MHz"),"Zeeman") 
         self.setattr_argument("Zeeman_attenuation", NumberValue(13.5,min=1.0,max=30.0),"Zeeman")
         self.setattr_argument("Zeeman_DDS_amplitude_scale", NumberValue(0.8,min=0.0,max=0.9),"Zeeman")
         
         # Push
         self.setattr_argument("Probe_push_frequency", NumberValue(40.*1e6,min=30*1e6,max=50.*1e6,scale=1e6,
                          unit="MHz"),"Probe")
         
    @kernel    
    def run(self):
         self.core.reset()
         self.set_dataset("blue_MOT.f_load3D", self.MOT3D_loading_frequency, broadcast=True, persist=True)
         self.set_dataset("blue_MOT.f_detect", self.MOT3D_detection_frequency, broadcast=True, persist=True)
         self.set_dataset("blue_MOT.attenuation3D",self.MOT3D_attenuation, broadcast=True, persist=True)
         self.set_dataset("blue_MOT.amplitude_scale3D",self.MOT3D_DDS_amplitude_scale, broadcast=True, persist=True)
         
         self.set_dataset("blue_MOT.f_load2D", self.MOT2D_loading_frequency, broadcast=True, persist=True)
         self.set_dataset("blue_MOT.attenuation2D",self.MOT2D_attenuation, broadcast=True, persist=True)
         self.set_dataset("blue_MOT.amplitude_scale2D",self.MOT2D_DDS_amplitude_scale, broadcast=True, persist=True)
         
         self.set_dataset("blue_MOT.f_loadZeeman", self.Zeeman_loading_frequency, broadcast=True, persist=True)
         self.set_dataset("blue_MOT.attenuationZeeman",self.Zeeman_attenuation, broadcast=True, persist=True)
         self.set_dataset("blue_MOT.amplitude_scaleZeeman",self.Zeeman_DDS_amplitude_scale, broadcast=True, persist=True)
         
         self.set_dataset("blue_MOT.f_push", self.Probe_push_frequency, broadcast=True, persist=True)
         
