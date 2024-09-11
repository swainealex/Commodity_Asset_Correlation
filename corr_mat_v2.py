#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep  8 14:38:05 2024

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

# Brent Crude Oil
# Natural Gas (Henry Hub Spot Price)
# Crude Oil (West Texas Intermediate)

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
plt.show()

# Forward fill NaN values (carry forward the last available price)
df_all_filled = df_all.fillna(method='ffill')

# Check if there are still any NaNs left
# print(df_all_filled.isna().sum())

# Dictionary to store correlation matrices for different time periods
matrices = {
    'Total Correlation': df_all_filled.corr(),
    'Last 5 Days': df_all_filled.tail(5).corr(),
    'Last 30 Days': df_all_filled.tail(30).corr(),
    'Year to Date (YTD)': df_all_filled.tail(365).corr(),
    'Last 5 Years': df_all_filled.tail(1826).corr()
}

# Rolling 30-day correlation (averaged)
rolling_corr = df_all_filled.rolling(window=30).corr().dropna()

# Function to plot a heatmap


def plot_heatmap(corr_matrix, title):
    plt.figure(figsize=(4, 3))
    sns.heatmap(corr_matrix, annot=True, cmap="inferno",
                vmin=-1, vmax=1, fmt=".2f")
    plt.title(title)
    plt.show()


# Loop through the dictionary and plot each correlation matrix
for period, corr_matrix in matrices.items():
    plot_heatmap(corr_matrix, f"Correlation Matrix - {period}")


# List of all commodity columns in the dataframe
commodities = ['Brent Oil Price', 'Natural Gas Price', 'Crude Oil Price']

# Set the window size for rolling correlation
window_size = 120

# Loop through all pairs of commodities
for commodity1, commodity2 in itertools.combinations(commodities, 2):
    # Compute rolling correlation between the two commodities
    rolling_corr = df_all_filled[commodity1].rolling(
        window=window_size).corr(df_all_filled[commodity2])

    # Plot the rolling correlation
    plt.figure(figsize=(10, 6))

    rolling_corr.plot(
        title=f'Rolling {window_size}-Day Correlation between {commodity1} and {commodity2}', color='darkorange')

    plt.ylabel('Correlation')
    plt.xlabel('Date')
    plt.axhline(0, color='black', linestyle='--', linewidth=1)
    plt.grid(True)
    plt.show()
