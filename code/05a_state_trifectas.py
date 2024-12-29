import pandas as pd
from pathlib import Path
import rpy2.robjects as robjects
from rpy2.robjects.packages import importr
# let's create a set of locals referring to our directory and working directory 
home = Path.home()
work_dir = (home / 'election_inflation_analysis')
data = (work_dir / 'data')
raw_data = (data / 'raw')
clean_data = (data / 'clean')
input = (work_dir / 'input')
output = (work_dir / 'output')
code = Path.cwd() 

# import R packages
rmarkdown = importr('rmarkdown')
rmd_file = code / '05b_state_trifectas.Rmd'
try:
    robjects.r(f"""
    output_dir <- "{clean_data.as_posix()}"
    rmarkdown::render(
        input = "{rmd_file}",
        output_file = file.path(output_dir, "State_Trifectas_Ballotpedia_Scrape.pdf")
    )
    """)
    print(f"R Markdown rendered successfully. Output saved to: {clean_data}")
except Exception as e:
    print(f"Error rendering R Markdown: {e}")