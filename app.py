import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt 
from pypfopt import risk_models, plotting, expected_returns, EfficientFrontier
import streamlit as st 

st.markdown("<h1 style='text-align: center;'>Portfolio Analyzer & ESG Score</h1>", unsafe_allow_html=True)

st.sidebar.title("Add your Portfolio")
option = st.sidebar.radio(
    "Choose method", 
    ["CSV", "Manually"],
    captions=[
        "Upload your portfolio as a CSV.",
        "Enter it manually (recommended for smaller portfolios).",
    ]
)

upload = st.sidebar.container()

if option == "CSV":
    # CSV Upload
    uploaded_file = upload.file_uploader("Upload your portfolio as a CSV file", type=["csv"])
    if uploaded_file is not None:
        try:
            # Read the CSV file into a DataFrame
            portfolio = pd.read_csv(uploaded_file)
            # Validate the CSV structure
            required_columns = {"Ticker"}
            missing_columns = required_columns - set(portfolio.columns)
            
            if missing_columns:
                upload.error(f"Missing required columns: {', '.join(missing_columns)}")
            else:
                # Display the uploaded portfolio
                upload.success("Portfolio uploaded successfully!")
                st.dataframe(portfolio)
        except Exception as e:
            upload.error(f"Error reading the CSV file: {e}")
else:
    # Manual Entry
    upload.empty()
    portfolio = pd.DataFrame(columns=["Ticker"])

    portfolio = upload.data_editor(
        portfolio, 
        use_container_width=True,
        column_order=["Ticker"], 
        column_config={
            "Ticker": st.column_config.TextColumn("Stock Ticker"),
        },
        num_rows="dynamic",  # Allow dynamic number of rows
        key="portfolio_data_editor"
    )

    # Add a submit button to trigger the portfolio analysis
    submit_button = upload.button("Submit Portfolio")

    # Validate input when the submit button is pressed
    if submit_button:
        invalid_rows = []

        for idx, row in portfolio.iterrows():
            ticker = row['Ticker']

            # Check if the ticker is empty
            if not ticker.strip():
                invalid_rows.append(f"Row {idx+1}: Ticker is empty. Please enter a valid ticker.")

            # Check if the ticker exists by trying to fetch data using yfinance
            if ticker.strip():
                try:
                    stock_data = yf.Ticker(ticker).history(period="1d")
                    if stock_data.empty:
                        invalid_rows.append(f"Row {idx+1}: No data found for ticker '{ticker}'. Please enter a valid ticker.")
                except Exception as e:
                    invalid_rows.append(f"Row {idx+1}: Error fetching data for ticker '{ticker}': {e}")

        # Display error messages if any validation fails
        if invalid_rows:
            for error in invalid_rows:
                upload.error(error)
        else:
            upload.success("Portfolio is valid! Ready for analysis.")
