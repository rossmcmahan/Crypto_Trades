import csv
import pandas as pd
from datetime import datetime as dt
import os
from send_email import send_email_notifications

filename = "trades_made/trades_made.csv"
manipulated_file = 'trades_made/trades_made_' + dt.now().strftime("%Y%m%d") + '.csv'

raw_df = pd.read_csv(filename)
os.remove(filename)
clean_df = pd.DataFrame(columns = ['Ticker',
					'Bought_DateTime',
					'Bought_Quantity',
					'Bought_Price',
					'Sold_DateTime',
					'Sold_Quantity',
					'Sold_Price',
					'Time_Held',
					'Delta_Quantity',
					'Delta_Price',
					'%Change'])

mask = raw_df['Action'] == raw_df['Action'].shift()
raw_df = raw_df[~mask].reset_index(drop = True)
raw_df = raw_df.drop(raw_df.columns[0], axis = 1)

for idx in range(1, len(raw_df) + 1):
	if raw_df.loc[idx-1, 'Action'] == 'BUY':
		clean_df.loc[idx, 'Ticker'] = raw_df.loc[idx-1, 'Ticker']
		clean_df.loc[idx, 'Bought_DateTime'] = raw_df.loc[idx-1, 'DateTime']
		clean_df.loc[idx, 'Bought_Quantity'] = raw_df.loc[idx-1, 'Quantity']
		clean_df.loc[idx, 'Bought_Price'] = raw_df.loc[idx-1, 'Price']

	elif raw_df.loc[idx-1, 'Action'] == 'SELL':
		clean_df.loc[idx-1, 'Sold_DateTime'] = raw_df.loc[idx-1, 'DateTime']
		clean_df.loc[idx-1, 'Sold_Quantity'] = raw_df.loc[idx-1, 'Quantity']
		clean_df.loc[idx-1, 'Sold_Price'] = raw_df.loc[idx-1, 'Price']

clean_df = clean_df.reset_index(drop = True)

for idx in range(1, len(clean_df) + 1):
	clean_df.loc[idx-1, 'Time_Held'] = pd.to_datetime(clean_df.loc[idx-1, 'Sold_DateTime']) - pd.to_datetime(clean_df.loc[idx - 1, 'Bought_DateTime'])
	clean_df.loc[idx-1, 'Delta_Quantity'] = clean_df.loc[idx-1, 'Bought_Quantity'] - clean_df.loc[idx-1, 'Sold_Quantity']
	clean_df.loc[idx-1, 'Delta_Price'] = clean_df.loc[idx-1, 'Sold_Price'] - clean_df.loc[idx-1, 'Bought_Price']
	clean_df.loc[idx-1, '%Change'] = clean_df.loc[idx-1, 'Delta_Price'] / clean_df.loc[idx-1, 'Bought_Price']

	if idx == 1:
		clean_df.loc[idx-1, 'Position'] = 500 * ( 1 + clean_df.loc[idx-1, '%Change'])
	else:
		clean_df.loc[idx-1, 'Position'] = clean_df.loc[idx-2, 'Position'] * (1 + clean_df.loc[idx-1, '%Change'])

clean_df.to_csv(manipulated_file)
send_email_notifications(manipulated_file)
