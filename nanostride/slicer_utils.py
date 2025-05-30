import os
import subprocess
import zipfile
import shutil

def slice_and_extract(slicer_path, stl_path, config_path, output_dir, extracted_image_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    basename = os.path.splitext(os.path.basename(stl_path))[0]
    sl1_file = os.path.join(output_dir, f"{basename}.sl1")
    zip_file = os.path.join(output_dir, f"{basename}.zip")

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
        raise RuntimeError(f"Slicing failed:\n{result.stderr}")
    
    os.rename(sl1_file, zip_file)

    extract_temp = os.path.join(output_dir, "temp_extract")
    os.makedirs(extract_temp, exist_ok=True)

    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(extract_temp)

    png_files = [f for f in os.listdir(extract_temp) if f.endswith(".png")]
    if not png_files:
        raise FileNotFoundError("No PNG slice images found.")

    if os.path.exists(extracted_image_dir):
        shutil.rmtree(extracted_image_dir)
    os.makedirs(extracted_image_dir)

    for file in png_files:
        shutil.move(os.path.join(extract_temp, file), os.path.join(extracted_image_dir, file))

    shutil.rmtree(extract_temp)
    os.remove(zip_file)
