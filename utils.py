import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import seaborn as sns  # Added for better visualization

from pypfopt import risk_models, expected_returns, EfficientFrontier, plotting

# Fetch historical price data
def fetch_price_data(tickers, period="5y"):
    ohlc = yf.download(tickers, period=period)
    prices = ohlc["Close"].dropna(how="all")
    return prices

# Calculate expected returns and covariance matrix
def calculate_portfolio_metrics(prices):
    mu = expected_returns.capm_return(prices)
    S = risk_models.CovarianceShrinkage(prices).ledoit_wolf()
    return mu, S

import plotly.figure_factory as ff

def plot_covariance_matrix(prices):
    sample_cov = risk_models.sample_cov(prices, frequency=252)
    st.write(sample_cov)
    # fig, ax = plt.subplots(figsize=(10, 6))
    # plotting.plot_covariance(sample_cov, plot_correlation=True, ax=ax)
    # # st.plotly_chart(fig) 
    # plt.close(fig) 
    # return fig
    fig, ax = plt.subplots(figsize=(10, 6))

    # Alternative visualization: Seaborn heatmap
    sns.heatmap(sample_cov, cmap="viridis", annot=False, fmt=".2f", ax=ax)
    ax.set_title("Covariance Matrix Heatmap")

    # Prevent Matplotlib from displaying an empty global figure
    plt.close(fig)

    return fig  

from copy import deepcopy

def optimize_portfolio(mu, S, esg_scores, min_esg_score=0.6):
    """
    Optimizes portfolio weights based on expected returns, covariance, and ESG constraints.

    Args:
        mu (pd.Series): Expected returns.
        S (pd.DataFrame): Covariance matrix.
        esg_scores (np.array): ESG scores of stocks.
        min_esg_score (float): Minimum ESG constraint.

    Returns:
        weights (dict): Optimized portfolio weights.
        performance (tuple): (Expected Return, Volatility, Sharpe Ratio)
    """
    # Step 1: Optimize traditional portfolio (without ESG constraint)
    ef = EfficientFrontier(mu, S)
    ef.max_sharpe()  # Solves the optimization problem
    weights_no_esg = ef.clean_weights()
    perf_no_esg = ef.portfolio_performance()
    st.write("works")


    # Step 2: Optimize ESG-constrained portfolio **with a fresh instance**
    ef_esg = EfficientFrontier(mu, S)  # New instance
    ef_esg.add_constraint(lambda w: esg_scores @ w >= min_esg_score)  # Add constraint
    ef_esg.max_sharpe()  # Solve optimization again
    weights_esg = ef_esg.clean_weights()
    perf_esg = ef_esg.portfolio_performance()
    st.write("works")

    return weights_esg, perf_esg 



import numpy as np
import matplotlib.pyplot as plt
from pypfopt import EfficientFrontier, plotting

import numpy as np
import matplotlib.pyplot as plt
from pypfopt import EfficientFrontier, plotting
import streamlit as st

import plotly.graph_objects as go

def plot_efficient_frontier(mu, S, esg_scores, min_esg_score=0.6):
    ef = EfficientFrontier(mu, S, weight_bounds = (0,1))
    fig, ax = plt.subplots()
    ef_max_sharpe = ef.deepcopy()
    plotting.plot_efficient_frontier(ef, ax=ax, show_assets=True)

    # Find the tangency portfolio
    ef_max_sharpe.max_sharpe()
    ret_tangent, std_tangent, _ = ef_max_sharpe.portfolio_performance()
    ax.scatter(std_tangent, ret_tangent, marker="*", s=100, c="r", label="Max Sharpe")

    ef_esg_aggressive = EfficientFrontier(mu, S)
    portfolio_min_score = 0.8
    ef_esg_aggressive.add_constraint(lambda w: esg_scores @ w >= portfolio_min_score)
    plotting.plot_efficient_frontier(ef_esg_aggressive, ax=ax, show_assets=False)

    ef_esg_mild = EfficientFrontier(mu, S)
    portfolio_min_score = 0.6
    ef_esg_mild.add_constraint(lambda w: esg_scores @ w >= portfolio_min_score)
    plotting.plot_efficient_frontier(ef_esg_mild, ax=ax, show_assets=False)

    plt.close(fig)
    return fig


    
# Compare ESG and non-ESG portfolios
def compare_portfolios(mu, S, esg_scores):
    ef_no_esg = EfficientFrontier(mu, S)
    ef_no_esg.max_sharpe()
    perf_no_esg = ef_no_esg.portfolio_performance(verbose=False)

    ef_esg_mild = EfficientFrontier(mu, S)
    ef_esg_mild.add_constraint(lambda w: esg_scores @ w >= 0.6)
    ef_esg_mild.max_sharpe()
    perf_esg_mild = ef_esg_mild.portfolio_performance(verbose=False)

    ef_esg_agg = EfficientFrontier(mu, S)
    ef_esg_agg.add_constraint(lambda w: esg_scores @ w >= 0.8)
    ef_esg_agg.max_sharpe()
    perf_esg_agg = ef_esg_agg.portfolio_performance(verbose=False)

    df = pd.DataFrame({
        'No ESG Constraints': perf_no_esg,
        'Mild ESG Target (≥ 0.6)': perf_esg_mild,
        'Aggressive ESG Target (≥ 0.8)': perf_esg_agg
    }, index=['Expected Return', 'Annual Volatility', 'Sharpe Ratio'])
    
    return df
