import numpy as np
from PIL import Image
import os
import nifgen
import time
import math

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
    #float_waveform_normalized.tofile(f"{filename}.bin")


# Waveform streaming functionalities

# Determining allocation size
def allocation_size(waveform):
    total_size_bytes = os.path.getsize(waveform)
    max_chunk_size = 10 * 1024 * 1024 # 200MB

    valid_chunks = set()
    for i in range(1, int(math.isqrt(total_size_bytes))+1):
        if total_size_bytes % i == 0:
            complement = total_size_bytes // i
            if i <= max_chunk_size:
                valid_chunks.add(i)
            if complement <= max_chunk_size:
                valid_chunks.add(complement)
    return(max(valid_chunks) if valid_chunks else None)

def stream_waveform(waveform_path):

    # Determine chunk size and number of chunks
    chunk_size_bytes = allocation_size(waveform_path)
    total_size_bytes = os.path.getsize(waveform_path)
    num_chunks = total_size_bytes // chunk_size_bytes
    
    with open(waveform_path, "rb") as f:
        for _ in range(num_chunks):
            chunk = f.read(chunk_size_bytes)

            # Ensure chunk size is a multiple of 8 bytes (float64)
            valid_bytes = len(chunk) - (len(chunk) % 8)
            chunk = chunk[:valid_bytes]

            data = np.frombuffer(chunk, dtype='<f8').astype(np.float32)

            with nifgen.Session("Dev1") as session:
                session.output_mode = nifgen.OutputMode.SCRIPT
                session.arb_sample_rate = 25e6

                waveform_name = "streamwave"
                num_samples = len(data)

                # Allocate a named waveform
                session.allocate_named_waveform(waveform_name, num_samples)

                # Write the waveform using the name (not handle)
                session.write_waveform(waveform_name, data.tolist())

                # Write a script that references the named waveform
                session.write_script(f"""
                script main
                    repeat 1
                        generate {waveform_name}
                    end repeat
                end script
                """)

                # Start generation
                with session.initiate():
                    session.wait_until_done()