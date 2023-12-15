import csv
import os
import json
import os
import OpenSSL.crypto
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_trademarks(csv_path):
    """
    Load trademarks from the CSV file and return a dictionary mapping each trademark to its URL.
    """
    trademarks = {}
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            trademarks[row['Trademark']] = row['Domain']
    return trademarks

def load_files(directory):
    data = {'dns': None, 'whois': None, 'certificate': None, 'certificate_verified': None}
    try:
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if file.endswith('.dns.json'):
                with open(file_path, 'r') as f:
                    data['dns'] = json.load(f)
            elif file.endswith('.whois.json'):
                with open(file_path, 'r') as f:
                    data['whois'] = json.load(f)
            elif file.endswith('.certificate-verified') or file.endswith('.certificate-unverified'):
                data['certificate'], data['certificate_verified'] = load_certificate(file_path)
    except Exception as e:
        logging.error(f"Error loading files in {directory}: {e}")
    return data

def load_certificate(file_path):
    try:
        with open(file_path, 'rb') as f:
            pem_data = f.read()
            certificate = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, pem_data)
            certificate_data = {
                'subject': extract_x509_name(certificate.get_subject()),
                'issuer': extract_x509_name(certificate.get_issuer()),
                'serial_number': certificate.get_serial_number(),
                'valid_from': certificate.get_notBefore().decode(),
                'valid_until': certificate.get_notAfter().decode(),
                'subject_alternative_names': get_san(certificate)
            }
            certificate_verified = file_path.endswith('.certificate-verified')
        return certificate_data, certificate_verified
    except Exception as e:
        logging.error(f"Error loading certificate from {file_path}: {e}")
        return None, None


def extract_x509_name(x509name):
    """
    Extract details from X509Name object and return as a dictionary.
    Skip components that fail to decode.
    """
    components = []
    for name, value in x509name.get_components():
        try:
            decoded_name = name.decode('utf-8')
            decoded_value = value.decode('utf-8')
        except UnicodeDecodeError:
            try:
                decoded_name = name.decode('iso-8859-1')
                decoded_value = value.decode('iso-8859-1')
            except UnicodeDecodeError:
                continue
        
        components.append((decoded_name, decoded_value))

    return dict(components)

def get_san(certificate):
    """
    Extract Subject Alternative Names from a certificate.
    """
    san = []
    for i in range(certificate.get_extension_count()):
        ext = certificate.get_extension(i)
        if 'subjectAltName' in str(ext.get_short_name()):
            san.extend([e.strip() for e in str(ext).split(',')])
    return san

def parse_certificate_date(date_str):
    """
    Parse the certificate date from string to datetime object.
    """
    return datetime.strptime(date_str, '%Y%m%d%H%M%SZ')

def process_candidate_domain(candidate_domain_dir, trademark_data, candidate_domain, trademark_domain):
    """
    Process each candidate domain directory.
    """
    local_comparisons = {
        'share_cert_serial_number': [],
        'share_cert_subject_CN': [],
        'cert_validity_within_hour': [],
        'shared_dns_a_record': [],
        'overlap_subject_alternative_names': [],
        'shared_whois_org': [],
        'shared_whois_email': [],
        'shared_whois_address': []
    }

    try:
        candidate_data = load_files(candidate_domain_dir)

        if candidate_data['certificate'] and trademark_data['certificate']:
            if candidate_data['certificate']['serial_number'] == trademark_data['certificate']['serial_number']:
                local_comparisons['share_cert_serial_number'].append((trademark_domain, candidate_domain, trademark_data['certificate_verified'], candidate_data['certificate_verified']))
            
            candidate_cn = candidate_data['certificate']['subject'].get('CN')
            trademark_cn = trademark_data['certificate']['subject'].get('CN')
            if candidate_cn and trademark_cn and candidate_cn == trademark_cn:
                local_comparisons['share_cert_subject_CN'].append((trademark_domain, candidate_domain, trademark_data['certificate_verified'], candidate_data['certificate_verified']))

            candidate_valid_from = parse_certificate_date(candidate_data['certificate']['valid_from'])
            candidate_valid_until = parse_certificate_date(candidate_data['certificate']['valid_until'])
            trademark_valid_from = parse_certificate_date(trademark_data['certificate']['valid_from'])
            trademark_valid_until = parse_certificate_date(trademark_data['certificate']['valid_until'])
            if abs((candidate_valid_from - trademark_valid_from).total_seconds()) <= 3600 and abs((candidate_valid_until - trademark_valid_until).total_seconds()) <= 3600:
                local_comparisons['cert_validity_within_hour'].append((trademark_domain, candidate_domain, trademark_data['certificate_verified'], candidate_data['certificate_verified']))

            candidate_sans = set(candidate_data['certificate']['subject_alternative_names'])
            trademark_sans = set(trademark_data['certificate']['subject_alternative_names'])
            overlapping_sans = candidate_sans.intersection(trademark_sans)
            if overlapping_sans:
                local_comparisons['overlap_subject_alternative_names'].append((trademark_domain, candidate_domain, list(overlapping_sans)))
        
        if candidate_data['dns'] and trademark_data['dns']:
            candidate_dns_a_records = set(candidate_data['dns'].get('A', []))
            trademark_dns_a_records = set(trademark_data['dns'].get('A', []))
            
            overlapping_ips = candidate_dns_a_records.intersection(trademark_dns_a_records)
            if overlapping_ips:
                local_comparisons['shared_dns_a_record'].append((trademark_domain, candidate_domain, list(overlapping_ips)))

        redacted_values = {'REDACTED FOR PRIVACY', 'DATA REDACTED', 'Data protected, not disclosed', 'Not Disclosed Not Disclosed', 'GDPR Masked', 'Not Disclosed'}

        if candidate_data['whois'] and trademark_data['whois']:
            candidate_org = candidate_data['whois'].get('org')
            trademark_org = trademark_data['whois'].get('org')
            if candidate_org and trademark_org and candidate_org == trademark_org and candidate_org not in redacted_values:
                local_comparisons['shared_whois_org'].append((trademark_domain, candidate_domain, candidate_org))

            candidate_email = candidate_data['whois'].get('emails')
            trademark_email = trademark_data['whois'].get('emails')
            if candidate_email and trademark_email and candidate_email == trademark_email:
                local_comparisons['shared_whois_email'].append((trademark_domain, candidate_domain, candidate_email))

            candidate_address = candidate_data['whois'].get('address')
            trademark_address = trademark_data['whois'].get('address')
            if candidate_address and trademark_address and candidate_address == trademark_address and candidate_address not in redacted_values:
                local_comparisons['shared_whois_address'].append((trademark_domain, candidate_domain, candidate_address))

    except Exception as e:
        logging.error(f"Error processing candidate domain {candidate_domain} for trademark {trademark_domain}: {e}")

    return local_comparisons

def write_to_csv(data, file_path, comparison_type):
    """
    Write the given data to a CSV file with a customized header based on comparison type.
    """
    headers = {
        'share_cert_serial_number': ['Trademark Domain', 'Candidate Domain', 'Trademark Certificate Verified', 'Candidate Certificate Verified'],
        'share_cert_subject_CN': ['Trademark Domain', 'Candidate Domain', 'Trademark Certificate Verified', 'Candidate Certificate Verified'],
        'cert_validity_within_hour': ['Trademark Domain', 'Candidate Domain', 'Trademark Certificate Verified', 'Candidate Certificate Verified'],
        'shared_dns_a_record': ['Trademark Domain', 'Candidate Domain', 'Overlapping IPs'],
        'overlap_subject_alternative_names': ['Trademark Domain', 'Candidate Domain', 'Overlapping SANs'],
        'shared_whois_org': ['Trademark Domain', 'Candidate Domain', 'Organization'],
        'shared_whois_email': ['Trademark Domain', 'Candidate Domain', 'Email'],
        'shared_whois_address': ['Trademark Domain', 'Candidate Domain', 'Address']
    }

    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers[comparison_type])
        for item in data:
            writer.writerow(item)

def process_trademark(args):
    trademark_dir, domain, trademark_data = args
    combined_results = {
        'share_cert_serial_number': [],
        'share_cert_subject_CN': [],
        'cert_validity_within_hour': [],
        'shared_dns_a_record': [],
        'overlap_subject_alternative_names': [],
        'shared_whois_org': [],
        'shared_whois_email': [],
        'shared_whois_address': []
    }
    try:
        for candidate_domain in os.listdir(trademark_dir):
            candidate_domain_dir = os.path.join(trademark_dir, candidate_domain)
            if os.path.isdir(candidate_domain_dir) and candidate_domain != domain:
                result = process_candidate_domain(candidate_domain_dir, trademark_data, candidate_domain, domain)
                for key in combined_results:
                    combined_results[key].extend(result[key])

    except Exception as e:
        logging.error(f"Error processing trademark {domain} in directory {trademark_dir}: {e}")
    return combined_results


def main():
    csv_path = 'data/raw/combined_trademarks_list_full.csv'
    trademarks = load_trademarks(csv_path)
    base_dir = 'data/simple_scrape'
    output_dir = 'data/simple_scrape_preprocess'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Total number of trademarks: {len(trademarks)}")

    tasks = []
    for trademark, domain in trademarks.items():
        trademark_dir = os.path.join(base_dir, trademark)
        if os.path.isdir(trademark_dir):
            trademark_domain_dir = os.path.join(trademark_dir, domain)
            if os.path.isdir(trademark_domain_dir):
                trademark_data = load_files(trademark_domain_dir)
                tasks.append((trademark_dir, domain, trademark_data))
    
    print(f"Total number of tasks: {len(tasks)}")

    with ThreadPoolExecutor(max_workers=200) as executor:
        results = list(tqdm(executor.map(process_trademark, tasks), total=len(tasks)))

    combined_comparisons = {
        'share_cert_serial_number': [],
        'share_cert_subject_CN': [],
        'cert_validity_within_hour': [],
        'shared_dns_a_record': [],
        'overlap_subject_alternative_names': [],
        'shared_whois_org': [],
        'shared_whois_email': [],
        'shared_whois_address': []
    }
    for local_results in results:
        for key in combined_comparisons:
            combined_comparisons[key].extend(local_results[key])

    for comparison_type, data in combined_comparisons.items():
        file_path = os.path.join(output_dir, f'{comparison_type}.csv')
        write_to_csv(data, file_path, comparison_type)

if __name__ == "__main__":
    main()