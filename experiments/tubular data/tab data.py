import pandas as pd
import numpy as np
from IGTD_Functions import min_max_transform, table_to_image

# 1. Load your dataset
df = pd.read_csv("Datasets/csv/spoofing-merged-gps-only.csv")

# 2. Drop non-numeric columns and labels for image input
# Exclude 'timestamp' and 'label' (they are not features for image encoding)
feature_cols = [col for col in df.columns if col not in ['timestamp', 'label']]
df_features = df[feature_cols].select_dtypes(include=[np.number])

# 3. Normalize features to [0, 1]
norm_data = min_max_transform(df_features.values)

# 4. Determine the scale for the image (try to make it as square as possible)
num_features = norm_data.shape[1]
side = int(np.ceil(np.sqrt(num_features)))  # e.g., 84 features -> 10x10 image (100 pixels)
scale = (side, side)

# 5. Set IGTD parameters
fea_dist_method = 'Pearson'
image_dist_method = 'Euclidean'
save_image_size = 4
max_step = 500
val_step = 30
error = 'abs'
output_dir = 'igtd_spoofing_gps_output'

# 6. Run IGTD to generate images
table_to_image(
    norm_data,
    scale,
    fea_dist_method,
    image_dist_method,
    save_image_size,
    max_step,
    val_step,
    output_dir,
    error
)

print("IGTD image generation complete. Check the 'igtd_spoofing_gps_output/data' folder for output images.")