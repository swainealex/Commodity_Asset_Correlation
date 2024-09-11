#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 10 11:52:50 2024

@author: alexswaine
"""

import seaborn as sns
import itertools
import requests
import pandas as pd
import matplotlib.pyplot as plt

# Your API key
api_key = '0Xp45zCtf9hxMyS4jP5HLvJRvgIWLmsWy029sF5V'

# Dictionary of commodity URLs
urls = {
    'Brent Oil': f'https://api.eia.gov/v2/seriesid/PET.RBRTE.D?api_key={api_key}',
    'Natural Gas': f'https://api.eia.gov/v2/seriesid/NG.RNGWHHD.D?api_key={api_key}',
    'Crude Oil': f'https://api.eia.gov/v2/seriesid/PET.RWTC.D?api_key={api_key}'
}

# Create an empty DataFrame to store all the data
df_all = pd.DataFrame()

# Loop through each URL and fetch data
for commodity, url in urls.items():
    response = requests.get(url)
    data = response.json()

    # Check if the response contains the data key
    if 'response' in data and 'data' in data['response']:
        dates = [item['period'] for item in data['response']['data']]
        prices = [item['value'] for item in data['response']['data']]

        # Create a DataFrame for each commodity
        df = pd.DataFrame(list(zip(dates, prices)), columns=[
                          'Date', f'{commodity} Price'])
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)

        # Merge each commodity into the main DataFrame
        if df_all.empty:
            df_all = df
        else:
            df_all = df_all.join(df, how='outer')

# Plot the data
plt.figure(figsize=(10, 6))
for column in df_all.columns:
    plt.plot(df_all.index, df_all[column], label=column)

plt.title('Commodity Prices Over Time')
plt.xlabel('Date')
plt.ylabel('Price, $')
plt.legend()
plt.grid(True)
plt.savefig('commodity_prices_historical.png', dpi=400)
plt.show()

# Forward fill NaN values (carry forward the last available price)
df_all_filled = df_all.fillna(method='ffill')
available_data_length = len(df_all_filled)

# Dictionary to store correlation matrices for different time periods
matrices = {
    'Total Correlation': df_all_filled.corr(),
    'Last 5 Days': df_all_filled.tail(5).corr(),
    'Last 30 Days': df_all_filled.tail(30).corr(),
    'Year to Date (YTD)': df_all_filled.tail(min(365, available_data_length)).corr(),
    'Last 5 Years': df_all_filled.tail(min(1826, available_data_length)).corr()
}

# Function to plot and save a heatmap


def plot_heatmap(corr_matrix, title, filename):
    plt.figure(figsize=(4, 3))
    sns.heatmap(corr_matrix, annot=True, annot_kws={
                "size": 10}, fmt=".2f", cmap="Spectral", vmin=-1, vmax=1)
    plt.title(title)
    plt.savefig(filename, dpi=400)
    plt.show()


# Loop through the dictionary and plot each correlation matrix
for period, corr_matrix in matrices.items():
    plot_heatmap(corr_matrix, f"Correlation Matrix - {period}",
                 f'correlation_matrix_{period.replace(" ", "_").lower()}.png')

# Define different timeframes and their corresponding rolling windows
timeframes = {
    'Last 5 Days': 1,  # Using 1-day rolling window
    'Last 30 Days': 5,  # Using 5-day rolling window
    'Year to Date (YTD)': 30,  # Using 30-day rolling window
    'Last 5 Years': 60  # Using 60-day rolling window
}

# Function to plot and save rolling correlations


def plot_rolling_corr(df, commodities, timeframe, window, filename):
    plt.figure(figsize=(10, 6))
    for commodity1, commodity2 in itertools.combinations(commodities, 2):
        rolling_corr = df[commodity1].rolling(
            window=window).corr(df[commodity2])
        plt.plot(df.index, rolling_corr, label=f'{commodity1} vs {commodity2}')
    plt.title(f'Rolling {window}-Day Correlation - {timeframe}')
    plt.ylabel('Correlation')
    plt.xlabel('Date')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(fontsize=10)
    plt.axhline(0, color='black', linestyle='--', linewidth=1)
    plt.legend()
    plt.grid(True)
    plt.savefig(filename, dpi=400)
    plt.show()


# List of all commodity columns in the dataframe
commodities = ['Brent Oil Price', 'Natural Gas Price', 'Crude Oil Price']

# Loop through each timeframe and plot the corresponding rolling correlations
for timeframe, window in timeframes.items():
    df_timeframe = df_all_filled if timeframe == 'Total Correlation' else df_all_filled.tail({
        'Last 5 Days': 5, 'Last 30 Days': 30, 'Year to Date (YTD)': 365, 'Last 5 Years': 1826}[timeframe])
    plot_rolling_corr(df_timeframe, commodities, timeframe, window,
                      f'rolling_corr_{timeframe.replace(" ", "_").lower()}.png')
