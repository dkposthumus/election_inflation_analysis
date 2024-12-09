import pandas as pd
from pathlib import Path
# let's create a set of locals referring to our directory and working directory 
work_dir = Path('/Users/danpost/Dropbox/inflation_election')
data = (work_dir / 'data')
election_data = (data / 'election_data')
inflation_data = (data / 'inflation_data')
code = Path.cwd() 

# first, pull in clean bea data 
bea_msa_rpp = pd.read_csv(inflation_data / 'clean/bea_msa_rpp.csv')
# we only want the cumulative biden inflation; collapse on averages by MSA
bea_msa_rpp = bea_msa_rpp.groupby(['msa', 'category'], as_index=False)['cumulative biden rpp percent change'].mean()
# next, election data and crosswalk
crosswalk = pd.read_csv(f'{data}/county_msa_crosswalk_cleaned.csv')
election_data = pd.read_csv(f'{election_data}/clean/trump_2020_2024.csv')
# first merge election and crosswalk:
election_merged = election_data.merge(crosswalk, on=['state', 'county_name'], 
                                      how='outer', indicator=True)
election_merged = election_merged[election_merged['_merge'] == 'both'] # filter to BOTH
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
master = pd.merge(bea_msa_rpp, filtered, on='msa', 
            how='outer', indicator=True)
print(master['_merge'].value_counts(normalize=True)) # check how successful our merge was
# export data 
master.to_csv(f'{data}/bea_county_msa_master.csv', index=False)