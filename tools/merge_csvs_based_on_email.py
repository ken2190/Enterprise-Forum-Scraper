import pandas as pd

target = pd.read_csv('r1.csv', low_memory=False)
source = pd.read_csv('r2.csv' ,low_memory=False)





merged = target.merge(source, how='left', on='email')
merged.to_csv('OUTPUT.csv', index=False)

