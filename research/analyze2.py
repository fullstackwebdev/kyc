#!/usr/bin/env python3

import os
import json
import base64
import pandas as pd
import numpy as np
import pyarrow.parquet as pq
from pathlib import Path
from typing import Dict, List, Any
import random

def debug_print_type(obj: Any, prefix: str = "") -> None:
    """Print type information for debugging."""
    if isinstance(obj, dict):
        print(f"{prefix}Dict containing:")
        for k, v in obj.items():
            print(f"{prefix}  {k}: {type(v)}")
            if isinstance(v, (dict, list, np.ndarray)):
                debug_print_type(v, prefix + "    ")
    elif isinstance(obj, list):
        print(f"{prefix}List containing: {type(obj[0]) if obj else 'empty'}")
        if obj and isinstance(obj[0], (dict, list, np.ndarray)):
            debug_print_type(obj[0], prefix + "  ")
    elif isinstance(obj, np.ndarray):
        print(f"{prefix}Numpy array shape: {obj.shape}, dtype: {obj.dtype}")

def numpy_to_python(obj: Any) -> Any:
    """Convert numpy types to Python native types."""
    if isinstance(obj, np.ndarray):
        return [numpy_to_python(x) for x in obj.tolist()]
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: numpy_to_python(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [numpy_to_python(item) for item in obj]
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        print(f"Warning: Unknown type encountered: {type(obj)}")
        return str(obj)

def load_parquet_files(data_dir: str) -> Dict[str, pd.DataFrame]:
    """Load all parquet files from the specified directory."""
    data_path = Path(data_dir)
    parquet_files = {}
    
    for file in data_path.glob("*.parquet"):
        name = file.stem
        parquet_files[name] = pd.read_parquet(file)
        print(f"Loaded {name} with {len(parquet_files[name])} records")
    
    return parquet_files

def convert_to_jsonl(df: pd.DataFrame, output_path: str, dataset_type: str):
    """Convert DataFrame to JSONL format with base64-encoded images."""
    records = []
    
    for idx, row in df.iterrows():
        try:
            # Convert row to dictionary
            row_dict = row.to_dict()
            
            # Debug print for first record
            if idx == 0:
                print("\nFirst record structure:")
                debug_print_type(row_dict)
            
            # Extract and convert image data
            image_data = row_dict['image'].get('bytes', b'')
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            # Convert words to list and join
            words = numpy_to_python(row_dict.get('words', []))
            text_content = ' '.join(words) if isinstance(words, list) else ''
            
            # Create record with explicit numpy conversion
            record = {
                'id': f"{dataset_type}_{idx}",
                'image': image_b64,
                'content': text_content,
                'metadata': {
                    'source': dataset_type,
                    'label_string': numpy_to_python(row_dict.get('label_string', [])),
                    'labels': numpy_to_python(row_dict.get('labels', [])),
                    'boxes': numpy_to_python(row_dict.get('boxes', []))
                }
            }
            
            # Test JSON serialization for each record
            try:
                json.dumps(record)
            except TypeError as e:
                print(f"\nJSON serialization failed for record {idx}")
                debug_print_type(record)
                raise e
            
            records.append(record)
            
            if idx > 0 and idx % 20 == 0:
                print(f"Processed {idx} records...")
            
        except Exception as e:
            print(f"\nError processing record {idx}")
            print(f"Error type: {type(e)}")
            print(f"Error message: {str(e)}")
            continue
    
    # Write to JSONL file
    print(f"\nWriting {len(records)} records to {output_path}")
    with open(output_path, 'w') as f:
        for i, record in enumerate(records):
            try:
                f.write(json.dumps(record) + '\n')
            except TypeError as e:
                print(f"\nFailed to write record {i}")
                debug_print_type(record)
                raise e
    
    return records

def display_sample_and_schema(records: List[Dict], n_samples: int = 25):
    """Display sample records and schema information."""
    if not records:
        print("No records to display")
        return
    
    # Display schema
    print("\nSchema:")
    schema = {
        "id": "string",
        "image": "base64 encoded PNG",
        "content": "string (extracted from words)",
        "metadata": {
            "source": "string (train/valid)",
            "label_string": "list of strings",
            "labels": "list of integers",
            "boxes": "list of coordinate lists"
        }
    }
    print(json.dumps(schema, indent=2))
    
    # Get random samples (but first remove the actual image data for display)
    samples = random.sample(records, min(n_samples, len(records)))
    print(f"\nSample of {len(samples)} records (image data truncated):")
    for sample in samples[:3]:  # Show first 3 samples
        display_sample = sample.copy()
        if len(display_sample['image']) > 50:
            display_sample['image'] = display_sample['image'][:50] + '...'
        print(json.dumps(display_sample, indent=2))

def main():
    base_dir = Path("sizhkhy/passports/data")
    output_dir = Path("converted_data")
    output_dir.mkdir(exist_ok=True)
    
    print(f"Looking for parquet files in: {base_dir.absolute()}")
    
    # Load parquet files
    parquet_files = load_parquet_files(base_dir)
    all_records = []
    
    # Process each dataset
    for dataset_type, df in parquet_files.items():
        output_path = output_dir / f"{dataset_type}.jsonl"
        print(f"\nProcessing {dataset_type} dataset...")
        records = convert_to_jsonl(df, output_path, dataset_type)
        all_records.extend(records)
        print(f"Created {output_path} with {len(records)} records")
    
    # Display samples and schema
    display_sample_and_schema(all_records)

if __name__ == "__main__":
    main()
