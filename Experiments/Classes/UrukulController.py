
"""
Created on Mon Feb 14 15:48:49 2022

@author: ejporter
"""

from artiq.experiment import EnvExperiment, NumberValue, delay, ms, kernel, TInt32, parallel
import numpy as np


class _DDSController(EnvExperiment):
    def build(self, urukul_num, ch_names, default_vals):
        """Initialize the core and urukul devices."""
        self.setattr_device("core")

        self.setattr_device(f'urukul{urukul_num}_cpld')
        self.AOMs = list(ch_names)

        self.scales = default_vals['scales']
        self.freqs = default_vals['freqs']
        self.attens = default_vals['attens']

        self.urukul_channels = [self.get_device(f"urukul{urukul_num}_ch{i}") for i in range(4)]

        for i in range(len(self.AOMs)):
            AOM = self.AOMs[i]
            self.setattr_argument(f"scale_{AOM}", NumberValue(self.scales[i], min=0.0, max=0.9), f"{AOM}_AOMs")
            self.setattr_argument(f"atten_{AOM}", NumberValue(self.attens[i], min=1.0, max=30), f"{AOM}_AOMs")
            self.setattr_argument(f"freq_{AOM}", NumberValue(self.freqs[i]*1e6, min=50*1e6, max=350*1e6, scale=1e6, unit='MHz'),  f"{AOM}_AOMs")

    def prepare_aoms(self):
        raise Exception("prepare_aoms() not implemented")
         # Child classes MUST override this method

    @kernel
    def init_aoms(self, on=False):

        delay(10*ms)
        self.urukul1_cpld.init()

        for i in range(len(self.AOMs)):
            delay(10*ms)

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
        delay(10*ms)
