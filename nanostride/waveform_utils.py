import numpy as np
from PIL import Image
import os

def create_bidirectional_waveforms(image_dir, serpentine=True):
    waveforms = []

    image_files = sorted([
        f for f in os.listdir(image_dir)
        if f.endswith(".png")
    ])

    for i, filename in enumerate(image_files):
        path = os.path.join(image_dir, filename)
        img = Image.open(path).convert("L")
        binary = (np.array(img) > 128).astype(np.uint8)

        for row_index in range(binary.shape[0]):
            row = binary[row_index]
            if serpentine and ((i % 2 == 0 and row_index % 2 == 1) or
                               (i % 2 == 1 and row_index % 2 == 0)):
                row = row[::-1]
            waveforms.append(row)
    
    return np.concatenate(waveforms)

def save_binary_waveform(waveform, filename):
    float_waveform_normalized = waveform.astype(np.float64) * 2 - 1
    float_waveform_normalized.astype('<f8').tofile(f"{filename}.bin")
