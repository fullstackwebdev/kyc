#!/usr/bin/env python3

import pyarrow.parquet as pq
from pathlib import Path

def main():
    # Set the directory path
    data_dir = Path("sizhkhy/passports/data")
    print(f"Looking for parquet files in: {data_dir.absolute()}")
    
    # Check if directory exists
    if not data_dir.exists():
        print(f"Directory not found: {data_dir}")
        return
    
    # Find all parquet files
    parquet_files = list(data_dir.glob("*.parquet"))
    if not parquet_files:
        print(f"No parquet files found in {data_dir}")
        return
    
    # Examine each file
    for file_path in parquet_files:
        print(f"\nExamining: {file_path.name}")
        try:
            # Open the parquet file
            pf = pq.ParquetFile(file_path)
            
            # Print basic info
            print(f"Number of row groups: {pf.num_row_groups}")
            print(f"Schema:")
            print(pf.schema_arrow)
            
            # Read first row group
            table = pf.read_row_group(0)
            print(f"\nFirst row group has {len(table)} rows")
            
        except Exception as e:
            print(f"Error examining {file_path.name}: {str(e)}")

if __name__ == "__main__":
    main()
