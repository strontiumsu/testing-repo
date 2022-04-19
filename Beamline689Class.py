# -*- coding: utf-8 -*-
"""
Created on Wed Mar 30 18:37:28 2022

@author: sr
"""

from artiq.experiment import *
import numpy as np
from fit_image import Fit2DGaussParabola
   


class Beamline689(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("ttl5")
        self.setattr_device("urukul2_cpld")
    

        self.setattr_argument("Red_MOT_AOM_frequency",
            Scannable(default=[NoScan(84*1e6), RangeScan(80*1e6, 90*1e6, 10, randomize=False)],scale=1e6,
                      unit="MHz"),"Red_MOT")

        self.setattr_argument("Red_MOT_DDS_amplitude_scale",NumberValue(0.8,min=0.0,max=0.9),"Red_MOT")
        self.setattr_argument("Red_MOT_Urukul_attenuation",NumberValue(30.0,min=0.0,max=30.0),"Red_MOT")
        

        self.urukul_hmc_ref_Red_MOT = self.get_device("urukul2_ch0")
        
        self.urukul_meas = [self.get_device("urukul2_ch0")]

                  
    def set_atten(self):
        self.Red_MOT_dds_scale=self.Red_MOT_DDS_amplitude_scale
           
        self.Red_MOT_iatten=self.Red_MOT_Urukul_attenuation

        
    @kernel    
    def init_aoms(self):
        
        delay(1*ms)
        self.urukul2_cpld.init()

        self.urukul_hmc_ref_Red_MOT.init()
        self.urukul_hmc_ref_Red_MOT.set_mu(0x40000000, asf=self.urukul_hmc_ref_Red_MOT.amplitude_to_asf(self.Red_MOT_dds_scale))
        self.urukul_hmc_ref_Red_MOT.set_att(self.Red_MOT_iatten)
        self.urukul_hmc_ref_Red_MOT.sw.on()

        
        urukul_ch =self.urukul_meas[0]
        urukul_ch.init()
        fRed_MOT = self.Red_MOT_AOM_frequency.sequence[0]
        dds_ftw_Red_MOT=self.urukul_meas[0].frequency_to_ftw(fRed_MOT)
                
        urukul_ch.set_mu(dds_ftw_Red_MOT, asf=urukul_ch.amplitude_to_asf(self.Red_MOT_dds_scale))
        urukul_ch.set_att(self.Red_MOT_iatten)
        urukul_ch.sw.on()
        
        
         
        
    @kernel 
    def set_Red_MOT_aom_frequency(self, freq): 
      
        urukul_ch =self.urukul_meas[0]
        dds_ftw_Red_MOT_AOM=self.urukul_meas[0].frequency_to_ftw(freq)
        urukul_ch.set_mu(dds_ftw_Red_MOT_AOM, asf=urukul_ch.amplitude_to_asf(self.Red_MOT_dds_scale)) 
        
        
    @kernel 
    def shift_Red_MOT_aom_frequency(self, df): 
        
     
        urukul_ch =self.urukul_meas[0]
        dds_ftw_Red_MOT_AOM=self.urukul_meas[0].frequency_to_ftw(self.Red_MOT_AOM_frequency+df*1e6)
        urukul_ch.set_mu(dds_ftw_Red_MOT_AOM, asf=urukul_ch.amplitude_to_asf(self.Red_MOT_dds_scale)) 
        
#    @kernel 
#    def set_Red_MOT_broadband(self):     # Pulse the 3D MOT beams on for duration t
        
