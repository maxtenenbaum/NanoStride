import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from nanostride import slice_and_extract, create_bidirectional_waveforms, save_binary_waveform, find_prusaslicer


def main():
    try:
        slicer_path = find_prusaslicer()
    except FileNotFoundError as e:
        print(e)
        exit(1)

    slice_and_extract(
        slicer_path=slicer_path,
        stl_path="test_files/pyramid.stl",
        config_path="scripts/config.ini",
        output_dir="slices_script",
        extracted_image_dir="skull_slices",
    )

    waveform = create_bidirectional_waveforms("skull_slices", serpentine=True)
    save_binary_waveform(waveform, "waveform_120px.bin")

if __name__ == "__main__":
    main()
