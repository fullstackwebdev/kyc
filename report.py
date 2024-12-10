import json
from pathlib import Path

def generate_report(input_file):
    """
    Reads the input JSON Lines file and generates a report.
    
    Args:
        input_file (str): Path to the input JSON Lines file.
    """
    with open(input_file, 'r') as f:
        results = [json.loads(line) for line in f]

    for result in results:
        print("Timestamp:", result['timestamp'])
        print("Document Type:", result['results']['first_pass']['reasoning'])
        print("Country:", result['results']['first_pass']['country'])
        print("Security Features:", result['results']['first_pass']['list_of_security_features'])
        print("Error Check:", 'No Errors' if not result['results']['error_check']['has_errors'] else 'Errors Found')
        print("Error Feedback:", result['results']['error_check']['error_feedback'])
        print("Score:", result['results']['error_check']['score'])
        print("PII Extraction:")
        pii_extraction = result['results']['pII_extraction']
        if pii_extraction:
            for item in pii_extraction.split('\n'):
                print(item)
        else:
            print("N/A")
        
        # Handle the identification field separately
        identification = result['results']['identification']
        if identification:
            print("Identification:")
            for line in identification.split('\n'):
                print(line)
        else:
            print("Identification: N/A")
        print()

if __name__ == "__main__":
    input_file = 'output.jsonl'
    generate_report(input_file)