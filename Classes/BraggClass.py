
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
        self.AOMs = ["Dipole", 'Bragg1', 'Bragg2', "Homodyne"]
        # self.AOMs = ['Bragg1', 'Bragg2', "Homodyne1", 'Homodyne2']

        
        # default values for all params for all AOMs
        self.scales = [0.8, 0.8, 0.8, 0.8]
        
        self.attens = [14.0, 11.0, 11.0, 30.0]
        # self.attens = [18.0, 5.0, 20.0, 20.0]
        
        self.freqs = [80.0, 100.0, 100.0, 80.0]  
        # self.freqs = [110.0, 110.0, 80.00000, 200.0]  
        
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
        self.scales = [self.scale_Dipole, self.scale_Bragg1, self.scale_Bragg2, self.scale_Homodyne]
        self.attens = [self.atten_Dipole, self.atten_Bragg1, self.atten_Bragg2, self.atten_Homodyne]      
        self.freqs = [self.freq_Dipole, self.freq_Bragg1, self.freq_Bragg2, self.freq_Homodyne]
        
    @kernel
    def init_aoms(self, on=False): 
        delay(10*ms)
        self.urukul2_cpld.init()
        
        i = -1
        for ch in self.urukul_channels:
            i += 1
            delay(10*ms)
            ch.init()            
            ch.set(self.freqs[i], amplitude=self.scales[i])
            ch.set_att(self.attens[i])
            
            if on: ch.sw.on()
            else: ch.sw.off()
        delay(10 * ms)
            
        
    # basic AOM methods
    @kernel
    def AOMs_on(self, AOMs):
        with parallel:
            for aom in AOMs:
                self.urukul_channels[self.index_artiq(aom)].sw.on()

    @kernel
    def AOMs_off(self, AOMs):
        with parallel:
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
                ind = self.index_artiq(aom)
                self.attens[ind] = atten
                self.urukul_channels[ind].set_att(atten)

    
    @kernel        
    def set_AOM_scales(self, scale_list):
        with parallel:
            for aom, scale in scale_list:
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
        self.urukul_channels[3].set_phase_mode(mode)
    @kernel
    def switch_profile(self, prof=0):
        self.urukul_channels[0].cpld.set_profile(prof)
 
    @kernel
    def bragg_pulse(self,time):
        self.AOMs_on(["Bragg2", "Bragg1"])        
        delay(time)
        self.AOMs_off(["Bragg2", "Bragg1"])
        
    
    def index_artiq(self, aom) -> TInt32:
        for i in range(len(self.AOMs)):
            if self.AOMs[i] == aom:
                return i
        raise Exception("No AOM with that name")