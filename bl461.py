# -*- coding: utf-8 -*-
"""
Created on Tue Jan 11 16:42:25 2022

@author: sr
"""

from artiq.experiment import *
import numpy as np
from fit_image import Fit2DGaussParabola
   
reps = 1

class BL461(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("ttl5")
        self.setattr_device("urukul0_cpld")
        self.setattr_device("urukul1_cpld")
        self.setattr_device("sampler0")
        self.adc_0=self.get_device("sampler0")
    
        # Probe AOMs
        self.setattr_argument("Probe_AOM_frequency",
            Scannable(default=[NoScan(230*1e6), RangeScan(210*1e6, 250*1e6, 10, randomize=False)],scale=1e6,
                      unit="MHz"),"Probe")

        self.setattr_argument("Probe_DDS_amplitude_scale",NumberValue(0.8,min=0.0,max=0.9),"Probe")
        self.setattr_argument("Probe_Urukul_attenuation",NumberValue(30.0,min=0.0,max=30.0),"Probe")
        
        
        self.setattr_argument("ProbeDP_AOM_frequency",
            Scannable(default=[NoScan(100*1e6), RangeScan(75*1e6, 125*1e6, 10, randomize=False)],scale=1e6,
                      unit="MHz"),"ProbeDP")

        self.setattr_argument("ProbeDP_DDS_amplitude_scale",NumberValue(0.8,min=0.0,max=0.8),"ProbeDP")
        self.setattr_argument("ProbeDP_Urukul_attenuation",NumberValue(30.0,min=1.0,max=30.0),"ProbeDP")
        
        
        # 3D MOT AOM
        self.setattr_argument("MOT3D_AOM_frequency",
            Scannable(default=[NoScan(100*1e6), RangeScan(75*1e6, 125*1e6, 10, randomize=False)],scale=1e6,
                      unit="MHz"),"MOT3D")

        self.setattr_argument("MOT3D_DDS_amplitude_scale",NumberValue(0.8,min=0.0,max=0.8),"MOT3D")
        self.setattr_argument("MOT3D_Urukul_attenuation",NumberValue(30.0,min=1.0,max=30.0),"MOT3D")
        
        
        self.setattr_argument("MOT3DDP_AOM_frequency",
            Scannable(default=[NoScan(100*1e6), RangeScan(75*1e6, 125*1e6, 10, randomize=False)],scale=1e6,
                      unit="MHz"),"MOT3DDP")

        self.setattr_argument("MOT3DDP_DDS_amplitude_scale",NumberValue(0.8,min=0.0,max=0.8),"MOT3DDP")
        self.setattr_argument("MOT3DDP_Urukul_attenuation",NumberValue(30.0,min=1.0,max=30.0),"MOT3DDP")
        
        
        # Zeeman slower AOM
        self.setattr_argument("ZeemanDP_AOM_frequency",
            Scannable(default=[NoScan(265*1e6), RangeScan(25*1e6, 280*1e6, 10, randomize=False)],scale=1e6,
                      unit="MHz"),"ZeemanDP")

        self.setattr_argument("ZeemanDP_DDS_amplitude_scale",NumberValue(0.8,min=0.0,max=0.95),"ZeemanDP")
        self.setattr_argument("ZeemanDP_Urukul_attenuation",NumberValue(30.0,min=0.0,max=30.0),"ZeemanDP")
        
        # 2D MOT AOM
        self.setattr_argument("MOT2D_AOM_frequency",
            Scannable(default=[NoScan(100*1e6), RangeScan(75*1e6, 125*1e6, 10, randomize=False)],scale=1e6,
                      unit="MHz"),"MOT2D")

        self.setattr_argument("MOT2D_DDS_amplitude_scale",NumberValue(0.8,min=0.0,max=0.8),"MOT2D")
        self.setattr_argument("MOT2D_Urukul_attenuation",NumberValue(30.0,min=1.0,max=30.0),"MOT2D")
        
        
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
        self.urukul_hmc_ref_probeDP = self.get_device("urukul1_ch1")
        self.urukul_hmc_ref_MOT3DDP = self.get_device("urukul0_ch1")
        self.urukul_hmc_ref_MTS = self.get_device("urukul0_ch2")
        self.urukul_hmc_ref_ZeemanDP = self.get_device("urukul0_ch3")
        self.urukul_hmc_ref_MOT2D = self.get_device("urukul1_ch0")
        self.urukul_hmc_ref_MOT3D = self.get_device("urukul1_ch3")
        
        #self.urukul_meas = [self.get_device("urukul0_ch" + str(i)) for i in range(4)]
        #self.urukul_meas.append('urukul1_ch1')
        self.urukul_meas = [self.get_device("urukul0_ch0"),self.get_device("urukul0_ch1"),self.get_device("urukul0_ch2"),self.get_device("urukul0_ch3"),self.get_device("urukul1_ch0"),self.get_device("urukul1_ch1"),self.get_device("urukul1_ch3")]
        # The same waveform is output on all first 4 SAWG channels (first DAC).
        #self.flist = [i for i in range(140,240)]
       
       
        
    def prepare(self):
     
           #print(self.AOM_frequency.sequence)
           self.probe_dds_scale=self.Probe_DDS_amplitude_scale
           self.probeDP_dds_scale=self.ProbeDP_DDS_amplitude_scale
           self.MOT3D_dds_scale=self.MOT3D_DDS_amplitude_scale
           self.ZeemanDP_dds_scale=self.ZeemanDP_DDS_amplitude_scale
           self.MOT2D_dds_scale=self.MOT2D_DDS_amplitude_scale
           self.MTS_dds_scale=self.MTS_DDS_amplitude_scale
           self.MOT3DDP_dds_scale=self.MOT3DDP_DDS_amplitude_scale
           
           self.probe_iatten=self.Probe_Urukul_attenuation
           self.probeDP_iatten=self.ProbeDP_Urukul_attenuation
           self.MOT3D_iatten=self.MOT3D_Urukul_attenuation
           self.ZeemanDP_iatten=self.ZeemanDP_Urukul_attenuation
           self.MOT2D_iatten=self.MOT2D_Urukul_attenuation
           self.MTS_iatten=self.MTS_Urukul_attenuation
           self.MOT3DDP_iatten=self.MOT3DDP_Urukul_attenuation
           
           self.adc_data=[0.1 for ii in range(reps*len(self.ZeemanDP_AOM_frequency.sequence))]
          
         
                  
    @kernel
    def run(self):
        #flist = range(140,240)
        #for df in range(200):
        #atten = [0.0,1.0,2.0,3.0,4.0,5.0,6.0,7.0,8.0,9.0,10.0,11.0,12.0]
        #for iatten in atten:
            
            self.core.reset()
            delay(1*ms)
           
            self.urukul0_cpld.init()
            self.urukul1_cpld.init()
            
            #self.adc_0.init()
           # self.adc_0.set_gain_mu(0,0)
            #self.adc_0.set_gain_mu(1,0)
            #self.adc_0.set_gain_mu(2,0)

            #delay(1*ms)
            self.urukul_hmc_ref_probe.init()
            self.urukul_hmc_ref_probe.set_mu(0x40000000, asf=self.urukul_hmc_ref_probe.amplitude_to_asf(self.probe_dds_scale))
            self.urukul_hmc_ref_probe.set_att(self.probe_iatten)
            self.urukul_hmc_ref_probe.sw.on()
            
            #delay(1*ms)
            
            self.urukul_hmc_ref_probeDP.init()
            self.urukul_hmc_ref_probeDP.set_mu(0x40000000, asf=self.urukul_hmc_ref_probeDP.amplitude_to_asf(self.probeDP_dds_scale))
            self.urukul_hmc_ref_probeDP.set_att(self.probeDP_iatten)
            self.urukul_hmc_ref_probeDP.sw.on()
            
            #delay(1*ms)
            
            self.urukul_hmc_ref_MOT3DDP.init()
            self.urukul_hmc_ref_MOT3DDP.set_mu(0x40000000, asf=self.urukul_hmc_ref_MOT3DDP.amplitude_to_asf(self.MOT3DDP_dds_scale))
            self.urukul_hmc_ref_MOT3DDP.set_att(self.MOT3DDP_iatten)
            self.urukul_hmc_ref_MOT3DDP.sw.on()
            
            
            #delay(1*ms)
            
            self.urukul_hmc_ref_ZeemanDP.init()
            self.urukul_hmc_ref_ZeemanDP.set_mu(0x40000000, asf=self.urukul_hmc_ref_ZeemanDP.amplitude_to_asf(self.ZeemanDP_dds_scale))
            self.urukul_hmc_ref_ZeemanDP.set_att(self.ZeemanDP_iatten)
            self.urukul_hmc_ref_ZeemanDP.sw.on()
            
            #delay(1*ms)
            
            self.urukul_hmc_ref_MOT2D.init()
            self.urukul_hmc_ref_MOT2D.set_mu(0x40000000, asf=self.urukul_hmc_ref_MOT2D.amplitude_to_asf(self.MOT2D_dds_scale))
            self.urukul_hmc_ref_MOT2D.set_att(self.MOT2D_iatten)
            self.urukul_hmc_ref_MOT2D.sw.on()
            
            #delay(1*ms)
            
            self.urukul_hmc_ref_MTS.init()
            self.urukul_hmc_ref_MTS.set_mu(0x40000000, asf=self.urukul_hmc_ref_MTS.amplitude_to_asf(self.MTS_dds_scale))
            self.urukul_hmc_ref_MTS.set_att(self.MTS_iatten)
            self.urukul_hmc_ref_MTS.sw.on()
            
            
            self.urukul_hmc_ref_MOT3D.init()
            self.urukul_hmc_ref_MOT3D.set_mu(0x40000000, asf=self.urukul_hmc_ref_MOT3D.amplitude_to_asf(self.MOT3D_dds_scale))
            self.urukul_hmc_ref_MOT3D.set_att(self.MOT3D_iatten)
            self.urukul_hmc_ref_MOT3D.sw.on()
            
             
            fprobe = self.Probe_AOM_frequency.sequence[0]
            dds_ftw_probe=self.urukul_meas[0].frequency_to_ftw(fprobe)
            
            urukul_ch =self.urukul_meas[0]
            #delay(1*ms)
            urukul_ch.init()
            urukul_ch.set_mu(dds_ftw_probe, asf=urukul_ch.amplitude_to_asf(self.probe_dds_scale))
            urukul_ch.set_att(self.probe_iatten)
            urukul_ch.sw.on()
            
            
            # fMOT3DDP = self.MOT3DDP_AOM_frequency.sequence[0]
            # dds_ftw_MOT3DDP=self.urukul_meas[1].frequency_to_ftw(fMOT3DDP)
                
            # urukul_ch =self.urukul_meas[1]
            #    # delay(0.15*ms)
            # urukul_ch.init()
            # urukul_ch.set_mu(dds_ftw_MOT3DDP, asf=urukul_ch.amplitude_to_asf(self.MOT3DDP_dds_scale))
            # urukul_ch.set_att(self.MOT3DDP_iatten)
            # urukul_ch.sw.on() 
            
            
            fMTS = self.MTS_AOM_frequency.sequence[0]
            dds_ftw_MTS=self.urukul_meas[2].frequency_to_ftw(fMTS)
                
            urukul_ch =self.urukul_meas[2]
               # delay(0.15*ms)
            urukul_ch.init()
            urukul_ch.set_mu(dds_ftw_MTS, asf=urukul_ch.amplitude_to_asf(self.MTS_dds_scale))
            urukul_ch.set_att(self.MTS_iatten)
            urukul_ch.sw.on() 
            
            
            ## Scan Zeeman double pass AOM
            
            # urukul_ch =self.urukul_meas[3]
                    
            # urukul_ch.init()
                    
            # urukul_ch.set_att(self.ZeemanDP_iatten)
            # urukul_ch.sw.on()
            
            # for kk in range(8500):
            #     for ii in range(len(self.ZeemanDP_AOM_frequency.sequence)):
                     
            #         fZeemanDP = self.ZeemanDP_AOM_frequency.sequence[ii]
            #         dds_ftw_ZeemanDP=self.urukul_meas[3].frequency_to_ftw(fZeemanDP)
            #         delay(2*ms)
            #         urukul_ch.set_mu(dds_ftw_ZeemanDP, asf=urukul_ch.amplitude_to_asf(self.ZeemanDP_dds_scale))
                
            fZeemanDP = self.ZeemanDP_AOM_frequency.sequence[0]
            dds_ftw_ZeemanDP=self.urukul_meas[3].frequency_to_ftw(fZeemanDP)
                
            urukul_ch =self.urukul_meas[3]
                #delay(0.15*ms)
            urukul_ch.init()
            urukul_ch.set_mu(dds_ftw_ZeemanDP, asf=urukul_ch.amplitude_to_asf(self.ZeemanDP_dds_scale))
            urukul_ch.set_att(self.ZeemanDP_iatten)
            urukul_ch.sw.on()
                            
                
            fMOT2D = self.MOT2D_AOM_frequency.sequence[0]
            dds_ftw_MOT2D=self.urukul_meas[4].frequency_to_ftw(fMOT2D)
                
            urukul_ch =self.urukul_meas[4]
                #delay(0.15*ms)
            urukul_ch.init()
            urukul_ch.set_mu(dds_ftw_MOT2D, asf=urukul_ch.amplitude_to_asf(self.MOT2D_dds_scale))
            urukul_ch.set_att(self.MOT2D_iatten)
            urukul_ch.sw.on() 
            
         
            fprobeDP = self.ProbeDP_AOM_frequency.sequence[0]
            dds_ftw_probeDP=self.urukul_meas[5].frequency_to_ftw(fprobeDP)
            
            urukul_ch =self.urukul_meas[5]
            delay(1*ms)
            urukul_ch.init()
            urukul_ch.set_mu(dds_ftw_probeDP, asf=urukul_ch.amplitude_to_asf(self.probeDP_dds_scale))
            urukul_ch.set_att(self.probeDP_iatten)
            urukul_ch.sw.on() 
            
            
            fMOT3D = self.MOT3D_AOM_frequency.sequence[0]
            dds_ftw_MOT3D=self.urukul_meas[6].frequency_to_ftw(fMOT3D)
                
            urukul_ch =self.urukul_meas[6]
               # delay(0.15*ms)
            urukul_ch.init()
            urukul_ch.set_mu(dds_ftw_MOT3D, asf=urukul_ch.amplitude_to_asf(self.MOT3D_dds_scale))
            urukul_ch.set_att(self.MOT3D_iatten)
            urukul_ch.sw.on() 

            
            ##Scan Probe Double Pass AOM
            
            
            urukul_ch =self.urukul_meas[1]
                    
            urukul_ch.init()
                    
            urukul_ch.set_att(self.MOT3DDP_iatten)
            urukul_ch.sw.on()
            
            for kk in range(8500):
                for ii in range(len(self.MOT3DDP_AOM_frequency.sequence)):
                     
                    fMOT3DDP = self.MOT3DDP_AOM_frequency.sequence[ii]
                    dds_ftw_MOT3DDP=self.urukul_meas[1].frequency_to_ftw(fMOT3DDP)
                    delay(2*ms)
                    urukul_ch.set_mu(dds_ftw_MOT3DDP, asf=urukul_ch.amplitude_to_asf(self.MOT3DDP_dds_scale))
            
            
            
            
            ##Scan Probe Double Pass AOM
            
            
            # urukul_ch =self.urukul_meas[5]
                    
            # urukul_ch.init()
                    
            # urukul_ch.set_att(self.probeDP_iatten)
            # urukul_ch.sw.on()
            
            # for kk in range(8500):
            #     for ii in range(len(self.ProbeDP_AOM_frequency.sequence)):
                     
            #         fprobeDP = self.ProbeDP_AOM_frequency.sequence[ii]
            #         dds_ftw_probeDP=self.urukul_meas[5].frequency_to_ftw(fprobeDP)
            #         delay(2*ms)
            #         urukul_ch.set_mu(dds_ftw_probeDP, asf=urukul_ch.amplitude_to_asf(self.probeDP_dds_scale))
                      
                
               
         
                
            
            # dat=[0.1,0.5]
            # for ii in range(len(self.ZeemanDP_AOM_frequency.sequence)):
            #     delay(1*ms)
            #     fZeemanDP = self.ZeemanDP_AOM_frequency.sequence[ii]
            #     dds_ftw_ZeemanDP=self.urukul_meas[3].frequency_to_ftw(fZeemanDP)
                
            #     urukul_ch =self.urukul_meas[3]
            #     delay(1*ms)
            #     urukul_ch.init()
            #     urukul_ch.set_mu(dds_ftw_ZeemanDP, asf=urukul_ch.amplitude_to_asf(self.ZeemanDP_dds_scale))
            #     urukul_ch.set_att(self.ZeemanDP_iatten)
            #     urukul_ch.sw.on() 
                
            #     delay(1*ms)
            #     self.adc_0.sample(dat)
            #     self.adc_data[ii]=dat[1]
            #     delay(1*ms)
            
            # delay(1*ms)        
            # self.set_dataset("Measured_PD_signal", self.adc_data, broadcast=True)
            # self.set_dataset("Frequency", self.ZeemanDP_AOM_frequency.sequence, broadcast=True)
            # print(self.adc_data)
            