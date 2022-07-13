# -*- coding: utf-8 -*-
"""
Created on Mon Feb 14 16:39:41 2022

@author: sr
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Feb 14 15:48:49 2022

@author: sr

Functions:

Controls some aspects of the HCDL lock setup    
Sets the parameters of the HCDL MTS AOM and double-pass AOM before the HDCL setup

"""

from artiq.experiment import *
import numpy as np     

class three_photon(EnvExperiment):
      
    
    def build(self):
        
        self.setattr_device("urukul0_cpld")
        
        # Offset AOM
        self.setattr_argument("Offset_AOM_frequency",NumberValue(240*1e6,scale=1e6,unit='MHz'),"Offset_AOM") 
        self.setattr_argument("Offset_AOM_DDS_amplitude_scale",NumberValue(0.8),"Offset_AOM")
        self.setattr_argument("Offset_AOM_DDS_attenuation",NumberValue(4.0),"Offset_AOM")
     
    
        # 679 DP AOM
        
        self.setattr_argument("DP_679_AOM_frequency",NumberValue(200*1e6,scale=1e6,unit='MHz'),"Three_photon") 
        self.setattr_argument("DP_679_AOM_DDS_amplitude_scale",NumberValue(0.8),"Three_photon")
        self.setattr_argument("DP_679_AOM_DDS_attenuation",NumberValue(9.0),"Three_photon")
        
        # 679 switch AOM
        self.setattr_argument("switch_679_AOM_frequency",NumberValue(200*1e6,scale=1e6,unit='MHz'),"Three_photon") # ramp duration
        self.setattr_argument("switch_679_AOM_DDS_amplitude_scale",NumberValue(0.8),"Three_photon")
        self.setattr_argument("switch_679_AOM_Urukul_attenuation",NumberValue(9.0),"Three_photon")

        # 689 DP AOM
        
        self.setattr_argument("DP_689_AOM_frequency",NumberValue(80*1e6,scale=1e6,unit='MHz'),"Three_photon") # ramp duration
        self.setattr_argument("DP_689_AOM_DDS_amplitude_scale",NumberValue(0.8),"Three_photon")
        self.setattr_argument("DP_689_AOM_Urukul_attenuation",NumberValue(4.0),"Three_photon")
        

        self.urukul_hmc_ref_Offset_AOM = self.get_device("urukul0_ch0")
        self.urukul_hmc_ref_DP_679_AOM = self.get_device("urukul0_ch1")
        self.urukul_hmc_ref_switch_679_AOM = self.get_device("urukul0_ch2")
        self.urukul_hmc_ref_DP_689_AOM = self.get_device("urukul0_ch3")
        
        self.urukul_meas = [self.get_device("urukul0_ch0"),self.get_device("urukul0_ch2"),self.get_device("urukul0_ch1"),self.get_device("urukul0_ch3")]

        
    def set_atten(self):
        
        self.Offset_AOM_dds_scale=self.Offset_AOM_DDS_amplitude_scale
        
        self.Offset_AOM_iatten=self.Offset_AOM_DDS_attenuation
        
        
        self.DP_679_AOM_dds_scale=self.DP_679_AOM_DDS_amplitude_scale
        self.switch_679_AOM_dds_scale=self.switch_679_AOM_DDS_amplitude_scale
        self.DP_689_AOM_dds_scale=self.DP_689_AOM_DDS_amplitude_scale
        
        
        self.DP_679_AOM_iatten=self.DP_679_AOM_DDS_attenuation
        self.switch_679_AOM_iatten=self.switch_679_AOM_Urukul_attenuation
        self.DP_689_AOM_iatten=self.DP_689_AOM_Urukul_attenuation
      
    @kernel    
    def init_aoms(self):
        
        delay(1*ms)
        self.urukul0_cpld.init()
        
        self.urukul_hmc_ref_Offset_AOM.init()
        self.urukul_hmc_ref_Offset_AOM.set_mu(0x40000000, asf=self.urukul_hmc_ref_Offset_AOM.amplitude_to_asf(self.Offset_AOM_dds_scale))
        self.urukul_hmc_ref_Offset_AOM.set_att(self.Offset_AOM_iatten)
        self.urukul_hmc_ref_Offset_AOM.sw.on()
            
        self.urukul_hmc_ref_DP_679_AOM.init()
        self.urukul_hmc_ref_DP_679_AOM.set_mu(0x40000000, asf=self.urukul_hmc_ref_DP_679_AOM.amplitude_to_asf(self.DP_679_AOM_dds_scale))
        self.urukul_hmc_ref_DP_679_AOM.set_att(self.DP_679_AOM_iatten)
        self.urukul_hmc_ref_DP_679_AOM.sw.on()
            
        self.urukul_hmc_ref_switch_679_AOM.init()
        self.urukul_hmc_ref_switch_679_AOM.set_mu(0x40000000, asf=self.urukul_hmc_ref_switch_679_AOM.amplitude_to_asf(self.switch_679_AOM_dds_scale))
        self.urukul_hmc_ref_switch_679_AOM.set_att(self.switch_679_AOM_iatten)
        self.urukul_hmc_ref_switch_679_AOM.sw.on()
        
        self.urukul_hmc_ref_DP_689_AOM.init()
        self.urukul_hmc_ref_DP_689_AOM.set_mu(0x40000000, asf=self.urukul_hmc_ref_DP_689_AOM.amplitude_to_asf(self.DP_689_AOM_dds_scale))
        self.urukul_hmc_ref_DP_689_AOM.set_att(self.DP_689_AOM_iatten)
        self.urukul_hmc_ref_DP_689_AOM.sw.on()
        
        
        self.set_offset_aom_frequency()
        
        
        self.set_DP_679_frequency()
        self.set_switch_679_frequency()
        self.set_DP_689_frequency()
        
       
        
    @kernel 
    def set_offset_aom_frequency(self): 
        
        fOffset = self.Offset_AOM_frequency
        urukul_ch =self.urukul_meas[0]
        dds_ftw_Offset_AOM=self.urukul_meas[0].frequency_to_ftw(fOffset)
        urukul_ch.set_mu(dds_ftw_Offset_AOM, asf=urukul_ch.amplitude_to_asf(self.Offset_AOM_DDS_amplitude_scale))     
        
       
    @kernel 
    def set_DP_679_frequency(self): 
        
        f_679_DP = self.DP_679_AOM_frequency
        urukul_ch =self.urukul_meas[1]
        dds_ftw_f_679_DP=self.urukul_meas[1].frequency_to_ftw(f_679_DP)
        urukul_ch.set_mu(dds_ftw_f_679_DP, asf=urukul_ch.amplitude_to_asf(self.DP_679_AOM_dds_scale))
        
  
        
    @kernel 
    def set_switch_679_frequency(self): 
      
        f_679_switch = self.switch_679_AOM_frequency
        urukul_ch =self.urukul_meas[2]
        dds_ftw_679_switch=self.urukul_meas[2].frequency_to_ftw(f_679_switch)
        urukul_ch.set_mu(dds_ftw_679_switch, asf=urukul_ch.amplitude_to_asf(self.switch_679_AOM_DDS_amplitude_scale))    
        
    @kernel 
    def set_DP_689_frequency(self): 
        
        f_689_DP = self.DP_689_AOM_frequency
        urukul_ch =self.urukul_meas[3]
        dds_ftw_f_689_DP=self.urukul_meas[3].frequency_to_ftw(f_689_DP)
        urukul_ch.set_mu(dds_ftw_f_689_DP, asf=urukul_ch.amplitude_to_asf(self.DP_689_AOM_dds_scale))
        
        
    
        
    