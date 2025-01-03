import streamlit as st
import pandas as pd
import numpy as np
from utils import (
    fetch_price_data,
    calculate_portfolio_metrics,
    optimize_portfolio,
    plot_covariance_matrix,
    plot_efficient_frontier,
    compare_portfolios,
)

st.markdown("<h1 style='text-align: center;'>Portfolio Optimizer & ESG Score</h1>", unsafe_allow_html=True)

st.sidebar.title("Add Your Portfolio")
option = st.sidebar.radio(
    "Choose method", ["CSV", "Manually"],
    captions=["Upload your portfolio as a CSV.", "Enter it manually."]
)

portfolio = pd.DataFrame()  # Ensure it's always defined

if option == "CSV":
    uploaded_file = st.sidebar.file_uploader("Upload a CSV", type=["csv"])
    if uploaded_file:
        try:
            portfolio = pd.read_csv(uploaded_file)
            if "Ticker" not in portfolio.columns:
                st.error("CSV must contain a 'Ticker' column.")
            else:
                st.success("Portfolio uploaded!")
                st.dataframe(portfolio)
        except Exception as e:
            st.error(f"Error reading CSV: {e}")

else:  # Manual Entry
    portfolio = pd.DataFrame(columns=["Ticker"])
    portfolio = st.data_editor(portfolio, use_container_width=True, num_rows="dynamic", key="portfolio_data_editor")
    if st.sidebar.button("Submit"):
        if portfolio.empty or portfolio['Ticker'].isnull().any():
            st.error("Please enter valid stock tickers.")
        else:
            st.success("Portfolio submitted.")

if not portfolio.empty:
    tickers = portfolio['Ticker'].tolist()
    st.write(tickers)
    
    st.write("### Portfolio Analysis")
    with st.spinner("Fetching stock data..."):
        try:
            prices = fetch_price_data(tickers)
            st.write(prices.tail())

            # Display historical prices
            st.write("### Historical Prices")
            st.line_chart(prices)

            # Portfolio statistics
            mu, S = calculate_portfolio_metrics(prices)

            # ESG scores (placeholder)
            esg_scores = np.round(np.random.uniform(0.1, 0.9, len(tickers)), 1)
            min_esg_score = st.sidebar.slider("Minimum ESG Score", 0.3, 0.8, 0.6, 0.1)

            # Optimize and display portfolio weights
            weights, perf = optimize_portfolio(mu, S, esg_scores, min_esg_score)
            st.write("### Portfolio Weights")
            st.bar_chart(pd.DataFrame(weights, index=[0]).T)

            # Display performance
            st.write("### Portfolio Performance")
            st.write(f"Expected Return: {perf[0]:.2%}")
            st.write(f"Volatility: {perf[1]:.2%}")
            st.write(f"Sharpe Ratio: {perf[2]:.2f}")

            # Covariance matrix visualization
            st.write("### Covariance Matrix")
            fig = plot_covariance_matrix(prices)
            st.pyplot(fig, use_container_width = True) 
            # Efficient frontier visualization
            st.write("### Efficient Frontier")
            # st.write("works")

            fig = plot_efficient_frontier(mu, S, esg_scores, min_esg_score=0.6)
            # st.write("works")

            st.pyplot(fig, use_container_width = True)
            # Compare portfolios
            st.write("### Portfolio Comparison")
            comparison_df = compare_portfolios(mu, S, esg_scores)
            st.dataframe(comparison_df)

        except Exception as e:
            st.error(f"Error during analysis: {e}")
else:
    st.info("Upload a portfolio to begin.")
