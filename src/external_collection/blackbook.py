import os
import csv
from time import time

def load_trademarks(csv_path):
    trademarks = {}
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            trademarks[row['Trademark']] = row['Domain']
    return trademarks

def load_blackbook_data(csv_path):
    blackbook_domains = {}
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            blackbook_domains[row['Domain']] = (row['Malware'], row['Date added'], row['Source'])
    return blackbook_domains

def write_to_csv(data, file_path):
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Trademark Domain', 'Candidate Domain', 'Threat', 'Malware', 'Date Added', 'Source'])
        for item in data:
            writer.writerow(item)

def main():
    csv_path = 'data/raw/combined_trademarks_list_full.csv'
    trademarks = load_trademarks(csv_path)
    blackbook_data = load_blackbook_data('blackbook/blackbook.csv')

    base_dir = 'data/simple_scrape'
    output_dir = 'data/simple_scrape_preprocess'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    domains_to_check = []

    for trademark, domain in trademarks.items():
        trademark_dir = os.path.join(base_dir, trademark)
        if os.path.isdir(trademark_dir):
            for candidate_domain in os.listdir(trademark_dir):
                domains_to_check.append((domain, candidate_domain))

    start_time = time()
    print("Checking {} domains".format(len(domains_to_check)))

    matches = []
    for domain, candidate_domain in domains_to_check:
        if candidate_domain in blackbook_data:
            malware_info = blackbook_data[candidate_domain]
            matches.append((domain, candidate_domain, *malware_info))

    write_to_csv(matches, os.path.join(output_dir, 'blackbook_results.csv'))

    print("Time taken to check domains: {}".format(time() - start_time))

if __name__ == "__main__":
    main()
