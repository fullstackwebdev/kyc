# KYC POV - Know Your Customer Proof of Value

KYC POV is a simple Python script that processes a directory of images (e.g., passports, ID cards) and generates a JSON output file with information about each document. The script uses a document classification and PII extraction pipeline to analyze the images and extract relevant data.

## Usage

To use the KYC POV script, follow these steps:

Set the required environment variables and run the script with the input directory:

   ```
   export MODEL_NAME="qwen" 
   export API_BASE="http://localhost:6002/v1"
   export API_KEY="fake-key"
   python kyc.py --input images/
   ```

   This will process all the images in the `images/` directory and write the results to the `output.jsonl` file.

Sample output:

```
Found 5 images
Output will be written to: output.jsonl
Using 8 threads
Processing passport-2 with format .jpg
Processing License-2 with format .jpg
Processing passport-1 with format .jpeg
Processing License-3 with format .jpeg
Processing License 1 with format .png
Processing images: 100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 5/5 [00:00<00:00,  8.96it/s]
Complete! Successfully processed 5 out of 5 images
Output written to: output.jsonl
```

## Output JSON Format

The `output.jsonl` file is a JSON Lines file, where each line represents the analysis results for a single image. The format of each entry is as follows:

```json
{
  "id": "passport-1",
  "filename": "images/passport-1.jpeg",
  "timestamp": "2024-12-09T18:53:32.028045",
  "results": {
    "first_pass": {
      "reasoning": "This is a United States passport, which is a type of identification document used for international travel. It contains personal information such as the holder's name, date of birth, and place of birth, as well as a photograph and a signature. The document also includes security features and a list of security features.",
      "contains_text": true,
      "country": "United States of America",
      "list_of_security_features": "The passport includes a variety of security features such as a hologram, a watermarked photograph, and a microtext signature.",
      "visual_elements": "The visual elements include a portrait of the holder, the American flag, and a bald eagle. The document also features a variety of colors and patterns, including red, white, and blue."
    },
    "error_check": {
      "reasoning": "The image provided is a passport from the United States of America. The document contains the following details: the name of the cardholder is John Doe, the date of birth is 15th March 1996, the place of birth is California, USA, the passport number is 963545637, the issuing authority is the Department of State, the expiration date is 14th April 2027, and there is a photograph of the cardholder's face. The physical descriptors and signature are not explicitly listed in the image, but typically include details such as height, weight, eye color, etc., and the cardholder's actual signature, respectively.",
      "has_errors": false,
      "error_feedback": "No errors or missing information found in the document analysis.",
      "score": 1.0
    },
    "pII_extraction": "- **Name**: John Doe\n- **Date of Birth**: 15 Mar 1996\n- **Address**: California, USA\n- **ID Number**: 963545637\n- **Issuing Authority**: Department of State\n- **Expiration Date**: 14 Apr 2027\n- **Photograph**: A current photo of the cardholder's face\n- **Physical Descriptors**: Not explicitly listed in the image, but typically includes details such as height, weight, eye color, etc.\n- **Signature**: The cardholder's actual signature",
    "identification": "{\"name\":\"John Doe\",\"dob\":\"15 Mar 1996\",\"address\":\"California, USA\",\"id_number\":\"963545637\",\"issuing_authority\":\"Department of State\",\"expiration_date\":\"14 Apr 2027\",\"photograph\":\"A current photo of the cardholder's face\",\"physical_descriptors\":\"Not explicitly listed in the image, but typically includes details such as height, weight, eye color, etc.\",\"signature\":\"The cardholder's actual signature\"}"
  }
}\n
```

## Generating a Report

The `report.py` script can be used to generate a human-readable report from the `output.jsonl` file. To use it, simply run:

```
python report.py
```

```
Timestamp: 2024-12-09T18:51:39.039574
Document Type: This is a United States passport, which is a type of identification document used for international travel. It contains personal information such as the holder's name, date of birth, and place of birth, as well as a photograph and a signature. The document also includes security features and a list of security features.
Country: United States of America
Security Features: The passport includes a variety of security features such as a hologram, a watermarked photograph, and a microtext signature.
Error Check: No Errors
Error Feedback: No errors or missing information found in the document analysis.
Score: 1.0
PII Extraction:
- **Name**: John Doe
- **Date of Birth**: 15 Mar 1996
- **Address**: California, USA
- **ID Number**: 963545637
- **Issuing Authority**: Department of State
- **Expiration Date**: 14 Apr 2027
- **Photograph**: A current photo of the cardholder's face
- **Physical Descriptors**: Not explicitly listed in the image, but typically includes details such as height, weight, eye color, etc.
- **Signature**: The cardholder's actual signature
Identification:
"{\"name\":\"John Doe\",\"dob\":\"15 Mar 1996\",\"address\":\"California, USA\",\"id_number\":\"963545637\",\"issuing_authority\":\"Department of State\",\"expiration_date\":\"14 Apr 2027\",\"photograph\":\"A current photo of the cardholder's face\",\"physical_descriptors\":\"Not explicitly listed in the image, but typically includes details such as height, weight, eye color, etc.\",\"signature\":\"The cardholder's actual signature\"}"

Timestamp: 2024-12-09T18:51:39.109987
Document Type: This is a passport, as indicated by the presence of a photograph, a machine-readable zone (MRZ), and the design elements typical of a passport, such as the eagle and the American flag.
Country: United States of America
Security Features: The passport contains several security features, including a hologram, a watermarked image, a microprint, and a UV security feature. There is also a machine-readable zone (MRZ) at the bottom of the passport.
Error Check: Errors Found
Error Feedback: The image is a passport, not a driver's license. The reference text provided is for a driver's license, which includes fields such as "issuing authority," "expiration date," and "photograph," which are not present in the image. The image does not contain a photograph, and the text fields are not filled out with the information provided in the reference text.
Score: 0.0
PII Extraction:
- Name: Benjamin Franklin
- Date of Birth: 17 Jan 1706
- Address: 15 Jan 2028
- ID Number: 575034801
- Issuing Authority: Department of Motor Vehicles
- Expiration Date: 15 Jan 2028
- Photograph: A current photo of the cardholder's face, used for identification purposes.
- Physical Descriptors: Details about the person's physical characteristics, like height, weight, eye color, etc.
- Signature: The cardholder's actual signature, used for verification purposes.
Identification:
"{\"name\":\"Benjamin Franklin\",\"dob\":\"17 Jan 1706\",\"address\":\"15 Jan 2028\",\"id_number\":\"575034801\",\"issuing_authority\":\"Department of Motor Vehicles\",\"expiration_date\":\"15 Jan 2028\",\"photograph\":\"A current photo of the cardholder's face, used for identification purposes.\",\"physical_descriptors\":\"Details about the person's physical characteristics, like height, weight, eye color, etc.\",\"signature\":\"The cardholder's actual signature, used for verification purposes.\"}"

Timestamp: 2024-12-09T18:51:39.444309
Document Type: This is a California Driver's License, which is a form of identification used for verifying the identity of an individual. It is a valid form of KYC material.
Country: California
Security Features: The document contains a variety of security features, including a hologram, a watermarked background, a microprint, and a UV security feature.
Error Check: No Errors
Error Feedback: The document appears to be a complete and accurate representation of a California driver's license. All required information is present, and the layout follows the standard format for such documents.
Score: 1.0
PII Extraction:
N/A
Identification:
"{\"name\":\"[Full Legal Name]\",\"dob\":\"[MM/DD/YYYY]\",\"address\":\"[Current Residential Address]\",\"id_number\":\"[Unique Identification Number]\",\"issuing_authority\":\"[Government Agency or Department]\",\"expiration_date\":\"[Date When ID Document Will Expire]\",\"photograph\":\"[Current Photo of Cardholder's Face]\",\"physical_descriptors\":\"[Details About the Person's Physical Characteristics]\",\"signature\":\"[Cardholder's Actual Signature]\"}"

Timestamp: 2024-12-09T18:51:39.493198
Document Type: This is a North Carolina Driver's License, which is a type of identification document used for verifying the identity and age of an individual. It is a valid form of KYC material.
Country: North Carolina, USA
Security Features: The document contains several security features, including a holographic overlay, a microprint, a watermarked image, and a security thread.
Error Check: No Errors
Error Feedback: No errors or missing information found in the provided document.
Score: 1.0
PII Extraction:
- **Name**: John Q. Public
- **Date of Birth**: 05/28/1952
- **Address**: 1234 Your Street, Your City, NC 55555-1234
- **ID Number**: 1000123456789
- **Issuing Authority**: North Carolina Department of Motor Vehicles
- **Expiration Date**: 05/28/2024
- **Photograph**: Present
- **Physical Descriptors**: Height 5'10", Hair Color: Gry, Eye Color: Gry, 12 Restr
- **Signature**: Present
Identification:
"{\"name\":\"John Q. Public\",\"dob\":\"05/28/1952\",\"address\":\"1234 Your Street, Your City, NC 55555-1234\",\"id_number\":\"1000123456789\",\"issuing_authority\":\"North Carolina Department of Motor Vehicles\",\"expiration_date\":\"05/28/2024\",\"photograph\":\"Present\",\"physical_descriptors\":\"Height 5'10\",\"signature\":\"Present\"}"

Timestamp: 2024-12-09T18:51:39.495485
Document Type: This is a Pennsylvania Driver's License, which is a form of identification used for various purposes, including verifying the identity of an individual. It is not for Real ID purposes, indicating it may not be accepted for federal identification purposes.
Country: Pennsylvania
Security Features: The document contains a variety of security features, including a holographic overlay, microtext, and a watermarked image of the state seal.
Error Check: No Errors
Error Feedback: The document is complete and accurate. There are no errors or missing information.
Score: 1.0
PII Extraction:
Name: Janice Ann Sample
Date of Birth: 01/07/2005
Address: 123 Main Street, Apt. 1, Harrisburg, PA 17101-0000
ID Number: 999999999
Issuing Authority: Pennsylvania Department of Motor Vehicles
Expiration Date: 01/08/2026
Photograph: Present
Physical Descriptors: Height: 5'05", Eyes: BLU
Signature: Present
Identification:
"{\"name\":\"Janice Ann Sample\",\"dob\":\"01/07/2005\",\"address\":\"123 Main Street, Apt. 1, Harrisburg, PA 17101-0000\",\"id_number\":\"999999999\",\"issuing_authority\":\"Pennsylvania Department of Motor Vehicles\",\"expiration_date\":\"01/08/2026\",\"photograph\":\"Present\",\"physical_descriptors\":\"Height: 5'05\",\"signature\":\"Present\"}"

```