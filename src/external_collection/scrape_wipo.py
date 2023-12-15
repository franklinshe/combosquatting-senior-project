import requests
from bs4 import BeautifulSoup
import csv
import re

def clean_and_extract_urls(html_list):
    cleaned_urls = []

    # Regular expression pattern to match HTML tags
    html_tag_pattern = r'<.*?>'

    # Iterate through the HTML list
    for html in html_list:
        # Remove HTML tags
        cleaned_text = re.sub(html_tag_pattern, '', html)

        # Remove newline characters and spaces
        cleaned_text = cleaned_text.replace('\n', '').strip()

        # Append cleaned URL to the list
        cleaned_urls.append(cleaned_text)

    # Filter out empty strings (if any)
    cleaned_urls = [url for url in cleaned_urls if url]

    return cleaned_urls

# Function to scrape and extract data from a WIPO page
def scrape_wipo_page(case_id):
    url = f"https://www.wipo.int/amc/en/domains/search/case.jsp?case_id={case_id}"
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all rows with <td> elements
        rows = soup.find_all('tr')

        case_number = None
        domain_names = []
        decision = None
        complainant = None

        for row in rows:
            header = row.find('td').find('b')
            data = row.find_all('td')[-1]

            if header and data:
                header_text = header.get_text(strip=True)
                data_text = data.get_text(strip=True)

                if header_text == "WIPO Case Number":
                    case_number = data_text
                elif header_text == "Domain name(s)":
                    domain_names.extend(clean_and_extract_urls(data.prettify().split('<br/>')))
                elif header_text == "Decision":
                    decision = data_text
                elif header_text == "Complainant":
                    complainant = data_text

        entries = []
        # Create an entry in CSV for the scraped data
        for domain_name in domain_names:
            if domain_name.strip() and decision:
                entries.append((domain_name.strip(), case_id, case_number, decision, complainant))
        
        if not entries:
            return None
        
        return entries

    return None

# Function to save the scraped data to a CSV file
def save_to_csv(data, filename):
    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)

if __name__ == "__main__":
    start_case_id = 50198
    end_case_id = 67614

    filename = "wipo_data.csv"

    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Domain Name", "Case ID", "WIPO Case Number", "Decision", "Complainant"])

    for case_id in range(start_case_id, end_case_id + 1):
        entries = scrape_wipo_page(case_id)
        if entries:
            save_to_csv(entries, filename)
        else:
            with open("wipo_errors.txt", "a") as f:
                f.write(f"{case_id}\n")
        
        if case_id % 1000 == 0:
            progress = (case_id - 2 + 1) / (end_case_id - 2 + 1) * 100
            print(f"Progress: {case_id} | {progress:.2f}%")

    print("Finished")