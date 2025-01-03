import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt 
from pypfopt import risk_models, plotting, expected_returns, EfficientFrontier



def fetch_data(tickers):
    ohlc = yf.download(tickers, period="5y")
    # ohlc.tail()
    prices = ohlc["Close"].dropna(how="all")
    # prices.tail() 
    return prices

def 