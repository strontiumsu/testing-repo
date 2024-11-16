# -*- coding: utf-8 -*-
"""
Created on Tue Nov 12 16:01:44 2024

@author: ejporter
"""

from artiq.experiment import *
import numpy as np


class _UrukulClass(EnvExperiment):


    def build(self):
        self.setattr_device("core")
        self.setattr_device("urukul0_cpld")


        # names for all our AOMs
        self.AOMs = ["Sideband", 'Push', 'AI1', "AI2"]

        # default values for all params for all AOMs
        self.scales = [0.8, 0.8, 0.8, 0.8]
        self.attens = [10.0, 10.0, 10.0, 10.0]
        self.freqs = [4.0, 80.0, 80.0, 80.0]



        self.urukul_channels = [self.get_device("urukul0_ch0"),
                                self.get_device("urukul0_ch1"), 
                                self.get_device("urukul0_ch2"),
                                self.get_device("urukul0_ch3")]

        # setting attributes to controll all AOMs
        for i in range(len(self.AOMs)):
            AOM = self.AOMs[i]
            self.setattr_argument(f"scale_{AOM}", NumberValue(self.scales[i], min=0.0, max=0.9), f"{AOM}_AOMs")
            self.setattr_argument(f"atten_{AOM}", NumberValue(self.attens[i], min=1.0, max=30), f"{AOM}_AOMs")
            self.setattr_argument(f"freq_{AOM}", NumberValue(self.freqs[i]*1e6, min=0.1000*1e6, max=350.000*1e6, scale=1e6, unit='MHz'),  f"{AOM}_AOMs")


    def prepare_aoms(self):
        self.scales = [self.scale_Dipole, self.scale_Bragg1, self.scale_Bragg2, self.scale_Homodyne]
        self.attens = [self.atten_Dipole, self.atten_Bragg1, self.atten_Bragg2, self.atten_Homodyne]
        self.freqs = [self.freq_Dipole, self.freq_Bragg1, self.freq_Bragg2, self.freq_Homodyne]

    @kernel
    def init_aoms(self, on=False):
        delay(50*ms)
        self.urukul0_cpld.init()
        for i in range(len(self.AOMs)):
            delay(1*ms)

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



    def index_artiq(self, aom) -> TInt32:
        for i in range(len(self.AOMs)):
            if self.AOMs[i] == aom:
                return i
        raise Exception("No AOM with that name")
