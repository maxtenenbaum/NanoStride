import os
import subprocess
import zipfile
import shutil
from PIL import Image

def slice_and_extract(
        slicer_path,
        stl_path,
        config_path,
        output_dir,
        extracted_image_dir
):
    os.makedirs(output_dir, exist_ok=True)
    
    basename = os.path.splitext(os.path.basename(stl_path))[0]
    sl1_file = os.path.join(output_dir, f"{basename}.sl1")
    zip_file = os.path.join(output_dir, f"{basename}.zip")

    # Slice the STL
    cmd = [
        slicer_path,
        "--load", config_path,
        "--center", "500,500",
        "--export-sla",
        stl_path,
        "--output", output_dir,
        "--layer-height", "1"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print('Error during slicing \n', result.stderr)
        return
    
    print("Slicing complete")

    # Step 2: Rename .sl1 to .zip
    if not os.path.exists(sl1_file):
        print("Expected SL1 file not found:", sl1_file)
        return

    os.rename(sl1_file, zip_file)
    print(f"Renamed {sl1_file} to {zip_file}")

    # Step 3: Extract .zip
    extract_temp = os.path.join(output_dir, "temp_extract")
    os.makedirs(extract_temp, exist_ok=True)

    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(extract_temp)
    print(f"Extracted zip to {extract_temp}")

    # New logic: collect all PNGs in the extracted folder (no images/ folder assumed)
    png_files = [f for f in os.listdir(extract_temp) if f.endswith(".png")]
    if not png_files:
        print("No PNG slice images found in SL1 archive.")
        return

    # Clean existing output dir
    if os.path.exists(extracted_image_dir):
        shutil.rmtree(extracted_image_dir)
    os.makedirs(extracted_image_dir, exist_ok=True)

    # Move PNGs to target folder
    for file in png_files:
        shutil.move(os.path.join(extract_temp, file), os.path.join(extracted_image_dir, file))

    print(f"Moved {len(png_files)} images to {extracted_image_dir}")

    # Cleanup
    shutil.rmtree(extract_temp)
    os.remove(zip_file)
    print("Cleaned up temp files.")

# Example usage:
slice_and_extract(
    slicer_path=r"C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer-console.exe",
    stl_path=".\\test_files\\skull.stl",
    config_path="config.ini",
    output_dir="slices_script",
    extracted_image_dir="skull_slices",
)