## Dataset Organization and Download Links

To set up this project with the original datasets, please download the files from the sources below and place them in their corresponding folders as shown in the directory structure.

### Original Data Sources

- **UAV-ATTACK Dataset**  
  Download from: [IEEE DataPort](https://ieee-dataport.org/open-access/uav-attack-dataset)  
  Place `spoofing-merged-gps-only.csv` in:  
  ```
  Datasets/csv/UAVATTACK/
  ```

- **2D Spoofing Dataset**  
  Download from: [Mendeley Data](https://data.mendeley.com/datasets/z7dj3yyzt8/3)  
  Place `GPS_Data_Simplified_2D_Feature_Map.xlsx` in:  
  ```
  Datasets/excel/2dSpoofingDataset/
  ```

### Synthetic Results

Our generated synthetic datasets can be found here:  
[Google Drive - Synthetic Results](https://drive.google.com/drive/folders/1l2LfGwJ8FRzE115wkMUHQRaGiru-SwGv)

---

### Final Folder Structure

Your directory should look like this after all files are downloaded and placed correctly:

```plaintext
Datasets/
├── csv/
│   └── UAVATTACK/
│       ├── spoofing-merged-gps-only.csv
│       ├── spoofing_ctgan_100000.csv
│       ├── spoofing_ctgan_1000000.csv
│       ├── spoofing_ctgan_10000.csv
│       ├── spoofing_gc_100000.csv
│       ├── spoofing_gc_1000000.csv
│       ├── spoofing_gc_10000.csv
│       ├── spoofing_tvae_100000.csv
│       ├── spoofing_tvae_1000000.csv
│       ├── spoofing_tvae_10000.csv
├── excel/
│   └── 2dSpoofingDataset/
│       ├── GPS_Data_Simplified_2D_Feature_Map.xlsx
│       ├── spoofing_ctgan_100000.csv
│       ├── spoofing_ctgan_1000000.csv
│       ├── spoofing_ctgan_10000.csv
│       ├── spoofing_gc_100000.csv
│       ├── spoofing_gc_1000000.csv
│       ├── spoofing_gc_10000.csv
│       ├── spoofing_tvae_100000.csv
│       ├── spoofing_tvae_1000000.csv
│       └── spoofing_tvae_10000.csv
```