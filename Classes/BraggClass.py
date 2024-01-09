
"""
Created on Mon Feb 14 15:48:49 2022

@author: sr

Functions:

Controls some aspects of the HCDL lock setup    
Sets the parameters of the HCDL MTS AOM and double-pass AOM before the HDCL setup

"""

from artiq.experiment import EnvExperiment, NumberValue, delay, ms, kernel, TInt32, parallel
import numpy as np

from artiq.coredevice.ad9910 import PHASE_MODE_TRACKING

class _Bragg(EnvExperiment):
      
    
    def build(self):
        self.setattr_device("core")        
        self.setattr_device("urukul2_cpld")
        
        
        # names for all our AOMs
        self.AOMs = ['Bragg1', 'Bragg2', "Homodyne1", 'Homodyne2']

        
        # default values for all params for all AOMs
        self.scales = [0.8, 0.8, 0.8, 0.8]
        
        self.attens = [18.0, 5.0, 20.0, 20.0]
        
        self.freqs = [110.0, 110.0, 80.00000, 200.0]  
        
        self.urukul_channels = [self.get_device("urukul2_ch0"),
                                self.get_device("urukul2_ch1"),
                                self.get_device("urukul2_ch2"),
                                self.get_device("urukul2_ch3")]

        # setting attributes to controll all AOMs       
        for i in range(len(self.AOMs)):
            AOM = self.AOMs[i]
            self.setattr_argument(f"scale_{AOM}", NumberValue(self.scales[i], min=0.0, max=0.9), f"{AOM}_AOMs")
            self.setattr_argument(f"atten_{AOM}", NumberValue(self.attens[i], min=1.0, max=30), f"{AOM}_AOMs")
            self.setattr_argument(f"freq_{AOM}", NumberValue(self.freqs[i]*1e6, min=50.0000*1e6, max=350.0000*1e6, scale=1e6, unit='MHz'),  f"{AOM}_AOMs")
        
        
    def prepare_aoms(self):
        self.scales = [self.scale_Bragg1, self.scale_Bragg2, self.scale_Homodyne1, self.scale_Homodyne2]
        self.attens = [self.atten_Bragg1, self.atten_Bragg2, self.atten_Homodyne1, self.atten_Homodyne2]      
        self.freqs = [self.freq_Bragg1, self.freq_Bragg2, self.freq_Homodyne1, self.freq_Homodyne2]
        #self.freqs = [self.freq_Bragg1, self.freq_Bragg2, 80*1e6, 79.999999*1e6]
        
    @kernel
    def init_aoms(self, on=False): 
        delay(10*ms)
        self.urukul2_cpld.init()

        for i in range(len(self.AOMs)):
            delay(10*ms)
           
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
            
        
    # basic AOM methods
    @kernel
    def AOMs_on(self, AOMs):
        for aom in AOMs:
            print(self.index_artiq(aom))
            ch = self.urukul_channels[self.index_artiq(aom)]
            ch.sw.on()
            #delay(0.5*ms)
    @kernel
    def AOMs_off(self, AOMs):
        for aom in AOMs:
            self.urukul_channels[self.index_artiq(aom)].sw.off()
            # delay(2*ms)
    @kernel        
    def set_AOM_freqs(self, freq_list): # takes in a list of tuples
        for aom, freq in freq_list:
            ind = self.index_artiq(aom)
            self.freqs[ind] = freq
            ch = self.urukul_channels[ind]
            set_freq = ch.frequency_to_ftw(freq)
            set_asf = ch.amplitude_to_asf(self.scales[ind])
            ch.set_mu(set_freq, asf=set_asf)

    def get_AOM_freqs(self):
        return self.freqs
    
    @kernel        
    def set_AOM_attens(self, atten_list):
        for aom, atten in atten_list:
            ind = self.index_artiq(aom)
            self.attens[ind] = atten
            self.urukul_channels[ind].set_att(atten)

    def get_AOM_attens(self):
        return self.attens
    
    @kernel        
    def set_AOM_scales(self, scale_list):
        for aom, scale in scale_list:
            ind = self.index_artiq(aom)
            self.scales[ind] = scale
            ch = self.urukul_channels[ind]
            set_freq = ch.frequency_to_ftw(self.freqs[ind])
            set_asf = ch.amplitude_to_asf(self.scales[ind])
            ch.set_mu(set_freq, asf=set_asf)

    def get_AOM_scales(self):
        return self.scales
    
    
    @kernel
    def bragg_pulse(self,time):
        self.AOMs_on(self.AOMs)
        self.hold(time)
        self.AOMs_off(self.AOMs)
        
    
    def index_artiq(self, aom) -> TInt32:
        for i in range(len(self.AOMs)):
            if self.AOMs[i] == aom:
                return i
        raise Exception("No AOM with that name")