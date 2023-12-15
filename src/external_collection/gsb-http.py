import os
import csv
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from time import time

def load_trademarks(csv_path):
    trademarks = {}
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            trademarks[row['Trademark']] = row['Domain']
    return trademarks

def is_domain_blacklisted(url, api_key):
    api_url = f'https://safebrowsing.googleapis.com/v4/threatMatches:find?key={api_key}'
    payload = {
        "threatInfo": {
            "threatTypes":      ["MALWARE", "SOCIAL_ENGINEERING"],
            "platformTypes":    ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [
                {"url": url}
            ]
        }
    }
    response = requests.post(api_url, data=json.dumps(payload))
    return response.json()

def check_threats(domain, candidate_domain, api_key):
    result = is_domain_blacklisted(candidate_domain, api_key)
    if result.get('matches'):
        return domain, candidate_domain, result['matches']
    else:
        return None

def write_to_csv(data, file_path):
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Trademark Domain', 'Candidate Domain', 'Threat'])
        for item in data:
            writer.writerow(item)

def main():
    csv_path = 'data/raw/combined_trademarks_list_full.csv'
    trademarks = load_trademarks(csv_path)

    base_dir = 'data/simple_scrape'
    output_dir = 'data/simple_scrape_preprocess'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    api_key = 'API_KEY_HERE'
    domains_to_check = []

    start_time = time()

    counter = 0

    for trademark, domain in trademarks.items():
        trademark_dir = os.path.join(base_dir, trademark)
        if os.path.isdir(trademark_dir):
            for candidate_domain in os.listdir(trademark_dir):
                domains_to_check.append((domain, candidate_domain))

    print("Checking {} domains".format(len(domains_to_check)))
    print("Load time: {}".format(time() - start_time))
    start_time = time()
    threat_results = []

    with ThreadPoolExecutor(max_workers=200) as executor:
        futures = [executor.submit(check_threats, domain, candidate_domain, api_key) for domain, candidate_domain in domains_to_check]
        for future in tqdm(as_completed(futures), total=len(futures), desc="Checking domains"):
            result = future.result()
            if result:
                threat_results.append(result)

    print("Check time: {}".format(time() - start_time))

    write_to_csv(threat_results, os.path.join(output_dir, 'threat_results.csv'))

if __name__ == "__main__":
    main()
