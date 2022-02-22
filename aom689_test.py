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
   


class AOM689Test(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("ttl5")
        self.setattr_device("urukul1_cpld")
    
        # Probe AOMs
        self.setattr_argument("Probe_AOM_frequency",
            Scannable(default=[NoScan(84*1e6), RangeScan(80*1e6, 90*1e6, 10, randomize=False)],scale=1e6,
                      unit="MHz"),"Probe")

        self.setattr_argument("Probe_DDS_amplitude_scale",NumberValue(0.8,min=0.0,max=0.9),"Probe")
        self.setattr_argument("Probe_Urukul_attenuation",NumberValue(30.0,min=0.0,max=30.0),"Probe")
        
        
        
        
        # Urukul clock output syntonized to the RTIO clock.
        # Can be used as HMC830 reference on Sayma RTM.
        # When using this reference, Sayma must be recalibrated every time Urukul
        # is rebooted, as Urukul is not synchronized to the Kasli.
        self.urukul_hmc_ref_probe = self.get_device("urukul1_ch2")

        
        self.urukul_meas = [self.get_device("urukul1_ch" + str(i)) for i in range(3)]
        # The same waveform is output on all first 4 SAWG channels (first DAC).
        #self.flist = [i for i in range(140,240)]
       
       
        
    def prepare(self):
     
           #print(self.AOM_frequency.sequence)
           self.probe_dds_scale=self.Probe_DDS_amplitude_scale
           
           self.probe_iatten=self.Probe_Urukul_attenuation

           
         
                  
    @kernel
    def run(self):
        #flist = range(140,240)
        #for df in range(200):
        #atten = [0.0,1.0,2.0,3.0,4.0,5.0,6.0,7.0,8.0,9.0,10.0,11.0,12.0]
        #for iatten in atten:
            
            self.core.reset()
            delay(1*ms)
            self.urukul1_cpld.init()


            delay(1*ms)
            self.urukul_hmc_ref_probe.init()
            self.urukul_hmc_ref_probe.set_mu(0x40000000, asf=self.urukul_hmc_ref_probe.amplitude_to_asf(self.probe_dds_scale))
            self.urukul_hmc_ref_probe.set_att(self.probe_iatten)
            self.urukul_hmc_ref_probe.sw.on()
            
            
            
    
            fprobe = self.Probe_AOM_frequency.sequence[0]
            dds_ftw_probe=self.urukul_meas[0].frequency_to_ftw(fprobe)
            
            urukul_ch =self.urukul_meas[2]
            delay(1*ms)
            urukul_ch.init()
            urukul_ch.set_mu(dds_ftw_probe, asf=urukul_ch.amplitude_to_asf(self.probe_dds_scale))
            urukul_ch.set_att(self.probe_iatten)
            urukul_ch.sw.on()