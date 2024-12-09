import pandas as pd
from pathlib import Path
# let's create a set of locals referring to our directory and working directory 
work_dir = Path('/Users/danpost/Dropbox/inflation_election')
data = (work_dir / 'data')
election_data = (data / 'election_data')
inflation_data = (data / 'inflation_data')
code = Path.cwd() 

'''first we have to clean the crosswalk data 
we want a dataset that has:
- state 
- county 
- MSA 
so that we can merge on state / county'''
county_state_crosswalk = pd.read_excel(f'{data}/county_msa_crosswalk_raw.xlsx', 
                                       sheet_name='Jul. 2023 Crosswalk')
county_state_crosswalk = county_state_crosswalk[['County Title', 'MSA Title']]
# first, create state variable 
county_state_crosswalk['state'] = county_state_crosswalk['County Title'].apply(lambda x: x.split(',')[1].strip() if ',' in x else None)
# now create county variable
county_state_crosswalk['county_name'] = county_state_crosswalk['County Title'].apply(lambda x: x.split(',')[0].strip() if ',' in x else None)
# now drop 'county' from all values of county variable
identifiers = ['County', 'Municipio', 'Municiplatiy', 'Borough', 'Planning Region']
for identifier in identifiers:
    county_state_crosswalk['county_name'] = county_state_crosswalk['county_name'].str.replace(identifier, 
                            '', case=False).str.strip()
# now clean MSA variable
county_state_crosswalk['msa'] = county_state_crosswalk['MSA Title'].apply(lambda x: x.split(',')[0].strip() if ',' in x else None)
county_state_crosswalk = county_state_crosswalk[['state', 'county_name', 'msa']]
# now make all observations lowercase
county_state_crosswalk = county_state_crosswalk.applymap(lambda x: x.lower() if isinstance(x, str) else x)
# export so that we can check
county_state_crosswalk.to_csv(f'{data}/county_msa_crosswalk_cleaned.csv', 
                              index=False)

# next, let's clean the county/fips crosswalk
county_fips_crosswalk = pd.read_csv(f'{data}/county_fips_crosswalk_raw.csv')
county_fips_crosswalk = county_fips_crosswalk.applymap(lambda x: x.lower() if isinstance(x, str) else x)
county_fips_crosswalk.rename(columns={'fipscounty': 'fips',
                                      'countyname_fips': 'county'}, inplace=True)
county_fips_crosswalk = county_fips_crosswalk[['fips', 'county']]
county_fips_crosswalk.to_csv(f'{data}/county_fips_crosswalk_clean.csv', index=False)