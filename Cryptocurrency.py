# -*- coding: utf-8 -*-
"""bitcoin_lstm_streamlit_1.py

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1wbXV73UjZP9oPv-jJ7KdwU1ueaKIrFLP
"""
import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt
# from tensorflow.keras.models import Sequential
# from tensorflow.keras.layers import LSTM, Dense
from keras.models import Sequential
from keras.layers import LSTM, Dense

from sklearn.preprocessing import MinMaxScaler
import warnings
import streamlit as st
from PIL import Image

# Ignore warnings
warnings.filterwarnings("ignore")

# Streamlit configuration
st.set_page_config(page_icon="📈", layout="wide", initial_sidebar_state="expanded")
st.markdown("<style>.main {padding-top: 0px;}</style>", unsafe_allow_html=True)

# Add images
st.sidebar.image("Pic1.png", use_container_width=True)
st.image("Pic2.png", use_container_width=True)

# Add main title
st.markdown("<h1 style='text-align: center; margin-top: -20px;'>Cryptocurrency Price Prediction with LSTM</h1>", unsafe_allow_html=True)


# Sidebar inputs
st.sidebar.header("Model Parameters")
crypto_symbol = st.sidebar.text_input("Cryptocurrency Name", "BTC-USD")
prediction_ahead = st.sidebar.number_input("Prediction Days Ahead", min_value=1, max_value=30, value=7, step=1)

if st.sidebar.button("Predict"):
    # Step 1: Pull crypto data for the last 1 year
    btc_data = yf.download(crypto_symbol, period='1y', interval='1d')
    btc_data = btc_data[['Close']].dropna()

    # Prepare data for LSTM
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(btc_data)

    # Correct split for training and testing datasets
    train_size = int(len(scaled_data) * 0.8)
    train_data = scaled_data[:train_size]
    test_data = scaled_data[train_size:]

    def create_dataset(data, time_step=1):
        X, y = [], []
        for i in range(len(data) - time_step):
            X.append(data[i:(i + time_step), 0])
            y.append(data[i + time_step, 0])
        return np.array(X), np.array(y)

    # Use 80% of the total data for training and 20% for testing
    time_step = 60
    X_train, y_train = create_dataset(scaled_data[:train_size], time_step)
    X_test, y_test = create_dataset(scaled_data[train_size - time_step:], time_step)

    # Reshape input to be [samples, time steps, features]
    X_train = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)
    X_test = X_test.reshape(X_test.shape[0], X_test.shape[1], 1)

    # Build LSTM model
    model = Sequential()
    model.add(LSTM(50, return_sequences=True, input_shape=(time_step, 1)))
    model.add(LSTM(50, return_sequences=False))
    model.add(Dense(25))
    model.add(Dense(1))

    model.compile(optimizer='adam', loss='mean_squared_error')
    model.fit(X_train, y_train, batch_size=1, epochs=5, verbose=0)

    # Make predictions
    train_predictions = model.predict(X_train)
    test_predictions = model.predict(X_test)

    # Inverse transform predictions and actual values
    train_predictions = scaler.inverse_transform(train_predictions)
    y_train = scaler.inverse_transform(y_train.reshape(-1, 1))
    test_predictions = scaler.inverse_transform(test_predictions)
    y_test = scaler.inverse_transform(y_test.reshape(-1, 1))

    # Forecast for future days
    last_60_days = scaled_data[-time_step:]
    future_input = last_60_days.reshape(1, time_step, 1)
    future_forecast = []

    for _ in range(prediction_ahead):
        next_pred = model.predict(future_input)[0, 0]
        future_forecast.append(next_pred)
        next_input = np.append(future_input[0, 1:], [[next_pred]], axis=0)
        future_input = next_input.reshape(1, time_step, 1)

    future_forecast = scaler.inverse_transform(np.array(future_forecast).reshape(-1, 1))

    # Latest close price and last predicted price
    latest_close_price = float(btc_data['Close'].iloc[-1])
    last_predicted_price = float(future_forecast[-1])

    # Centered layout for metrics
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
        f"""
        <div style="display: flex; justify-content: space-around;">
            <div style="background-color: #B4B4B8; color: black; padding: 10px; border-radius: 10px; text-align: center;">
                <h3>Latest Close Price</h3>
                <p style="font-size: 20px;">${latest_close_price:.2f}</p>
            </div>
            <div style="background-color: #B4B4B8; color: black; padding: 10px; border-radius: 10px; text-align: center;">
                <h3>Price After {prediction_ahead} Days</h3>
                <p style="font-size: 20px;">${last_predicted_price:.2f}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
        )
    st.markdown("<br>", unsafe_allow_html=True)


    # Plot the results
    plt.figure(figsize=(14, 5))
    plt.plot(btc_data.index, btc_data['Close'], label='Actual', color='blue')
    plt.axvline(x=btc_data.index[train_size], color='gray', linestyle='--', label='Train/Test Split')

    # Train/Test and Predictions
    train_range = btc_data.index[time_step:train_size]
    test_range = btc_data.index[train_size:train_size + len(test_predictions)]
    plt.plot(train_range, train_predictions[:len(train_range)], label='Train Predictions', color='green')
    plt.plot(test_range, test_predictions[:len(test_range)], label='Test Predictions', color='orange')

    # Future Predictions
    future_index = pd.date_range(start=btc_data.index[-1], periods=prediction_ahead + 1, freq='D')[1:]
    plt.plot(future_index, future_forecast, label=f'{prediction_ahead}-Day Forecast', color='red')

    plt.title(f'{crypto_symbol} LSTM Model Predictions')
    plt.xlabel('Date')
    plt.ylabel('Price (USD)')
    plt.legend()
    st.pyplot(plt)

# Footer with enhanced styling
st.markdown("""
    <div style='background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center;'>
        <p style='color: #7F8C8D; font-size: 0.8em;'>Created with ❤️ by Ashish Saha using TensorFlow and Streamlit.</p>
        <p style='color: #7F8C8D; font-size: 0.8em;'>Disclaimer: This is not financial advice. Please do your own research before making any investment decisions.</p>
    </div>
""", unsafe_allow_html=True)
# Streamlit run Cryptocurrency.py
