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

# Function to calculate total balance and real profit
def calculate_balance(transactions, current_btc_price):
    total_btc_held = 0  # Total BTC still held
    total_invested = 0  # Total USD spent on remaining Bitcoin
    realized_profit = 0  # Profit from sold Bitcoin

    for transaction in transactions:
        usd_value = transaction['value_in_usd']
        btc_quantity = transaction['quantity_in_btc']
        btc_price_at_transaction = transaction['btc_price_at_transaction']

        if transaction['type'] == "buy":
            # Add to total BTC held and total invested
            total_btc_held += btc_quantity
            total_invested += usd_value
        elif transaction['type'] == "sell":
            # Calculate the average cost per BTC held (cost basis)
            cost_basis_per_btc = total_invested / total_btc_held

            # Calculate the cost of the BTC being sold
            cost_basis_of_sold_btc = cost_basis_per_btc * btc_quantity
            
            # Calculate the realized profit: (Sell price - Cost basis) * quantity sold
            realized_profit += (btc_price_at_transaction * btc_quantity) - cost_basis_of_sold_btc
            
            # Adjust total BTC held and total invested after selling
            total_btc_held -= btc_quantity
            total_invested -= cost_basis_of_sold_btc  # Subtract the cost of the sold BTC

    # Value of Bitcoin still held at the current price
    current_value_of_btc_held = total_btc_held * current_btc_price

    # Real profit is the sum of realized profit and the unrealized profit from BTC still held
    unrealized_profit = current_value_of_btc_held - total_invested
    real_profit = realized_profit + unrealized_profit

    return total_btc_held, total_invested, real_profit

# Function to calculate percentage change
def calculate_percentage_change(current_value, previous_value):
    if previous_value == 0:
        return 0
    percentage_change = ((current_value - previous_value) / previous_value) * 100
    return percentage_change

# Function to format values with proper sign placement
def format_currency(value):
    if value >= 0:
        return f"${value:.2f}"
    else:
        return f"-${abs(value):.2f}"

# Function to display data in a formatted table
def display_data(current_usd_value, total_btc_held, real_profit, total_invested, last_update_diff, hour_diff, last_update_percentage, hour_percentage):
    # Clear the terminal before displaying new updates
    os.system('cls' if os.name == 'nt' else 'clear')

    table = Table(title="My Wallet (Bitcoin)")

    # Standard columns
    table.add_column("Description", justify="left", style="cyan", no_wrap=True)
    table.add_column("Value", justify="right", style="magenta")
    table.add_column("Percentage", justify="right", style="green")

    # Add price and balance data
    table.add_row("Current BTC Price (USD)", format_currency(current_usd_value), "")
    table.add_row("Total BTC Held", f"{total_btc_held:.8f}", "")
    table.add_row("Total Balance (USD)", format_currency(current_usd_value * total_btc_held), "")

    # Display the difference from the last update and from the last hour
    table.add_row("", "", "")

    # Color for last update percentage
    last_update_color = "green" if last_update_percentage >= 0 else "red"
    last_update_sign = "+" if last_update_percentage >= 0 else "-"
    table.add_row("[bold cyan]Last Update Difference (USD)[/bold cyan]", f"[bold yellow]{format_currency(last_update_diff)}[/bold yellow]", f"[bold {last_update_color}]{last_update_sign}{abs(last_update_percentage):.2f}%[/bold {last_update_color}]")

    # Color for last hour percentage
    hour_color = "green" if hour_percentage >= 0 else "red"
    hour_sign = "+" if hour_percentage >= 0 else "-"
    table.add_row("[bold cyan]Last Hour Difference (USD)[/bold cyan]", f"[bold yellow]{format_currency(hour_diff)}[/bold yellow]", f"[bold {hour_color}]{hour_sign}{abs(hour_percentage):.2f}%[/bold {hour_color}]")

    # Separate sections
    table.add_row("", "", "")

    # Apply green for positive values and red for negative values
    real_profit_color = "green" if real_profit >= 0 else "red"
    real_profit_sign = "+" if real_profit >= 0 else "-"

    # Calculate the percentage profit or loss
    percentage_profit = (real_profit / total_invested) * 100 if total_invested > 0 else 0
    percentage_profit_sign = "+" if percentage_profit >= 0 else "-"

    # Columns highlighting real profit, total invested, and percentage
    table.add_row(f"[bold {real_profit_color}]Real Profit (USD)[/bold {real_profit_color}]", f"[bold {real_profit_color}]{real_profit_sign}{format_currency(abs(real_profit))}[/bold {real_profit_color}]", f"[bold {real_profit_color}]{percentage_profit_sign}{abs(percentage_profit):.2f}%[/bold {real_profit_color}]")
    table.add_row(f"[bold cyan]Total Invested (USD)[/bold cyan]", f"[bold cyan]{format_currency(total_invested)}[/bold cyan]", "")

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
            last_update_percentage = 0
        else:
            last_update_diff = current_usd_value - last_update_value
            last_update_percentage = calculate_percentage_change(current_usd_value, last_update_value)

        last_update_value = current_usd_value

        # Calculate the difference from the last hour (60 updates, assuming ~30 seconds per update)
        if len(usd_price_history) >= 60:
            one_hour_ago_value = usd_price_history[-60]
        else:
            one_hour_ago_value = usd_price_history[0]  # Use the initial value if there haven't been 60 updates yet

        hour_diff = current_usd_value - one_hour_ago_value
        hour_percentage = calculate_percentage_change(current_usd_value, one_hour_ago_value)

        total_btc_held, total_invested, real_profit = calculate_balance(transactions, current_usd_value)

        # Display the data with the differences
        display_data(current_usd_value, total_btc_held, real_profit, total_invested, last_update_diff, hour_diff, last_update_percentage, hour_percentage)

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

# Start monitoring with an interval of 60 seconds
monitor_bitcoin_binance(transactions, interval=60)
