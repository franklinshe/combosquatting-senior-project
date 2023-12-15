import json
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

from webscraper_helper import (gather_and_save_dns_and_ip_info, gather_and_save_whois_info,
                           gather_and_save_certificate_info, gather_and_save_html_content, 
                           gather_and_save_final_url, gather_and_save_favicon, 
                           save_load_time)

BASE_DIR = 'data/processed'
CANDIDATE_DOMAIN_PATH = 'data/raw/candidate_domains_filtered.json'

def save_error(domain_folder, domain, errors):
    error_file = os.path.join(domain_folder, f"{domain}.loadtime.txt")
    with open(error_file, 'a') as file:
        for error in errors:
            file.write(error + '\n' + '-' * 50 + '\n')

def main():
    with open(CANDIDATE_DOMAIN_PATH, 'r') as file:
        data = json.load(file)
    
    options = Options()
    options.headless = True

    counter = 0
    
    for trademark, domains in data.items():
        for domain in domains:
            if counter > 10:
                return
            counter += 1
            domain_folder = os.path.join(BASE_DIR, trademark, domain)
            os.makedirs(domain_folder, exist_ok=True)

            errors = []

            error_message = gather_and_save_dns_and_ip_info(domain, domain_folder)
            if error_message:
                errors.append(error_message)

            error_message = gather_and_save_whois_info(domain, domain_folder)
            if error_message:
                errors.append(error_message)

            try:
                with webdriver.Chrome(options=options) as browser:
                    start_time = time.time()
                    browser.get(f"http://{domain}")
                    end_time = time.time()

                    error_message = gather_and_save_html_content(browser, domain, domain_folder)
                    if error_message:
                        errors.append(error_message)

                    error_message = gather_and_save_certificate_info(browser, domain, domain_folder)
                    if error_message:
                        errors.append(error_message)

                    error_message = gather_and_save_final_url(browser, domain, domain_folder)
                    if error_message:
                        errors.append(error_message)

                    error_message = gather_and_save_favicon(domain, domain_folder, browser.current_url)
                    if error_message:
                        errors.append(error_message)

                    error_message = save_load_time(end_time - start_time, domain, domain_folder)
                    if error_message:
                        errors.append(error_message)
            except WebDriverException as e:
                errors.append(f"Failed to load {domain}. Error: {e}")

            if errors:
                save_error(domain_folder, domain, errors)

if __name__ == "__main__":
    main()
