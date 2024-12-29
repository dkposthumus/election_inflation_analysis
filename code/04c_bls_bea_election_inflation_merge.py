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


# define priority_order for states that we'll use for state-msa mapping
priority_order = [
    "california",
    "texas",
    "florida",
    "new york",
    "pennsylvania",
    "illinois",
    "ohio",
    "georgia",
    "north carolina",
    "michigan",
    "new jersey",
    "virginia",
    "washington",
    "arizona",
    "massachusetts",
    "tennessee",
    "indiana",
    "missouri",
    "maryland",
    "wisconsin",
    "colorado",
    "minnesota",
    "south carolina",
    "alabama",
    "louisiana",
    "kentucky",
    "oregon",
    "oklahoma",
    "connecticut",
    "utah",
    "iowa",
    "nevada",
    "arkansas",
    "mississippi",
    "kansas",
    "new mexico",
    "nebraska",
    "idaho",
    "west virginia",
    "hawaii",
    "new hampshire",
    "maine",
    "montana",
    "rhode island",
    "delaware",
    "south dakota",
    "north dakota",
    "alaska",
    "vermont",
    "wyoming"
]

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

# we want a crosswalk from msa to county_name (prioritizing states by population)
def prioritize_state(states):
    for state in priority_order:
        if state in states:
            return state
    return states[0]  # Default to the first state if none in priority_order match

state_crosswalk = election_merged_dict['pres'].groupby('msa', as_index=False).agg({
    'state': lambda x: prioritize_state(x.unique())
})

for office, labels in zip(['house', 'pres', 'senate'], [['dem', 'rep'], ['trump'], ['dem', 'rep']]):
    # with msa's in hand, now let's remake the trump vote share variables:
    df = election_merged_dict[office]
    if office == 'pres':
        df = df.groupby('msa', as_index=False).agg({
            f'{office} totalvotes, 2020': 'sum',
            f'{office} totalvotes, 2024': 'sum',
            f'{office} trump votecount, 2020': 'sum',
            f'{office} trump votecount, 2024': 'sum'
        })
    if office == 'house' or office == 'senate':
        df = df.groupby('msa', as_index=False).agg({
            f'{office} totalvotes, 2020': 'sum',
            f'{office} totalvotes, 2024': 'sum',
            f'{office} dem votecount, 2020': 'sum',
            f'{office} dem votecount, 2024': 'sum',
            f'{office} rep votecount, 2020': 'sum',
            f'{office} rep votecount, 2024': 'sum'
        })
    for label in labels:
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
# now merge back on state as a variable 
election_data = election_data.merge(state_crosswalk, on='msa', how='outer', indicator=False)
# now merge inflation data with election data
master = election_data.merge(bls_msa_cpi, on='msa', how='outer', indicator=True)
master.to_csv(f'{clean_data}/msa_bls_level_master.csv', index=False) # export to CSV the MSA-based master data

master = election_data.merge(bea_msa_rpp, on='msa', how='outer', indicator=True)
master.to_csv(f'{clean_data}/msa_bea_level_master.csv', index=False) # export to CSV the MSA-based master data