import json
import os
import time
import csv
from multiprocessing.pool import ThreadPool

from webscraper_helper import (gather_and_save_dns_and_ip_info, gather_and_save_whois_info,
                           gather_and_save_certificate_info_simple)

BASE_DIR = 'data/simple_scrape'
CANDIDATE_DOMAIN_PATH = 'data/raw/candidate_domains_filtered.json'

def save_error(domain_folder, domain, errors):
    error_file = os.path.join(domain_folder, f"{domain}.error.txt")
    with open(error_file, 'w') as file:
        for error in errors:
            file.write(error + '\n' + '-' * 50 + '\n')

def save_error_flags(domain, error_flags):
    csv_file_path = os.path.join(BASE_DIR, 'domain_errors.csv')
    with open(csv_file_path, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([domain, error_flags['dns_error'], error_flags['ip_error'], error_flags['whois_error'], error_flags['cert_error'], error_flags['exception']])

def process_domain(trademark, domain, BASE_DIR):
    try:
        domain_folder = os.path.join(BASE_DIR, trademark, domain)
        os.makedirs(domain_folder, exist_ok=True)

        errors = []
        error_flags = {'dns_error': 0, 'ip_error': 0, 'whois_error': 0, 'cert_error': 0, 'exception': 0}

        ip_address, error_message = gather_and_save_dns_and_ip_info(domain, domain_folder)
        if error_message:
            errors.append(error_message)
            error_flags['dns_error'] = 1

        error_message = gather_and_save_whois_info(domain, domain_folder)
        if error_message:
            errors.append(error_message)
            error_flags['whois_error'] = 1

        if ip_address:
            error_message, error_flag = gather_and_save_certificate_info_simple(domain, domain_folder, ip_address)
            if error_message:
                errors.append(error_message)
                error_flags['cert_error'] = error_flag
        else:
            error_flags['ip_error'] = 1
            error_flags['cert_error'] = 3

        if errors:
            save_error(domain_folder, domain, errors)
        
        save_error_flags(domain, error_flags)

    except Exception as e:
        error_flags['exception'] = str(e)
        save_error_flags(domain, error_flags)
        print(f"Error processing {domain}: {str(e)}")

def generate_tasks(data, BASE_DIR):
    tasks = []
    # counter = 0
    for trademark, domains in data.items():
        for domain in domains:
            # counter += 1
            # if counter < 600000:
            #     continue
            tasks.append((trademark, domain, BASE_DIR))
            # if counter > 610000:
            #     return tasks
        
    print("Number of domains:", len(tasks))
    return tasks

def main():
   # t1 = time.time()
   # with open(CANDIDATE_DOMAIN_PATH, 'r') as file:
   #     data = json.load(file)

   # BASE_DIR = 'data/simple_scrape'

   # csv_file_path = os.path.join(BASE_DIR, 'domain_errors.csv')
   # with open(csv_file_path, 'w', newline='') as csvfile:
   #     writer = csv.writer(csvfile)
   #     writer.writerow(['Domain', 'DNS Error', 'IP Error', 'WHOIS Error', 'Certificate Error', 'Exception'])

   # tasks = generate_tasks(data, BASE_DIR)

   # pool = ThreadPool(processes = 250)
   # pool.starmap(process_domain, tasks)
   # pool.close()
   # pool.join()

   # print(f"Total time: {round(time.time() - t1, 2)} seconds")

if __name__ == "__main__":
    main()
