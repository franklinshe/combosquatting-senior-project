import pandas as pd

def load_data(filepath):
    return pd.read_csv(filepath)

def count_non_zero_errors(df, columns):
    return df[columns].apply(lambda x: (x != 0).sum())

def calculate_error_percentages(error_counts, total):
    return error_counts / total * 100

def get_domains_with_any_error(df, columns):
    df['Any Error'] = df[columns].sum(axis=1) > 0
    return df[df['Any Error']]

# Load datasets
domain_error_file = 'data/simple_scrape/domain_errors.csv'
trademark_file = 'data/raw/combined_trademarks_list_full.csv'

domain_data = load_data(domain_error_file)
trademark_data = load_data(trademark_file)

# Settings for display
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

error_columns = ['DNS Error', 'IP Error', 'WHOIS Error', 'Certificate Error', 'Exception']

# Error counts and percentages for all domains
all_error_counts = count_non_zero_errors(domain_data, error_columns)
all_error_counts['Any Error'] = len(get_domains_with_any_error(domain_data, error_columns))
all_error_percentages = calculate_error_percentages(all_error_counts, len(domain_data))

# Processing for trademark domains
trademark_domains = set(trademark_data['Domain'])
filtered_domains = domain_data[domain_data['Domain'].isin(trademark_domains)]

# Error counts and percentages for trademark domains
trademark_error_counts = count_non_zero_errors(filtered_domains, error_columns)
trademark_error_counts['Any Error'] = len(get_domains_with_any_error(filtered_domains, error_columns))
trademark_error_percentages = calculate_error_percentages(trademark_error_counts, len(filtered_domains))

# Domains with errors in trademark data
trademark_domains_with_errors = get_domains_with_any_error(filtered_domains, error_columns)

# Domains with any errors in all data
all_domains_with_errors = get_domains_with_any_error(domain_data, error_columns)

# Output
print("Error Counts for All Domains:\n", all_error_counts)
print("\nError Percentages for All Domains:\n", all_error_percentages)
print("\nError Counts for Trademark Domains:\n", trademark_error_counts)
print("\nError Percentages for Trademark Domains:\n", trademark_error_percentages)

# Exporting to CSV
trademark_export_file_path = 'trademark_domains_with_errors.csv'
all_export_file_path = 'all_domains_with_errors.csv'

trademark_domains_with_errors.to_csv(trademark_export_file_path, index=False)
# all_domains_with_errors.to_csv(all_export_file_path, index=False)

print(f"Exported trademark domains with errors to {trademark_export_file_path}")
# print(f"Exported all domains with errors to {all_export_file_path}")

# Identifying domains with Certificate Error = 2
certificate_error_2_domains = domain_data[domain_data['Certificate Error'] == 2]

# Exporting these domains to CSV
certificate_error_2_file_path = 'certificate_error_2_domains.csv'
certificate_error_2_domains.to_csv(certificate_error_2_file_path, index=False)

print(f"Exported domains with Certificate Error = 2 to {certificate_error_2_file_path}")