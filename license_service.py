import requests
from datetime import datetime
import csv
import io

class LicenseValidator:
    def __init__(self):
        self.sheet_url = "https://docs.google.com/spreadsheets/d/1-zNSIDD5iftss3SAurzmQKHgSc2ZYPC7BEyw2ZcQWrc/edit?usp=sharing"
        self.sheet_id = "1-zNSIDD5iftss3SAurzmQKHgSc2ZYPC7BEyw2ZcQWrc"
        
    def validate_license(self, license_key, user_email):
        """
        Validate license key against Google Sheets using CSV export
        Returns: dict with 'valid', 'expired', 'message' keys
        """
        try:
            # Create CSV export URL for the Google Sheet
            csv_url = f"https://docs.google.com/spreadsheets/d/{self.sheet_id}/export?format=csv&gid=0"
            
            # Fetch the CSV data
            response = requests.get(csv_url, timeout=10)
            response.raise_for_status()
            
            # Parse CSV data
            csv_data = csv.DictReader(io.StringIO(response.text))
            
            # Find matching license key
            for row in csv_data:
                stored_license_key = row.get('License Key', '').strip()
                if stored_license_key == license_key.strip():
                    # Check if email matches
                    sheet_email = row.get('Primary Email', '').strip().lower()
                    if sheet_email != user_email.lower():
                        return {
                            'valid': False,
                            'expired': False,
                            'message': 'License key is not associated with your email address.'
                        }
                    
                    # Check expiry date
                    expiry_date_str = row.get('Expiry Date', '').strip()
                    if expiry_date_str:
                        try:
                            # Try different date formats
                            expiry_date = None
                            for date_format in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']:
                                try:
                                    expiry_date = datetime.strptime(expiry_date_str, date_format)
                                    break
                                except ValueError:
                                    continue
                            
                            if expiry_date is None:
                                return {
                                    'valid': False,
                                    'expired': False,
                                    'message': 'Invalid expiry date format in database.'
                                }
                            
                            if expiry_date.date() < datetime.now().date():
                                return {
                                    'valid': False,
                                    'expired': True,
                                    'message': f'License key expired on {expiry_date.strftime("%Y-%m-%d")}.'
                                }
                        except Exception as e:
                            return {
                                'valid': False,
                                'expired': False,
                                'message': 'Error processing expiry date.'
                            }
                    
                    # All checks passed
                    return {
                        'valid': True,
                        'expired': False,
                        'message': 'License key is valid and active.',
                        'name': row.get('Name', ''),
                        'expiry_date': expiry_date_str
                    }
            
            # License key not found
            return {
                'valid': False,
                'expired': False,
                'message': 'License key not found in database.'
            }
            
        except requests.RequestException as e:
            print(f"Network error validating license: {str(e)}")
            return {
                'valid': False,
                'expired': False,
                'message': 'Unable to connect to license database. Please check your internet connection and try again.'
            }
        except Exception as e:
            print(f"Error validating license: {str(e)}")
            return {
                'valid': False,
                'expired': False,
                'message': 'Unable to validate license at this time. Please try again later.'
            }
    
    def get_all_licenses(self):
        """
        Retrieve all licenses from Google Sheets for expiry monitoring
        Returns: list of dicts with license data
        """
        try:
            # Create CSV export URL for the Google Sheet
            csv_url = f"https://docs.google.com/spreadsheets/d/{self.sheet_id}/export?format=csv&gid=0"
            
            # Fetch the CSV data
            response = requests.get(csv_url, timeout=10)
            response.raise_for_status()
            
            # Parse CSV data
            csv_data = csv.DictReader(io.StringIO(response.text))
            
            licenses = []
            for row in csv_data:
                license_key = row.get('License Key', '').strip()
                if license_key:  # Only include rows with license keys
                    licenses.append({
                        'license_key': license_key,
                        'name': row.get('Name', '').strip(),
                        'email': row.get('Primary Email', '').strip(),
                        'expiry_date': row.get('Expiry Date', '').strip()
                    })
            
            return licenses
            
        except Exception as e:
            print(f"Error fetching all licenses: {str(e)}")
            return []

# Create global instance
license_validator = LicenseValidator()