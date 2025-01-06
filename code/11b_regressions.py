import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress
import statsmodels.api as sm
# let's create a set of locals referring to our directory and working directory 
home = Path.home()
work_dir = (home / 'election_inflation_analysis')
data = (work_dir / 'data')
raw_data = (data / 'raw')
clean_data = (data / 'clean')
input = (work_dir / 'input')

output = (work_dir / 'output')
code = Path.cwd() 

# let's run a regression for each BEA inflation category by MSA and report statistics 
bea_master = pd.read_csv(f'{clean_data}/msa_bea_level_master.csv')
bea_master = bea_master[bea_master['_merge'] == 'both']

# generate dummy variables for each possible value of governing data 
bea_master = pd.get_dummies(bea_master, columns=['total_gov'], prefix='gov')

offices = ['house', 'pres']
labels = ['rep', 'trump']

def format_with_significance(estimate, std_error, p_value):
    if p_value < 0.01:
        significance = '***'
    elif p_value < 0.05:
        significance = '**'
    elif p_value < 0.1:
        significance = '*'
    else:
        significance = ''
    return f"{estimate:.3f} ({std_error:.3f}){significance}"

results = {}
# now run regression, where vote swing FOR trump is the outcome variable and we have dummy variables for each of the 3 possible values for 'total_gov' ('R', 'D', 'Split')
bea_categories = ['all items', 'goods', 'housing', 'other services', 'utilities']

# i think there would be some effect of being in a battleground state, where candidates devoted resources for campaigning in the presidential campsigns
# so let's add a dummy variable for battleground states
bea_master['battleground'] = bea_master['state'].apply(lambda x: 1 if x in [
    'georgia', 'pennsylvania', 'michigan', 'wisconsin', 'north carolina', 'nevada', 'arizona'
] else 0)

for office, label in zip(offices, labels):
    results_list = []
    df = bea_master.copy()
    if office == 'house' or office == 'senate':
        # for house/senate, we need to drop all observations where either the dem or republican candidates are 0 (missing) in 2020/2024
        for party in ['dem', 'rep']:
            df = df[(df[f'{office} {party} votecount, 2020'] > 0) & df[f'{office} {party} votecount, 2024'] > 0]
    if office == 'pres':
        df = df[(df['pres trump votecount, 2024'] > 0) & df['pres trump votecount, 2020'] > 0]
    for category in bea_categories:
        bea_master_category = df[df['category'] == category]
        bea_master_category = bea_master_category.dropna(subset=['cumulative biden rpp percent change'])
        X = bea_master_category[['gov_R', 'gov_D', 'gov_Split', 'cumulative biden rpp percent change', 'battleground']]
        X['R interaction'] = X['gov_R'] * X['cumulative biden rpp percent change']
        X['D interaction'] = X['gov_D'] * X['cumulative biden rpp percent change']
        X['Split interaction'] = X['gov_Split'] * X['cumulative biden rpp percent change']
        X['battleground interaction'] = X['battleground'] * X['cumulative biden rpp percent change']
        if office == 'pres':
            X = X[['R interaction', 'D interaction', 'Split interaction', 'gov_Split', 
            'cumulative biden rpp percent change', 'battleground', 'battleground interaction']]
        else:
            X = X[['R interaction', 'D interaction', 'Split interaction', 'gov_Split', 
            'cumulative biden rpp percent change']]
        #X = bea_master_category['cumulative biden rpp percent change']
        X = sm.add_constant(X)
        X = X.astype(float)
        y = bea_master_category[f'{office} {label} 2020-2024 swing']
        y = y.apply(pd.to_numeric, errors='coerce')
        X, y = X.align(y, join='inner', axis=0)
        model = sm.OLS(y, X).fit(cov_type='HC1')
        # Extract results for the current category
        result = {'office': office, 'label': label, 'category': category}
        for var in model.params.index:
            estimate = model.params[var]
            std_error = model.bse[var]
            p_value = model.pvalues[var]
            result[var] = format_with_significance(estimate, std_error, p_value)  # Format with asterisks
        results_list.append(result)
    results_df = pd.DataFrame(results_list)
    results_df.drop(columns=['office', 'label',
                             'cumulative biden rpp percent change'], inplace=True)
    results_df.rename(columns={'cumulative biden rpp percent change': 'Biden RPP Change',
                               'gov_R': 'R',
                               'gov_D': 'D',
                               'gov_Split': 'Split'}, inplace=True)
    # Convert to a LaTeX table
    latex_table = results_df.to_latex(
        index=False,          # Exclude DataFrame index
        column_format="l" + "c" * (len(results_df.columns) - 1), 
        caption=f'Regression Results by Category for {office}', 
        label="tab:regression_results",  # Add label for referencing in LaTeX
        escape=False          # Allow special characters like parentheses
    )
    latex_table = latex_table.replace('\\begin{table}', '\\begin{table}[H]')
    # Save to a .tex file
    file_path = f'{output}/msa_inflation_reg_{office}.tex'
    with open(file_path, 'w') as f:
        f.write(latex_table)
    # Print LaTeX table for review
    #print(latex_table)