#!/usr/bin/env python3
import os 
import argparse
import json
import base64
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

from dataclasses import asdict
from typing import Optional
import traceback

import sys
import imghdr
# Basic setup
litellm.suppress_debug_info = True
dotenv.load_dotenv()



MODEL_NAME = os.getenv("MODEL_NAME", "qwen")
API_BASE = os.getenv("API_BASE", "http://localhost:6002/v1")
API_KEY = os.getenv("API_KEY", "fake-key")


# Configure LM
qwen_lm = dspy.LM(
    # model="openai/qwen",
    model=f"openai/{MODEL_NAME}",
    # api_base="http://localhost:6002/v1",
    api_base=API_BASE,
    # api_key="fake-key",
    api_key=API_KEY,
    max_tokens=2000,
    temperature=0.1
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
    # IMPORTANT: Use dspy.Image for image input, not string type
    image: dspy.Image = InputField()
    previous_feedback: str = InputField(desc="Previous feedback if this is a retry, or 'N/A'")
    
    # Basic outputs matching original implementation style
    if_kyc_material: bool = OutputField(desc="True if the image is KYC material")
    contains_text: bool = OutputField(desc="True if the image contains any text")
    country: str = OutputField(desc="Country of issue")
    list_of_security_features: str = OutputField(desc="List of security features or N/A")
    visual_elements: str = OutputField(desc="Description of non-text visual elements or N/A")

   

class ExtractPIISignatureLongForm(dspy.Signature):
    """Extract personally identifiable information (PII) from a document image, including 
Name - The full legal name of the individual, usually written as First Middle Last.
Date of Birth - The person's date of birth, often shown as MM/DD/YYYY.
Address - The cardholder's current residential address.
ID Number - A unique identification number assigned to the individual, such as a driver's license or state ID number.
Issuing Authority - The government agency or department that issued the ID, such as the Department of Motor Vehicles.
Expiration Date - The date when the ID document will expire and need to be renewed.
Photograph - A current photo of the cardholder's face, used for identification purposes.
Physical Descriptors - Details about the person's physical characteristics, like height, weight, eye color, etc.
Signature - The cardholder's actual signature, """
    
    #image 
    image: dspy.Image = InputField()
    pII_information_long_form: str = OutputField(desc="Extracted PII information in long form")


#import pydantic stuff
from pydantic import BaseModel

class Identification(BaseModel):
    name: str
    dob: str
    address: str
    id_number: str
    issuing_authority: str
    expiration_date: str
    photograph: str
    physical_descriptors: str
    signature: str

class ExtractPIISignature(dspy.Signature):
    """Extract personally identifiable information (PII) from a document image, including
    Name - The full legal name of the individual, usually written as First Middle Last.
    Date of Birth - The person's date of birth, often shown as MM/DD/YYYY.
    Address - The cardholder's current residential address.
    ID Number - A unique identification number assigned to the individual, such as a driver's license or state ID number.
    Issuing Authority - The government agency or department that issued the ID, such as the Department of Motor Vehicles.
    Expiration Date - The date when the ID document will expire and need to be renewed.
    Photograph - A current photo of the cardholder's face, used for identification purposes.
    Physical Descriptors - Details about the person's physical characteristics, like height, weight, eye color, etc.
    Signature - The cardholder's actual signature.
    """

    # pII_information_long_form is the input
    pII_information = InputField(desc="Extracted PII information in long form")
    identification: Identification = OutputField(desc="Extracted PII information in structured form")




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
    # Keep same input structure as reference
    image: dspy.Image = InputField()
    reference_text: str = InputField()
    raw_ocr_text: str = InputField()
    
    # Match reference implementation outputs
    has_errors: bool = OutputField(desc="True if any errors or missing information found")
    error_feedback: str = OutputField(desc="Detailed feedback about errors or missing information")
    score: float = OutputField(desc="The score of the analysis")

class ImageAnalysisPipeline(dspy.Module):
    def __init__(self):
        super().__init__()
        self.initial_analysis = dspy.ChainOfThought(DocumentClassificationSignature)
        self.error_check = dspy.ChainOfThought(ErrorCheckSignature)
        self.extract_pii = dspy.ChainOfThought(ExtractPIISignatureLongForm)
        self.extract_pii_information = dspy.ChainOfThought(ExtractPIISignature)
    
    def forward(self, image, reference_text):
        # Follow reference implementation flow exactly
        initial_results = self.initial_analysis(
            image=image,
            previous_feedback="N/A"
        )
        


        # Extract PII information
        pII_information_long_form = self.extract_pii(image=image).pII_information_long_form

        # now we have the pII_extraction, we can pass it to the ExtractPIISignature
        # and get the structured information
        identification = self.extract_pii_information(pII_information=pII_information_long_form)


        data = identification.identification
        raw_ocr_text = json.dumps(data.json())


        error_check_results = self.error_check(
            image=image,
            reference_text=reference_text,
            raw_ocr_text=raw_ocr_text
        )
        # Keep retry logic from reference
        final_results = initial_results
        if error_check_results.has_errors:
            final_results = self.initial_analysis(
                image=image,
                previous_feedback=error_check_results.error_feedback
            )
        
        # Match reference output structure exactly
        return {
            "first_pass": {
                "reasoning": initial_results.reasoning,
                "contains_text": initial_results.contains_text,
                "country": initial_results.country,
                "list_of_security_features": initial_results.list_of_security_features,
                "visual_elements": initial_results.visual_elements,
            },
            "error_check": {
                "reasoning": error_check_results.reasoning,
                "has_errors": error_check_results.has_errors,
                "error_feedback": error_check_results.error_feedback,
                "score": error_check_results.score
            },
            "pII_extraction": pII_information_long_form,
            "identification": raw_ocr_text
        }

import imghdr

def read_image_as_base64(image_path):
    """Read image file and convert to base64"""
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
            
        # Detect image type using imghdr
        image_type = imghdr.what(None, h=image_data)
        if image_type == 'jpeg':
            mime_type = 'image/jpeg'
        elif image_type == 'png':
            mime_type = 'image/png'
        else:
            # Handle other image types as needed
            mime_type = 'image/jpeg'
            
        b64_data = base64.b64encode(image_data).decode('utf-8')
        return f"data:{mime_type};base64,{b64_data}"
    except Exception as e:
        print(f"Error reading image {image_path}: {str(e)}")
        return None

def process_image(image_path, output_file, lock):
    """Process a single image file and write results to output file"""
    try:
        # Get image with correct mime type
        image_url = read_image_as_base64(Path(image_path))
        if not image_url:
            return False
            
        file_id = Path(image_path).stem
        print(f"Processing {file_id} with format {Path(image_path).suffix}")
        
        # Process with pipeline
        predictor = ImageAnalysisPipeline()
        results = predictor(image=image_url, reference_text="N/A")
        
        output_entry = {
            "id": file_id,
            "filename": str(image_path),
            "timestamp": datetime.now().isoformat(),
            "results": results
        }
        
        with lock:
            with open(output_file, 'a') as f:
                f.write(json.dumps(output_entry) + '\n')
                f.flush()
        
        print(f"Successfully processed {image_path}")
        return True
    except Exception as e:
        print(f"Error processing {image_path}: {str(e)}")
        print(f"Image format: {Path(image_path).suffix}")
        # full trace
        print(traceback.format_exc())
        # line numbers
        print(traceback.extract_tb(sys.exc_info()[2]))
        return False

def main():
    parser = argparse.ArgumentParser(description='Process directory of images with DSPy KYC pipeline')
    parser.add_argument('--input', required=True,
                        help='Input directory containing images')
    parser.add_argument('--output', default='output.jsonl',
                        help='Output JSONL file (default: output.jsonl)')
    parser.add_argument('--threads', type=int, default=8,
                        help='Number of processing threads (default: 8)')
    
    args = parser.parse_args()
    
    input_dir = Path(args.input)
    output_file = args.output
    
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input path {input_dir} is not a directory")
    
    # Get list of image files
    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png']:
        image_files.extend(input_dir.glob(ext))
    
    if not image_files:
        print(f"No image files found in {input_dir}")
        return
    
    print(f"Found {len(image_files)} images")
    print(f"Output will be written to: {output_file}")
    print(f"Using {args.threads} threads")
    
    # Create empty output file
    with open(output_file, 'w') as f:
        pass
    
    file_lock = threading.Lock()
    successful = 0
    
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = []
        for image_path in image_files:
            future = executor.submit(process_image, image_path, output_file, file_lock)
            futures.append(future)
        
        for future in tqdm(futures, desc="Processing images"):
            if future.result():
                successful += 1
    
    print(f"\nComplete! Successfully processed {successful} out of {len(image_files)} images")
    print(f"Output written to: {output_file}")

if __name__ == "__main__":
    main()