# -*- coding: utf-8 -*-
"""
Created on Tue Jun 29 17:38:56 2021

@author: sr
"""

from artiq.experiment import *
import numpy as np
from fit_image import Fit2DGaussParabola
   


class miniMOT(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("ttl5") # MOT driver TTL
        self.setattr_device("ttl4") # Camera TTL
        self.setattr_device("zotino0") # device for dac0
        self.dac_0=self.get_device("zotino0") # MOT current pulse shape dac
        self.cam=self.get_device("camera")
        
        self.setattr_device("urukul0_cpld") 
        
        # Camera
        self.setattr_argument("Exposure_Time",NumberValue(25*1e-3,min=10*1e-3,max=100*1e-3,scale=1e-3,
                      unit="ms"),"Camera")
        
        # Ablation laser pulsing
        self.setattr_argument("Ablation_Laser_Pulse",NumberValue(10.0,min=2.0,max=1000.0),"Ablation")
        self.setattr_device("ttl7") # Ablation laser TTL
           
        
        # 3D MOT AOM        
        self.setattr_argument("MOT_AOM_frequency",
            Scannable(default=[NoScan(100*1e6), RangeScan(90*1e6, 91*1e6, 10, randomize=False)],scale=1e6,
                      unit="MHz"),"MOT")

        self.setattr_argument("MOT_DDS_amplitude_scale",NumberValue(0.8,min=0.0,max=0.8),"MOT")
        self.setattr_argument("MOT_Urukul_attenuation",NumberValue(3.0,min=1.0,max=30.0),"MOT")
        
        
        # Urukul clock output syntonized to the RTIO clock.
        # Can be used as HMC830 reference on Sayma RTM.
        # When using this reference, Sayma must be recalibrated every time Urukul
        # is rebooted, as Urukul is not synchronized to the Kasli.
        self.urukul_hmc_ref_MOT = self.get_device("urukul0_ch2")
        self.urukul_meas = self.get_device("urukul0_ch2")
        
    
        # 3D MOT driver
        # self.setattr_argument("MOT_Pulse",
        #     Scannable(default=[NoScan(150*1e-3), RangeScan(10*1e-3, 30*1e-3, 10, randomize=False)],scale=1e-3,
        #               unit="ms"),"MOT_driver")
        self.setattr_argument("MOT_Pulse",NumberValue(150*1e-3,min=10*1e-3,max=1000*1e-3,scale=1e-3,
                      unit="ms"),"MOT_driver")
        self.setattr_argument("MOT_t_ramp",NumberValue(.030,min=-4.0,max=4.00,scale=1e-3,
                      unit="ms"),"MOT_driver")
        self.setattr_argument("Current_amplitude",NumberValue(2.0,min=-4.0,max=20.00,
                      unit="A"),"MOT_driver")
        self.setattr_argument("Npoints",NumberValue(100,min=0,max=100.00),"MOT_driver")
        self.setattr_argument("Npulses",NumberValue(10,min=0,max=100.00),"MOT_driver")
        
        
        
        
    def prepare(self):  
        # MOT coil pulse shape prep
        
        #Ensure odd number of points for driver ramps
        print(self.Npoints)
        self.npoints=self.Npoints
        if self.Npoints % 2 == 0:
            self.npoints += 1
        
        print(self.npoints)
        w=np.blackman(self.npoints+1)  
        # repeat middle element
        self.w1=np.insert(w,int((self.npoints)/2),w[int((self.npoints)/2)])
        self.A=self.Current_amplitude
        self.dt=self.MOT_t_ramp/self.npoints/2    
        self.t_flat=self.MOT_Pulse-2*self.MOT_t_ramp
        print(self.t_flat)
        
        # MOT beam prep
        self.MOT_dds_scale=self.MOT_DDS_amplitude_scale
        self.MOT_iatten=self.MOT_Urukul_attenuation
        
        # Camera
        #self.cam.set_exposure(self.Exposure_Time)
        #self.cam.arm(int(self.Npulses)+1)

         
                  
    @kernel
    def run(self):
            
            self.core.reset()
            self.dac_0.init()
            self.urukul0_cpld.init()
            
            delay(1*ms)
            self.urukul_hmc_ref_MOT.init()
            self.urukul_hmc_ref_MOT.set_mu(0x40000000, asf=self.urukul_hmc_ref_MOT.amplitude_to_asf(self.MOT_dds_scale))
            self.urukul_hmc_ref_MOT.set_att(self.MOT_iatten)
            self.urukul_hmc_ref_MOT.sw.on()
            
            fMOT = self.MOT_AOM_frequency.sequence[0]
            dds_ftw_MOT=self.urukul_meas.frequency_to_ftw(fMOT)
            urukul_ch =self.urukul_meas
            delay(1*ms)
            urukul_ch.init()
            urukul_ch.set_mu(dds_ftw_MOT, asf=urukul_ch.amplitude_to_asf(self.MOT_dds_scale))
            urukul_ch.set_att(self.MOT_iatten)
             
            
            # ######## bias frame ########
            # # pulse on MOT beams
            # urukul_ch.sw.on()
            # delay(1*ms)
            # # take bias image on camera
            # self.ttl4.on()
            # delay(1*ms)
            # self.ttl4.off()
            # self.cam.acquire()
            # delay(40*ms)
            # # pulse off MOT beams
            # urukul_ch.sw.off()
            # delay(20*ms)
            # ############################
            
            # ablation laser pulse (ms)
            # self.ablnPulse()
            # turns on on falling edge
            # self.ttl7.on()
            # delay(5*ms)
            # self.ttl7.off()
            
            
            for nn in range(int(self.Npulses)):
                delay(20*ms)
                with parallel:
                    with sequential:
                        for ii in range(int(self.npoints+1)):
                            
                            # MOT coil pulse rise 
                            if ii<self.npoints/2:
                                delay(self.dt)
                                self.dac_0.write_dac(0,self.A*self.w1[ii])
                                self.dac_0.load()
                                ii+=1
                            
                            # MOT pulse peak
                            elif ii==(self.npoints+1)/2:
                                self.ttl5.off()
                                
                                # pulse on MOT beam AOM
                                urukul_ch.sw.on()
                                
                                # ablation laser pulse (ms)
                                self.ablnPulse()
                                
                                # keep MOT at peak current
                                delay(self.t_flat/2)
                                
                                # # take science image on camera
                                # self.ttl4.on()
                                # delay(1*ms)
                                # self.ttl4.off()
                                # self.cam.acquire()
                                # delay(40*ms)
                                
                                # keep MOT at peak current
                                delay(self.t_flat/2)
                                
                                # pulse off MOT beam AOM
                                urukul_ch.sw.off()
                                
                                
                                self.ttl5.off()
                                ii+=1
                              
                            # MOT coil pulse fall
                            else:
                               delay(self.dt)
                               self.dac_0.write_dac(0,self.A*self.w1[ii])
                               self.dac_0.load()
                               ii+=1
                with sequential:
                    delay(self.MOT_t_ramp)
                    self.ttl5.off()
                    delay(5*ms)
                    self.ttl5.off()
                    
                
            # turns off on falling edge
            # self.ttl7.on()
            # delay(5*ms)
            # self.ttl7.off()
    
    @kernel                
    def ablnPulse(self):
        ####### ablation laser pulse (ms) #######
        # turns on on falling edge
        self.ttl7.on()
        delay(5*ms)
        self.ttl7.off()
        
        delay((self.Ablation_Laser_Pulse-5)*ms)
        
        # turns off on falling edge
        self.ttl7.on()
        delay(5*ms)
        self.ttl7.off()
        
    # def analyze(self): 

    #         ims=self.cam.get_all_images()
    #         self.cam.disarm()
            
    #         exp1full = ims[1]-ims[0]
    #         exp2full = ims[2]-ims[0]
            
    #         exp1 = exp1full
    #         #exp1[exp1full < 10] = 4000
    #         #exp1[exp1full > 1000] = 4000
            
    #         exp2 = exp1full
    #         #exp2[exp2full < 10] = 0
    #         #exp2[exp2full > 1000] = 0
            
    #         self.set_dataset("bias", ims[0], broadcast=True)
    #         self.set_dataset("exp1full", ims[1], broadcast=True)
    #         self.set_dataset("exp2full", ims[2], broadcast=True)
    #         self.set_dataset("exp1", exp1, broadcast=True)
    #         self.set_dataset("exp2", exp2, broadcast=True)
