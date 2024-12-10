#!/usr/bin/env python3

import argparse
import json
import uuid
import threading
import dspy
import dotenv
import litellm
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
from dspy.signatures import InputField, OutputField

# Basic setup
litellm.suppress_debug_info = True
dotenv.load_dotenv()

# Configure LM
qwen_lm = dspy.LM(
    model="openai/qwen",
    api_base="http://localhost:6002/v1",
    api_key="fake-key",
    max_tokens=1000,
    temperature=0.2
)
dspy.settings.configure(lm=qwen_lm)

class DocumentClassificationSignature(dspy.Signature):
    """You are a Know Your Customer (KYC) document verification expert. Analyze this identification document image.
    
    Rules:
    1. First identify if this is a passport or ID card
    2. Locate and identify which country issued this document
    3. Check document format and security features
    4. Note the document's overall condition and quality
    5. Document text layout and positioning
    6. Note any visual elements or features
    7. Look for tampering or unusual elements
    8. Assess photo quality and integration
    """
    image: dspy.Image = InputField()
    previous_feedback: str = InputField(desc="Previous feedback if this is a retry, or 'N/A'")
    
    if_kyc_material: bool = OutputField(desc="True if the image is KYC material")
    contains_text: bool = OutputField(desc="True if the image contains any text")
    country: str = OutputField(desc="Country of issue")
    list_of_security_features: str = OutputField(desc="List of security features")
    overall_condition: str = OutputField(desc="Overall condition and quality")
    tampering: bool = OutputField(desc="True if tampering or unusual elements found")
    visual_elements: str = OutputField(desc="Description of non-text visual elements")
    raw_ocr_text: str = OutputField(desc="Complete text extraction with formatting notes")
    pII_extraction: str = OutputField(desc="Name, address, personal information")

class ErrorCheckSignature(dspy.Signature):
    """Verify the completeness and accuracy of document analysis by comparing against reference data.
    Check every single detail character by character. This is not meant to be an overview or summary.
    
    Rules:
    1. Compare all text fields exactly
    2. Check numbers and dates carefully
    3. Verify name spellings precisely
    4. Look for missing or extra information
    5. Note any formatting differences
    6. Check for OCR errors or misreadings
    7. Verify document number formats
    """
    image: dspy.Image = InputField()
    reference_text: str = InputField()
    raw_ocr_text: str = InputField()
    
    has_errors: bool = OutputField(desc="True if any errors or missing information found")
    error_feedback: str = OutputField(desc="Detailed feedback about errors or missing information")
    score: float = OutputField(desc="The score of the analysis")









class ImageAnalysisPipeline(dspy.Module):
    def __init__(self):
        super().__init__()
        self.initial_analysis = dspy.ChainOfThought(DocumentClassificationSignature)
        self.error_check = dspy.ChainOfThought(ErrorCheckSignature)
    
    def forward(self, image, reference_text):
        initial_results = self.initial_analysis(
            image=image,
            previous_feedback="N/A"
        )
        
        error_check_results = self.error_check(
            image=image,
            reference_text=reference_text,
            raw_ocr_text=initial_results.raw_ocr_text
        )
        
        final_results = initial_results
        if error_check_results.has_errors:
            final_results = self.initial_analysis(
                image=image,
                previous_feedback=error_check_results.error_feedback
            )
        
        return {
            "first_pass": {
                "reasoning": initial_results.reasoning,
                "if_kyc_material": initial_results.if_kyc_material,
                "contains_text": initial_results.contains_text,
                "country": initial_results.country,
                "list_of_security_features": initial_results.list_of_security_features,
                "overall_condition": initial_results.overall_condition,
                "tampering": initial_results.tampering,
                "visual_elements": initial_results.visual_elements,
                "raw_ocr_text": initial_results.raw_ocr_text,
                "pII_extraction": initial_results.pII_extraction
            },
            "error_check": {
                "reasoning": error_check_results.reasoning,
                "has_errors": error_check_results.has_errors,
                "error_feedback": error_check_results.error_feedback,
                "score": error_check_results.score
            },
            "final_pass": {
                "reasoning": final_results.reasoning,
                "if_kyc_material": final_results.if_kyc_material,
                "contains_text": final_results.contains_text,
                "country": final_results.country,
                "list_of_security_features": final_results.list_of_security_features,
                "overall_condition": final_results.overall_condition,
                "tampering": final_results.tampering,
                "visual_elements": final_results.visual_elements,
                "raw_ocr_text": final_results.raw_ocr_text,
                "pII_extraction": final_results.pII_extraction
            } if error_check_results.has_errors else None
        }
def process_sample(sample, output_file, lock):
    """Process a single sample and write results to output file"""
    try:
        predictor = ImageAnalysisPipeline()
        
        # IMPORTANT: Keep exact image handling from reference
        image_b64 = sample['image']
        image_url = 'data:image/jpeg;base64,' + image_b64
        
        # Match reference text field name
        reference_text = sample.get('text', 'N/A')
        
        results = predictor(image=image_url, reference_text=reference_text)
        
        output_entry = {
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "input": {k: v for k, v in sample.items() if k != 'image'}
        }
        
        with lock:
            with open(output_file, 'a') as f:
                f.write(json.dumps(output_entry) + '\n')
                f.flush()
                
        return True
    except Exception as e:
        print(f"Error processing sample: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Process images with DSPy pipeline')
    parser.add_argument('--input', default='image_data_and_text.jsonl',
                        help='Input JSONL file (default: image_data_and_text.jsonl)')
    parser.add_argument('--output', default=None,
                        help='Output JSONL file (default: output_analysis_<uniqueid>.jsonl)')
    parser.add_argument('--threads', type=int, default=8,
                        help='Number of processing threads (default: 8)')
    
    args = parser.parse_args()
    
    input_file = Path(args.input)
    output_file = args.output or f"output_analysis_{str(uuid.uuid4())[:8]}.jsonl"
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file {input_file} not found")
    
    # Create empty output file
    with open(output_file, 'w') as f:
        pass
    
    with open(input_file, 'r') as f:
        samples = [json.loads(line) for line in f]
    
    if not samples:
        print(f"No samples found in {input_file}")
        return
    
    print(f"Found {len(samples)} samples")
    print(f"Output will be written to: {output_file}")
    print(f"Using {args.threads} threads")
    
    file_lock = threading.Lock()
    
    successful = 0
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = []
        for sample in samples:
            future = executor.submit(process_sample, sample, output_file, file_lock)
            futures.append(future)
        
        for future in tqdm(futures, desc="Processing samples"):
            if future.result():
                successful += 1
    
    print(f"\nComplete! Successfully processed {successful} out of {len(samples)} samples")
    print(f"Output written to: {output_file}")

if __name__ == "__main__":
    main()