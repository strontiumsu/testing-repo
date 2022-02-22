# -*- coding: utf-8 -*-
"""
Created on Mon Jan 31 14:15:14 2022

@author: sr
"""


from artiq.experiment import *
import numpy as np

class BL461Essential(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("ttl5")
        self.setattr_device("urukul0_cpld")
    
        # Probe AOMs
        self.setattr_argument("Probe_AOM_frequency",
            Scannable(default=[NoScan(230*1e6), RangeScan(210*1e6, 250*1e6, 10, randomize=False)],scale=1e6,
                      unit="MHz"),"Probe")

        self.setattr_argument("Probe_DDS_amplitude_scale",NumberValue(0.8,min=0.0,max=0.9),"Probe")
        self.setattr_argument("Probe_Urukul_attenuation",NumberValue(30.0,min=0.0,max=30.0),"Probe")
        
        
        
        # MTS AOM
        self.setattr_argument("MTS_AOM_frequency",
            Scannable(default=[NoScan(100*1e6), RangeScan(75*1e6, 125*1e6, 10, randomize=False)],scale=1e6,
                      unit="MHz"),"MTS")

        self.setattr_argument("MTS_DDS_amplitude_scale",NumberValue(0.8,min=0.0,max=0.8),"MTS")
        self.setattr_argument("MTS_Urukul_attenuation",NumberValue(30.0,min=1.0,max=30.0),"MTS")
        
        
        # Urukul clock output syntonized to the RTIO clock.
        # Can be used as HMC830 reference on Sayma RTM.
        # When using this reference, Sayma must be recalibrated every time Urukul
        # is rebooted, as Urukul is not synchronized to the Kasli.
        self.urukul_hmc_ref_probe = self.get_device("urukul0_ch0")
        self.urukul_hmc_ref_MTS = self.get_device("urukul0_ch2")
        
        
        self.urukul_meas = [self.get_device("urukul0_ch0"),self.get_device("urukul0_ch2")]
        # The same waveform is output on all first 4 SAWG channels (first DAC).
        #self.flist = [i for i in range(140,240)]
       
       
        
    def prepare(self):
     
           self.probe_dds_scale=self.Probe_DDS_amplitude_scale
           self.MTS_dds_scale=self.MTS_DDS_amplitude_scale
           
           self.probe_iatten=self.Probe_Urukul_attenuation
           self.MTS_iatten=self.MTS_Urukul_attenuation
           
         
                  
    @kernel
    def run(self):
            
            self.core.reset()
            delay(1*ms)
           
            self.urukul0_cpld.init()
            

            #delay(1*ms)
            self.urukul_hmc_ref_probe.init()
            self.urukul_hmc_ref_probe.set_mu(0x40000000, asf=self.urukul_hmc_ref_probe.amplitude_to_asf(self.probe_dds_scale))
            self.urukul_hmc_ref_probe.set_att(self.probe_iatten)
            self.urukul_hmc_ref_probe.sw.on()
            
           
            
            self.urukul_hmc_ref_MTS.init()
            self.urukul_hmc_ref_MTS.set_mu(0x40000000, asf=self.urukul_hmc_ref_MTS.amplitude_to_asf(self.MTS_dds_scale))
            self.urukul_hmc_ref_MTS.set_att(self.MTS_iatten)
            self.urukul_hmc_ref_MTS.sw.on()
            
            
             
            fprobe = self.Probe_AOM_frequency.sequence[0]
            dds_ftw_probe=self.urukul_meas[0].frequency_to_ftw(fprobe)
            
            urukul_ch =self.urukul_meas[0]
            #delay(1*ms)
            urukul_ch.init()
            urukul_ch.set_mu(dds_ftw_probe, asf=urukul_ch.amplitude_to_asf(self.probe_dds_scale))
            urukul_ch.set_att(self.probe_iatten)
            urukul_ch.sw.on()
            
            
            
            fMTS = self.MTS_AOM_frequency.sequence[0]
            dds_ftw_MTS=self.urukul_meas[1].frequency_to_ftw(fMTS)
                
            urukul_ch =self.urukul_meas[1]
               # delay(0.15*ms)
            urukul_ch.init()
            urukul_ch.set_mu(dds_ftw_MTS, asf=urukul_ch.amplitude_to_asf(self.MTS_dds_scale))
            urukul_ch.set_att(self.MTS_iatten)
            urukul_ch.sw.on() 
            
            
            
            