from gps_ids.images import TWO_D_IMAGES, manifest_path, split

manifest = split(TWO_D_IMAGES)
for cls, entry in manifest["classes"].items():
    print(f"{cls}: {len(entry['train'])} train, {len(entry['test'])} test")
print(f"Split membership recorded in {manifest_path(TWO_D_IMAGES)}")
