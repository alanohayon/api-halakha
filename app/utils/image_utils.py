import os
import glob

def get_latest_image_path(downloads_folder="/Users/alanohayon/Downloads"):
    image_extensions = ["*.jpg", "*.jpeg", "*.png", "*.gif", "*.webp"]
    image_files = []
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(downloads_folder, ext)))
    if not image_files:
        return None
    latest_image = max(image_files, key=os.path.getmtime)
    print("lget_latest_image_path latest_image", latest_image)
    return latest_image