import csv
import json
def load_trademarks_from_csv(filepath):
    trademarks = []
    print(f"Loading trademarks from {filepath}...")
    with open(filepath, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # skip the header
        for row in reader:
            trademarks.append(row[0].lower())  # Using lowercase to ensure matching
    print(f"Loaded {len(trademarks)} trademarks.")
    return trademarks

def load_domains_from_txt(filepath):
    print(f"Loading domains from {filepath}...")
    with open(filepath, 'r') as file:
        domains = [line.strip().lower() for line in file.readlines()]  # Using lowercase to ensure matching
    print(f"Loaded {len(domains)} domains.")
    return domains

def find_matching_domains(trademarks, domains):
    matches = {trademark: [] for trademark in trademarks}
    for trademark in trademarks:
        for domain in domains:
            if trademark in domain:
                matches[trademark].append(domain)
        print(f"Found {len(matches[trademark])} matching domains for trademark: {trademark}")
    return matches

def calculate_summary_statistics(matching_domains):
    summary_statistics = {}
    for trademark, matched_domains in matching_domains.items():
        summary_statistics[trademark] = len(matched_domains)
    return summary_statistics

def main():
    trademarks_csv_path = 'data/raw/combined_trademarks_list_full.csv'
    domains_txt_path = 'data/raw/unique_domains.txt'
    output_path = 'data/raw/candidate_domains.json'
    summary_csv_path = 'data/raw/summary_statistics.csv'  # New CSV file for summary statistics
    
    trademarks = load_trademarks_from_csv(trademarks_csv_path)
    domains = load_domains_from_txt(domains_txt_path)
    matching_domains = find_matching_domains(trademarks, domains)
    summary_statistics = calculate_summary_statistics(matching_domains)
    
    with open(output_path, 'w') as json_file:
        json.dump(matching_domains, json_file, indent=4)
    print(f"Data saved to {output_path}")
    
    with open(summary_csv_path, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['Trademark', 'Matches'])
        for trademark, matches in summary_statistics.items():
            writer.writerow([trademark, matches])
    print(f"Summary statistics saved to {summary_csv_path}")

if __name__ == "__main__":
    main()
