import pandas as pd
from pathlib import Path
# let's create a set of locals referring to our directory and working directory 
home = Path.home()
work_dir = (home / 'election_inflation_analysis')
data = (work_dir / 'data')
raw_data = (data / 'raw')
clean_data = (data / 'clean')
input = (work_dir / 'input')
output = (work_dir / 'output')
code = Path.cwd() 

county_state_crosswalk = pd.read_csv(f'{clean_data}/county_msa_crosswalk_cleaned.csv')
# read inflation data into file
inflation_data = pd.read_csv(f'{clean_data}/cpi_cumulative.csv')
election_data = pd.read_csv(f'{clean_data}/trump_2020_2024.csv')

# first merge election and crosswalk:
election_merged = election_data.merge(county_state_crosswalk, on=['state', 'county_name'], 
                                      how='outer', indicator=True)
election_merged = election_merged[election_merged['_merge'] == 'both'] # filter to BOTH
election_merged = election_merged.drop(columns='_merge')
# with msa's in hand, now let's remake the trump vote share variables:
filtered = election_merged.groupby('msa', as_index=False).agg({
        'totalvotes, 2020': 'sum',
        'totalvotes, 2024': 'sum',
        'trump votecount, 2020': 'sum',
        'trump votecount, 2024': 'sum'
})
for year in ['2020', '2024']:
    filtered[f'trump %, {year}'] = (filtered[f'trump votecount, {year}'] / filtered[f'totalvotes, {year}']) * 100
filtered['2020-2024 swing'] = filtered['trump %, 2024'] - filtered['trump %, 2020']
# now merge inflation data 
master = election_merged.merge(inflation_data, on='msa', how='outer', indicator=True)
master.to_csv(f'{clean_data}/county_level_master.csv', index=False) # export to CSV the county-based master data

master = filtered.merge(inflation_data, on='msa', how='outer', indicator=True)
master.to_csv(f'{clean_data}/msa_level_master.csv', index=False) # export to CSV the MSA-based Trump data