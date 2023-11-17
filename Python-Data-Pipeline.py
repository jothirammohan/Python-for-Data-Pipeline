import pandas as pd
import csv
import faker
import numpy as np

# Use a mapping file to replace a column value *************************************************************************
def load_mapping_file(mapping_file_path):
    mapping_dict = {}

    with open(mapping_file_path, 'r') as mapping_file:
        reader = csv.reader(mapping_file)
        next(reader)  # Skip header if present
        for row in reader:
            original_value, mapped_value = row
            mapping_dict[original_value] = mapped_value

    return mapping_dict

# Use Data cleaning & Data preparation techniques *************************************************************************
def preprocess_csv(input_csv_path, mapping_file_path):

    # Read CSV into a pandas DataFrame
    df = pd.read_csv(input_csv_path)

    # *******************************************************************************************************************
    # Data profiling
    print("Data Profiling:")
    print(df.info())
    print(df.describe())

    # *******************************************************************************************************************
    # Data cleaning (replace missing values, handle data types, etc.)
    df['MemberDOB'] = pd.to_datetime(df['MemberDOB'], errors='coerce')

    # *******************************************************************************************************************
    # Data filtering
    df = df[df['ChargeAmount'] > 0]  # Example: Filter rows where ChargeAmount is greater than 0

    # *******************************************************************************************************************
    # Data sorting
    df = df.sort_values(by=['ServiceStartDate'])

    # *******************************************************************************************************************
    # Data mapping (replace MemberFirstName with mapped values)
    mapping_dict = load_mapping_file(mapping_file_path)
    df['MemberFirstName'] = df['MemberFirstName'].map(mapping_dict)

    # *******************************************************************************************************************
    # Data masking (semantic masking for MemberFirstName if not found in the mapping)
    df['MemberFirstName'] = df['MemberFirstName'].apply(lambda x: faker.Faker().first_name() if pd.isnull(x) else x)

    # *******************************************************************************************************************
    # Data aggregating (group by and aggregate)
    aggregated_df = df.groupby(['ProviderName']).agg({'ChargeAmount': 'sum'}).reset_index()
    print("\nAggregated Data:")
    print(aggregated_df)

    # *******************************************************************************************************************
    # Data joining (example: joining with another dataset, you can adjust based on your needs)
    # additional_data = pd.read_csv('path/to/another/dataset.csv')
    # df = pd.merge(df, additional_data, on='common_column', how='left')

    # *******************************************************************************************************************
    # Numpy operation: Add a random adjustment to the total charge amount
    df['AdjustedChargeAmount'] = df['ChargeAmount'] + np.random.uniform(-10, 10, len(df))

    # *******************************************************************************************************************
    return df

# Generate 837 file using the dataframe *************************************************************************
def generate_837_file(df, output_edi_path):
    # Prepare an empty list to store EDI content
    edi_content = []

    for _, row in df.iterrows():
        # Build EDI segments based on the dataset for each row
        edi_segment = f"ISA*00          *00          *01*030240928      *30*421406317      *180807*1202*^*00501*000001507*0*T*:\n"
        edi_segment += f"GS*HC*030240928*421406317*20180807*12022605*150700*X*005010X222A1~\n"
        edi_segment += f"ST*837*0001*005010X222A1~\n"
        edi_segment += f"NM1*IL*1*{row['MemberLastName']}*{row['MemberFirstName']}****MI*{row['MemberID']}~\n"
        edi_segment += f"N3*{row['SubscriberAddress']}~\n"
        edi_segment += f"N4*{row['SubscriberCity']}*{row['SubscriberState']}*{row['SubscriberZip']}~\n"
        edi_segment += f"DMG*D8*{row['MemberDOB']}*{row['SubscriberGender']}~\n"
        edi_segment += f"NM1*PR*2*{row['ProviderName']}*****PI*{row['ProviderNPI']}~\n"
        edi_segment += f"CLM*{row['DiagnosisCode']}*{row['AdjustedChargeAmount']}***11:B:1*Y*A*Y*Y~\n"
        # Add more segments as needed based on your dataset structure

        # Close the current EDI transaction with SE and GE segments
        edi_segment += "SE*30*0001~\n"
        edi_segment += "GE*1*150700~\n"

        # Append the EDI segment to the content
        edi_content.append(edi_segment)

    # Write the entire EDI content to the output file
    with open(output_edi_path, 'w') as edi_file:
        edi_file.write(''.join(edi_content))

# Data directory
input_csv_path = 'A:\EDI_Input.csv'
output_edi_path = 'A:\output.edi'
mapping_file_path = 'A:\mapping.csv'

# Data preprocessing
processed_df = preprocess_csv(input_csv_path, mapping_file_path)

# Generate EDI file
generate_837_file(processed_df, output_edi_path)
