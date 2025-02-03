import config
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import time
import robin_stocks.robinhood as r
import os
from datetime import datetime
from send_email import send_email_notifications

# Login to Robinhood
username = os.getenv(config.USERNAME)
password = os.getenv(config.PASSWORD)
r.login(username, password, store_session=True)

# Function to fetch historical data
def get_historical_data(symbol = "BTC", interval = "5minute", span = "day"):
	try:

		historical_data = r.crypto.get_crypto_historicals(symbol, interval = interval, span = span)

		if not historical_data or len(historical_data) == 0:
			print(f"Failed to retrieve historical data for { symbol }.")
			return pd.DataFrame()

		# Convert data to a DataFrame
		df = pd.DataFrame(historical_data)
		df['time'] = pd.to_datetime(df['begins_at'])
		df['close'] = df['close_price'].astype(float)
		df.set_index('time', inplace = True)

		df = df[['close']]
		return df

	except Exception as e:
		print(f"Error while fetching historical data: {e}")
		return pd.DataFrame()

# Function to fetch the latest real-time price
def get_current_price(symbol="BTC", currency= "USD"):
	price = r.get_crypto_quote(symbol)

	if price['ask_price']:
		return float(price['ask_price'])
	else:
		print("Failed to fetch current price")
		return None

# Bollinger Bands Calculations
def calculate_bollinger_bands(data, window = 20, num_std_dev = 2):
	data['MA20'] = data['close'].rolling(window=window).mean()
	data['STD'] = data['close'].rolling(window=window).std()
	data['Upper'] = data['MA20'] + (data['STD'] * num_std_dev)
	data['Lower'] = data['MA20'] - (data['STD'] * num_std_dev)

	return data

# Trading Logic
def execute_trades(current_price, data, cash_percent = 0.01):
	# Fetch Robinhood account info
	account_info = r.profiles.load_account_profile()
	buying_power = float(account_info["buying_power"])
	trades_df = pd.DataFrame(columns = ['DateTime', 'Ticker', 'Action', 'Amount', 'Price'])

	# Check if the current price is below the lower Bollinger Band (Buy Signal)
	if (
		current_price < data['Lower'].iloc[-1]
		and not os.path.isfile("trades_made/trades_made.csv")
	) or (
		current_price < data['Lower'].iloc[-1]
		and pd.read_csv("trades_made/trades_made.csv")['Action'].iloc[-1] != "BUY"
	):
		trade = "BUY"
		buy_amount = buying_power * cash_percent # Buy 1% of cash
		crypto_quantity = buy_amount / current_price
		r.orders.order_buy_crypto_by_price("BTC", round(buy_amount, 8))
		positions = r.crypto.get_crypto_positions()
		if positions:
			for position in positions:
				if position["currency"]["code"] == "BTC":
					quantity = float(position["quantity"])
					r.orders.order_sell_stop_loss("BTC", quantity, (current_price*.9995))

		next_row = [[datetime.now(), "BTC", trade, crypto_quantity, current_price]]
		next_row_df = pd.DataFrame(next_row, columns = ["DateTime", "Ticker", "Action", "Quantity", "Price"])

		if not os.path.isfile("trades_made/trades_made.csv"):
			next_row_df.to_csv("trades_made/trades_made.csv", mode = "w", header = True, index = True)
		else:
			next_row_df.to_csv("trades_made/trades_made.csv", mode = "a", header = False, index = True)

	# Check if the current price is above the upper Bollinger Band (Sell Signal)
	if (
		current_price > data['Upper'].iloc[-1]
		and not os.path.isfile("trades_made/trades_made.csv")
	) or (
		current_price > data['Upper'].iloc[-1]
		and pd.read_csv("trades_made/trades_made.csv")['Action'].iloc[-1] != "SELL"
	):
		trade = "SELL"
		positions = r.crypto.get_crypto_positions()
		if positions:
			for position in positions:
				if position["currency"]["code"] == "BTC":
					quantity = float(position["quantity"])
					r.orders.order_sell_crypto_by_quantity("BTC", quantity)

					next_row = [[datetime.now(), "BTC", trade, 90, current_price]]
					next_row_df = pd.DataFrame(next_row, columns = ["DateTime", "Ticker", "Action", "Quantity", "Price"])

					if not os.path.isfile("trades_made/trades_made.csv"):
						next_row_df.to_csv("trades_made/trades_made.csv", mode = "w", header = True, index = True)
					else:
						next_row_df.to_csv("trades_made/trades_made.csv", mode = "a", header = False, index = True)

def plot_bollinger_bands(data, current_price=None):
	"""
	Plots Bollinger Bands and the current price.

	Args:
		data (pd.DataFrame): DataFrame containing close price, MA20, Upper, and Lower Bands.
		current_price (float): Latest BTC Price (Optional, for plotting the most recent price.
	"""

	# Plotting
	plt.figure(figsize=(12, 6))

	#Plot close prices
	plt.plot(data.index, data['close'], label='Close Price', color='blue', linewidth=1.5)

	# Plot Bollinger Bands
	plt.plot(data.index, data['MA20'], label='20-Day MA', color='orange', linestyle='--')
	plt.plot(data.index, data['Upper'], label='Upper Band', color='green', linestyle='--')
	plt.plot(data.index, data['Lower'], label='Lower Band', color='red', linestyle='--')

	# Highlight the Current Price
	if current_price:
		plt.axhline(y=current_price, color='purple', linestyle='-', linewidth=1, label=f'Current Price: { current_price }')

	# add titles and labels
	plt.title("Bitcoin Bollinger Bands Strategy", fontsize=16)
	plt.xlabel("Time", fontsize=12)
	plt.ylabel("Price (USD)", fontsize=12)
	plt.legend(loc="upper left")
	plt.grid(alpha=0.5)
	plt.tight_layout()

	# Save the plot
	plt.savefig("BTC_Bolly_Bands.png")
	plt.close()

	plt.pause(0.1) #pause for dynamic updates
	plt.clf() #Clear the plot for the next update

# Continuous Loop
def run_strategy():
	# Initialize historical data
	historical_data = get_historical_data(symbol="BTC", interval = "5minute", span = "day")

	if historical_data.empty:
		print("Unable to start strategy due to missing historical data.")
		return

	# Calculate initial Bollinger Bands
	historical_data = calculate_bollinger_bands(historical_data)

	while True:
		# Step 1: Fetch the latest real-time price
		current_price = get_current_price(symbol="BTC", currency="USD")
		if current_price is None:
			print("No current price available. Retrying...")
			time.sleep(1)
			continue

		# Step 2: Update historical data with the latest price
		new_row = {
			"close": current_price,
			"high": current_price,
			"low": current_price,
			"open": current_price,
			"volumeto": 0	# Volume is optional and not used in this strategy
			}
		new_data = pd.DataFrame([new_row], index = [datetime.now()])
		new_data.index = new_data.index.tz_localize('UTC')
		historical_data = pd.concat([historical_data, new_data]).tail(200)	# Keep the last 200 rows

		# Step 3: Recalculate Bollinger Bands
		historical_data = calculate_bollinger_bands(historical_data)

		# Step 4: Execute trading strategy
		execute_trades(current_price, historical_data, )

		# Wait before checking again
		time.sleep(1)

# Run the strategy
if __name__ == "__main__":
	trade = None
	try:
		run_strategy()
	except KeyboardInterrupt:
		print("Strategy stopped by user.")
	except Exception as e:
		print(f"Error encountered: {e}")
