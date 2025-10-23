import pandas as pd

# Load the data
df = pd.read_csv('data/BTC_USDT.csv')

# Rename open_time to Date
df.rename(columns={'open_time': 'Date'}, inplace=True)

# Drop unnecessary columns
cols_to_drop = ['close_time', 'ignore']
df.drop(columns=cols_to_drop, inplace=True)

# Save to new CSV
df.to_csv('data/cleaned.csv', index=False)
print("Preprocessed data saved to cleaned.csv")