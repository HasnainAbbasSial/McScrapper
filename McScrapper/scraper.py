import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urljoin

class FMCSAScraper:
    def __init__(self, start_mc, end_mc=None, entity_type='Carrier'):
        self.start_mc = start_mc
        self.end_mc = end_mc
        self.entity_type = entity_type
        self.should_stop = False
        self.session = requests.Session()
        
        # Set headers to mimic a browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def stop(self):
        self.should_stop = True
    
    def scrape(self, progress_callback, complete_callback):
        """Main scraping method"""
        current_mc = self.start_mc
        
        try:
            while not self.should_stop:
                # Check if we've reached the end MC
                if self.end_mc and current_mc > self.end_mc:
                    break
                
                progress_callback(current_mc, f'Checking MC {current_mc}...')
                
                try:
                    # Scrape individual MC
                    result = self.scrape_mc(current_mc)
                    
                    if result is None:
                        progress_callback(current_mc, 'Not found')
                    elif result == 'invalid':
                        progress_callback(current_mc, 'Invalid (filtered out)')
                    else:
                        progress_callback(current_mc, 'valid', result)
                    
                except Exception as e:
                    progress_callback(current_mc, f'Error: {str(e)}')
                
                # Delay to avoid being blocked
                time.sleep(1)
                current_mc += 1
                
        except Exception as e:
            progress_callback(current_mc, f'Scraping failed: {str(e)}')
        
        finally:
            complete_callback()
    
    def scrape_mc(self, mc_number):
        """Scrape data for a single MC number using complete FMCSA workflow"""
        
        # Step 1: Get main carrier snapshot
        main_data = self.get_main_carrier_data(mc_number)
        if not main_data:
            return None
        
        # Step 2: Get additional details from SMS and Registration pages
        enhanced_data = self.get_enhanced_carrier_data(main_data)
        
        if enhanced_data and self.is_valid_record(enhanced_data):
            return enhanced_data
        else:
            return 'invalid' if enhanced_data else None
    
    def get_main_carrier_data(self, mc_number):
        """Get main carrier data from FMCSA snapshot - MC search only"""
        url = 'https://safer.fmcsa.dot.gov/query.asp'
        
        # Only search by MC number - do NOT fall back to USDOT search
        params = {
            'searchtype': 'ANY',
            'query_type': 'queryCarrierSnapshot', 
            'query_param': 'MC_MX',
            'query_string': str(mc_number)
        }
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://safer.fmcsa.dot.gov',
                'Referer': 'https://safer.fmcsa.dot.gov/CompanySnapshot.aspx',
            }
            
            response = self.session.post(url, data=params, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.get_text().lower()
            
            # Check for specific error conditions and inactive records
            # Be very specific to avoid false positives from help text
            if 'record not found' in page_text:
                print(f"MC {mc_number}: Record not found - skipping")
                return None
            elif 'no records matching' in page_text:
                print(f"MC {mc_number}: No records matching - skipping") 
                return None
            elif 'querybadcharacter' in page_text:
                print(f"MC {mc_number}: Bad character in query - skipping")
                return None
            elif 'record inactive' in page_text:
                print(f"MC {mc_number}: Record inactive - skipping")
                return None
            elif 'is inactive in the safer database' in page_text:
                print(f"MC {mc_number}: Inactive in SAFER database - skipping")
                return None
            
            # Extract data from main page
            data = self.extract_main_data(soup, mc_number)
            
            # Validate that we actually found an MC record for this specific number
            if not self.validate_mc_match(soup, mc_number):
                print(f"MC {mc_number}: MC number mismatch - skipping")
                return None
            
            # Get USDOT number from MC link if available
            if not data.get('usdot_number'):
                mc_links = soup.find_all('a', href=re.compile(r'n_dotno=(\d+)'))
                for link in mc_links:
                    href = link.get('href', '')
                    usdot_match = re.search(r'n_dotno=(\d+)', href)
                    if usdot_match:
                        data['usdot_number'] = usdot_match.group(1)
                        break
            
            # Find SMS Results link for later use
            sms_links = soup.find_all('a', href=re.compile(r'sms.*safer_xfr.*DOT=(\d+)'))
            if sms_links:
                href = sms_links[0].get('href', '')
                data['sms_url'] = href if href.startswith('http') else 'http://ai.fmcsa.dot.gov' + href
            
            # Additional validation - ensure we have meaningful data
            if data.get('legal_name') and len(data['legal_name'].strip()) > 0:
                return data
            else:
                print(f"MC {mc_number}: No valid legal name found - skipping")
                return None
                
        except Exception as e:
            print(f"MC {mc_number}: Exception - {str(e)}")
            return None
    
    def validate_mc_match(self, soup, mc_number):
        """Validate that the returned page actually matches the requested MC number"""
        try:
            # Look for MC number in the page content
            page_text = soup.get_text()
            
            # Check if the MC number appears in the expected format
            mc_patterns = [
                f"MC-{mc_number}",
                f"MC {mc_number}",
                f"MC#{mc_number}",
                f"MC/MX Number = {mc_number}"
            ]
            
            for pattern in mc_patterns:
                if pattern in page_text:
                    return True
            
            # Also check in MC links
            mc_links = soup.find_all('a', href=re.compile(r'n_docketno=(\d+)'))
            for link in mc_links:
                href = link.get('href', '')
                docket_match = re.search(r'n_docketno=(\d+)', href)
                if docket_match and docket_match.group(1) == str(mc_number):
                    return True
            
            return False
            
        except Exception:
            return False
    
    def get_enhanced_carrier_data(self, main_data):
        """Get enhanced data from SMS and Registration pages"""
        if not main_data.get('sms_url'):
            return main_data
        
        try:
            # Follow SMS Results link
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Referer': 'https://safer.fmcsa.dot.gov/',
            }
            
            time.sleep(1)  # Be polite to the server
            sms_response = self.session.get(main_data['sms_url'], headers=headers, timeout=15)
            
            if sms_response.status_code == 200:
                sms_soup = BeautifulSoup(sms_response.content, 'html.parser')
                
                # Look for Carrier Registration Details link
                reg_links = sms_soup.find_all('a', string=re.compile(r'Carrier.*Registration.*Details', re.IGNORECASE))
                
                if reg_links:
                    reg_href = reg_links[0].get('href', '')
                    
                    if reg_href:
                        # Follow Registration Details link
                        if not reg_href.startswith('http'):
                            base_url = main_data['sms_url'].split('/SMS/')[0] if '/SMS/' in main_data['sms_url'] else 'http://ai.fmcsa.dot.gov'
                            reg_url = base_url + reg_href if reg_href.startswith('/') else base_url + '/' + reg_href
                        else:
                            reg_url = reg_href
                        
                        time.sleep(1)  # Be polite
                        reg_response = self.session.get(reg_url, headers=headers, timeout=15)
                        
                        if reg_response.status_code == 200:
                            reg_soup = BeautifulSoup(reg_response.content, 'html.parser')
                            
                            # Extract email and other details from registration page
                            self.extract_registration_data(reg_soup, main_data)
            
            return main_data
            
        except Exception as e:
            # Return main data even if enhanced scraping fails
            return main_data
    
    def is_no_results_page(self, soup):
        """Check if the page indicates no results found"""
        # Look for common "no results" indicators
        page_text = soup.get_text().lower()
        no_results_indicators = [
            'no records found',
            'search returned no results', 
            'no data available',
            'invalid search'
        ]
        
        return any(indicator in page_text for indicator in no_results_indicators)
    
    def extract_main_data(self, soup, mc_number):
        """Extract main data from FMCSA carrier snapshot page"""
        data = {
            'mc_number': str(mc_number),
            'usdot_number': '',
            'legal_name': '',
            'physical_address': '',
            'phone_number': '',
            'email': '',
            'entity_type': '',
            'usdot_status': '',
            'out_of_service_date': '',
            'operating_authority_status': ''
        }
        
        try:
            # Extract using FMCSA table structure
            rows = soup.find_all('tr')
            for row in rows:
                th_elements = row.find_all('th')
                td_elements = row.find_all('td')
                
                if th_elements and td_elements:
                    for th in th_elements:
                        label = th.get_text(strip=True).lower()
                        next_td = th.find_next('td')
                        
                        if next_td:
                            value = next_td.get_text(strip=True)
                            
                            if 'legal name' in label:
                                data['legal_name'] = value
                            elif 'entity type' in label:
                                data['entity_type'] = value
                            elif 'usdot number' in label:
                                numbers = re.findall(r'\d+', value)
                                if numbers:
                                    data['usdot_number'] = numbers[0]
                            elif 'physical address' in label:
                                # Clean address: combine lines and remove extra spaces
                                addr_parts = []
                                for line in next_td.stripped_strings:
                                    if line.strip():
                                        addr_parts.append(line.strip())
                                data['physical_address'] = ' '.join(addr_parts)
                            elif 'phone' in label:
                                clean_phone = re.sub(r'[^\d\-\(\)\+\s\.]', '', value)
                                if len(clean_phone) >= 10:
                                    data['phone_number'] = clean_phone
                            elif 'out of service date' in label:
                                data['out_of_service_date'] = value
                            elif 'operating status' in label or 'carrier status' in label:
                                data['usdot_status'] = value
                            elif 'operating authority' in label:
                                data['operating_authority_status'] = value
            
            # Clean up data
            for key in data:
                if isinstance(data[key], str):
                    data[key] = data[key].strip()
                    data[key] = re.sub(r'\s+', ' ', data[key])
                    data[key] = data[key].replace('\xa0', ' ').replace('\n', ' ')
            
            return data
            
        except Exception as e:
            return data
    
    def extract_registration_data(self, soup, data):
        """Extract additional data from carrier registration details page"""
        try:
            # Look for email in registration page
            page_text = soup.get_text()
            
            # Search for email addresses
            email_matches = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', page_text)
            if email_matches:
                # Filter out generic FMCSA emails
                for email in email_matches:
                    if not any(domain in email.lower() for domain in ['fmcsa.dot.gov', 'usdot.gov', 'dot.gov']):
                        data['email'] = email
                        break
            
            # Look for additional phone numbers or updated address
            rows = soup.find_all('tr')
            for row in rows:
                th_elements = row.find_all('th')
                td_elements = row.find_all('td')
                
                if th_elements and td_elements:
                    for th in th_elements:
                        label = th.get_text(strip=True).lower()
                        next_td = th.find_next('td')
                        
                        if next_td:
                            value = next_td.get_text(strip=True)
                            
                            if 'email' in label or 'e-mail' in label:
                                if '@' in value:
                                    data['email'] = value
                            elif 'phone' in label and not data.get('phone_number'):
                                clean_phone = re.sub(r'[^\d\-\(\)\+\s\.]', '', value)
                                if len(clean_phone) >= 10:
                                    data['phone_number'] = clean_phone
        
        except Exception as e:
            pass  # Don't fail if registration data extraction fails
    
    def extract_data(self, soup, mc_number):
        """Extract relevant data from the HTML using FMCSA-specific structure"""
        data = {
            'mc_number': str(mc_number),
            'usdot_number': '',
            'legal_name': '',
            'physical_address': '',
            'phone_number': '',
            'email': '',
            'entity_type': '',
            'usdot_status': '',
            'out_of_service_date': '',
            'operating_authority_status': ''
        }
        
        try:
            # Extract Legal Name from title or main heading
            title = soup.find('title')
            if title:
                title_text = title.get_text()
                if 'Company Snapshot' in title_text:
                    # Extract company name from title like "SAFER Web - Company Snapshot DOT INC"
                    parts = title_text.split('Company Snapshot')
                    if len(parts) > 1:
                        company_name = parts[1].strip()
                        if company_name and not any(x in company_name.lower() for x in ['safer', 'fmcsa', 'dot gov']):
                            data['legal_name'] = company_name
            
            # Look for specific FMCSA table structure
            rows = soup.find_all('tr')
            for row in rows:
                th_elements = row.find_all('th')
                td_elements = row.find_all('td')
                
                if th_elements and td_elements:
                    for th in th_elements:
                        label = th.get_text(strip=True).lower()
                        
                        # Find corresponding TD element
                        next_td = th.find_next('td')
                        if next_td:
                            value = next_td.get_text(strip=True)
                            
                            # Map FMCSA-specific labels
                            if 'legal name' in label:
                                data['legal_name'] = value
                            elif 'entity type' in label:
                                data['entity_type'] = value
                            elif 'usdot number' in label:
                                # Extract just the number
                                numbers = re.findall(r'\d+', value)
                                if numbers:
                                    data['usdot_number'] = numbers[0]
                            elif 'out of service date' in label or 'oos date' in label:
                                data['out_of_service_date'] = value
                            elif 'operating status' in label or 'carrier status' in label:
                                data['usdot_status'] = value
                            elif 'operating authority' in label:
                                data['operating_authority_status'] = value
                            elif 'phone' in label:
                                # Clean phone number
                                clean_phone = re.sub(r'[^\d\-\(\)\+\s\.]', '', value)
                                if len(clean_phone) >= 10:
                                    data['phone_number'] = clean_phone
                            elif 'email' in label or 'e-mail' in label:
                                if '@' in value:
                                    data['email'] = value
                            elif any(addr_term in label for addr_term in ['address', 'street', 'mailing']):
                                if not data['physical_address'] or len(value) > len(data['physical_address']):
                                    data['physical_address'] = value
            
            # Also try direct text extraction for backup
            page_text = soup.get_text()
            
            # Look for USDOT Number pattern in text
            if not data['usdot_number']:
                usdot_match = re.search(r'usdot number:\s*(\d+)', page_text, re.IGNORECASE)
                if usdot_match:
                    data['usdot_number'] = usdot_match.group(1)
            
            # Look for Legal Name in bold tags or specific patterns
            if not data['legal_name']:
                # Try to find company name in specific FMCSA patterns
                bold_elements = soup.find_all('b')
                for bold in bold_elements:
                    text = bold.get_text(strip=True)
                    # Skip generic FMCSA text
                    if text and not any(skip in text.lower() for skip in [
                        'company snapshot', 'safer', 'fmcsa', 'usdot', 'query', 'federal motor'
                    ]):
                        if len(text) > 3 and len(text) < 100:  # Reasonable company name length
                            data['legal_name'] = text
                            break
            
            # Clean up all data
            for key in data:
                if isinstance(data[key], str):
                    data[key] = data[key].strip()
                    data[key] = re.sub(r'\s+', ' ', data[key])
                    data[key] = data[key].replace('\xa0', ' ').replace('\n', ' ')
                    # Remove HTML entities
                    data[key] = data[key].replace('&nbsp;', ' ').replace('&amp;', '&')
            
            return data
            
        except Exception as e:
            raise Exception(f"Data extraction failed: {str(e)}")
    
    def _extract_field_from_text(self, label, value, data):
        """Helper method to extract fields based on label-value pairs"""
        if not value or value.lower() in ['none', 'n/a', '']:
            return
            
        label = label.lower()
        
        # Legal name patterns
        if any(pattern in label for pattern in ['legal name', 'entity name', 'dba name', 'company name']):
            if not data['legal_name'] or len(value) > len(data['legal_name']):
                data['legal_name'] = value
        
        # USDOT number patterns
        elif any(pattern in label for pattern in ['usdot number', 'usdot#', 'dot number', 'dot#']):
            # Extract numbers only
            numbers = re.findall(r'\d+', value)
            if numbers:
                data['usdot_number'] = numbers[0]
        
        # Entity type patterns
        elif any(pattern in label for pattern in ['entity type', 'carrier type', 'operation classification']):
            data['entity_type'] = value
        
        # Status patterns
        elif any(pattern in label for pattern in ['usdot status', 'status', 'carrier status']):
            data['usdot_status'] = value
        
        # Out of service patterns
        elif any(pattern in label for pattern in ['out of service', 'oos date', 'service date']):
            data['out_of_service_date'] = value
        
        # Authority patterns
        elif any(pattern in label for pattern in ['operating authority', 'authority status', 'authority']):
            data['operating_authority_status'] = value
        
        # Phone patterns
        elif any(pattern in label for pattern in ['phone', 'telephone', 'tel:']):
            # Clean phone number
            clean_phone = re.sub(r'[^\d\-\(\)\+\s]', '', value)
            if len(clean_phone) >= 10:
                data['phone_number'] = clean_phone
        
        # Email patterns
        elif any(pattern in label for pattern in ['email', 'e-mail', 'mail']):
            if '@' in value:
                data['email'] = value
        
        # Address patterns
        elif any(pattern in label for pattern in ['address', 'physical address', 'mailing address', 'street']):
            if not data['physical_address'] or len(value) > len(data['physical_address']):
                data['physical_address'] = value
    
    def _extract_with_regex(self, text, data):
        """Extract data using regex patterns"""
        # USDOT number pattern
        if not data['usdot_number']:
            usdot_match = re.search(r'usdot[^\d]*(\d+)', text, re.IGNORECASE)
            if usdot_match:
                data['usdot_number'] = usdot_match.group(1)
        
        # Phone number pattern
        if not data['phone_number']:
            phone_match = re.search(r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})', text)
            if phone_match:
                data['phone_number'] = phone_match.group(1)
        
        # Email pattern
        if not data['email']:
            email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
            if email_match:
                data['email'] = email_match.group(0)
    
    def is_valid_record(self, data):
        """Check if the record meets all filtering criteria"""
        try:
            # Check if we have basic required data
            if not data.get('legal_name'):
                return False
                
            # Check Entity Type (be more flexible for initial testing)
            entity_type = data.get('entity_type', '').lower()
            target_type = self.entity_type.lower()
            
            # For now, accept any entity type that has content
            # In production, you would uncomment the strict checking below
            if not entity_type:
                # If no entity type found, accept record (could be missing from scraping)
                pass
            else:
                # Allow partial matches for entity type
                if target_type == 'carrier' and 'carrier' not in entity_type:
                    return False
                elif target_type == 'broker' and 'broker' not in entity_type:
                    return False
                elif target_type == 'shipper' and 'shipper' not in entity_type:
                    return False
            
            # Check USDOT Status (be more flexible)
            usdot_status = data.get('usdot_status', '').lower()
            # For now, don't filter by status - accept all active records
            
            # Check Out of Service Date (should be None/empty)
            oos_date = data.get('out_of_service_date', '').lower()
            if oos_date and oos_date not in ['none', 'n/a', '', 'null', 'not applicable']:
                # Check if it's actually a date with numbers (indicating out of service)
                if re.search(r'\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}', oos_date):
                    return False
            
            # Check Operating Authority Status (be more flexible)
            auth_status = data.get('operating_authority_status', '').lower()
            # For now, don't filter by authority status
            
            return True
            
        except Exception as e:
            return False
    
    def clean_text(self, text):
        """Clean extracted text"""
        if not text:
            return ''
        
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common HTML artifacts
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        
        return text
