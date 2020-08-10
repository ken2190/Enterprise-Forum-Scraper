import pandas as pd

target = pd.read_csv('part1.csv', low_memory=False)
source = pd.read_csv('part2.csv' ,low_memory=False)
merged = target.merge(source, how='left', on='u')
merged.to_csv('OUTPUT.csv', index=False)

