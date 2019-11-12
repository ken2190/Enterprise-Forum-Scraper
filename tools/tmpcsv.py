import json
import pandas as pd

JSON_FILE = 'poshmark.json'
CSV_FILE = 'poshmark.csv'
OUTPUT_FILE = 'remaining.csv'

JSON_FIELD = 'email'
CSV_COL = 'e'

print('1. Reading Emails from JSON')
emails = set()
with open(JSON_FILE, 'r') as jsonfile:
    for single_json in jsonfile:
        json_response = json.loads(single_json)
        if not json_response.get(JSON_FIELD):
            continue
        emails.add(json_response[JSON_FIELD])
print('\tEmail read done\n')
print('2. Reading csv with Pandas')
df = pd.read_csv(CSV_FILE)
print('\tCSV Read done\n')
print('3. Filtering CSV w.r.t email')
final_df = df[~df[CSV_COL].isin(list(emails))]
print('\tFiltering Done\n')
print('4. Saving Filtered CSV')
final_df.to_csv(OUTPUT_FILE, index=False)
print('\tOutput Saved')




