import pandas as pd
from pathlib import Path

# 1. Where your CSVs are stored
DATA_DIR = Path("backend/data")

# 2. List all CSV files automatically (no manual typing needed)
csv_files = list(DATA_DIR.glob("*.csv"))

print(f"✅ Found {len(csv_files)} CSV files:", [f.name for f in csv_files])

# 3. Read and merge them
df_list = [pd.read_csv(f) for f in csv_files]
merged_df = pd.concat(df_list, ignore_index=True)

print(f"✅ Merged shape: {merged_df.shape}")

# 4. Save optimized Parquet file
output_file = DATA_DIR / "all_crops.parquet"
merged_df.to_parquet(output_file, index=False)

print(f"🎉 Saved merged file as {output_file}")
