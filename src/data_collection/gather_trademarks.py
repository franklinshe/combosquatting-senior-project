import csv

def save_data_to_csv(data, output_path):
    """Save the provided data to a CSV file."""
    with open(output_path, "w", newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)
    print(f"Data saved to {output_path}")

def main():
    # Define the data (hard coded for now)
    data = [
        ["Trademark", "Category", "Domain"],
        ["google", "Technology", "google.com"],
        ["facebook", "Social Media", "facebook.com"],
        ["youtube", "Streaming", "youtube.com"],
        ["microsoft", "Technology", "microsoft.com"],
        ["amazon", "Ecommerce", "amazon.com"],
        ["twitter", "Social Media", "twitter.com"],
        ["baidu", "Technology", "baidu.com"],
        ["instagram", "Social Media", "instagram.com"],
        ["akamai", "Internet", "akamai.com"],
        ["netflix", "Streaming", "netflix.com"],
    ]

    output_path = 'data/raw/sample_trademark_list.csv'
    save_data_to_csv(data, output_path)

if __name__ == "__main__":
    main()
