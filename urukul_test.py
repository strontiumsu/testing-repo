# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 14:09:47 2021

@author: sr
"""

from artiq.experiment import *
import numpy as np

   
class urukul_test(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        #self.setattr_device("ttl4")
        self.setattr_device("urukul1_cpld")
        #self.setattr_device("zotino0")
        #self.cam=self.get_device("camera")
        
      
        self.setattr_argument("AOM_frequency",
            Scannable(default=[NoScan(100*1e6), RangeScan(175*1e6, 225*1e6, 10, randomize=False)],scale=1e6,
                      unit="MHz"),"AOM")

        self.setattr_argument("DDS_amplitude_scale",NumberValue(1.0,min=0.0,max=1.0),"AOM")
        self.setattr_argument("Urukul_attenuation",NumberValue(4.0,min=0.0,max=30.0),"AOM")
     
        # Urukul clock output syntonized to the RTIO clock.
        # Can be used as HMC830 reference on Sayma RTM.
        # When using this reference, Sayma must be recalibrated every time Urukul
        # is rebooted, as Urukul is not synchronized to the Kasli.
        self.urukul_hmc_ref = self.get_device("urukul1_ch1")

        
        self.urukul_meas = [self.get_device("urukul1_ch" + str(i)) for i in range(3)]
        # The same waveform is output on all first 4 SAWG channels (first DAC).
        #self.flist = [i for i in range(140,240)]
       
       
        
    def prepare(self):
     
      
           self.dds_scale=self.DDS_amplitude_scale
           self.iatten=self.Urukul_attenuation
           
    @kernel
    def run(self):
   
            self.core.reset()
            self.urukul1_cpld.init()
             
            
            f0 = self.AOM_frequency.sequence[0]
            dds_ftw_0=self.urukul_meas[0].frequency_to_ftw(f0) 

            delay(1*ms)
            self.urukul_hmc_ref.init()
            self.urukul_hmc_ref.set_mu(0x40000000, asf=self.urukul_hmc_ref.amplitude_to_asf(self.dds_scale))
            self.urukul_hmc_ref.set_att(self.iatten)
            self.urukul_hmc_ref.sw.on()
            
            delay(1*ms)
           
            urukul_ch =self.urukul_meas[0]
            delay(1*ms)
            urukul_ch.init()
            urukul_ch.set_mu(dds_ftw_0, asf=urukul_ch.amplitude_to_asf(self.dds_scale))
            urukul_ch.set_att(self.iatten)
            urukul_ch.sw.on()
            
            
                
 