import csv
import os

def load_wipo_data(csv_path):
    wipo_data = {}
    decisions = set()
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            wipo_data[row['Domain Name']] = row['Decision']
            decisions.add(row['Decision'])
    return wipo_data, decisions

def load_trademarks(trademarks_path):
    trademarks = {}
    with open(trademarks_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            trademarks[row['Trademark']] = row['Domain']
    return trademarks

def write_to_csv(data, file_path):
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Trademark Domain', 'Candidate Domain', 'Decision'])
        for item in data:
            writer.writerow(item)

def main():
    wipo_csv_path = 'src/udrp_collection/wipo_data.csv'
    base_dir = 'data/simple_scrape'
    trademarks = load_trademarks('data/raw/combined_trademarks_list_full.csv')

    wipo_data, decisions = load_wipo_data(wipo_csv_path)
    print("Unique Decisions:", decisions)

    wipo_shared = []
    wipo_not_shared = []

    for trademark, domain in trademarks.items():
        trademark_dir = os.path.join(base_dir, trademark)
        if os.path.isdir(trademark_dir):
            for candidate_domain in os.listdir(trademark_dir):
                decision = wipo_data.get(candidate_domain)
                if decision:
                    if decision == 'Transfer':
                        wipo_shared.append((domain, candidate_domain, decision))
                    else:
                        wipo_not_shared.append((domain, candidate_domain, decision))

    write_to_csv(wipo_shared, 'wipo_shared.csv')
    write_to_csv(wipo_not_shared, 'wipo_not_shared.csv')

if __name__ == "__main__":
    main()
