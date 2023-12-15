import pandas as pd
import glob
import os

csv_files = glob.glob('data/simple_scrape_preprocess/*.csv')
dfs = {}

for file in csv_files:
    filename = os.path.basename(file)
    df = pd.read_csv(file)
    dfs[filename] = df

for filename, df in dfs.items():
    print(f"Number of entries in {filename}: {len(df)}")

def intersect_dfs(file_names, only_verified=False):
    first_file_name = file_names[0]
    intersection_df = dfs[first_file_name]

    for file_name in file_names[1:]:
        intersection_df = pd.merge(intersection_df, dfs[file_name], on=['Trademark Domain', 'Candidate Domain'], how='inner')

        if only_verified:
            intersection_df = intersection_df[(intersection_df['Trademark Certificate Verified'] == True) & 
                                              (intersection_df['Candidate Certificate Verified'] == True)]
    
    return intersection_df

def union_dfs(file_names, only_verified=False):
    dataframes = []

    for file_name in file_names:
        # Check if file exists in the dfs dictionary
        if file_name not in dfs:
            raise ValueError(f"DataFrame for {file_name} not found.")

        df = dfs[file_name]
        # Optionally filter for verified candidates
        if only_verified and 'Candidate Certificate Verified' in df.columns:
            print("yes", file_name)
            df = df[df['Candidate Certificate Verified'] == True]
        else:
            print("no", file_name)

        dataframes.append(df)

    # Concatenate all dataframes
    union_df = pd.concat(dataframes).drop_duplicates()
    union_df = union_df.drop_duplicates(subset=['Trademark Domain', 'Candidate Domain'])

    return union_df

union_dfs_list = ['share_cert_serial_number.csv', 'share_cert_subject_CN.csv', 'overlap_subject_alternative_names_verified.csv']
# union_dfs_list = ['blackbook_results.csv']


union_dfs = union_dfs(union_dfs_list, only_verified=True)
print(f"Number of entries in the union: {len(union_dfs)}")

# union_dfs.to_csv('data/union.csv', index=False)
# print("Union DataFrame saved to 'data/union.csv'")

unique_trademark_domains = union_dfs['Trademark Domain'].unique()
print("Number of unique trademark domains in union_dfs:", len(unique_trademark_domains))

for filename, df in dfs.items():
    if 'Candidate Certificate Verified' in df.columns:
        df = df[df['Candidate Certificate Verified'] == True]

    df = df.drop_duplicates(subset=['Trademark Domain', 'Candidate Domain'])
    union_dfs = union_dfs.drop_duplicates(subset=['Trademark Domain', 'Candidate Domain'])
    print("len after drop duplicates df", len(df))
    intersection = pd.merge(df, union_dfs, on=['Trademark Domain', 'Candidate Domain'], how='inner')

    print(f"Number and percent of entries in the intersection of {filename} and the union: {len(intersection)} ({len(intersection) / (len(df)+.0000000000001)* 100:.2f}%)")
    print(f"Number and percent unique trademark domains in the intersection of {filename} and the union: {len(intersection['Trademark Domain'].unique())} ({len(intersection['Trademark Domain'].unique()) / (len(df['Trademark Domain'].unique())+.0000000001) * 100:.2f}%)")
    print("-" * 80)