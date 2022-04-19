# -*- coding: utf-8 -*-
"""
Created on Tue Mar 15 19:05:09 2022

@author: sr
"""


from artiq.experiment import *
import numpy as np     

class DipoleTrap(EnvExperiment):
      
    
    def build(self):
        
        self.setattr_device("urukul2_cpld")
        
        
        # 3D MOT AOM  
        self.setattr_argument("Dipole_AOM_frequency",
            NumberValue(90*1e6, min= 90*1e6, max = 110*1e6,scale=1e6, unit="MHz"),"Dipole")
        self.setattr_argument("Dipole_DDS_amplitude_scale",NumberValue(0.8,min=0.0,max=0.8),"Dipole")
        self.setattr_argument("Dipole_Urukul_attenuation",NumberValue(6.0,min=1.0,max=30.0),"Dipole")
        
      
        self.urukul_hmc_ref_Dipole = self.get_device("urukul2_ch3")
        
        self.urukul_meas = [self.get_device("urukul2_ch3")]
        

    def set_atten_Dipole(self):   # set the DDS amplitude and attenuation for the Zeeman slower only
        self.DipoleZeeman_dds_scale=self.Dipole_DDS_amplitude_scale
        self.Dipole_iatten=self.Dipole_Urukul_attenuation
    
    def set_atten(self):
        self.Dipole_dds_scale=self.Dipole_DDS_amplitude_scale
        self.Dipole_iatten=self.Dipole_Urukul_attenuation
        
    @kernel    
    def init_aoms(self):
        
        delay(1*ms)
        self.urukul2_cpld.init()

        self.urukul_hmc_ref_Dipole.init()
        self.urukul_hmc_ref_Dipole.set_mu(0x40000000, asf=self.urukul_hmc_ref_Dipole.amplitude_to_asf(self.Dipole_dds_scale))
        self.urukul_hmc_ref_Dipole.set_att(self.Dipole_iatten)
        self.urukul_hmc_ref_Dipole.sw.on()
            

        urukul_ch =self.urukul_meas[0]
        urukul_ch.init()
        fDipole = self.Dipole_AOM_frequency
        dds_ftw_Dipole=self.urukul_meas[0].frequency_to_ftw(fDipole)
                
        urukul_ch.set_mu(dds_ftw_Dipole, asf=urukul_ch.amplitude_to_asf(self.Dipole_dds_scale))
        urukul_ch.set_att(self.Dipole_iatten)
        urukul_ch.sw.on()
    
        
    @kernel 
    def set_Dipole_aom_frequency(self, freq): 
      
        urukul_ch =self.urukul_meas[0]
        dds_ftw_Dipole_AOM=self.urukul_meas[0].frequency_to_ftw(freq)
        urukul_ch.set_mu(dds_ftw_Dipole_AOM, asf=urukul_ch.amplitude_to_asf(self.Dipole_dds_scale)) 
        
    @kernel 
    def shift_Dipole_aom_frequency(self,df): 
      
        
        urukul_ch =self.urukul_meas[0]
        dds_ftw_Dipole_AOM=self.urukul_meas[0].frequency_to_ftw(self.Dipole_AOM_frequency + df*1e6)
        urukul_ch.set_mu(dds_ftw_Dipole_AOM, asf=urukul_ch.amplitude_to_asf(self.Dipole_dds_scale)) 
        
        
    @kernel 
    def pulse_Dipole(self,t):     # Pulse the 3D MOT beams on for duration t
        urukul_ch =self.urukul_meas[0]
        urukul_ch.sw.on()  
        delay(t)
        urukul_ch.sw.off() 
        
    
    @kernel 
    def intensity_ramp_Dipole(self, peak, tramp, tflat):     # intensity stabalizes ramp for dipole trap
        urukul_ch =self.urukul_meas[0]
        urukul_ch.sw.on()  
        delay(t)
        urukul_ch.sw.off()
        
        
        
        
        
        
        
        