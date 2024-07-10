#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 25 09:31:01 2024

@author: ryanclairmont
"""


import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")


from artiq.experiment import *
import numpy as np
from CoolingClass import _Cooling
   


class Atom_scattering_count(EnvExperiment): #need to change this
    def build(self):
        self.setattr_device("core")
        self.setattr_device("sampler0")
        self.adc_0=self.get_device("sampler0") 
        self.MOTs = _Cooling(self)
 
        
        #attributes for this experiment
        #which frequencies to sweep through
        self.setattr_argument("Mot_frequency", Scannable(default=[RangeScan(90*1e6, 
                     100*1e6,5, randomize=False), NoScan(97*1e6)], scale=1e6, unit="MHz"),"PD")
        
         # which powers to sweep through
        self.setattr_argument("Mot_attenuation",
            Scannable(default=[RangeScan(6.0,30.0,5, randomize=False),NoScan(6.0)],scale=1,
                      unit="dBm"),"PD")
        
        
        self.setattr_argument("samples", NumberValue(5,min=0, max=100), "PD")
        self.setattr_argument("PD_delay", NumberValue(1.0*1e-3,min=0.0*1e-3,max=100.0*1e-3,scale=1e-3,
                      unit="ms"),"PD")
        
    def prepare(self):
        # initial datasets for the aoms and mot coils, does not run on core
        self.MOTs.prepare_aoms()
        self.MOTs.prepare_coils()

        
        
        #redefine the frequency and detuning sequences
        self.dets = self.Mot_frequency.sequence
        self.attens = self.Mot_attenuation.sequence
        
    @kernel    
    def run(self):
        
        self.core.reset()
        self.MOTs.init_coils()
        self.MOTs.init_ttls() 
        self.MOTs.init_aoms(on=False) #Initialize AOMs, but don't turn on lasers yet
        
        self.adc_0.init()
        
        # shots = len(self.dets)*len(self.attens)
        shots = len(self.attens)
        self.set_dataset('V_std', [0 for _ in range(shots)], broadcast = True)
        self.set_dataset('V', [0 for _ in range(shots)], broadcast = True)
        self.set_dataset('V_std_zero', [0 for _ in range(shots)], broadcast = True)
        self.set_dataset('V_zero', [0 for _ in range(shots)], broadcast = True)

        
        # Main loop
        jj = 0
        atten_std = self.MOTs.atten_3D
        det_std = self.MOTs.freq_3D
        # for det in self.dets:
        for atten in self.attens:
            delay(700*ms)
            
            #A
            self.MOTs.set_AOM_freqs([('3D', det_std)])
            self.MOTs.set_AOM_attens([('3D', atten_std)])
            delay(10*ms)
            self.MOTs.bMOT_pulse() #creates atoms cloud  # change
            
            #turn everything on
            
            self.MOTs.AOMs_on(self.MOTs.AOMs) #should turn all the AOMS on, including 3D, 2D, and repumper
            
            self.mutate_dataset("V_std", jj, self.sample_ADC())
            delay(5*ms)
            
            #B
            
            self.MOTs.set_AOM_freqs([('3D', det_std)])
            self.MOTs.set_AOM_attens([('3D', atten)])
            
            delay(2*ms)
            self.mutate_dataset("V", jj, self.sample_ADC())
            delay(5*ms)
            
            #C (turns everything off, clears out atoms)
            
            delay(20*ms)
            self.MOTs.atom_source_off() #turns off Zeeman and 2D
            
            delay(70*ms)
            self.MOTs.AOMs_off(self.MOTs.AOMs) 
            self.MOTs.coils_off()
            
            delay(1500*ms)
            
            #D
            
            self.MOTs.AOMs_on(self.MOTs.AOMs)
            self.mutate_dataset("V_zero", jj, self.sample_ADC())
            delay(70*ms)
            
            #E
            self.MOTs.set_AOM_freqs([('3D', det_std)])
            self.MOTs.set_AOM_attens([('3D', atten_std)])
            
            delay(50*ms)
            self.mutate_dataset("V_std_zero", jj, self.sample_ADC())
            delay(50*ms)
            
            # #turn everything off
            delay(20*ms)
            self.MOTs.atom_source_off() #turns off Zeeman
            delay(50*ms)
            self.MOTs.AOMs_off(["3D", "3P0_repump", "3P2_repump"]) #difference between 2D MOT and 3D (was the 2D the one explained earlier last week, with the lattice?)
            self.MOTs.coils_off()
            jj +=1
            delay(20*ms)
        
        
        
    @kernel         
    def sample_ADC(self):
        res = 0.
        CHANNELS = 8
        dat=[0.1 for _ in range(CHANNELS)]
        for jj in range(int(self.samples)):
            self.adc_0.sample(dat)
            res += float(dat[0])
            delay(self.PD_delay)
        return res/self.samples