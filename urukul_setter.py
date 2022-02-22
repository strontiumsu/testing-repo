# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 14:09:47 2021

@author: sr
"""

from artiq.experiment import *
import numpy as np
from fit_image import Fit2DGaussParabola
   


class UrukulSetter(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("ttl5")
        self.setattr_device("urukul0_cpld")
    
        # Probe AOMs
        self.setattr_argument("Probe0_AOM_frequency",
            Scannable(default=[NoScan(230*1e6), RangeScan(210*1e6, 250*1e6, 10, randomize=False)],scale=1e6,
                      unit="MHz"),"Probe0")

        self.setattr_argument("Probe0_DDS_amplitude_scale",NumberValue(0.8,min=0.0,max=0.9),"Probe0")
        self.setattr_argument("Probe0_Urukul_attenuation",NumberValue(30.0,min=0.0,max=30.0),"Probe0")
     
        
        self.setattr_argument("Probe1_AOM_frequency",
            Scannable(default=[NoScan(100*1e6), RangeScan(75*1e6, 125*1e6, 10, randomize=False)],scale=1e6,
                      unit="MHz"),"Probe1")

        self.setattr_argument("Probe1_DDS_amplitude_scale",NumberValue(0.8,min=0.0,max=0.8),"Probe1")
        self.setattr_argument("Probe1_Urukul_attenuation",NumberValue(30.0,min=1.0,max=30.0),"Probe1")
        
        
        # 3D MOT AOM
        
        self.setattr_argument("MOT_AOM_frequency",
            Scannable(default=[NoScan(100*1e6), RangeScan(75*1e6, 125*1e6, 10, randomize=False)],scale=1e6,
                      unit="MHz"),"MOT")

        self.setattr_argument("MOT_DDS_amplitude_scale",NumberValue(0.8,min=0.0,max=0.8),"MOT")
        self.setattr_argument("MOT_Urukul_attenuation",NumberValue(30.0,min=1.0,max=30.0),"MOT")
        
        
        # Urukul clock output syntonized to the RTIO clock.
        # Can be used as HMC830 reference on Sayma RTM.
        # When using this reference, Sayma must be recalibrated every time Urukul
        # is rebooted, as Urukul is not synchronized to the Kasli.
        self.urukul_hmc_ref_probe0 = self.get_device("urukul0_ch0")
        self.urukul_hmc_ref_probe1 = self.get_device("urukul0_ch1")
        self.urukul_hmc_ref_MOT = self.get_device("urukul0_ch2")
        
        self.urukul_meas = [self.get_device("urukul0_ch" + str(i)) for i in range(3)]
        # The same waveform is output on all first 4 SAWG channels (first DAC).
        #self.flist = [i for i in range(140,240)]
       
       
        
    def prepare(self):
     
           #print(self.AOM_frequency.sequence)
           self.probe0_dds_scale=self.Probe0_DDS_amplitude_scale
           self.probe1_dds_scale=self.Probe1_DDS_amplitude_scale
           self.MOT_dds_scale=self.MOT_DDS_amplitude_scale
           
           self.probe0_iatten=self.Probe0_Urukul_attenuation
           self.probe1_iatten=self.Probe1_Urukul_attenuation
           self.MOT_iatten=self.MOT_Urukul_attenuation
           
         
                  
    @kernel
    def run(self):
        #flist = range(140,240)
        #for df in range(200):
        #atten = [0.0,1.0,2.0,3.0,4.0,5.0,6.0,7.0,8.0,9.0,10.0,11.0,12.0]
        #for iatten in atten:
            
            self.core.reset()
            delay(1*ms)
            self.urukul0_cpld.init()


            delay(1*ms)
            self.urukul_hmc_ref_probe0.init()
            self.urukul_hmc_ref_probe0.set_mu(0x40000000, asf=self.urukul_hmc_ref_probe0.amplitude_to_asf(self.probe0_dds_scale))
            self.urukul_hmc_ref_probe0.set_att(self.probe0_iatten)
            self.urukul_hmc_ref_probe0.sw.on()
            
            delay(1*ms)
            
            self.urukul_hmc_ref_probe1.init()
            self.urukul_hmc_ref_probe1.set_mu(0x40000000, asf=self.urukul_hmc_ref_probe1.amplitude_to_asf(self.probe1_dds_scale))
            self.urukul_hmc_ref_probe1.set_att(self.probe1_iatten)
            self.urukul_hmc_ref_probe1.sw.on()
            
            delay(1*ms)
            
            self.urukul_hmc_ref_MOT.init()
            self.urukul_hmc_ref_MOT.set_mu(0x40000000, asf=self.urukul_hmc_ref_MOT.amplitude_to_asf(self.MOT_dds_scale))
            self.urukul_hmc_ref_MOT.set_att(self.MOT_iatten)
            self.urukul_hmc_ref_MOT.sw.on()
            
            
    
            fprobe0 = self.Probe0_AOM_frequency.sequence[0]
            dds_ftw_probe0=self.urukul_meas[0].frequency_to_ftw(fprobe0)
            
            urukul_ch =self.urukul_meas[0]
            delay(1*ms)
            urukul_ch.init()
            urukul_ch.set_mu(dds_ftw_probe0, asf=urukul_ch.amplitude_to_asf(self.probe0_dds_scale))
            urukul_ch.set_att(self.probe0_iatten)
            urukul_ch.sw.on()
         
            fprobe1 = self.Probe1_AOM_frequency.sequence[0]
            dds_ftw_probe1=self.urukul_meas[0].frequency_to_ftw(fprobe1)
            
            urukul_ch =self.urukul_meas[1]
            delay(1*ms)
            urukul_ch.init()
            urukul_ch.set_mu(dds_ftw_probe1, asf=urukul_ch.amplitude_to_asf(self.probe1_dds_scale))
            urukul_ch.set_att(self.probe1_iatten)
            urukul_ch.sw.on() 
         
            fMOT = self.MOT_AOM_frequency.sequence[0]
            dds_ftw_MOT=self.urukul_meas[2].frequency_to_ftw(fMOT)
            urukul_ch =self.urukul_meas[2]
            delay(1*ms)
            urukul_ch.init()
            urukul_ch.set_mu(dds_ftw_MOT, asf=urukul_ch.amplitude_to_asf(self.MOT_dds_scale))
            urukul_ch.set_att(self.MOT_iatten)
            urukul_ch.sw.on() 
            
        
   
                        