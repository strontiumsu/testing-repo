# -*- coding: utf-8 -*-
"""
Created on Tue Mar 14 17:49:55 2023

@author: E. Porter
"""

from artiq.experiment import *
import time

class _Picomotor(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.pico = self.get_device("newfocus8742")
    
    def get_identity(self) -> TStr:
        return self.pico.ask("*IDN?")
        
    def reset(self):
        self.pico.do("*RS?")
    
    def abort(self):
        self.pico.do("AB")
    
    def set_acceleration(self, motor, acc):
        self.pico.do("AC", motor, acc)
    
    def get_acceleration(self, motor) -> TInt32:
        return int(self.pico.ask("AC?", motor))
    
    def set_home(self, motor):
        self.pico.do("DH", motor)
    
    def get_home(self, motor) -> TInt32:
        return int(self.pico.ask("DH?", motor))
    
    def move(self, motor, direc):
        self.pico.do("MV", motor, direc)
    
    def set_position(self, motor, pos):
        self.pico.do("PA", motor, pos)
        while self.get_current_position(motor) != pos:
            time.sleep(1/1000)
    
    def get_position(self, motor) -> TInt32:
        return int(self.pico.ask("PA?", motor))
    
    def get_current_position(self, motor) -> TInt32:
        return int(self.pico.ask("TP?", motor))
    
    def set_relative(self, motor, rel):
        current = self.get_position(motor)
        self.pico.do("PR", motor, rel)
        while self.get_current_position(motor)-current != rel:
            time.sleep(1/1000)

    
    def get_relative(self, motor) -> TInt32:
        return int(self.pico.ask("PR?", motor))
    
    def set_velocity(self, motor, vel):
        self.pico.do("VA", motor, vel)
    
    def get_velocity(self, motor) -> TInt32:
        return int(self.pico.ask("VA?", motor))
    
    def stop(self, motor):
        self.pico.do("ST", motor)
        
   
        
    