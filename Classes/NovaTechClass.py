# -*- coding: utf-8 -*-
"""
Created on Thu Jan 12 09:32:14 2023

@author: sr
"""

from artiq.experiment import *

class _NovaTech(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.nova = self.get_device("novatech409b")
    
    def setup(self):
        self.nova.setup()
    
    def close(self):
        self.nova.close()
        
    def reset(self):
        self.nova.reset()
    
    def set_phase_continuous(self, is_cont):
        self.nova.set_phase_continuous(is_cont)
        
    def set_simultaneous_update(self, sim):
        self.nova.set_simultaneous_update(sim)
        
    def do_simultaneous_update(self):
        self.nova.do_simultaneous_update()
        
   
    def set_freq(self, channel, freq):
        self.nova.set_freq(channel, freq)
        
    def set_gain(self, channel, gain):
        self.nova.set_gain(channel, gain)
        
    def set_phase(self, channel, phase):
        self.nova.set_phase(channel, phase)
        
   
        
   
        
    