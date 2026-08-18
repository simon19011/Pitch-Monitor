import pyaudio
import numpy as np
import keyboard
import time

testing = False

p = pyaudio.PyAudio()
SAMPLE_RATE = 44100
BUFFER_SIZE = 4096 #16384
NOISE_GATE = 275

NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

stream = None

def get_microphone_raw():
    data = stream.read(BUFFER_SIZE)
    samples = np.frombuffer(data, dtype = np.int16)
    return samples

def get_RMS(samples):
    # Gets Root Mean Square(RMS) to determine if sound is loud enough to be percieved
    samples = samples.astype(np.float32)

    rms = np.sqrt(np.mean(samples ** 2))

    return rms

def get_frequency(samples):
    # Using Fast Fourier Transform(FFT) to find peak frequency(magnitude) and thus frequency
    rms  = get_RMS(samples)

    if rms < NOISE_GATE:
        return None
    
    fft = np.fft.rfft(samples)
    magnitude = np.abs(fft)
    frequencies = np.fft.rfftfreq(len(samples), 1 / SAMPLE_RATE)
    frequency_index = np.argmax(magnitude)
    frequency = frequencies[frequency_index]

    if frequency <= 0:
        return None
    
    return frequency

def get_note(frequency):
    midi = round(69 + 12 * np.log2(frequency / 440))
    note = NOTES[midi % 12]
    octave = midi // 12 - 1 
    return f"{note}{octave}"

def get_midi(frequency):
    if frequency is None or frequency <= 0:
        return None
    
    midi = round(69 + 12 * np.log2(frequency / 440))
    return midi

def get_exact_midi(frequency):
    if frequency is None or frequency <= 0:
            return None
        
    exact_midi = 69 + 12 * np.log2(frequency / 440)
    return exact_midi

def start_microphone_recording():
    global stream

    if stream is not None:
        return

    stream = p.open(
        format = pyaudio.paInt16,
        channels = 1,
        rate = SAMPLE_RATE,
        input = True,
        frames_per_buffer = BUFFER_SIZE
    )

def stop_microphone_recording():
    global stream

    if stream is None:
        return

    stream.close()
    stream = None

def get_current_pitch():
    global stream

    if stream is None:
        return None

    samples = get_microphone_raw()
    return get_frequency(samples)








# Testing
while testing:
    if keyboard.is_pressed('space'):
        if stream is None:
            start_microphone_recording()
            print("Microphone ON!")
        else:
            stop_microphone_recording()
            print("Microphone OFF!")

        while keyboard.is_pressed('space'):
            time.sleep(0.01)

    if stream is not None:
        frequency = get_frequency(get_microphone_raw())
        note = get_note(frequency)

        print(frequency)
        print (note)

