# -*- coding: utf-8 -*-
"""
Created on Thu Feb 17 16:42:49 2022

@author: sr
"""

from artiq.experiment import *
import numpy as np    


class Blue_MOT3D_init_dataset(EnvExperiment):

    def build(self):
         self.setattr_device("core")
         # 3D MOT
         self.setattr_argument("MOT3D_loading_frequency", NumberValue(89*1e6,min=10.0*1e6,max=200.00*1e6,scale=1e6,
                          unit="MHz"),"3D MOT") 
         self.setattr_argument("MOT3D_detection_frequency", NumberValue(91*1e6,min=10.0*1e6,max=200.00*1e6,scale=1e6,
                          unit="MHz"),"3D MOT")
         self.setattr_argument("MOT3D_attenuation", NumberValue(6.0,min=1.0,max=30.0),"3D MOT")
         self.setattr_argument("MOT3D_DDS_amplitude_scale", NumberValue(0.8,min=0.0,max=0.9),"3D MOT")
         
    @kernel    
    def run(self):
         self.core.reset()
         self.set_dataset("blue_MOT.f_load", self.MOT3D_loading_frequency, broadcast=True)
         self.set_dataset("blue_MOT.f_detect", self.MOT3D_detection_frequency, broadcast=True)
         self.set_dataset("blue_MOT.attenuation",self.MOT3D_attenuation, broadcast=True)
         self.set_dataset("blue_MOT.amplitude_scale",self.MOT3D_DDS_amplitude_scale, broadcast=True)
         

         
