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

# we need to clean/prepare MSA-level data from the BEA for RPP (price parity)
raw_bea_msa = pd.read_excel(f'{raw_data}/bea_msa_rpp.xlsx', skiprows=5)
'''
We have a few problems/features of this dataset to clean:
- reshape long to create a panel dataset 
- remove unnecessary columns
- the MSA names are a mess
'''
# first -- make all string variables lowercase 
msa_rpp_df = raw_bea_msa.copy() 
msa_rpp_df = msa_rpp_df.applymap(lambda x: x.lower() if isinstance(x, str) else x)
# generate 2020-2022 cumulative inflation (percent change in RPP):
msa_rpp_df['cumulative biden rpp percent change'] = ((msa_rpp_df['2022'] - msa_rpp_df['2020']) / msa_rpp_df['2020'] ) * 100
# next reshape long
msa_rpp_df = pd.melt(
    msa_rpp_df,
    id_vars=['GeoFips', 'GeoName', 'LineCode', 'Description',
                'cumulative biden rpp percent change'], # Columns to keep as identifiers
    value_vars=['2008', '2009', '2010', '2011', '2012', '2013',
                '2013', '2014', '2015', '2016', '2017', '2018', 
                '2019', '2020', '2021', '2022'],  # Columns to unpivot
    var_name='year',         # Name for the new variable column
    value_name='rpp'       # Name for the new value column
)
# replace everything after the first comma in msa name
msa_rpp_df['GeoName'] = msa_rpp_df['GeoName'].str.split(',').str[0]
# replace a bunch of values for the 'Description' Variable: 
recode_categories_dict = {
    'rpps: all items': 'all items',
    '  rpps: goods': 'goods',
    '  rpps: services: housing': 'housing',
    '  rpps: services: utilities': 'utilities',
    '  rpps: services: other': 'other services'
}
# apply the recode
msa_rpp_df['Description'] = msa_rpp_df['Description'].replace(recode_categories_dict)
# drop the LineCode variable
msa_rpp_df.drop(columns=['LineCode'], inplace=True)
# re-name columns
msa_rpp_df.rename(columns = {
    'GeoFips': 'fips',
    'GeoName': 'msa',
    'Description': 'category'
    }, inplace=True)
# save the dataset
msa_rpp_df.to_csv(f'{clean_data}/bea_msa_rpp.csv', index=False)