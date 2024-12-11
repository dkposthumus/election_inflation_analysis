import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress
# let's create a set of locals referring to our directory and working directory 
home = Path.home()
work_dir = (home / 'election_inflation_analysis')
data = (work_dir / 'data')
raw_data = (data / 'raw')
clean_data = (data / 'clean')
input = (work_dir / 'input')
output = (work_dir / 'output')
code = Path.cwd() 


def swing_scatterplot(df, categories, office, formal_office, label, formal_label, inflation_var):
        if office == 'house' or office == 'senate':
            # for house/senate, we need to drop all observations where either the dem or republican candidates are 0 (missing) in 2020/2024
            for party in ['dem', 'rep']:
                df = df[(df[f'{office} {party} votecount, 2020'] > 0) & df[f'{office} {party} votecount, 2024'] > 0]
        for category in categories:
            category_df = df[df['category'] == category]
            # drop all missing observations for swing / inflation
            category_df = category_df.dropna(subset=[f'{office} {label} 2020-2024 swing', 
                                                     f'cumulative biden {inflation_var}'])
            x = category_df[f'cumulative biden {inflation_var}']
            y = category_df[f'{office} {label} 2020-2024 swing']
            plt.scatter(x, y)
            plt.axhline(y=0, color='black', linestyle='--')
            try:
                slope, intercept, r_value, p_value, std_err = linregress(x, y)
                line = slope * x + intercept
            except:
                print(f'Error in fitting linear line of best fit for {office} {category}')
                continue
            plt.plot(x, line, color='black', label=f"Best Fit: y={slope:.2f}x+{intercept:.2f}")
            plt.title(f'{formal_office.title()} {formal_label.title()} Vote Change and Cumulative Inflation, MSA Level, \n Jan. 2021 - Sept. 2024, Category: {category.title()}')
            plt.xlabel('Cumulative Inflation (%)')
            plt.ylabel(f'{formal_office.title()} {formal_label.title()} Vote Change Since 2020')
            plt.grid(True)
            plt.tight_layout(pad=2.0)
            #plt.legend()
            plt.savefig(f'{output}/{office}_{category}_msa_swing_scatter.png')
            plt.close()

offices = ['house', 'senate', 'pres']
labels = ['rep', 'rep', 'trump']
formal_labels = ['Republican', 'Republican', 'Trump']
formal_offices = ['House', 'Senate', 'Presidential']

# read master dataset 
bls_master = pd.read_csv(f'{clean_data}/msa_bls_level_master.csv')
bls_master = bls_master[bls_master['_merge'] == 'both']
bls_categories = ['rent', 'food', 'apparel', 'transportation', 'medical care', 
              'recreation', 'education and communication', 'motor fuel']
for office, label, formal_label, formal_office in zip(offices, labels, 
                                                      formal_labels, formal_offices):
    swing_scatterplot(bls_master, bls_categories, office, formal_office, 
                      label, formal_label, 'inflation')

# read in BEA master dataset and plot 
bea_master = pd.read_csv(f'{clean_data}/msa_bea_level_master.csv')
bea_master = bea_master[bea_master['_merge'] == 'both']
bea_categories = ['all items', 'goods', 'housing', 'other services', 'utilities']
for office, label, formal_label, formal_office in zip(offices, labels, 
                                                      formal_labels, formal_offices):
    swing_scatterplot(bea_master, bea_categories, office, 
                      formal_office, label, formal_label, 'rpp percent change')
    
# now let's plot how far ahead senate/house candidates ran in 2024 
offices = ['house', 'senate']

for df, categories, inflation_var in zip([bls_master, bea_master], 
                                               [bls_categories, bea_categories],
                                               ['inflation', 'rpp percent change']):
    for office, label, formal_label, formal_office in zip(offices, labels, 
                                                          formal_labels, formal_offices):
        temp_df = df.copy()
        for party in ['dem', 'rep']:
            temp_df = temp_df[(temp_df[f'{office} {party} votecount, 2020'] > 0) & temp_df[f'{office} {party} votecount, 2024'] > 0]
        temp_df['rep run ahead of trump %'] = temp_df[f'{office} rep %, 2024'] - df['pres trump %, 2024']
        for category in categories:
            category_df = temp_df[temp_df['category'] == category]
            category_df = category_df.dropna(subset=[f'{office} {label} %, 2024'])
            x = category_df[f'cumulative biden {inflation_var}']
            y = category_df['rep run ahead of trump %']
            plt.scatter(x, y)
            try:
                slope, intercept, r_value, p_value, std_err = linregress(x, y)
                line = slope * x + intercept
                plt.plot(x, line, color='black', label=f"Best Fit: y={slope:.2f}x+{intercept:.2f}")
            except:
                print(f'Error in fitting linear line of best fit for {office} {category}')
                continue
            plt.title(f'{formal_office.title()} Republican - Trump Vote Share , MSA Level, \n 2020 vs. 2024, Category: {category.title()}')
            plt.xlabel(f'Cumulative Biden {inflation_var.title()} (%)')
            plt.ylabel(f'{formal_office.title()} Republican - Trump Vote Share, 2024 (%)')
            plt.grid(True)
            plt.tight_layout(pad=2.0)
            plt.savefig(f'{output}/{office}_{category}_rep_run_ahead_of_trump.png')
            plt.show()