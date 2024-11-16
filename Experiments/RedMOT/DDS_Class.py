# -*- coding: utf-8 -*-
"""
Created on Tue Nov 12 16:38:22 2024

@author: ejporter
"""

from artiq import *

class _DDS_Class(EnvExperiment):
    """
    A class to control DDS channels on an Urukul device.

    Attributes:
        urukul (str): The Urukul instance identifier (e.g., 'urukul0').
        AOMs (list): List of AOM names.
        scales (list): List of scale values for each AOM.
        attens (list): List of attenuation values for each AOM.
        freqs (list): List of frequency values (in Hz) for each AOM.
    """
    
    def build(self, urukul, AOMs, scales, attens, freqs, channels = [0,1,2,3]):
        
        try:
            assert len(channels) == len(AOMs) == len(scales) == len(attens) == len(freqs)
            self.urukul = urukul
            self.channels = channels
            
            self.setattr_device("core")
            self.setattr_device(f"{self.urukul}_cpld")
            self.urukul_cpld = self.get_device(f"{self.urukul}_cpld")
            
    
            self.urukul_channels = [self.get_device(f"{self.urukul}_ch{i}") for i in channels]
            
            self.AOMs = AOMs
            self.scales = scales
            self.attens = attens
            self.freqs = freqs
            self.index_dict = {}
            for ch, aom in zip(channels, AOMs):
                self.index_dict[ch] = aom
            # setting attributes to controll all AOMs
            
            for AOM, scale, atten, freq in zip(self.AOMs, self.scales, self.attens, self.freqs):
                self.setattr_argument(f"scale_{AOM}", NumberValue(scale, min=0.0, max=0.9), f"{AOM}_AOMs")
                self.setattr_argument(f"atten_{AOM}", NumberValue(atten, min=1.0, max=30), f"{AOM}_AOMs")
                self.setattr_argument(f"freq_{AOM}", NumberValue(freq*1e6, min=0.1000*1e6, max=350.0000*1e6, scale=1e6, unit='MHz'),  f"{AOM}_AOMs")
            
        except Exception as e:
            raise RuntimeError(f"Error in build method: {e}")
        
    def prepare_channels(self):
        self.scales = [self.getattr(self, f"scale_{AOM}") for AOM in self.AOMs]
        self.attens = [self.getattr(self, f"atten_{AOM}") for AOM in self.AOMs]
        self.freqs = [self.getattr(self, f"freq_{AOM}") for AOM in self.AOMs]
    
    @kernel
    def init_channels(self, on=False):
        delay(50*ms)
        self.urukul_cpld.init()
        for i in range(len(self.AOMs)):
            ch = self.urukul_channels[i]
            ch.init()

            set_f = ch.frequency_to_ftw(self.freqs[i])
            set_asf = ch.amplitude_to_asf(self.scales[i])
            ch.set_mu(set_f, asf=set_asf)
            ch.set_att(self.attens[i])
            
            if on:
                ch.sw.on()
            else:
                ch.sw.off()
        delay(50*ms)
      
    @kernel
    def AOMs_on(self, AOMs):
        if AOMs == 'all':
            AOMs = self.AOMs
        with parallel:
           for aom in AOMs:
               self.urukul_channels[self.index_dict[aom]].sw.on()
        
    @kernel
    def AOMs_off(self, AOMs):
        if AOMs == 'all':
            AOMs = self.AOMs
        with parallel:
           for aom in AOMs:
               self.urukul_channels[self.index_dict[aom]].sw.off()
    
        
    
    
    
