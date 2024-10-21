import requests
import time
import os
import json
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, BarColumn, TimeRemainingColumn

console = Console()

# Function to get the Bitcoin price in USD using the Binance API
def get_bitcoin_price_binance():
    url = 'https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT'
    response = requests.get(url)
    data = response.json()
    bitcoin_price_usd = float(data['price'])
    return bitcoin_price_usd

# Function to load transactions from a JSON file
def load_transactions_from_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data['transactions']

# Function to calculate total balance and profit
def calculate_balance(transactions):
    total_invested = 0
    total_btc = 0
    profit = 0

    for transaction in transactions:
        type_ = transaction['type']
        usd_value = transaction['value_in_usd']
        btc_quantity = transaction['quantity_in_btc']
        if type_ == "buy":
            total_invested += usd_value * btc_quantity
            total_btc += btc_quantity
        elif type_ == "sell":
            total_invested -= usd_value * btc_quantity
            profit += usd_value * btc_quantity

    return total_btc, total_invested, profit

# Function to calculate gain/loss percentage
def calculate_gain_percentage(current_value, total_invested, total_btc):
    total_current_value = current_value * total_btc
    gain = total_current_value - total_invested
    gain_percentage = (gain / total_invested) * 100 if total_invested > 0 else 0
    return gain_percentage, gain

# Function to display data in a formatted table
def display_data(current_usd_value, total_btc, gain_percentage, profit_usd, last_update_diff, hour_diff):
    # Clear the terminal before displaying new updates
    os.system('cls' if os.name == 'nt' else 'clear')

    table = Table(title="My Wallet (Bitcoin)")

    # Standard columns
    table.add_column("Description", justify="left", style="cyan", no_wrap=True)
    table.add_column("Value", justify="right", style="magenta")

    # Add price and balance data
    table.add_row("Current BTC Price (USD)", f"${current_usd_value:.2f}")
    table.add_row("Total BTC", f"{total_btc:.4f}")
    table.add_row("Total Balance (USD)", f"${current_usd_value * total_btc:.2f}")

    # Display the difference from the last update and from the last hour
    table.add_row("", "")
    table.add_row("[bold cyan]Last Update Difference (USD)[/bold cyan]", f"[bold yellow]${last_update_diff:.2f}[/bold yellow]")
    table.add_row("[bold cyan]Last Hour Difference (USD)[/bold cyan]", f"[bold yellow]${hour_diff:.2f}[/bold yellow]")

    # Separate sections
    table.add_row("", "")

    # Apply green for positive values and red for negative values
    color = "green" if gain_percentage >= 0 else "red"

    # Columns highlighting profit
    table.add_row(f"[bold {color}]Gain/Loss Percentage[/bold {color}]", f"[bold {color}]{gain_percentage:.2f}%[/bold {color}]")
    table.add_row(f"[bold {color}]Profit (USD)[/bold {color}]", f"[bold {color}]${profit_usd:.2f}[/bold {color}]")

    console.print(table)

# Monitoring loop
def monitor_bitcoin_binance(transactions, interval=30):
    last_update_value = None
    one_hour_ago_value = None  # Value for comparing the price 1 hour ago (60 updates)

    usd_price_history = []  # Keep the history of prices

    while True:
        current_usd_value = get_bitcoin_price_binance()
        usd_price_history.append(current_usd_value)

        # Calculate the difference from the last update
        if last_update_value is None:
            last_update_diff = 0
        else:
            last_update_diff = current_usd_value - last_update_value

        last_update_value = current_usd_value

        # Calculate the difference from the last hour (60 updates)
        if len(usd_price_history) >= 60:
            one_hour_ago_value = usd_price_history[-60]
        else:
            one_hour_ago_value = usd_price_history[0]  # Use the initial value if there haven't been 60 updates yet

        hour_diff = current_usd_value - one_hour_ago_value

        total_btc, total_invested, profit = calculate_balance(transactions)
        gain_percentage, profit_usd = calculate_gain_percentage(current_usd_value, total_invested, total_btc)

        # Display the data with the differences
        display_data(current_usd_value, total_btc, gain_percentage, profit_usd, last_update_diff, hour_diff)

        # Countdown to the next update using `rich` Progress
        with Progress(
            "[progress.description]{task.description}",
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeRemainingColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Next update in", total=interval)
            while not progress.finished:
                time.sleep(1)
                progress.update(task, advance=1)

# Load transactions from the JSON file
transactions = load_transactions_from_file('transactions.json')

# Start monitoring with an interval of 30 seconds
monitor_bitcoin_binance(transactions, interval=30)
