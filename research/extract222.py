import pyarrow.parquet as pq
import json
import os
import base64
import numpy as np

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                          np.int16, np.int32, np.int64, np.uint8,
                          np.uint16, np.uint32, np.uint64)):
            return int(obj)
        if isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)
        if isinstance(obj, bytes):
            return base64.b64encode(obj).decode('utf-8')
        return super(NumpyEncoder, self).default(obj)

# Create output directories
os.makedirs('output/with_images', exist_ok=True)
os.makedirs('output/without_images', exist_ok=True)

# Find all parquet files
def find_parquet_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.parquet'):
                yield os.path.join(root, file)

# Process each parquet file
for parquet_file in find_parquet_files('.'):
    print(f"Processing {parquet_file}")
    
    # Read parquet file
    table = pq.read_table(parquet_file)
    df = table.to_pandas()
    
    # Get base filename
    filename = os.path.basename(parquet_file).replace('.parquet', '.jsonl')
    
    # Save with images
    with open(f'output/with_images/{filename}', 'w') as f:
        for record in df.to_dict('records'):
            f.write(json.dumps(record, cls=NumpyEncoder) + '\n')
    
    # Save without images
    if 'image' in df.columns:
        df_no_img = df.drop('image', axis=1)
    else:
        df_no_img = df
        
    with open(f'output/without_images/{filename}', 'w') as f:
        for record in df_no_img.to_dict('records'):
            f.write(json.dumps(record, cls=NumpyEncoder) + '\n')

print("Conversion complete!")
