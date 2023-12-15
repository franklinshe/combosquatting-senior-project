import json
import pandas as pd

# Load the outliers.csv file
outliers_csv_file = 'data/raw/outliers.csv'
outliers_df = pd.read_csv(outliers_csv_file)

# Extract the list of outliers trademarks
outliers_list = outliers_df['Trademark'].tolist()

# Load the candidate_domains_all.json file
json_file = 'data/raw/candidate_domains_all.json'
with open(json_file, 'r') as f:
    candidate_domains = json.load(f)

# Get the number of trademarks and domains in the original JSON
num_trademarks_all = len(candidate_domains)
num_domains_all = sum(len(domains) for domains in candidate_domains.values())

# Filter the candidate_domains dictionary to remove trademarks in outliers
filtered_candidate_domains = {trademark: domains for trademark, domains in candidate_domains.items() if trademark not in outliers_list}

# Save the filtered candidate domains to candidate_domains_filtered.json
filtered_json_file = 'data/raw/candidate_domains_filtered.json'
with open(filtered_json_file, 'w') as f:
    json.dump(filtered_candidate_domains, f, indent=4)

# Get the number of trademarks and domains in the filtered JSON
num_trademarks_filtered = len(filtered_candidate_domains)
num_domains_filtered = sum(len(domains) for domains in filtered_candidate_domains.values())

# Calculate the reduction percentages
reduction_percentage_trademarks = ((num_trademarks_all - num_trademarks_filtered) / num_trademarks_all) * 100
reduction_percentage_domains = ((num_domains_all - num_domains_filtered) / num_domains_all) * 100

# Print the results
print(f"Number of Trademarks in Original JSON: {num_trademarks_all}")
print(f"Number of Domains in Original JSON: {num_domains_all}")
print(f"Number of Trademarks in Filtered JSON: {num_trademarks_filtered}")
print(f"Number of Domains in Filtered JSON: {num_domains_filtered}")
print(f"Number of Trademarks in Filtered JSON less than Original: {num_trademarks_all - num_trademarks_filtered}")
print(f"Percentage Reduction in Trademarks: {reduction_percentage_trademarks:.2f}%")
print(f"Percentage Reduction in Domains: {reduction_percentage_domains:.2f}%")

