# -*- coding: utf-8 -*-
"""
Created on Tue Sep 21 11:34:31 2021

@author: sr
"""

# -*- coding: utf-8 -*-
"""
Created on Fri Aug 13 10:37:36 2021

@author: sr
"""

from artiq.experiment import *
import numpy as np
from fit_image import Fit2DGaussParabola
   


class AOM689_dual_Test(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("ttl5")
        self.setattr_device("urukul1_cpld")
    
        # Tone 1 
        self.setattr_argument("t1_frequency",
            Scannable(default=[NoScan(84*1e6), RangeScan(60*1e6, 110*1e6, 10, randomize=False)],scale=1e6,
                      unit="MHz"),"Tone_1")

        self.setattr_argument("t1_amplitude_scale",NumberValue(0.8,min=0.0,max=0.9),"Tone_1")
        self.setattr_argument("t1_attenuation",NumberValue(30.0,min=0.0,max=30.0),"Tone_1")
        
        # Tone 2
        self.setattr_argument("t2_frequency",
            Scannable(default=[NoScan(84*1e6), RangeScan(60*1e6, 110*1e6, 10, randomize=False)],scale=1e6,
                      unit="MHz"),"Tone_2")

        self.setattr_argument("t2_amplitude_scale",NumberValue(0.8,min=0.0,max=0.9),"Tone_2")
        self.setattr_argument("t2_attenuation",NumberValue(30.0,min=0.0,max=30.0),"Tone_2")
        
        
        
        # Urukul clock output syntonized to the RTIO clock.
        # Can be used as HMC830 reference on Sayma RTM.
        # When using this reference, Sayma must be recalibrated every time Urukul
        # is rebooted, as Urukul is not synchronized to the Kasli.
        self.urukul_hmc_ref_t1 = self.get_device("urukul1_ch2")
        self.urukul_hmc_ref_t2 = self.get_device("urukul1_ch3")
        
        self.urukul_meas = [self.get_device("urukul1_ch" + str(i)) for i in range(4)]
        # The same waveform is output on all first 4 SAWG channels (first DAC).
        #self.flist = [i for i in range(140,240)]
       
       
        
    def prepare(self):
     
           #print(self.AOM_frequency.sequence)
           self.t1_dds_scale=self.t1_amplitude_scale
           self.t1_iatten=self.t1_attenuation
           
           self.t2_dds_scale=self.t2_amplitude_scale
           self.t2_iatten=self.t2_attenuation

           
         
                  
    @kernel
    def run(self):
        #flist = range(140,240)
        #for df in range(200):
        #atten = [0.0,1.0,2.0,3.0,4.0,5.0,6.0,7.0,8.0,9.0,10.0,11.0,12.0]
        #for iatten in atten:
            
            self.core.reset()
            delay(1*ms)
            self.urukul1_cpld.init()


            delay(2*ms)
            self.urukul_hmc_ref_t1.init()
            self.urukul_hmc_ref_t1.set_mu(0x40000000, asf=self.urukul_hmc_ref_t1.amplitude_to_asf(self.t1_dds_scale))
            self.urukul_hmc_ref_t1.set_att(self.t1_iatten)
            self.urukul_hmc_ref_t1.sw.on()
            
            delay(1*ms)
            self.urukul_hmc_ref_t2.init()
            self.urukul_hmc_ref_t2.set_mu(0x40000000, asf=self.urukul_hmc_ref_t2.amplitude_to_asf(self.t2_dds_scale))
            self.urukul_hmc_ref_t2.set_att(self.t2_iatten)
            self.urukul_hmc_ref_t2.sw.on()
            
            
    
            ft1 = self.t1_frequency.sequence[0]
            dds_ftw_t1=self.urukul_meas[0].frequency_to_ftw(ft1)
            
            urukul_ch =self.urukul_meas[2]
            delay(1*ms)
            urukul_ch.init()
            urukul_ch.set_mu(dds_ftw_t1, asf=urukul_ch.amplitude_to_asf(self.t1_dds_scale))
            urukul_ch.set_att(self.t1_iatten)
            urukul_ch.sw.on()
            
            ft2 = self.t2_frequency.sequence[0]
            dds_ftw_t2=self.urukul_meas[0].frequency_to_ftw(ft2)
            
            urukul_ch =self.urukul_meas[3]
            delay(1*ms)
            urukul_ch.init()
            urukul_ch.set_mu(dds_ftw_t2, asf=urukul_ch.amplitude_to_asf(self.t2_dds_scale))
            urukul_ch.set_att(self.t2_iatten)
            urukul_ch.sw.on()