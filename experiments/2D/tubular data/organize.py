import os
import shutil

# Set this to the directory where your photos are
PHOTO_DIR = "image-results-spoofing"

# Loop through all files in the directory
for filename in os.listdir(PHOTO_DIR):
    # Only process files that match the expected format
    if '-' in filename:
        folder_name = filename.split('-')[0]
        folder_path = os.path.join(PHOTO_DIR, folder_name)

        # Create the folder if it doesn't exist
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # Move the file into the corresponding folder
        src_path = os.path.join(PHOTO_DIR, filename)
        dst_path = os.path.join(folder_path, filename)
        shutil.move(src_path, dst_path)
        print(f"Moved {filename} to {folder_path}")