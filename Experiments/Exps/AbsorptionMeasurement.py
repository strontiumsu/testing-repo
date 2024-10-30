# -*- coding: utf-8 -*-
"""
Created on Thu Jan 11 16:05:45 2024

@author: E. Porter
"""


from artiq.experiment import EnvExperiment, BooleanValue, kernel, us, ms, NumberValue, delay, parallel, sequential, RTIOUnderflow

# imports
import numpy as np
from CoolingClass import _Cooling
from CameraClass import _Camera



## pseudocode

## generate Blue MOT.
## drop atoms
## wait small time with repumpers on ~200 us
## turn on profiler exposure
## flash blue light
## exposure ends
## collect image
## shift frequency


class AbsorptionMeasurementExp(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.MOTs = _Cooling(self)
        self.setattr_device("ttl4")
        self.Camera = _Camera(self)
        
        #set attributes here
        
    def prepare(self):
        
        self.MOTs.prepare_aoms(10)
        self.MOTs.prepare_coils()
        self.Camera.camera_init()
        
    @kernel
    def run(self):
        self.core.reset()
        #self.ttl4.off()
        self.MOTs.init_coils()
        self.MOTs.init_ttls()
        self.MOTs.init_aoms(on=False)
        
        if 0:
            self.MOTs.take_background_image_exp(self.Camera)
            delay(100*ms)
            for i in range(25):
            
                self.Camera.arm()
                delay(200*ms)
                
                self.MOTs.AOMs_off(["Probe"])
                
                delay(100*ms)
                self.MOTs.bMOT_load()
                self.MOTs.atom_source_off()
                self.MOTs.AOMs_off(["3D"])
                
                delay(0.2*ms)
                self.MOTs.AOMs_off(["3P0_repump", "3P2_repump"])
                self.MOTs.coils_off()
                with parallel:
                    with sequential:
                        self.MOTs.take_MOT_image(self.Camera)
                    with sequential:
                        delay(0.2*ms)
                        self.MOTs.AOMs_on(['Probe'])
                        delay(1000*us)
                        self.MOTs.AOMs_off(['Probe'])
                
                delay(50*ms)
                self.Camera.process_image(save=True, name='', bg_sub=True)
                delay(200*ms)
                
        else:
            self.MOTs.AOMs_off(["Probe"])
            
            delay(100*ms)
            self.MOTs.bMOT_load()
            self.MOTs.atom_source_off()
            self.MOTs.AOMs_off(["3D"])
            
            delay(0.2*ms)
            self.MOTs.AOMs_off(["3P0_repump", "3P2_repump"])
            
            #delay(0.2*ms)
            self.ttl4.on()
            delay(1*ms)
            self.MOTs.AOMs_on(['Probe'])
            delay(100*us)
            self.MOTs.AOMs_off(['Probe'])
            delay(10*ms)
            self.ttl4.off()
            self.MOTs.coils_off()
            
            delay(200*ms)
        