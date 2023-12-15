import os
import csv
from gglsbl import SafeBrowsingList
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

def check_threats(domain, candidate_domain, api_key):
    sbl = SafeBrowsingList(api_key) 
    threat_list = sbl.lookup_url(candidate_domain)
    if threat_list is None:
        return None
    else:
        return domain, candidate_domain, list(threat_list)


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

    api_key = 'AIzaSyCIWLSLlbr_UNWP-x7ktCCV85I5muZCGao'
    domains_to_check = []

    counter = 0

    start_time = time()

    for trademark, domain in trademarks.items():
        trademark_dir = os.path.join(base_dir, trademark)
        if os.path.isdir(trademark_dir):
            for candidate_domain in os.listdir(trademark_dir):
                domains_to_check.append((domain, candidate_domain))
         
    print("Time taken to load data: {}".format(time() - start_time))
    start_time = time()

    print("Checking {} domains".format(len(domains_to_check)))
    threat_results = []

    with ThreadPoolExecutor(max_workers=500) as executor:
        futures = [executor.submit(check_threats, domain, candidate_domain, api_key) for domain, candidate_domain in domains_to_check]
        for future in tqdm(as_completed(futures), total=len(futures), desc="Checking domains"):
            result = future.result()
            if result:
                threat_results.append(result)
                print(result)
                # break


    write_to_csv(threat_results, os.path.join(output_dir, 'gsb_threat_results.csv'))

    print("Time taken to check domains: {}".format(time() - start_time))
if __name__ == "__main__":
    main()
