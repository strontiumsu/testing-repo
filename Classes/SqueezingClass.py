# -*- coding: utf-8 -*-
"""
Created on Mon Jan 30 18:16:29 2023

@author: sr

Desc: This file contains the class that controls all 698 aoms and methods for 3v experiment (loading, ect.)
"""

from artiq.experiment import RTIOUnderflow, EnvExperiment, BooleanValue, NumberValue, delay, ms, sequential, kernel, TInt32, parallel, us
import numpy as np
from artiq.coredevice.ad9910 import PHASE_MODE_TRACKING

import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

class _Squeezing(EnvExperiment):
    
    def build(self):
        self.setattr_device("core")
        
        ## TTLs      
        #self.setattr_device("ttl7") # for turning on bias field pulse
        self.setattr_device("ttl2") # Integrator hold
        
        
        
        ## AOMS
        
        # RF synth sources
        self.setattr_device('urukul0_cpld')
        
        # names for all our AOMs
        self.AOMs = ['CavityProbe', 'Beam2', "Beam3", "Beam4"]
       
        # default values for all params for all AOMs
        self.scales = [0.8, 0.8, 0.8, 0.8]     
        self.attens = [5.0, 4.0, 7.0, 7.0]      
        self.freqs = [100.0, 80.0, 80.0, 80.0]
   
        self.urukul_channels = [self.get_device("urukul0_ch0"),
                                self.get_device("urukul0_ch1"),
                                self.get_device("urukul0_ch2"),
                                self.get_device("urukul0_ch3")]
        
        # setting attributes to controll all AOMs       
        for i in range(len(self.AOMs)):
            AOM = self.AOMs[i]
            self.setattr_argument(f"scale_{AOM}", NumberValue(self.scales[i], min=0.0, max=0.9), "Squeezing")
            self.setattr_argument(f"atten_{AOM}", NumberValue(self.attens[i], min=1.0, max=30), "Squeezing")
            self.setattr_argument(f"freq_{AOM}", NumberValue(self.freqs[i]*1e6, min=50*1e6, max=350*1e6, scale=1e6, unit='MHz',ndecimals = 5), "Squeezing")

    #<><><><><><><>
    # AOM Functions
    #<><><><><><><>
       
    def prepare_aoms(self):
        self.scales = [self.scale_CavityProbe, self.scale_Beam2, self.scale_Beam3, 
                       self.scale_Beam4]
        
        self.attens = [self.atten_CavityProbe, self.atten_Beam2, self.atten_Beam3, 
                       self.atten_Beam4]

        self.freqs = [self.freq_CavityProbe, self.freq_Beam2, self.freq_Beam3, 
                       self.freq_Beam4]
        
        self.beams = ['CavityProbe']


    @kernel
    def init_aoms(self, on=False):
   
        delay(10*ms)
        self.urukul0_cpld.init()
        delay(10*ms)
        
        for i in range(len(self.AOMs)):
            delay(2*ms)
            ch =  self.urukul_channels[i]
            ch.init()            
            set_f = ch.frequency_to_ftw(self.freqs[i])
            set_asf = ch.amplitude_to_asf(self.scales[i])
            ch.set_mu(set_f, asf=set_asf)
            ch.set_att(self.attens[i])
            if on:
                ch.sw.on()
            else:                
                ch.sw.off()
        delay(10*ms)
     
    @kernel
    def init_ttls(self):
        delay(100*ms)
        self.ttl2.output()
        delay(5*ms)
        self.ttl2.off()
        delay(5*ms)
        
    # basic AOM methods
    @kernel
    def AOMs_on(self, AOMs):
        with parallel:
            self.ttl2.on()
            for aom in AOMs:
                self.urukul_channels[self.index_artiq(aom)].sw.on()

    @kernel
    def AOMs_off(self, AOMs):
        with parallel:
            self.ttl2.off()
            for aom in AOMs:
                self.urukul_channels[self.index_artiq(aom)].sw.off()


    @kernel        
    def set_AOM_freqs(self, freq_list): # takes in a list of tuples
        with parallel:
            for aom, freq in freq_list:
                ind = self.index_artiq(aom)
                self.freqs[ind] = freq
                ch = self.urukul_channels[ind]
                set_freq = ch.frequency_to_ftw(freq)
                set_asf = ch.amplitude_to_asf(self.scales[ind])
                ch.set_mu(set_freq, asf=set_asf)
    
    @kernel        
    def set_AOM_attens(self, atten_list):
        with parallel:
            for aom, atten in atten_list:
                ind  = self.index_artiq(aom)
                self.attens[ind] = atten
                self.urukul_channels[ind].set_att(atten)

    @kernel        
    def set_AOM_scales(self, scale_list):
        with parallel:
            for aom, scale in scale_list.items():
                ind = self.index_artiq(aom)
                self.scales[ind] = scale
                ch = self.urukul_channels[ind]
                set_freq = ch.frequency_to_ftw(self.freqs[ind])
                set_asf = ch.amplitude_to_asf(self.scales[ind])
                ch.set_mu(set_freq, asf=set_asf)

    
    @kernel
    def set_AOM_phase(self, aom_name, freq, ph, t, prof=0):
        ind = self.index_artiq(aom_name)
        self.freqs[ind] = freq
        ch = self.urukul_channels[ind]
        ch.set(freq, phase=ph, phase_mode=PHASE_MODE_TRACKING, ref_time_mu=t, profile=prof)
        
    @kernel
    def set_phase_mode(self, mode):
        self.urukul_channels[0].set_phase_mode(mode)
        self.urukul_channels[1].set_phase_mode(mode)
        self.urukul_channels[2].set_phase_mode(mode)
    
    @kernel
    def switch_profile(self, prof=0):
        self.urukul_channels[0].cpld.set_profile(prof)
        
        
    
    @kernel 
    def cavity_probe_pulse(self,t):
        self.AOMs_on(self.beams)
        delay(t)
        self.AOMs_off(self.beams)
        
    # @kernel 
    # def cavity_probe_scan(self,t,f0,f1,num):
    #     dt = t/num
    #     for step in range(int(num)):
    #         self.set_AOM_freqs([("CavityProbe",f0+((f1-f0)/t)*step*dt )])
    #         self.AOMs_on(self.beams)
    #         delay(dt)
    #         self.AOMs_off(self.beams)
        
     
    
    def index_artiq(self, aom) -> TInt32:
        for i in range(len(self.AOMs)):
            if self.AOMs[i] == aom:
                return i
        raise Exception("No AOM with that name")
        