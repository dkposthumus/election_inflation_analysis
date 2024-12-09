import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress
# let's create a set of locals referring to our directory and working directory 
work_dir = Path('/Users/danpost/Dropbox/inflation_election')
data = (work_dir / 'data')
election_data = (data / 'election_data')
inflation_data = (data / 'inflation_data')
output = (work_dir / 'output')
code = Path.cwd() 

# read master dataset 
master_filtered = pd.read_csv(f'{data}/msa_level_master.csv')
master_filtered = master_filtered[master_filtered['_merge'] == 'both']
categories = ['rent', 'food', 'apparel', 'transportation', 'medical care', 
              'recreation', 'education and communication', 'motor fuel']
for category in categories:
    category_df = master_filtered[master_filtered['category'] == category]
    x = category_df['cumulative biden inflation']
    y = category_df['2020-2024 swing']
    plt.scatter(x, y)
    plt.axhline(y=0, color='black', linestyle='--')
    slope, intercept, r_value, p_value, std_err = linregress(x, y)
    line = slope * x + intercept
    plt.plot(x, line, color='black', label=f"Best Fit: y={slope:.2f}x+{intercept:.2f}")
    plt.title(f'Trump Vote Change and Cumulative Inflation, MSA Level, \n Jan. 2021 - Sept. 2024, Category: {category.title()}')
    plt.xlabel('Cumulative Inflation (%)')
    plt.ylabel('Trump Vote Change Since 2020')
    plt.grid(True)
    plt.tight_layout(pad=2.0)
    #plt.legend()
    plt.savefig(f'{output}/{category}_msa_swing_scatter.png')
    plt.show()

# read in BEA master dataset and plot 
master_filtered = pd.read_csv(f'{data}/bea_county_msa_master.csv')
master_filtered = master_filtered[master_filtered['_merge'] == 'both']
categories = ['all items', 'goods', 'housing', 'other services', 'utilities']
master_filtered = master_filtered[master_filtered['msa']!='boston-cambridge-newton']
master_filtered = master_filtered.dropna()
for category in categories:
    category_df = master_filtered[master_filtered['category'] == category]
    x = category_df['cumulative biden rpp percent change']
    y = category_df['2020-2024 swing']
    plt.scatter(x, y)
    plt.axhline(y=0, color='black', linestyle='--')
    slope, intercept, r_value, p_value, std_err = linregress(x, y)
    line = slope * x + intercept
    plt.plot(x, line, color='black', label=f"Best Fit: y={slope:.2f}x+{intercept:.2f}")
    plt.title(f'Trump Vote Change and Cumulative % Change in RPP, MSA Level, \n 2020-2022 Category: {category.title()}')
    plt.xlabel('Cumulative Change in Relative Price Parity (RPP) (%)')
    plt.ylabel('Trump Vote Change Since 2020')
    plt.grid(True)
    plt.tight_layout(pad=2.0)
    #plt.legend()
    plt.savefig(f'{output}/{category}_bea_msa_swing_scatter.png')
    plt.show()