import requests 
import pandas as pd
from pathlib import Path
# let's create a set of locals referring to our directory and working directory 
work_dir = Path('/Users/danpost/Dropbox/inflation_election')
data = (work_dir / 'data')
election_data = (data / 'election_data')
inflation_data = (data / 'inflation_data')
code = Path.cwd() 

# we need to define a dictionary with the series IDs by city / series:
categories = ['rent', 'food', 'apparel', 'transportation', 'medical care', 
              'recreation', 'education and communication', 'motor fuel']
category_codes = ['EHA', 'AF11', 'AA', 'AT', 'AM', 'AR', 'AE', 'ETB']
cities = ['Atlanta-Sandy Springs-Roswell', 'Baltimore-Columbia-Towson', 'Boston-Cambridge-Newton', 
          'Chicago-Naperville-Elgin', 'Dallas-Fort Worth-Arlington', 'Denver-Aurora-Centennial', 
          'Detroit-Warren-Dearborn', 'Houston-Pasadena-The Woodlands', 
          'Los Angeles-Long Beach-Anaheim', 'Miami-Fort Lauderdale-West Palm Beach', 
          'Minneapolis-St. Paul-Bloomington', 'New York-Newark-Jersey City', 
          'Philadelphia-Camden-Wilmington', 'Phoenix-Mesa-Chandler', 'Riverside-San Bernardino-Ontario', 
          'St. Louis', 'San Diego-Chula Vista-Carlsbad', 'San Francisco-Oakland-Fremont', 
          'Seattle-Tacoma-Bellevue', 
          'Tampa-St. Petersburg-Clearwater', 'Urban Alaska', 'Urban Hawaii', 'Washington-Arlington-Alexandria']
city_codes = ['S35CS', 'S35ES', 'S11AS', 'S23AS', 'S37AS', 'S48BS', 'S23BS', 'S37BS',
              'S49AS', 'S35BS', 'S24AS', 'S12AS', 'S12BS', 'S48AS', 'S49CS',
              'S24BS', 'S49ES', 'S49BS', 'S49DS', 
              'S35DS', 'S49GS', 'S49FS', 'A311S']
'''series_ids['Atlanta'] = ['housing': 'CUURS35CSAH',
                        'food': 'CUURS35CSAF1',
                        'apparel': 'CUURS35CSAA',
                        'transportation': 'CUURS35CSAT',
                        'medical care': 'CUURS35CSAM',
                        'recreation': 'CUURS35CSAR',
                        'education and communication': 'CUURS35CSAE'' '''
BLS_API_URL = 'https://api.bls.gov/publicAPI/v2/timeseries/data/'
api_key = 'd48a6f346e8b44448a4fac5a8d79f5d3'
data_frames = []
for category, cat_code in zip(categories, category_codes):
    for city, city_code in zip(cities, city_codes):
        series_id = f'CUUR{city_code}{cat_code}'
        # Prepare the API request
        headers = {'Content-type': 'application/json'}
        request_data = {
            'seriesid': [series_id],
            'registrationkey': api_key,
            'startyear': '2019',
            'endyear': '2024'
        }
        # Fetch data from the API
        response = requests.post(BLS_API_URL, json=request_data, headers=headers)
        # Check for a valid response
        if response.status_code == 200:
            # Parse JSON response
            data = response.json()
            # Extract relevant data
            series_data = data['Results']['series'][0]['data']
            df = pd.DataFrame(series_data)
            # Add category and city for context
            df['category'] = category
            df['msa'] = city
            df['series_id'] = series_id
            # Keep only relevant columns and rename
            if df.shape[0] > 0:
                df = df[['category', 'msa', 'series_id', 'year', 'period', 'value']]
                df.rename(columns={'value': 'price_index'}, inplace=True)
                # Append to the list of DataFrames
                data_frames.append(df)
            else:
                print(f"No data available for {series_id}")
        else:
            print(f"Failed to fetch data for {series_id}: {response.status_code}")

# Combine all DataFrames into a single panel DataFrame
panel_df = pd.concat(data_frames, ignore_index=True)
# Save to CSV for further analysis
panel_df.to_csv(f'{inflation_data}/clean/msa_bls_cpi.csv', index=False)

msa_cpi_df = panel_df.copy()
# first create yearmonth variable
msa_cpi_df['month'] = msa_cpi_df['period'].str[-2:]
msa_cpi_df['yearmonth'] = msa_cpi_df['year'].astype(str) + msa_cpi_df['month']
msa_cpi_df['date'] = pd.to_datetime(msa_cpi_df['yearmonth'], format='%Y%m')
msa_cpi_df = msa_cpi_df.applymap(lambda x: x.lower() if isinstance(x, str) else x)
# now we can drop the year and month columns
msa_cpi_df.drop(columns=['year', 'month', 'yearmonth'], inplace=True)
# now find cumulative inflation by city and category
# first, convert price_index to floating 
msa_cpi_df['price_index'] = msa_cpi_df['price_index'].astype(float)
msa_cpi_pivoted = msa_cpi_df.pivot_table(index=['msa', 'category'], columns='date', 
                                         values='price_index')
def calculate_cumulative_inflation(row):
    start_value = row['2021-01-01'] if pd.notna(row['2021-01-01']) else row['2021-02-01']
    end_value = row['2024-09-01'] if pd.notna(row['2024-09-01']) else row['2024-10-01']
    if pd.notna(end_value):  # Ensure the fallback is not also missing
        return ((end_value - start_value) / start_value) * 100
    else:
        return None  # Return None if both values are missing
# Apply the function row-wise
msa_cpi_pivoted['cumulative biden inflation'] = msa_cpi_pivoted.apply(calculate_cumulative_inflation, axis=1)
msa_cpi_pivoted = msa_cpi_pivoted[['cumulative biden inflation']]
# export cumulative inflation file
msa_cpi_pivoted.to_csv(f'{inflation_data}/clean/cpi_cumulative.csv', index=True)
