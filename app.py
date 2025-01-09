import time
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf  # Add this import
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

upload = st.sidebar.container()

portfolio = pd.DataFrame()  # Ensure it's always defined

if option == "CSV":
    upload.empty()
    uploaded_file = upload.file_uploader("Upload a CSV", type=["csv"])
    if uploaded_file:
        try:
            portfolio = pd.read_csv(uploaded_file)
            if "Ticker" not in portfolio.columns:
                upload.error("CSV must contain a 'Ticker' column.")
            else:
                upload.success("Portfolio uploaded!")
                with upload.expander("Tickers extracted"):
                    st.dataframe(portfolio, use_container_width=True, hide_index=True)
        except Exception as e:
            upload.error(f"Error reading CSV: {e}")

else:  # Manual Entry
    upload.empty()
    portfolio = pd.DataFrame(columns=["Ticker"])
    portfolio = upload.data_editor(portfolio, use_container_width=True, num_rows="dynamic", key="portfolio_data_editor")
    submit_button = upload.button("Submit")


def get_stock_info(ticker):
    """Fetch detailed stock information."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            'name': info.get('longName', 'N/A'),
            'sector': info.get('sector', 'N/A'),
            'current_price': info.get('currentPrice', 'N/A'),
            'currency': info.get('currency', 'USD'),
            'market_cap': info.get('marketCap', 'N/A'),
        }
    except Exception as e:
        st.warning(f"Could not fetch details for {ticker}: {str(e)}")
        return None

def retry_operation(operation, max_retries=3):
    """Retry an operation with exponential backoff."""
    for i in range(max_retries):
        try:
            return operation()
        except Exception as e:
            if i == max_retries - 1:
                raise e
            st.warning(f"Attempt {i+1} failed, retrying...")
            time.sleep(2 ** i)  # Exponential backoff


if not portfolio.empty and ((option == "CSV") or (option == "Manually" and submit_button)):
    if option == "Manually":
        if portfolio.empty or portfolio['Ticker'].isnull().any():
            upload.error("Please enter valid stock tickers.")
        else:
            upload.success("Portfolio submitted.")
            
    tickers = portfolio['Ticker'].tolist()
    
    # Display detailed stock information
    st.write("### Stock Details")
    stock_details = []
    for ticker in tickers:
        info = get_stock_info(ticker)
        if info:
            stock_details.append({
                'Ticker': ticker,
                'Company Name': info['name'],
                'Current Price': f"{info['current_price']} {info['currency']}",
                'Sector': info['sector'],
                'Market Cap': f"${info['market_cap']:,}" if isinstance(info['market_cap'], (int, float)) else 'N/A'
            })
    
    if stock_details:
        st.dataframe(pd.DataFrame(stock_details), use_container_width=True, hide_index=True)
    
    st.write("### Portfolio Analysis")
    with st.spinner("Fetching stock data..."):
        try:
            prices = retry_operation(lambda: fetch_price_data(tickers))
            if prices is not None and not prices.empty:
                st.write("#### Recent Price History")
                st.write(prices.tail())
                
                # Display historical prices
                st.write("### Historical Prices")
                st.line_chart(prices)
                
                # Portfolio statistics with retry
                try:
                    mu, S = retry_operation(lambda: calculate_portfolio_metrics(prices))
                    if mu is None or S is None:
                        raise ValueError("Portfolio metrics calculation failed")
                except Exception as e:
                    st.error(f"Failed to calculate portfolio metrics: {str(e)}")
                    st.stop()

                # ESG scores (placeholder)
                esg_scores = np.round(np.random.uniform(0.1, 0.9, len(tickers)), 1)
                min_esg_score = st.sidebar.slider("Minimum ESG Score", 0.3, 0.8, 0.6, 0.1)

                # Optimize portfolio with retry
                try:
                    weights, perf = retry_operation(
                        lambda: optimize_portfolio(mu, S, esg_scores, min_esg_score)
                    )
                    
                    st.write("### Portfolio Weights")
                    weights_df = pd.DataFrame(weights, index=[0]).T
                    weights_df.columns = ['Weight']
                    st.bar_chart(weights_df)

                    # Display performance metrics
                    st.write("### Portfolio Performance")
                    metrics_df = pd.DataFrame({
                        'Metric': ['Expected Return', 'Volatility', 'Sharpe Ratio'],
                        'Value': [f"{perf[0]:.2%}", f"{perf[1]:.2%}", f"{perf[2]:.2f}"]
                    })
                    st.table(metrics_df)

                except Exception as e:
                    st.error(f"Portfolio optimization failed: {str(e)}")
                    st.warning("Try adjusting your minimum ESG score or selecting different stocks.")

                # Visualizations with individual error handling
                for visualization in [
                    ("Covariance Matrix", lambda: plot_covariance_matrix(prices)),
                    ("Efficient Frontier", lambda: plot_efficient_frontier(mu, S, esg_scores, min_esg_score)),
                    ("Portfolio Comparison", lambda: compare_portfolios(mu, S, esg_scores))
                ]:
                    st.write(f"### {visualization[0]}")
                    try:
                        result = retry_operation(visualization[1])
                        if visualization[0] == "Portfolio Comparison":
                            st.dataframe(result)
                        elif visualization[0] == "Efficient Frontier":
                            st.pyplot(result, use_container_width=True)
                        else:
                            st.plotly_chart(result, use_container_width=True)
                    except Exception as e:
                        st.error(f"Failed to generate {visualization[0]}: {str(e)}")
                        st.warning("This visualization will be skipped. Please try again with different parameters.")

            else:
                st.error("No price data available for the selected stocks.")
                
        except Exception as e:
            st.error(f"An error occurred while processing your portfolio: {str(e)}")
            st.warning("Please check your input data and try again.")
else:
    st.info("Upload a portfolio to begin.")



