import pandas as pd
from pathlib import Path
# let's create a set of locals referring to our directory and working directory 
work_dir = Path('/Users/danpost/Dropbox/inflation_election')
data = (work_dir / 'data')
election_data = (data / 'election_data')
inflation_data = (data / 'inflation_data')
code = Path.cwd() 

historical_election = pd.read_csv(f'{election_data}/raw/county_pres_2000_2020.csv')
election_2024 = pd.read_excel(f'{election_data}/raw/(2024-12-05) Pres_Election_Data_2024_0.6.xlsx', sheet_name='County')

# first filter historical election to include only 2020 elections
election_2020 = historical_election[historical_election['year'] == 2020]
trump_2020 = election_2020[election_2020['candidate'] == 'DONALD J TRUMP']
# we have a problem; not all counties have TOTALS, so we would have to sum those ourselves (very annoying)
for state in trump_2020['state'].unique():
    state_df = trump_2020[trump_2020['state'] == state]
    for county in state_df['county_name'].unique():
        county_df = state_df[state_df['county_name'] == county]
        if 'TOTAL' not in county_df['mode'].unique():
            total_candidatevotes = county_df['candidatevotes'].sum()
            total_votes = county_df['totalvotes'].mean()
            total_row = {col: None for col in trump_2020.columns}  # Initialize with None
            total_row['state'] = state
            total_row['county_name'] = county
            total_row['mode'] = 'TOTAL'
            total_row['candidatevotes'] = total_candidatevotes
            total_row['totalvotes'] = total_votes
            trump_2020 = pd.concat([trump_2020, pd.DataFrame([total_row])], ignore_index=True)
trump_2020 = trump_2020[trump_2020['mode'] == 'TOTAL']
trump_2020['trump %, 2020'] = (trump_2020['candidatevotes'] / trump_2020['totalvotes']) * 100
trump_2020['trump votecount, 2020'] = trump_2020['candidatevotes']
trump_2020 = trump_2020[['state', 'totalvotes', 'county_name', 'trump votecount, 2020', 'trump %, 2020']]
trump_2020.rename(columns={'totalvotes': 'totalvotes, 2020'}, inplace=True)
trump_2020 = trump_2020.dropna(subset=['county_name']) # drop all rows where 'county_name' is missing
trump_2020 = trump_2020.dropna(subset=['trump %, 2020']) # drop all w/missing trump vote obs
# force all observations to be entirely lowercase
trump_2020 = trump_2020.applymap(lambda x: x.lower() if isinstance(x, str) else x)
trump_2020 = trump_2020[trump_2020['county_name'] != 'st. louis city']

# now filter 2024 election data to include only Trump
trump_2024 = election_2024[['state', 'county_name', 'trump %, 2024', 'trump votecount, 2024', 
                            'Total Vote', 'LSAD_TRANS']]
trump_2024 = trump_2024[trump_2024['LSAD_TRANS'].isin(['County', 'Parish'])]
# we have to miscellaneously do some renaming 
for problem, solution in zip(['LaSalle', 'St. Louis', 'Coös'],
                            ['la salle', 'st. louis county', 'coos']):
    trump_2024.loc[trump_2024['county_name'] == problem, 'county_name'] = solution
trump_2024.loc[trump_2024['state'] == 'DC', 'state'] = 'District of Columbia'
trump_2024.rename(columns={'Total Vote': 'totalvotes, 2024'}, inplace=True)
trump_2024['trump %, 2024'] = trump_2024['trump %, 2024'] * 100 # convert to percentage
trump_2024 = trump_2024.dropna(subset=['county_name']) # drop all rows where 'county_name' is missing
trump_2024 = trump_2024.dropna(subset=['trump %, 2024']) # drop all w/missing trump vote obs
# now rename all states, which are abbreviations to the lowercase state names
state_mapping = {
    'AL': 'alabama', 'AK': 'alaska', 'AZ': 'arizona', 
    'AR': 'arkansas', 'CA': 'california',
    'CO': 'colorado', 'CT': 'connecticut', 'DE': 'delaware', 
    'FL': 'florida', 'GA': 'georgia',
    'HI': 'hawaii', 'ID': 'idaho', 'IL': 'illinois', 
    'IN': 'indiana', 'IA': 'iowa',
    'KS': 'kansas', 'KY': 'kentucky', 'LA': 'louisiana', 
    'ME': 'maine', 'MD': 'maryland',
    'MA': 'massachusetts', 'MI': 'michigan', 'MN': 'minnesota', 
    'MS': 'mississippi', 'MO': 'missouri',
    'MT': 'montana', 'NE': 'nebraska', 'NV': 'nevada', 
    'NH': 'new hampshire', 'NJ': 'new jersey',
    'NM': 'new mexico', 'NY': 'new york', 
    'NC': 'north carolina', 'ND': 'north dakota',
    'OH': 'ohio', 'OK': 'oklahoma', 'OR': 'oregon', 
    'PA': 'pennsylvania', 'RI': 'rhode island',
    'SC': 'south carolina', 'SD': 'south dakota', 'TN': 'tennessee', 
    'TX': 'texas', 'UT': 'utah',
    'VT': 'vermont', 'VA': 'virginia', 'WA': 'washington', 
    'WV': 'west virginia', 'WI': 'wisconsin', 'WY': 'wyoming'
}
trump_2024['state'] = trump_2024['state'].map(lambda x: state_mapping.get(x, x.lower()))
trump_2024 = trump_2024.applymap(lambda x: x.lower() if isinstance(x, str) else x)

# now merge OUTER
trump_2020_2024 = trump_2020.merge(trump_2024, on=['state', 'county_name'], how='outer')
trump_2020_2024['trump %, 2024'] = pd.to_numeric(trump_2020_2024['trump %, 2024'], errors='coerce')
trump_2020_2024['trump %, 2024'] = trump_2020_2024['trump %, 2024'].astype('float64')
# let's make another column, change in trump vote share
trump_2020_2024['2020-2024 swing'] = trump_2020_2024['trump %, 2024'] - trump_2020_2024['trump %, 2020']

trump_2020_2024.to_csv(f'{election_data}/clean/trump_2020_2024.csv', index=False)