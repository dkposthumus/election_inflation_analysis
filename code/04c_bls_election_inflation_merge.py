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
bls_msa_cpi = pd.read_csv(f'{clean_data}/cpi_cumulative.csv')
bea_msa_rpp = pd.read_csv(f'{clean_data}/bea_msa_rpp.csv')

# first merge election and crosswalk:
election_merged_dict = {}
for offices in ['house', 'senate', 'pres']:
    election_data = pd.read_csv(f'{clean_data}/{offices}_2020_2024.csv')
    election_merged = election_data.merge(county_state_crosswalk, on=['state', 'county_name'], 
                                          how='outer', indicator='merge')
    election_merged = election_merged[election_merged['merge'] == 'both'] # filter to BOTH
    election_merged = election_merged.drop(columns='merge')
    election_merged_dict[offices] = election_merged

for office, label in zip(['house', 'senate', 'pres'], ['rep', 'rep', 'trump']):
    # with msa's in hand, now let's remake the trump vote share variables:
    df = election_merged_dict[office]
    df = df.groupby('msa', as_index=False).agg({
        f'{office} totalvotes, 2020': 'sum',
        f'{office} totalvotes, 2024': 'sum',
        f'{office} {label} votecount, 2020': 'sum',
        f'{office} {label} votecount, 2024': 'sum'
    })
    for year in ['2020', '2024']:
        df[f'{office} {label} %, {year}'] = (df[f'{office} {label} votecount, {year}'] / df[f'{office} totalvotes, {year}']) * 100
    df[f'{office} {label} 2020-2024 swing'] = df[f'{office} {label} %, 2024'] - df[f'{office} {label} %, 2020']
    election_merged_dict[office] = df
# now concatenate horizontally all dataframes in the dictionary
house = election_merged_dict['house']
senate = election_merged_dict['senate']
trump = election_merged_dict['pres']
#merge everything 
election_data = pd.merge(house, senate, on='msa', how='outer', indicator='senate-house _merge')
election_data = pd.merge(election_data, trump, on='msa', how='outer', indicator='congress-trump _merge')
# now merge inflation data with election data
master = election_data.merge(bls_msa_cpi, on='msa', how='outer', indicator=True)
master.to_csv(f'{clean_data}/msa_bls_level_master.csv', index=False) # export to CSV the MSA-based master data

master = election_data.merge(bea_msa_rpp, on='msa', how='outer', indicator=True)
master.to_csv(f'{clean_data}/msa_bea_level_master.csv', index=False) # export to CSV the MSA-based master data