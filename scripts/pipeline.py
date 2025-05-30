from nanostride import slice_and_extract, create_bidirectional_waveforms, save_binary_waveform

def main():
    slice_and_extract(
        slicer_path=r"C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer-console.exe",
        stl_path="test_files/skull.stl",
        config_path="config.ini",
        output_dir="slices_script",
        extracted_image_dir="skull_slices",
    )

    waveform = create_bidirectional_waveforms("skull_slices", serpentine=True)
    save_binary_waveform(waveform, "waveform_output")

if __name__ == "__main__":
    main()
