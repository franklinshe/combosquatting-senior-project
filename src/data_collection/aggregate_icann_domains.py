import os

# Function to extract domain addresses from a file
def extract_domains_from_file(filename):
    domains = set()
    print(f"Extracting domains from {filename}...")
    with open(filename, 'r') as file:
        for line in file:
            parts = line.strip().split()
            if len(parts) >= 1:
                domain = parts[0].rstrip('.')  # Remove periods from the end
                if domain.count('.') == 1:  # Check if it's not a subdomain
                    domains.add(domain)
    return domains

def main():
    input_directory = 'data/icann_zone_requests/'
    input_files = ['com.txt', 'info.txt', 'net.txt', 'org.txt']

    unique_domains = set()

    for filename in input_files:
        full_path = os.path.join(input_directory, filename)
        domains = extract_domains_from_file(full_path)
        unique_domains.update(domains)

    output_directory = 'data/raw/'
    output_filename = 'unique_domains.txt'

    with open(os.path.join(output_directory, output_filename), 'w') as output_file:
        for domain in unique_domains:
            output_file.write(f"{domain}\n")

    print(f"Unique domain addresses have been saved to '{os.path.join(output_directory, output_filename)}'")

if __name__ == "__main__":
    main()
