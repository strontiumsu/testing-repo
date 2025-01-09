# -*- coding: utf-8 -*-
"""
Created on Fri Aug 23 10:16:17 2024

@author: ejporter

"""
import numpy as np
from scipy.signal import gaussian
import matplotlib.pyplot as plt
import pyvisa

class WaveformGenerator:
    """
    A class for generating custom waveform pulses for experiments using AWGs (Arbitrary Waveform Generators).

    This class provides methods for creating and managing square and Gaussian pulses,
    storing them as arrays for further use in experiments.

    Class Variables:
        max_amplitude (float): Maximum allowed amplitude for waveforms.
        min_amplitude (float): Minimum allowed amplitude for waveforms.
        default_sample_rate (float): Default sample rate in Hz.

    **Example Usage**:
    ```python
    wg = WaveformGenerator(sample_rate=1e6)
    wg.add_square_pulse(start_time=0, duration=1e-3, amplitude=1.0)
    wg.add_gaussian_pulse(start_time=1e-3, duration=2e-3, amplitude=0.8, std_dev=5e-4)
    ```
    """

    def __init__(self, sample_rate=10e6, max_amplitude: float = 5.0):
        """
        Initialize the WaveformGenerator with a specified sampling rate.

        Args:
            sample_rate (float): The sampling rate in samples per second.
        """
        self.sample_rate = sample_rate  # Samples per second
        self.time_array = np.array([])
        self.amplitude_array = np.array([])
        self.max_amplitude=max_amplitude

    def _validate_pulse_parameters(self, start_time, duration, amplitude):
        if amplitude > self.max_amplitude:
            raise ValueError("Amplitude too large.")
        if start_time < 0:
            raise ValueError("Start time must be non-negative.")
        if duration <= 0:
            raise ValueError("Duration must be greater than zero.")
        if amplitude < 0:
            raise ValueError("Amplitude must be non-negative.")
        if self.time_array.size > 0 and start_time < self.time_array[-1]:
            raise ValueError("Start time overlaps with an existing pulse.")

    def add_square_pulse(self, start_time, duration, amplitude):
        """
        Add a square pulse to the waveform.

        Args:
            start_time (float): The starting time of the pulse in seconds.
            duration (float): The duration of the pulse in seconds.
            amplitude (float): The amplitude of the pulse.
        """
        self._validate_pulse_parameters(start_time, duration, amplitude)

        t = np.arange(start_time, start_time + duration, 1 / self.sample_rate)
        pulse = np.full_like(t, amplitude)
        self._append_pulse(t, pulse)

    def add_gaussian_pulse(self, start_time, duration, amplitude, std_dev):
        """
        Add a Gaussian pulse to the waveform.

        Args:
            start_time (float): The starting time of the pulse in seconds.
            duration (float): The duration of the pulse in seconds.
            amplitude (float): The amplitude of the pulse.
            std_dev (float): The standard deviation of the Gaussian pulse.
        """
        self._validate_pulse_parameters(start_time, duration, amplitude)

        t = np.arange(start_time, start_time + duration, 1 / self.sample_rate)
        t_centered = t - (start_time + duration / 2)
        pulse = amplitude * np.exp(-t_centered**2 / (2 * std_dev**2))
        self._append_pulse(t, pulse)

    def _append_pulse(self, t, pulse):
        """
        Append a pulse to the existing waveform arrays.

        Args:
            t (numpy.ndarray): Array of time values.
            pulse (numpy.ndarray): Array of amplitude values corresponding to the time values.
        """
        self.time_array = np.concatenate((self.time_array, t))
        self.amplitude_array = np.concatenate((self.amplitude_array, pulse))

    def plot_waveform(self):
        """
        Plot the generated waveform using Matplotlib.

        This provides a visual representation of the time-domain waveform.
        """
        if self.time_array.size == 0 or self.amplitude_array.size == 0:
            raise ValueError("No waveform data to plot.")

        plt.figure(figsize=(10, 5))
        plt.plot(self.time_array, self.amplitude_array, label="Waveform")
        plt.xlabel("Time (s)")
        plt.ylabel("Amplitude")
        plt.title("Generated Waveform")
        plt.legend()
        plt.grid(True)
        plt.show()

    def reset_waveform(self):
        """
        Clear the current waveform data.
        """
        self.time_array = np.array([])
        self.amplitude_array = np.array([])

    def save_waveform(self, filename):
        """
        Save the waveform to a file.

        Args:
            filename (str): The file path to save the waveform.
        """
        np.savez(filename, time_array=self.time_array, amplitude_array=self.amplitude_array)

    def load_waveform(self, filename):
        """
        Load a waveform from a file.

        Args:
            filename (str): The file path to load the waveform from.
        """
        data = np.load(filename)
        self.time_array = data['time_array']
        self.amplitude_array = data['amplitude_array']
