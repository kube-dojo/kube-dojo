---
title: "XGBoost & Gradient Boosting"
slug: ai-ml-engineering/classical-ml/module-8.2-xgboost-gradient-boosting
sidebar:
  order: 903
---
> **AI/ML Engineering Track** | Complexity: `[COMPLEX]` | Time: 5-6
> **Migrated from neural-dojo** — pending pipeline polish

## What You'll Be Able to Do

By the end of this module, you will:
- Understand time series fundamentals (stationarity, seasonality, trends)
- Master classical forecasting methods (ARIMA, Prophet)
- Build deep learning time series models (LSTM, Transformers)
- Implement temporal feature engineering
- Build anomaly detection systems for time series data

---

## Why Time Series Matters

Imagine you're a weather forecaster in ancient Egypt, watching the Nile's water levels. Each year, the river floods, bringing life-giving water to crops. But when will it flood? How high will it rise? Your entire civilization depends on predicting a pattern that repeats over time.

This is time series analysis - finding patterns in sequential data to predict the future. And it's everywhere:

```
Where Time Series Lives:
├── Finance
│   ├── Stock prices (hourly, daily)
│   ├── Trading volumes
│   └── Economic indicators
├── Operations
│   ├── Server load prediction
│   ├── Inventory forecasting
│   └── Energy demand
├── IoT & Sensors
│   ├── Temperature monitoring
│   ├── Equipment vibration
│   └── Network traffic
└── Business
    ├── Sales forecasting
    ├── Customer demand
    └── Resource planning
```

**Did You Know?** Amazon's demand forecasting system processes over 300 million time series daily. Each product in each warehouse is a separate time series. Getting forecasts right by just 1% accuracy improvement saved them over $100 million annually in inventory costs!

---

## The Anatomy of Time Series

### What Makes Time Series Special?

Unlike regular tabular data where rows are independent, time series has a crucial property: **temporal dependency**. Today's value depends on yesterday's value, which depends on the day before, and so on.

```
Regular Data vs Time Series:

REGULAR TABULAR DATA:
┌─────────────────────────────────────┐
│  Row 1: [features] → [label]        │  Each row is independent
│  Row 2: [features] → [label]        │  Order doesn't matter
│  Row 3: [features] → [label]        │  Shuffle = same model
└─────────────────────────────────────┘

TIME SERIES DATA:
┌─────────────────────────────────────┐
│  t=1: value₁ ────────────┐          │
│  t=2: value₂ ←───────────┤          │  Each depends on past
│  t=3: value₃ ←───────────┤          │  Order is EVERYTHING
│  t=4: value₄ ←───────────┘          │  Shuffle = destroy data
└─────────────────────────────────────┘
```

### The Three Components of Time Series

Every time series can be decomposed into three fundamental components:

```
TIME SERIES = TREND + SEASONALITY + RESIDUAL

               Original Signal
                    │
    ┌───────────────┼───────────────┐
    │               │               │
    ▼               ▼               ▼
  TREND        SEASONALITY      RESIDUAL
(long-term)   (repeating)     (random noise)
    │               │               │
    │               │               │
    ▼               ▼               ▼
  ╱              ╱╲╱╲            ∼∼∼∼
 ╱              ╱  ╲ ╱          ∼  ∼
╱              ╱    ╲          ∼    ∼


Example: Retail Sales
─────────────────────
TREND: Sales growing 5% per year (business expansion)
SEASONALITY: Spikes every December (holiday shopping)
RESIDUAL: Random day-to-day variation
```

**The Grocery Store Analogy**: Imagine tracking daily milk sales:
- **Trend**: Sales slowly increasing as neighborhood population grows
- **Seasonality**: Higher on weekends (families cook more), lower mid-week
- **Weekly pattern**: People buy on payday (biweekly)
- **Residual**: Random - maybe a recipe went viral on TikTok today

---

## Stationarity: The Foundation of Forecasting

### What is Stationarity?

A time series is **stationary** if its statistical properties don't change over time. Think of it like a calm lake versus a river flowing to the ocean.

```
STATIONARY (Like a Calm Lake):
─────────────────────────────
Statistical properties stay constant over time.
Mean: μ ≈ constant
Variance: σ² ≈ constant
Autocorrelation: same pattern

       ──────────────────────────
      ╱╲  ╱╲  ╱╲  ╱╲  ╱╲  ╱╲  ╱╲
     ╱  ╲╱  ╲╱  ╲╱  ╲╱  ╲╱  ╲╱  ╲
    ──────────────────────────────


NON-STATIONARY (Like a River to Ocean):
───────────────────────────────────────
Properties change over time.
Mean: drifting up or down
Variance: expanding or contracting

                            ╱╲
                          ╱╲╱ ╲
                      ╱╲╱╲╱    ╲╱╲
                 ╱╲╱╲╱              ╲
         ╱╲╱╲╱╲╱                     ╲
    ╱╲╱╲╱
   ╱
```

### Why Stationarity Matters

Most classical forecasting methods **require** stationarity. Here's why:

```python
# Non-stationary: Yesterday's patterns don't apply to tomorrow
# Because the underlying process is changing!

# Example: Stock price in 2020 vs 2024
# - Different economic conditions
# - Different company size
# - Different market sentiment
# Can't just extrapolate!

# Solution: Make it stationary through DIFFERENCING
# Instead of predicting price, predict CHANGE in price
#
# price_t → change_t = price_t - price_{t-1}
```

### Testing for Stationarity: The ADF Test

The Augmented Dickey-Fuller (ADF) test tells us if a series is stationary:

```
ADF TEST INTERPRETATION:
────────────────────────

H₀ (Null): Series has a unit root (NON-stationary)
H₁ (Alt): Series is stationary

p-value < 0.05 → Reject H₀ → Series IS stationary
p-value ≥ 0.05 → Fail to reject → Series is NOT stationary

Example Results:
────────────────
Raw stock prices:     p = 0.87  → Non-stationary (expected!)
First difference:     p = 0.001 → Stationary (good for ARIMA)
Log returns:          p = 0.001 → Stationary (finance standard)
```

**Did You Know?** The unit root concept comes from the characteristic equation of an AR process. If the root equals 1 (a "unit root"), shocks to the system persist forever rather than dying out. This is why stock prices are non-stationary - a $10 increase today doesn't mean it'll drop $10 tomorrow. The change is permanent!

---

## Classical Methods: ARIMA

### The ARIMA Family

ARIMA stands for **A**uto**R**egressive **I**ntegrated **M**oving **A**verage. It's the Swiss Army knife of time series forecasting.

```
ARIMA COMPONENTS:
─────────────────

AR (AutoRegressive) - p:
  "Today depends on recent past values"
  y_t = c + φ₁·y_{t-1} + φ₂·y_{t-2} + ... + ε_t

  Like: "Temperature today ≈ 0.9 × temperature yesterday"


I (Integrated) - d:
  "How many times we difference to make stationary"
  d=0: Already stationary
  d=1: First difference (y_t - y_{t-1})
  d=2: Second difference (rarely needed)

  Like: "Don't predict price, predict price CHANGE"


MA (Moving Average) - q:
  "Today depends on recent forecast errors"
  y_t = c + ε_t + θ₁·ε_{t-1} + θ₂·ε_{t-2} + ...

  Like: "I was wrong by X yesterday, adjust for that"


ARIMA(p, d, q) notation:
────────────────────────
ARIMA(1, 0, 0) = AR(1) - Simple autoregressive
ARIMA(0, 1, 1) = IMA(1,1) - Random walk with MA
ARIMA(1, 1, 1) = Common balanced model
ARIMA(5, 1, 0) = AR with 5 lags, differenced once
```

### Seasonal ARIMA: SARIMA

For data with seasonality (most real data!), we use SARIMA:

```
SARIMA(p, d, q)(P, D, Q, s)
           │         │
           │         └── Seasonal components
           └── Non-seasonal components

s = seasonal period (12 for monthly, 7 for daily with weekly pattern)

Example: Monthly sales with yearly seasonality
SARIMA(1, 1, 1)(1, 1, 1, 12)
  │  │  │  │  │  │  │
  │  │  │  │  │  │  └── 12-month seasonal period
  │  │  │  │  │  └── Seasonal MA(1)
  │  │  │  │  └── Seasonal difference (year-over-year)
  │  │  │  └── Seasonal AR(1)
  │  │  └── Non-seasonal MA(1)
  │  └── Non-seasonal difference
  └── Non-seasonal AR(1)
```

### How to Choose ARIMA Parameters

The traditional approach uses ACF and PACF plots:

```
ACF (Autocorrelation Function):
───────────────────────────────
Correlation between y_t and y_{t-k} for all lags k

Interpretation:
- Slow decay → Non-stationary (need differencing)
- Cuts off after lag q → MA(q) model
- Decays exponentially → AR model

PACF (Partial Autocorrelation Function):
────────────────────────────────────────
Correlation between y_t and y_{t-k} AFTER removing
effect of intermediate lags

Interpretation:
- Cuts off after lag p → AR(p) model
- Decays exponentially → MA model


CHOOSING p AND q:
─────────────────
┌─────────────┬──────────────┬──────────────┐
│   Pattern   │     ACF      │    PACF      │
├─────────────┼──────────────┼──────────────┤
│   AR(p)     │ Exponential  │ Cuts off     │
│             │ decay        │ after lag p  │
├─────────────┼──────────────┼──────────────┤
│   MA(q)     │ Cuts off     │ Exponential  │
│             │ after lag q  │ decay        │
├─────────────┼──────────────┼──────────────┤
│  ARMA(p,q)  │ Exponential  │ Exponential  │
│             │ decay        │ decay        │
└─────────────┴──────────────┴──────────────┘
```

**Did You Know?** Box and Jenkins developed the ARIMA methodology in 1970, and it remained the gold standard for forecasting for over 40 years. Their book "Time Series Analysis: Forecasting and Control" has been cited over 60,000 times. George Box famously said, "All models are wrong, but some are useful."

---

## Facebook Prophet: Democratizing Forecasting

### Why Prophet Changed Everything

In 2017, Facebook released Prophet, making forecasting accessible to analysts without deep statistical expertise:

```
TRADITIONAL ARIMA WORKFLOW:
───────────────────────────
1. Check stationarity (ADF test)
2. Apply differencing if needed
3. Examine ACF/PACF plots
4. Choose p, d, q parameters
5. Fit model, check residuals
6. If residuals bad, go back to step 3
7. Handle seasonality separately
8. Add external regressors manually
9. Deal with missing data
10. Hope it works...

PROPHET WORKFLOW:
─────────────────
1. prophet.fit(df)
2. prophet.predict(future)
3. Done! 
```

### How Prophet Works

Prophet uses a decomposable model with three components:

```
y(t) = g(t) + s(t) + h(t) + ε_t

Where:
g(t) = Trend (growth)
s(t) = Seasonality (Fourier series)
h(t) = Holidays/events
ε_t  = Error term


TREND MODEL:
────────────
Linear:     g(t) = k·t + m
Logistic:   g(t) = C / (1 + exp(-k(t - m)))

Prophet automatically detects "changepoints" where
the growth rate k changes!

      Before Facebook's Algorithm Change
                ╱╱╱╱
               ╱
              ╱
             ╱
      ──────╱
            │
            └── Changepoint detected!


SEASONALITY (Fourier Series):
─────────────────────────────
s(t) = Σ [aₙ·cos(2πnt/P) + bₙ·sin(2πnt/P)]

For yearly seasonality (P=365.25):
  - 10 Fourier terms by default
  - Captures complex patterns

For weekly seasonality (P=7):
  - 3 Fourier terms by default
  - Captures day-of-week effects
```

### Prophet's Secret Weapons

```
PROPHET ADVANTAGES:
───────────────────

1. HANDLES MISSING DATA
   ───────────────────
   No need to interpolate! Prophet just ignores gaps.

2. ROBUST TO OUTLIERS
   ───────────────────
   Uses robust regression internally.

3. CHANGEPOINT DETECTION
   ──────────────────────
   Automatically finds where trends change.

4. HOLIDAY EFFECTS
   ────────────────
   Built-in support for irregular events.
   holidays = pd.DataFrame({
       'holiday': ['superbowl', 'thanksgiving'],
       'ds': ['2024-02-11', '2024-11-28']
   })

5. INTERPRETABLE COMPONENTS
   ────────────────────────
   See exactly what each component contributes.

6. UNCERTAINTY INTERVALS
   ──────────────────────
   Automatic prediction intervals!
```

**Did You Know?** Prophet was developed by Sean Taylor and Ben Letham at Facebook to forecast daily active users and ad revenue. They needed something that "worked out of the box" for thousands of time series with minimal human intervention. The name "Prophet" reflects their goal: to make accurate predictions (prophecies) about the future.

---

## Deep Learning for Time Series

### When to Use Deep Learning

```
CLASSICAL vs DEEP LEARNING DECISION:
────────────────────────────────────

Use CLASSICAL (ARIMA, Prophet) when:
├── Single time series
├── Clear seasonality patterns
├── Limited data (<1000 points)
├── Interpretability needed
├── Fast training required
└── Simple relationships

Use DEEP LEARNING when:
├── Multiple related time series
├── Complex, non-linear patterns
├── Lots of data (>10,000 points)
├── Multiple input variables
├── State-of-the-art accuracy needed
└── Willing to trade interpretability
```

### Recurrent Neural Networks (RNNs)

RNNs were designed specifically for sequential data:

```
VANILLA RNN:
────────────
Each timestep, the hidden state carries information forward.

h_t = tanh(W_h · h_{t-1} + W_x · x_t + b)
y_t = W_y · h_t + b_y

                    ┌───────────────────────────────────────┐
                    │                                       │
                    ▼                                       │
 x_1 ─→ [RNN] ─→ h_1 ─→ [RNN] ─→ h_2 ─→ [RNN] ─→ h_3 ─→ [RNN] ─→ h_4
          │              │              │              │
          ▼              ▼              ▼              ▼
         y_1            y_2            y_3            y_4


PROBLEM: Vanishing Gradients!
─────────────────────────────
As we backpropagate through many timesteps,
gradients get multiplied repeatedly.

0.9 × 0.9 × 0.9 × ... × 0.9 (100 times) ≈ 0.000027

The gradient vanishes! Can't learn long-term dependencies.
```

### LSTM: Long Short-Term Memory

LSTMs solve the vanishing gradient problem with gates:

```
LSTM CELL ARCHITECTURE:
───────────────────────

        ┌─────────────────────────────────────────────────┐
        │                                                 │
        │   ┌─────┐     ┌─────┐     ┌─────┐              │
 c_{t-1}───►│  ×  │────►│  +  │────►│     │─────────► c_t│
        │   └──┬──┘     └──┬──┘     │     │              │
        │      │           │        │     │              │
        │   ┌──┴──┐     ┌──┴──┐     │     │              │
        │   │ f_t │     │ i_t │     │     │              │
        │   │Forget│    │Input│     │     │              │
        │   │ Gate │    │ Gate│     │     │              │
        │   └──┬──┘     └──┬──┘     │     │              │
        │      │     ×     │        │  ×  │              │
        │      │     │     │        │     │              │
        │      │  ┌──┴──┐  │        │     │              │
        │      │  │ c̃_t │  │        │     │              │
        │      │  │ New │  │        │     │              │
        │      │  │Memory│ │        │     │              │
        │      │  └──┬──┘  │        └──┬──┘              │
        │      │     │     │           │                 │
        │      └──┬──┴──┬──┘        ┌──┴──┐              │
        │         │     │           │ o_t │              │
        │         │     │           │Output│             │
        │         │     │           │ Gate │             │
        │         │     │           └──┬──┘              │
        │         │     │              │                 │
 h_{t-1}─────────►│─────│──────────────►──────────► h_t  │
        │         │     │                                │
        │         │     │                                │
        └─────────┴─────┴────────────────────────────────┘
                  │     │
                  x_t   x_t


GATE FUNCTIONS:
───────────────
f_t = σ(W_f · [h_{t-1}, x_t] + b_f)   # Forget gate
i_t = σ(W_i · [h_{t-1}, x_t] + b_i)   # Input gate
o_t = σ(W_o · [h_{t-1}, x_t] + b_o)   # Output gate
c̃_t = tanh(W_c · [h_{t-1}, x_t] + b_c) # New memory

c_t = f_t ⊙ c_{t-1} + i_t ⊙ c̃_t      # Cell state update
h_t = o_t ⊙ tanh(c_t)                 # Hidden state

The cell state c_t acts like a "conveyor belt" -
information can flow unchanged through time!
```

**Did You Know?** LSTMs were invented by Sepp Hochreiter and Jürgen Schmidhuber in 1997. For years, the paper was largely ignored because computing power wasn't sufficient. It wasn't until 2014-2015 that LSTMs became practical, winning competitions and powering Google Translate. Schmidhuber often jokes that deep learning's success came 20 years late!

### GRU: A Simpler Alternative

Gated Recurrent Units simplify LSTMs while keeping most benefits:

```
GRU vs LSTM:
────────────

LSTM: 3 gates (forget, input, output) + cell state
GRU:  2 gates (reset, update) + no cell state

GRU EQUATIONS:
z_t = σ(W_z · [h_{t-1}, x_t])         # Update gate
r_t = σ(W_r · [h_{t-1}, x_t])         # Reset gate
h̃_t = tanh(W · [r_t ⊙ h_{t-1}, x_t])  # Candidate
h_t = (1 - z_t) ⊙ h_{t-1} + z_t ⊙ h̃_t # New state


COMPARISON:
───────────
┌──────────────┬───────────┬───────────┐
│   Aspect     │   LSTM    │    GRU    │
├──────────────┼───────────┼───────────┤
│ Parameters   │ More      │ Fewer     │
│ Training     │ Slower    │ Faster    │
│ Performance  │ ≈ Same    │ ≈ Same    │
│ Long deps    │ Slightly  │ Slightly  │
│              │ better    │ worse     │
└──────────────┴───────────┴───────────┘

Rule of thumb: Try GRU first (faster), switch to
LSTM if you need longer memory.
```

---

## Transformers for Time Series

### Why Transformers Work for Time Series

The same attention mechanism that revolutionized NLP works for time series:

```
ATTENTION IN TIME SERIES:
─────────────────────────

Traditional RNN: Sequential processing
  t=1 → t=2 → t=3 → t=4 → ... → t=100

  Problem: Information from t=1 might not reach t=100!

Transformer: Direct connections to ALL timesteps

       t=1  t=2  t=3  t=4  ...  t=100
        │    │    │    │         │
        └────┴────┴────┴─────────┘
                   │
              Attention can
              directly access
              any timestep!

Example: Forecasting energy demand
─────────────────────────────────
To predict Monday 8am demand, attention can:
- Look at last Monday 8am (7 days ago)
- Look at yesterday 8am
- Look at same day last year
- Ignore irrelevant midnight data

It LEARNS which past times are relevant!
```

### Temporal Fusion Transformer (TFT)

Google's TFT is state-of-the-art for time series:

```
TFT ARCHITECTURE:
─────────────────

┌─────────────────────────────────────────────────────┐
│                   OUTPUT LAYER                       │
│              (Quantile predictions)                  │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────┐
│              TEMPORAL SELF-ATTENTION                 │
│         (Which past times matter most?)              │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────┐
│              LSTM ENCODER-DECODER                    │
│            (Sequential processing)                   │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────┐
│            VARIABLE SELECTION NETWORK                │
│    (Which input features are important?)             │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────┐
│                   INPUT EMBEDDING                    │
│   Static vars | Past observed | Known future         │
│   (store ID)  | (past sales)  | (promotions)         │
└─────────────────────────────────────────────────────┘


TFT INNOVATIONS:
────────────────
1. Variable Selection: Learns which features matter
2. Static Enrichment: Uses metadata (store type, etc.)
3. Interpretable Attention: See which past times mattered
4. Multi-horizon: Predicts multiple future steps at once
5. Quantile Output: Uncertainty estimates built-in
```

**Did You Know?** The 2020 M5 Forecasting Competition on Kaggle (42,840 time series of Walmart sales) was won by teams using LightGBM, not deep learning! This surprised many researchers. The lesson: for many real-world problems, gradient boosting with good feature engineering still beats complex neural networks. Deep learning shines when you have millions of related time series.

---

## ️ Model Selection Guide

Choosing the right time series model is more art than science, but here's a framework that works in practice.

### The Decision Framework

Think of choosing a time series model like choosing a transportation method. You wouldn't take a bicycle for a cross-country trip, and you wouldn't rent a private jet to go to the grocery store. The right choice depends on your journey—or in our case, your data and requirements.

**Simple Exponential Smoothing** is like walking: basic, reliable, works for short distances, requires no special equipment. Use it for stable data without trends or seasonality.

**ARIMA** is like driving a car: more powerful, handles highways (trends) and turns (some patterns), requires some skill to operate. Use it for data with clear autocorrelation patterns.

**Prophet** is like using Uber: easy to call, handles most common routes automatically, good default choices. Use it for daily business data where you want quick results.

**Deep Learning (LSTM/Transformer)** is like operating a commercial aircraft: powerful, efficient at scale, requires significant training and infrastructure, overkill for short trips. Use it for thousands of related time series with abundant data.

### When Each Model Shines

**Choose Exponential Smoothing when:**
- You have a single stable time series
- No strong trend or seasonality exists
- You need a quick baseline
- Interpretability is critical (stock levels, simple demand)

**Choose ARIMA/SARIMA when:**
- Clear autocorrelation exists in your data (check ACF plot)
- You need statistical rigor and hypothesis testing
- The series has regular seasonality (monthly, quarterly, yearly)
- You want to understand the underlying statistical process
- Example: Economic indicators, utility demand, financial returns

**Choose Prophet when:**
- You have daily/weekly data with multiple seasonality patterns
- Missing values are common (Prophet handles gaps gracefully)
- Holidays and special events affect your series
- You need quick deployment without extensive tuning
- Business stakeholders need interpretable trend/seasonality decomposition
- Example: Website traffic, retail sales, social media metrics

**Choose Gradient Boosting + Features when:**
- You have strong exogenous variables (weather, promotions, events)
- Multiple related series share patterns
- You have moderate data (1,000-100,000 points)
- Feature engineering is your strength
- Example: Retail demand, energy forecasting, transportation planning

**Choose Deep Learning when:**
- You have millions of related time series
- Patterns are complex and non-linear
- Abundant data exists (100,000+ points per series, or cross-series learning)
- You have GPU infrastructure and ML expertise
- The business value justifies the complexity investment
- Example: Global e-commerce (Amazon), ride-sharing (Uber), cloud infrastructure (AWS)

### The Ensemble Approach

In practice, the best production systems don't choose one model—they combine multiple approaches. This is similar to how you might check both Google Maps and Waze before a long drive, trusting the consensus route more than either alone.

A simple but effective ensemble strategy:

```python
def ensemble_forecast(series, forecast_horizon):
    """
    Simple ensemble combining ARIMA, Prophet, and naive baseline.
    """
    from statsmodels.tsa.arima.model import ARIMA
    from prophet import Prophet
    import pandas as pd
    import numpy as np

    forecasts = {}

    # 1. Naive baseline (last value repeated)
    forecasts['naive'] = np.full(forecast_horizon, series.iloc[-1])

    # 2. ARIMA
    try:
        arima = ARIMA(series, order=(5, 1, 2))
        arima_fit = arima.fit()
        forecasts['arima'] = arima_fit.forecast(steps=forecast_horizon).values
    except:
        forecasts['arima'] = forecasts['naive']

    # 3. Prophet
    try:
        prophet_df = pd.DataFrame({'ds': series.index, 'y': series.values})
        model = Prophet(yearly_seasonality=True, weekly_seasonality=True)
        model.fit(prophet_df)
        future = model.make_future_dataframe(periods=forecast_horizon)
        forecasts['prophet'] = model.predict(future)['yhat'].iloc[-forecast_horizon:].values
    except:
        forecasts['prophet'] = forecasts['naive']

    # Simple average ensemble
    ensemble = np.mean([forecasts['naive'], forecasts['arima'], forecasts['prophet']], axis=0)

    return ensemble, forecasts
```

**Why ensembles work**: Different models capture different patterns. ARIMA might excel at autoregressive patterns but miss holiday effects. Prophet handles holidays but might overfit changepoints. By averaging, we reduce the risk of any single model's weaknesses dominating.

### Common Pitfalls in Model Selection

**Pitfall 1: Always choosing the most complex model**
A simple exponential smoothing model that's well-tuned often beats a misconfigured LSTM. Start simple, add complexity only when simpler models fail.

**Pitfall 2: Ignoring baseline comparisons**
Always compare to naive forecasts (y_t = y_{t-1} or y_t = y_{t-365}). If your fancy model can't beat naive, something is wrong with your data or evaluation.

**Pitfall 3: Optimizing for the wrong metric**
Different business problems need different metrics. Overage costs differ from shortage costs. Ensure your optimization metric matches business impact.

**Pitfall 4: Forgetting about inference time**
A model that takes 10 seconds to forecast might work in batch, but if you need real-time predictions for 10,000 series, that's 28 hours of compute per cycle. Consider latency requirements early.

---

## Temporal Feature Engineering

### Creating Features from Time

Raw timestamps hide valuable information:

```
FROM A SINGLE TIMESTAMP, EXTRACT:
─────────────────────────────────

datetime: 2024-11-28 14:30:00 (Thanksgiving Thursday)

Calendar Features:
├── year: 2024
├── month: 11
├── day: 28
├── hour: 14
├── minute: 30
├── day_of_week: 3 (Thursday)
├── day_of_year: 333
├── week_of_year: 48
├── quarter: 4
├── is_weekend: False
├── is_month_start: False
├── is_month_end: False
└── is_year_end: False

Cyclical Encoding (for neural networks):
├── hour_sin: sin(2π × 14/24) = 0.866
├── hour_cos: cos(2π × 14/24) = -0.5
├── day_sin: sin(2π × 3/7) = 0.975
├── day_cos: cos(2π × 3/7) = -0.223
└── month_sin/cos: ...

Holiday Features:
├── is_holiday: True (Thanksgiving)
├── days_to_holiday: 0
├── days_since_holiday: 0
└── holiday_type: "thanksgiving"
```

### Lag Features: Looking Back in Time

```
LAG FEATURES:
─────────────
The most powerful time series features!

Original data:
─────────────
│ Date       │ Sales │
├────────────┼───────┤
│ 2024-11-25 │  100  │
│ 2024-11-26 │  120  │
│ 2024-11-27 │  110  │
│ 2024-11-28 │  ???  │  ← Predict this

With lag features:
─────────────────
│ Date       │ Sales │ lag_1 │ lag_2 │ lag_7 │
├────────────┼───────┼───────┼───────┼───────┤
│ 2024-11-25 │  100  │   95  │   90  │   98  │
│ 2024-11-26 │  120  │  100  │   95  │  115  │
│ 2024-11-27 │  110  │  120  │  100  │  105  │
│ 2024-11-28 │  ???  │  110  │  120  │  102  │
                │      │      │
                │      │      └── Same day last week
                │      └── 2 days ago
                └── Yesterday's sales

Now the model can learn:
"Sales ≈ 0.3×lag_1 + 0.1×lag_2 + 0.5×lag_7"
```

### Rolling Statistics

```
ROLLING WINDOW FEATURES:
────────────────────────

│ Date       │ Sales │ roll_mean_7 │ roll_std_7 │ roll_max_7 │
├────────────┼───────┼─────────────┼────────────┼────────────┤
│ 2024-11-28 │  ???  │    107.5    │    8.2     │    120     │

roll_mean_7 = mean of last 7 days' sales
roll_std_7  = std dev of last 7 days (volatility!)
roll_max_7  = max of last 7 days (recent peak)


EXPANDING WINDOW (cumulative):
─────────────────────────────
│ Date       │ Sales │ expanding_mean │ days_since_start │
├────────────┼───────┼────────────────┼──────────────────┤
│ 2024-11-28 │  ???  │     98.5       │       333        │

expanding_mean = mean of ALL historical data
Useful for detecting regime changes!


EXPONENTIAL MOVING AVERAGE:
───────────────────────────
EMA gives more weight to recent observations.

EMA_t = α × value_t + (1-α) × EMA_{t-1}

α = 0.1: Slow EMA (long memory)
α = 0.5: Fast EMA (recent focus)
```

**Did You Know?** The most important feature in many time series competitions is simply "same day last year" (lag_365 or lag_364 depending on day-of-week alignment). In the M5 competition, this single feature provided more predictive power than dozens of other engineered features combined!

---

## Anomaly Detection in Time Series

### What Makes an Anomaly?

```
TYPES OF ANOMALIES:
───────────────────

1. POINT ANOMALY
   A single value that's unusual

   Normal: 100, 102, 98, 105, [500], 101, 99
                              ^^^^ Point anomaly!

2. CONTEXTUAL ANOMALY
   Normal in one context, anomalous in another

   Summer: 85°F normal
   Winter: 85°F ANOMALY! (should be ~40°F)

3. COLLECTIVE ANOMALY
   A sequence that's unusual as a group

   Normal: ~100, ~100, ~100
   Anomaly: 50, 50, 50, 50, 50  (individually ok, but...)
            ^^^^^^^^^^^^^^^^^
            Five consecutive lows is suspicious!


REAL-WORLD EXAMPLES:
────────────────────
├── Fraud Detection: Unusual spending pattern
├── Server Monitoring: CPU spike at 3am
├── Manufacturing: Machine vibration change
├── Healthcare: Heart rate irregularity
└── Finance: Flash crash in stock price
```

### Statistical Methods

```
Z-SCORE METHOD:
───────────────
z = (x - μ) / σ

If |z| > 3, it's an anomaly (3-sigma rule)

        │           ▲
        │          ╱ ╲
        │         ╱   ╲
        │        ╱     ╲     99.7% of data
        │       ╱       ╲    within ±3σ
        │      ╱         ╲
        │     ╱           ╲
        │────╱─────────────╲────
        │   -3σ   μ        3σ
        │    │             │
        └────┴─────────────┴────
           Anomaly zone!


IQR METHOD (Robust to outliers):
────────────────────────────────
Q1 = 25th percentile
Q3 = 75th percentile
IQR = Q3 - Q1

Lower bound = Q1 - 1.5 × IQR
Upper bound = Q3 + 1.5 × IQR

Values outside bounds = anomalies
```

### Machine Learning Methods

```
ISOLATION FOREST:
─────────────────
Idea: Anomalies are easier to isolate!

Normal points: Need many splits to isolate
Anomalies: Few splits to isolate (they're "far" from others)

                  │
           ┌──────┴──────┐
           │             │
     ┌─────┴─────┐       ●  ← Anomaly isolated in 1 split!
     │           │
   ┌─┴─┐       ┌─┴─┐
   ●   ●       ●   ●  ← Normal points need more splits


Isolation score = average path length to isolate point
Low path length = likely anomaly


AUTOENCODERS FOR ANOMALY DETECTION:
───────────────────────────────────

Train autoencoder on NORMAL data only:
  Input → [Encoder] → Latent → [Decoder] → Reconstruction

For new data:
  reconstruction_error = ||input - reconstructed||

  Normal data: Low error (autoencoder learned these patterns)
  Anomalies: High error (never seen before, can't reconstruct!)

        Reconstruction Error
              │
    Anomaly   │    ●
    threshold │─────────────●────
              │      ●    ●
              │   ●●●●●●●●●
              │  ●  ●  ●
              └──────────────────
                   Data points
```

**Did You Know?** Netflix uses time series anomaly detection to monitor their 200+ microservices. They process millions of metrics per second and need to detect issues within seconds. Their system "Telltale" uses a combination of statistical methods and machine learning, automatically learning what's "normal" for each service without human labeling!

---

## Forecasting at Scale

### The Multiple Time Series Problem

```
SINGLE vs MULTIPLE TIME SERIES:
───────────────────────────────

SINGLE TIME SERIES (Traditional):
─────────────────────────────────
One model per series. Works for 1-100 series.

Product A → ARIMA_A
Product B → ARIMA_B
Product C → ARIMA_C
...
Time: O(n) models to train


MULTIPLE TIME SERIES (Modern):
──────────────────────────────
One model for ALL series. Essential for 1000+ series.

Product A ──┐
Product B ──┼──→ [Global Model] ──→ All forecasts
Product C ──┤
...        ─┘

Benefits:
- Learns patterns across series
- Handles cold start (new products)
- Much faster (1 model, not n)
- Often more accurate!
```

### Hierarchical Forecasting

```
HIERARCHY EXAMPLE (Retail):
───────────────────────────

                    Total Company
                         │
           ┌─────────────┼─────────────┐
           │             │             │
        Region A     Region B      Region C
           │             │             │
      ┌────┼────┐   ┌────┼────┐   ┌────┼────┐
      │    │    │   │    │    │   │    │    │
    Store Store Store Store Store Store Store Store Store
      1    2    3    4    5    6    7    8    9


RECONCILIATION PROBLEM:
───────────────────────
If you forecast each level independently:
  Total forecast: $1,000,000
  Sum of regions:   $950,000  ← Doesn't match!

Solutions:
1. Top-down: Forecast total, split proportionally
2. Bottom-up: Forecast stores, sum up
3. Optimal reconciliation: Combine all levels optimally
```

---

## Practical Considerations

### Handling Missing Data

```
STRATEGIES FOR MISSING VALUES:
──────────────────────────────

1. FORWARD FILL (LOCF)
   Last Observation Carried Forward
   [10, 20, NaN, NaN, 50] → [10, 20, 20, 20, 50]
   Good for: Slow-changing data (prices, states)

2. BACKWARD FILL
   [10, NaN, NaN, 40, 50] → [10, 40, 40, 40, 50]
   Good for: When future is more relevant

3. LINEAR INTERPOLATION
   [10, NaN, NaN, 40, 50] → [10, 20, 30, 40, 50]
   Good for: Smooth continuous data

4. SEASONAL INTERPOLATION
   Use same time from previous cycle
   Good for: Strongly seasonal data

5. MODEL-BASED IMPUTATION
   Train model on non-missing data, predict missing
   Good for: Complex patterns
```

### Evaluation Metrics

```
FORECASTING METRICS:
────────────────────

MAE (Mean Absolute Error):
  MAE = mean(|actual - predicted|)
  Interpretable: "Average error is $X"

RMSE (Root Mean Square Error):
  RMSE = sqrt(mean((actual - predicted)²))
  Penalizes large errors more

MAPE (Mean Absolute Percentage Error):
  MAPE = mean(|actual - predicted| / |actual|) × 100%
  Scale-independent
  Problem: undefined when actual = 0!

SMAPE (Symmetric MAPE):
  SMAPE = mean(2|A - P| / (|A| + |P|)) × 100%
  Handles zeros better

MASE (Mean Absolute Scaled Error):
  MASE = MAE / MAE_of_naive_forecast
  < 1 means better than naive
  The gold standard for academics!


WHICH TO USE?
─────────────
├── Business stakeholders: MAE (easy to explain)
├── Scale comparison: MAPE/SMAPE
├── Academic: MASE
└── Optimization: Usually RMSE (differentiable)
```

### Avoiding Data Leakage

```
TIME SERIES CROSS-VALIDATION:
─────────────────────────────

WRONG (standard k-fold):
────────────────────────
Randomly split data - FUTURE leaks into PAST!
  Train: [▓▓▓░░▓▓░▓▓]  (random mix)
  Test:  [░░░▓▓░░▓░░]

  Model might see Dec 2024 in training,
  then "predict" Nov 2024 in test. CHEATING!


CORRECT (time-based):
─────────────────────

Walk-forward validation:
  Fold 1: Train [▓▓▓░░░░░░░] Test [░▓░░░░░░░░]
  Fold 2: Train [▓▓▓▓░░░░░░] Test [░░▓░░░░░░░]
  Fold 3: Train [▓▓▓▓▓░░░░░] Test [░░░▓░░░░░░]
  Fold 4: Train [▓▓▓▓▓▓░░░░] Test [░░░░▓░░░░░]
          ─────────────────────────────────────→ time

Always train on PAST, test on FUTURE!


GAP BETWEEN TRAIN AND TEST:
───────────────────────────
If forecasting 7 days ahead, leave 7-day gap:
  Train: [▓▓▓▓▓▓░░░░░░░░] Gap [░░░░░░░] Test [▓▓▓]

Prevents target leakage through lagged features!
```

---

##  Production War Stories

### The $50 Million Inventory Mistake

**March 2022, Major Retailer**

A retail forecasting team deployed a new demand forecasting model that improved accuracy by 3% on historical data. What they didn't realize: the model was trained on 2019-2021 data, which included the COVID anomaly period. The model had learned that "March = panic buying spike."

When March 2022 arrived and no pandemic panic occurred, the model predicted massive demand. The company overstocked by $50 million worth of inventory. Perishables spoiled. Warehouses overflowed. Discounting destroyed margins.

**The Root Cause**: No regime change detection. The model assumed future would look like the past, including a once-in-century pandemic.

```python
# The Fix: Regime detection before forecasting
def detect_regime_change(series, window=30, threshold=2.0):
    """Detect when the underlying pattern has fundamentally changed."""
    rolling_mean = series.rolling(window).mean()
    rolling_std = series.rolling(window).std()

    # Check if recent data is wildly different from historical patterns
    recent_zscore = (series.iloc[-window:].mean() - rolling_mean.iloc[-window*2:-window].mean()) / rolling_std.iloc[-window*2:-window].mean()

    if abs(recent_zscore) > threshold:
        print(f"️ REGIME CHANGE DETECTED: z-score = {recent_zscore:.2f}")
        print("   Consider retraining on post-change data only!")
        return True
    return False

# Usage: Run before every forecast cycle
if detect_regime_change(sales_data):
    model = retrain_on_recent_data(sales_data, months=3)
else:
    model = use_full_historical_model(sales_data)
```

**Lesson**: Always monitor for regime changes. A model that was perfect yesterday might be worthless today.

---

### The 0.01% That Cost Millions

**September 2019, Financial Services Company**

A quant team built an algorithmic trading model that forecasted stock prices with 99.99% directional accuracy in backtesting. They deployed it with $100 million in capital.

In the first week, the model lost $3 million. The "99.99% accuracy" was meaningless because they had committed the cardinal sin of time series: **data leakage through look-ahead bias**.

Their feature engineering calculated technical indicators using the full dataset (including future prices), then "predicted" the past. The model was essentially memorizing, not forecasting.

```python
# WRONG: Look-ahead bias (what they did)
def calculate_rsi_wrong(df):
    """This code looks at the ENTIRE series, including future!"""
    df['RSI'] = talib.RSI(df['close'], timeperiod=14)  # Calculated on ALL data
    return df

# CORRECT: Point-in-time calculation
def calculate_rsi_correct(df, current_idx):
    """Only use data available at the time of prediction."""
    # Only calculate on data up to current_idx
    historical_data = df.loc[:current_idx, 'close']
    return talib.RSI(historical_data, timeperiod=14).iloc[-1]

# Or use expanding window approach
def create_features_safely(df):
    """Create features using only past data at each point."""
    features = pd.DataFrame(index=df.index)

    for i in range(14, len(df)):
        # At time i, we only know prices 0 to i-1
        historical = df['close'].iloc[:i]
        features.loc[df.index[i], 'RSI'] = calculate_rsi_on_history(historical)

    return features
```

**The Fix**: Implement strict point-in-time feature engineering. Every feature at time t must only use data from times < t.

---

### The Anomaly That Wasn't

**July 2023, Cloud Infrastructure Provider**

An ML team built an anomaly detection system to monitor 50,000 server metrics. It was sensitive and fast, flagging anomalies within seconds. Operations loved it—at first.

Within a month, the team was overwhelmed. The system generated 10,000+ alerts daily. Most were false positives from normal daily patterns (high CPU at 9 AM when employees log in) or weekly patterns (backup jobs on Sunday nights).

The model treated every deviation from a static baseline as anomalous, ignoring the fact that servers have predictable cycles.

```python
# WRONG: Static threshold (what they did)
def detect_anomaly_naive(value, historical_mean, historical_std):
    z_score = (value - historical_mean) / historical_std
    return abs(z_score) > 3  # Static threshold

# CORRECT: Seasonally-adjusted detection
def detect_anomaly_seasonal(value, timestamp, historical_data):
    """Account for hour-of-day and day-of-week patterns."""
    hour = timestamp.hour
    day = timestamp.dayofweek

    # Get historical values for same hour and day
    similar_times = historical_data[
        (historical_data.index.hour == hour) &
        (historical_data.index.dayofweek == day)
    ]

    if len(similar_times) < 10:
        # Not enough history for this time slot
        return False, "Insufficient history"

    seasonal_mean = similar_times.mean()
    seasonal_std = similar_times.std()

    z_score = (value - seasonal_mean) / (seasonal_std + 1e-6)

    if abs(z_score) > 3:
        return True, f"Anomaly: z={z_score:.2f} vs typical for {hour}:00 on {day}"
    return False, "Normal"
```

After implementing seasonal baselines, false positives dropped by 90%, and the team could actually respond to real issues.

**Lesson**: Time series anomaly detection must account for temporal patterns. 9 AM behavior is different from 3 AM behavior.

---

## ️ Common Mistakes

### Mistake 1: Shuffling Time Series Data

```python
#  WRONG: Random train/test split destroys temporal structure
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
# Future data can leak into training!

#  CORRECT: Time-based split preserves temporal order
split_idx = int(len(X) * 0.8)
X_train, X_test = X[:split_idx], X[split_idx:]
y_train, y_test = y[:split_idx], y[split_idx:]
# Training only sees past, testing only sees future
```

**Why it matters**: Random shuffling lets your model "peek" at the future. It will show amazing validation scores but fail completely in production.

---

### Mistake 2: Ignoring Seasonality When Differencing

```python
#  WRONG: Only first-order differencing for seasonal data
diff_wrong = series.diff(1)  # Removes trend but not seasonality

#  CORRECT: Seasonal differencing for seasonal data
# For monthly data with yearly seasonality:
diff_correct = series.diff(12)  # Remove yearly pattern
diff_correct = diff_correct.diff(1)  # Then remove trend
```

**The symptom**: Residuals still show periodic patterns in ACF plot. Model captures trend but completely misses that December is always different from July.

---

### Mistake 3: Using Future Information in Features

```python
#  WRONG: Rolling features that look into the future
df['moving_avg'] = df['sales'].rolling(window=7, center=True).mean()
#                                                    ^^^^^ Uses 3 future days!

#  CORRECT: Only use past data
df['moving_avg'] = df['sales'].rolling(window=7, center=False).mean().shift(1)
#                                               ^^^^^ Only past ^^^^^^ Exclude current
```

**Why it's subtle**: center=True is the default in some libraries and seems harmless, but it uses future values in the calculation.

---

### Mistake 4: Overfitting to Recent Data

```python
#  WRONG: Training only on last 3 months
model = Prophet()
model.fit(df[df['ds'] > '2024-09-01'])  # Misses yearly seasonality!

#  CORRECT: Include at least 2 full cycles of your longest seasonality
# For yearly seasonality, use 2+ years of data
model = Prophet()
model.fit(df[df['ds'] > '2022-09-01'])  # Captures 2 full years
```

**The trap**: Recent data feels most relevant, but short windows can't capture long seasonal patterns. Your model won't know that January always differs from July.

---

### Mistake 5: Ignoring Scale When Comparing Forecasts

```python
#  WRONG: Comparing MAPE across very different series
mape_product_a = 5.2%   # Sales: $1M/month
mape_product_b = 45.3%  # Sales: $100/month (!)

# Product B seems terrible, but 45% of $100 is only $45 error!
# Product A at 5% of $1M is $50,000 error!

#  CORRECT: Use scale-independent metrics or absolute errors
# Option 1: Compare MAE in dollars
mae_a = 50000  # Much larger actual impact
mae_b = 45     # Tiny actual impact

# Option 2: Use MASE (Mean Absolute Scaled Error)
# Compares your model to a naive baseline on the same series
mase_a = 0.8   # 20% better than naive
mase_b = 1.2   # 20% worse than naive (worry about this one!)
```

**Lesson**: MAPE punishes forecasting low-volume items unfairly. Use MASE or weighted metrics for portfolio forecasting.

---

##  Economics of Time Series Forecasting

### ROI Breakdown by Industry

| Industry | Use Case | 1% Accuracy Gain Value | Typical Investment |
|----------|----------|------------------------|-------------------|
| **Retail** | Demand forecasting | $50M+ (inventory costs) | $500K |
| **Energy** | Load forecasting | $10M+ (grid balance) | $1M |
| **Finance** | Trading signals | $100M+ (alpha capture) | $5M |
| **Logistics** | Capacity planning | $20M+ (fleet optimization) | $300K |
| **Healthcare** | Patient volume | $5M+ (staffing costs) | $200K |

### Cost Structure of Production Forecasting Systems

```
TOTAL ANNUAL COST: $500K - $2M (enterprise scale)
──────────────────────────────────────────────────

Infrastructure (40%):
├── Compute for training: $5K-50K/month
├── Real-time inference: $2K-20K/month
├── Data storage: $1K-10K/month
└── Monitoring systems: $1K-5K/month

Personnel (50%):
├── Data scientists: 2-5 FTEs
├── ML engineers: 1-3 FTEs
└── Domain experts: 0.5-1 FTE

Tools & Services (10%):
├── Cloud ML platforms
├── Feature stores
└── Experiment tracking
```

### When to Build vs Buy

| Factor | Build Custom | Use Prophet/Auto-ARIMA | Buy Platform |
|--------|-------------|------------------------|--------------|
| Time series count | >10,000 | <100 | 100-10,000 |
| Customization need | High | Low | Medium |
| Team expertise | Deep ML | Basic stats | Varies |
| Time to value | 6-12 months | 1-2 weeks | 1-3 months |
| Annual cost | $500K+ | $50K | $100K-300K |

**Did You Know?** Walmart's forecasting system handles 500 million time series (every item × every store × every hour). Improving accuracy by 1 point on their largest 1% of series has the same dollar impact as improving the bottom 50% by 20 points. Focus your effort where the money is!

---

##  Debugging and Troubleshooting

### Problem: Model Predicts Flat Line

**Symptom**: Your forecast is a straight horizontal line near the mean.

**Diagnosis**: This usually means the model can't find patterns and defaults to predicting the average. Common causes:

1. **Data is truly random**: Some series (like stock prices) have very weak autocorrelation. The best predictor of tomorrow's price is today's price (random walk).

2. **Wrong differencing**: Over-differencing removes all signal. If you've differenced twice and predictions are flat, try d=1 or d=0.

3. **Feature scaling issues**: If your features are on vastly different scales, the model might ignore small-scale but important features.

```python
# Check if your series has predictable patterns
from statsmodels.graphics.tsaplots import plot_acf
import matplotlib.pyplot as plt

def diagnose_flat_predictions(series):
    """Diagnose why model predicts flat line."""
    # Check autocorrelation
    fig, ax = plt.subplots(figsize=(10, 4))
    plot_acf(series.dropna(), lags=40, ax=ax)
    plt.title("Autocorrelation - Strong patterns = tall bars")
    plt.show()

    # Check variance
    print(f"Mean: {series.mean():.4f}")
    print(f"Std Dev: {series.std():.4f}")
    print(f"Coefficient of Variation: {series.std()/series.mean()*100:.1f}%")

    # Check if naive forecast is better
    naive_mae = abs(series - series.shift(1)).mean()
    mean_mae = abs(series - series.mean()).mean()
    print(f"\nNaive (y_t = y_{t-1}) MAE: {naive_mae:.4f}")
    print(f"Mean prediction MAE: {mean_mae:.4f}")

    if naive_mae < mean_mae:
        print(" Series has predictable structure (naive beats mean)")
    else:
        print("️ Series might be unpredictable (mean beats naive)")
```

---

### Problem: Predictions Are Always One Step Behind

**Symptom**: Your forecast perfectly tracks actuals but shifted by one timestep.

**Diagnosis**: This is classic data leakage. Your model learned to copy the previous value because you accidentally included lagged target in features.

```python
# Common leak: Target at t-1 included as feature for predicting t
# The model learns: y_t ≈ y_{t-1} (just copy previous value)

# Check for this:
def check_for_lag_leak(predictions, actuals):
    """Detect if predictions are just lagged actuals."""
    # Correlation with lag-1 actual
    corr_lag1 = np.corrcoef(predictions[1:], actuals[:-1])[0, 1]
    # Correlation with actual
    corr_actual = np.corrcoef(predictions, actuals)[0, 1]

    print(f"Correlation with lag-1 actual: {corr_lag1:.4f}")
    print(f"Correlation with actual: {corr_actual:.4f}")

    if corr_lag1 > corr_actual:
        print("️ LEAK DETECTED: Predictions track lagged values!")
        print("   Check your features for data leakage")
```

**Fix**: Ensure your lag features at time t only use values from t-2 or earlier for predicting t+1.

---

### Problem: Great Training Metrics, Terrible Production Performance

**Symptom**: Model shows 95%+ accuracy in development but fails in production.

**Diagnosis**: Almost always one of these issues:

1. **Train/test contamination**: Used random split instead of time split
2. **Look-ahead bias**: Features computed on full dataset
3. **Target leakage**: Features contain target information
4. **Regime change**: Production data is fundamentally different

```python
def validate_training_integrity(model_metrics, production_metrics):
    """Check if training performance is realistic."""
    train_mae = model_metrics['train_mae']
    val_mae = model_metrics['val_mae']
    prod_mae = production_metrics['mae']

    print(f"Training MAE: {train_mae:.4f}")
    print(f"Validation MAE: {val_mae:.4f}")
    print(f"Production MAE: {prod_mae:.4f}")

    # Warning signs
    if train_mae < val_mae * 0.5:
        print("️ Training much better than validation - likely overfitting")

    if prod_mae > val_mae * 2:
        print(" Production 2x worse than validation - check for:")
        print("   1. Data leakage in validation")
        print("   2. Regime change in production")
        print("   3. Feature pipeline differences")

    ratio = prod_mae / val_mae
    if 0.8 < ratio < 1.2:
        print(" Production performance matches expectations")
```

---

### Problem: ARIMA Convergence Warnings

**Symptom**: statsmodels throws convergence warnings or optimization failures.

**Diagnosis**: ARIMA optimization can be finicky. Common fixes:

```python
from statsmodels.tsa.arima.model import ARIMA
import warnings

def fit_arima_robust(series, order, max_attempts=5):
    """Fit ARIMA with multiple optimization attempts."""

    methods = ['lbfgs', 'bfgs', 'powell', 'nm', 'cg']
    best_model = None
    best_aic = np.inf

    for method in methods[:max_attempts]:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")

                model = ARIMA(series, order=order)
                fitted = model.fit(method=method)

                if fitted.aic < best_aic:
                    best_aic = fitted.aic
                    best_model = fitted
                    print(f"Method {method}: AIC={fitted.aic:.2f} ")

        except Exception as e:
            print(f"Method {method}: Failed ({str(e)[:50]})")

    if best_model is None:
        print("All methods failed. Try:")
        print("1. Check for missing values")
        print("2. Try simpler order (lower p, q)")
        print("3. Ensure data is numeric")

    return best_model
```

---

### Problem: Prophet Is Too Slow

**Symptom**: Prophet takes minutes to fit on large datasets.

**Diagnosis**: Prophet uses MCMC sampling which is compute-intensive. Speed up options:

```python
from prophet import Prophet

def fast_prophet_fit(df, quick_mode=True):
    """Configure Prophet for faster training."""

    if quick_mode:
        model = Prophet(
            # Reduce MCMC samples (default is 1000)
            mcmc_samples=0,  # Use MAP estimation instead

            # Reduce changepoint detection
            n_changepoints=10,  # Default is 25

            # Simplify seasonality
            yearly_seasonality=5,  # Fewer Fourier terms (default 10)
            weekly_seasonality=3,  # Default is 3

            # Disable uncertainty intervals for speed
            uncertainty_samples=0
        )
    else:
        model = Prophet()  # Full accuracy mode

    model.fit(df)
    return model

# Also consider: sample your data for initial exploration
# Full data for final model only
```

---

##  Real-World Success Stories

### Uber: Dynamic Pricing at Scale

Uber's pricing engine processes millions of time series forecasts in real-time. Every region, every hour, every day needs a demand prediction to set prices that balance supply and demand. Their forecasting system, called "COTA" (Competition and TAxi), combines:

1. **Hierarchical forecasting**: City → Zone → Grid cell → Time bucket
2. **External features**: Weather, events, holidays, historical demand
3. **Ensemble approach**: Gradient boosting for baseline, LSTM for complex patterns

The impact? Uber reduced driver idle time by 15% and increased rider satisfaction by ensuring cars are positioned where demand will appear. At their scale, a 1% improvement in forecast accuracy translates to $200 million annually in better resource allocation.

**Technical insight**: Uber discovered that simple lag features (same time yesterday, same day last week) provided 60% of their model's predictive power. Deep learning added 5-10% on top, but the marginal cost of complexity often wasn't worth it for new markets with limited data.

---

### Amazon: 300 Million Forecasts Daily

Amazon's forecasting system is perhaps the world's largest production time series application. Every SKU in every warehouse needs daily demand predictions to drive:

- **Inventory ordering**: When and how much to order
- **Warehouse placement**: Which warehouse should hold stock
- **Shipping optimization**: Pre-positioning for anticipated demand

Their system, documented in the 2022 paper "AutoGluon-Timeseries," uses an AutoML approach that:

1. Automatically tries multiple models (ARIMA, Prophet, DeepAR, simple baselines)
2. Selects the best model per series
3. Combines predictions through weighted ensembling

The result: Amazon reduced inventory carrying costs by 15% while maintaining 99%+ in-stock rates. For a company with billions in inventory, this represents hundreds of millions in savings.

**Key lesson**: Amazon found that model selection matters more than model complexity. A simple exponential smoothing model often beats LSTM for stable products, while deep learning excels for products with complex promotional patterns.

---

### Capital One: Fraud Detection in Milliseconds

Credit card fraud detection is fundamentally a time series problem. Capital One processes 50,000+ transactions per second, each needing a fraud score within 100 milliseconds. Their system combines:

1. **Customer behavioral sequences**: What's normal for this cardholder?
2. **Merchant risk patterns**: How does this merchant's transaction flow look?
3. **Temporal anomaly detection**: Is this timing unusual?

They reduced fraud losses by 25% while decreasing false positive rates by 15%—meaning fewer annoyed customers getting their legitimate purchases declined.

**Technical architecture**: The system uses a streaming approach where LSTM models pre-compute customer embeddings hourly, while real-time scoring uses lightweight models that compare new transactions against these embeddings. This hybrid architecture achieves the speed requirements while maintaining accuracy.

---

### Netflix: Understanding Viewing Patterns

Netflix uses time series forecasting for capacity planning, knowing that a big premiere can spike traffic 10x. Their approach:

1. **Seasonal decomposition**: Identify weekly patterns (peak on weekends) and yearly patterns (holidays)
2. **Event modeling**: Account for show premieres, sporting events, and cultural moments
3. **Geographic cascading**: A show premieres at midnight in each timezone, creating predictable traffic waves

By accurately forecasting viewership, Netflix reduced their infrastructure costs by 30% while improving streaming quality. Over-provisioning wastes money; under-provisioning causes buffering.

**Did You Know?** Netflix found that their forecasting accuracy improved by 12% simply by adding "day since last release of similar content" as a feature. Viewers binge-watch, so demand patterns after a new season release follow predictable decay curves that vary by genre.

---

### Instacart: Predicting Grocery Demand

Instacart faces a unique forecasting challenge: predicting which products customers will order, when, and in what quantities—with the added complexity of perishable goods.

Their 2023 ML system processes 50,000+ time series (products × stores) and learned several critical lessons:

1. **Hierarchical helps**: Forecasting "dairy products" first, then drilling down to "2% milk," then specific brands improves accuracy for low-volume items
2. **Weather is king**: Temperature and precipitation are the two most important external features for grocery demand
3. **Substitution modeling**: When a product is out of stock, demand shifts to alternatives—ignoring this creates systematic bias

The business impact: Instacart reduced food waste by 20% (better predictions mean less over-ordering) while improving customer satisfaction through higher in-stock rates.

---

##  Interview Preparation

### Question 1: Explain stationarity and why it matters

**Answer**: Stationarity means the statistical properties of a time series (mean, variance, autocorrelation) don't change over time. It matters because most classical forecasting methods assume stationarity. If a series is non-stationary, yesterday's patterns don't reliably predict tomorrow—the underlying process is changing.

To test stationarity, I use the Augmented Dickey-Fuller (ADF) test. If the p-value is below 0.05, we reject the null hypothesis of a unit root, meaning the series is stationary. If it's non-stationary, we apply differencing (subtracting the previous value) until it becomes stationary. The number of differences needed is the 'd' parameter in ARIMA(p,d,q).

---

### Question 2: How do you prevent data leakage in time series problems?

**Answer**: Data leakage in time series comes from three main sources:

1. **Random train/test splits**: Instead, always use time-based splits where training data is strictly before test data.

2. **Look-ahead bias in features**: Every feature at time t must only use information from times before t. Be especially careful with rolling calculations—use `center=False` and `.shift(1)`.

3. **Target leakage**: Features that directly encode the target or are caused by the target. For example, using "total monthly sales" to predict daily sales within that month.

To validate, I always leave a gap between training and test sets equal to the forecast horizon. If I'm predicting 7 days ahead, there should be at least a 7-day gap to simulate realistic conditions.

---

### Question 3: When would you use Prophet vs ARIMA vs deep learning?

**Answer**: The choice depends on several factors:

**Prophet** when:
- You have daily data with strong weekly/yearly seasonality
- Missing values or outliers are common
- You need to handle holidays and special events
- Business stakeholders need interpretable components
- You have limited statistical expertise

**ARIMA/SARIMA** when:
- You need a statistical baseline
- Data is hourly or has unusual seasonality
- You want explicit control over model parameters
- Residual analysis for model diagnostics is important

**Deep Learning (LSTM, Transformer)** when:
- You have multiple related time series (>1000)
- Patterns are complex and non-linear
- You have abundant data (>10,000 points per series)
- Multiple exogenous variables affect the forecast
- You're willing to sacrifice interpretability for accuracy

In practice, I often start with Prophet or ARIMA as a baseline, then try gradient boosting with lag features (which wins many competitions), and only move to deep learning if those approaches plateau.

---

### Question 4: How do you handle multiple time series at scale?

**Answer**: At scale (1000+ time series), training individual models becomes impractical. I use global models that learn across all series:

1. **Feature engineering**: Create a unified feature set including series-specific static features (store type, product category), temporal features (day of week, holidays), and lag features (same time last week, last year).

2. **Global model**: Train a single model (typically LightGBM or a Transformer) on all series together. The model learns patterns that transfer across series.

3. **Hierarchical reconciliation**: If series have a hierarchy (stores → regions → total), forecast at each level and reconcile using optimal combination methods to ensure consistency.

4. **Cold start handling**: For new series with no history, the global model can still forecast using static features and patterns learned from similar series.

This approach is more accurate than individual models because rare patterns in one series might be common across the portfolio.

---

### Question 5: Design a real-time anomaly detection system for server metrics

**System Design Answer**:

**Requirements clarification**:
- Volume: 50,000 servers × 100 metrics × per-minute = 5M data points/minute
- Latency: Detect anomalies within 60 seconds
- False positive tolerance: <1% to avoid alert fatigue

**Architecture**:
```
┌────────────────────────────────────────────────────────────┐
│                    ARCHITECTURE                             │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  Metrics ─→ Kafka ─→ Flink Processor ─→ Anomaly Scorer     │
│                           │                   │             │
│                           ▼                   ▼             │
│                     Feature Store      Alert Router         │
│                     (Redis + S3)            │               │
│                           │                 ▼               │
│                           └──────→  PagerDuty/Slack        │
└────────────────────────────────────────────────────────────┘
```

**Anomaly detection approach**:
1. **Seasonal baseline**: For each metric × hour × day-of-week, maintain rolling mean and std
2. **Ensemble scoring**: Combine Z-score with Isolation Forest for robustness
3. **Suppression rules**: Group related alerts (same server, same root cause)
4. **Adaptive thresholds**: Tighten thresholds for critical services, relax for dev environments

**Key design decisions**:
- Use streaming (Flink) rather than batch for low latency
- Store baselines in Redis for sub-millisecond lookups
- Implement alert correlation to reduce noise (100 metrics spiking on one server = 1 alert)

---

##  Key Takeaways

1. **Time series data is fundamentally different**: Temporal dependency means order matters. Never shuffle time series data, and always use time-based train/test splits.

2. **Stationarity is the foundation**: Most classical methods require stationary data. Use the ADF test to check, and apply differencing to transform non-stationary series.

3. **Decompose to understand**: Every time series can be broken into trend, seasonality, and residual components. Understanding these components guides model selection and feature engineering.

4. **ARIMA is the workhorse**: The (p,d,q) parameters capture autoregression, differencing, and moving average effects. Use ACF/PACF plots to guide parameter selection, or let auto-ARIMA search for you.

5. **Prophet democratized forecasting**: Facebook's Prophet handles holidays, missing data, and changepoints automatically. It's the best "just works" solution for daily business data.

6. **Deep learning needs scale**: LSTMs and Transformers shine when you have thousands of related time series and abundant data. For single series, classical methods often win.

7. **Feature engineering wins competitions**: Lag features (yesterday, last week, last year) and rolling statistics often outperform complex models. The M5 competition proved gradient boosting + good features beats deep learning.

8. **Data leakage is the silent killer**: Point-in-time feature engineering is critical. One leaked feature can make a useless model look perfect in backtesting.

9. **Anomaly detection needs context**: A value that's normal at 9 AM might be anomalous at 3 AM. Always build seasonally-aware baselines to reduce false positives.

10. **Monitor for regime change**: Models trained on historical data assume the future resembles the past. Detect when underlying patterns shift and retrain accordingly.

---

## Hands-On Exercises

### Exercise 1: Build Complete ARIMA Pipeline

```python
"""
Complete ARIMA forecasting pipeline with proper evaluation.
"""
import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error

def check_stationarity(series, significance=0.05):
    """
    Test for stationarity using Augmented Dickey-Fuller test.

    Returns True if series is stationary (p-value < significance).
    """
    result = adfuller(series.dropna())
    adf_stat = result[0]
    p_value = result[1]

    print(f"ADF Statistic: {adf_stat:.4f}")
    print(f"p-value: {p_value:.4f}")

    if p_value < significance:
        print(" Series IS stationary (reject null hypothesis)")
        return True
    else:
        print(" Series is NOT stationary (fail to reject null)")
        return False

def make_stationary(series, max_diff=2):
    """
    Apply differencing until series is stationary.

    Returns (transformed_series, number_of_differences).
    """
    current = series.copy()
    d = 0

    while not check_stationarity(current) and d < max_diff:
        d += 1
        current = current.diff().dropna()
        print(f"\nAfter {d} difference(s):")

    return current, d

def select_arima_order(series, max_p=5, max_q=5):
    """
    Use information criteria to select best ARIMA(p,d,q) parameters.
    """
    # Make stationary first
    stationary, d = make_stationary(series)

    # Grid search over p and q
    best_aic = np.inf
    best_order = None

    for p in range(max_p + 1):
        for q in range(max_q + 1):
            try:
                model = ARIMA(series, order=(p, d, q))
                fitted = model.fit()

                if fitted.aic < best_aic:
                    best_aic = fitted.aic
                    best_order = (p, d, q)
                    print(f"ARIMA({p},{d},{q}): AIC={fitted.aic:.2f}")
            except:
                continue

    print(f"\nBest order: ARIMA{best_order} with AIC={best_aic:.2f}")
    return best_order

def walk_forward_validation(series, order, test_size=30):
    """
    Evaluate ARIMA using walk-forward validation (time-respecting CV).

    At each step:
    1. Train on all data up to time t
    2. Predict time t+1
    3. Move forward and repeat
    """
    history = list(series[:-test_size])
    predictions = []
    actuals = list(series[-test_size:])

    for i in range(test_size):
        # Fit model on history
        model = ARIMA(history, order=order)
        fitted = model.fit()

        # Predict next value
        forecast = fitted.forecast(steps=1)[0]
        predictions.append(forecast)

        # Add actual to history (simulates getting new data)
        history.append(actuals[i])

        if (i + 1) % 10 == 0:
            print(f"Progress: {i + 1}/{test_size} predictions")

    # Calculate metrics
    mae = mean_absolute_error(actuals, predictions)
    rmse = np.sqrt(mean_squared_error(actuals, predictions))

    print(f"\nWalk-Forward Validation Results:")
    print(f"MAE: {mae:.4f}")
    print(f"RMSE: {rmse:.4f}")

    return predictions, actuals, mae, rmse

# Example usage:
# df = pd.read_csv('sales.csv', parse_dates=['date'], index_col='date')
# series = df['sales']
# order = select_arima_order(series)
# predictions, actuals, mae, rmse = walk_forward_validation(series, order)
```

---

### Exercise 2: Prophet vs ARIMA Comparison

```python
"""
Head-to-head comparison of Prophet and ARIMA on the same dataset.
"""
import pandas as pd
import numpy as np
from prophet import Prophet
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_absolute_error
import matplotlib.pyplot as plt

def prepare_prophet_data(series):
    """Convert pandas Series to Prophet format (ds, y columns)."""
    df = pd.DataFrame({
        'ds': series.index,
        'y': series.values
    })
    return df

def compare_forecasters(series, forecast_horizon=30):
    """
    Compare Prophet vs ARIMA on the same train/test split.
    """
    # Split data
    train = series[:-forecast_horizon]
    test = series[-forecast_horizon:]

    results = {}

    # --- PROPHET ---
    print("Training Prophet...")
    prophet_df = prepare_prophet_data(train)
    prophet_model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False
    )
    prophet_model.fit(prophet_df)

    # Make future dataframe
    future = prophet_model.make_future_dataframe(periods=forecast_horizon)
    prophet_forecast = prophet_model.predict(future)
    prophet_preds = prophet_forecast['yhat'].iloc[-forecast_horizon:].values

    results['Prophet'] = {
        'predictions': prophet_preds,
        'mae': mean_absolute_error(test.values, prophet_preds)
    }

    # --- ARIMA ---
    print("Training ARIMA...")
    # Using auto-selected order (you'd use select_arima_order in practice)
    arima_model = ARIMA(train, order=(5, 1, 2))
    arima_fitted = arima_model.fit()
    arima_preds = arima_fitted.forecast(steps=forecast_horizon)

    results['ARIMA'] = {
        'predictions': arima_preds,
        'mae': mean_absolute_error(test.values, arima_preds)
    }

    # --- COMPARISON ---
    print("\n" + "=" * 50)
    print("COMPARISON RESULTS")
    print("=" * 50)
    for name, data in results.items():
        print(f"{name:15} MAE: {data['mae']:.4f}")

    # Determine winner
    winner = min(results.keys(), key=lambda k: results[k]['mae'])
    print(f"\n Winner: {winner}")

    # Plot comparison
    plt.figure(figsize=(12, 6))
    plt.plot(test.index, test.values, 'k-', label='Actual', linewidth=2)
    plt.plot(test.index, results['Prophet']['predictions'], 'b--', label='Prophet')
    plt.plot(test.index, results['ARIMA']['predictions'], 'r--', label='ARIMA')
    plt.legend()
    plt.title('Prophet vs ARIMA Forecast Comparison')
    plt.xlabel('Date')
    plt.ylabel('Value')
    plt.tight_layout()
    plt.savefig('forecast_comparison.png')

    return results

# Analyze Prophet components
def analyze_prophet_components(model, forecast):
    """Visualize what Prophet learned about trend and seasonality."""
    fig = model.plot_components(forecast)
    plt.tight_layout()
    plt.savefig('prophet_components.png')

    # Extract component strengths
    trend_range = forecast['trend'].max() - forecast['trend'].min()
    yearly_range = forecast['yearly'].max() - forecast['yearly'].min()

    print(f"\nComponent Analysis:")
    print(f"Trend range: {trend_range:.2f}")
    print(f"Yearly seasonality range: {yearly_range:.2f}")
    print(f"Ratio (seasonality/trend): {yearly_range/trend_range:.2%}")
```

---

### Exercise 3: LSTM Time Series Model

```python
"""
LSTM model for time series forecasting with proper sequence creation.
"""
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error

class LSTMForecaster(nn.Module):
    """
    LSTM architecture for time series prediction.
    """
    def __init__(self, input_size=1, hidden_size=64, num_layers=2, dropout=0.2):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout
        )

        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        # x shape: (batch, sequence_length, input_size)
        lstm_out, _ = self.lstm(x)

        # Take the last output
        last_output = lstm_out[:, -1, :]

        # Predict
        prediction = self.fc(last_output)
        return prediction

def create_sequences(data, look_back=30):
    """
    Create input sequences and targets for LSTM training.

    Given [1, 2, 3, 4, 5] with look_back=3:
    X = [[1,2,3], [2,3,4]]
    y = [4, 5]
    """
    X, y = [], []
    for i in range(len(data) - look_back):
        X.append(data[i:(i + look_back)])
        y.append(data[i + look_back])
    return np.array(X), np.array(y)

def train_lstm_forecaster(series, look_back=30, epochs=100, batch_size=32):
    """
    Complete LSTM training pipeline with proper time split.
    """
    # Scale data to [0, 1]
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(series.values.reshape(-1, 1))

    # Create sequences
    X, y = create_sequences(scaled_data.flatten(), look_back)

    # Time-based split (80% train, 20% test)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    print(f"Training samples: {len(X_train)}")
    print(f"Test samples: {len(X_test)}")

    # Convert to PyTorch tensors
    X_train = torch.FloatTensor(X_train).unsqueeze(-1)
    y_train = torch.FloatTensor(y_train).unsqueeze(-1)
    X_test = torch.FloatTensor(X_test).unsqueeze(-1)
    y_test = torch.FloatTensor(y_test).unsqueeze(-1)

    # Create DataLoader
    train_dataset = TensorDataset(X_train, y_train)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=False)
    # Note: shuffle=False for time series!

    # Initialize model
    model = LSTMForecaster()
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    # Training loop
    model.train()
    for epoch in range(epochs):
        total_loss = 0
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        if (epoch + 1) % 20 == 0:
            print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(train_loader):.6f}")

    # Evaluate
    model.eval()
    with torch.no_grad():
        predictions = model(X_test)

    # Inverse transform to original scale
    preds_original = scaler.inverse_transform(predictions.numpy())
    actuals_original = scaler.inverse_transform(y_test.numpy())

    mae = mean_absolute_error(actuals_original, preds_original)
    print(f"\nTest MAE: {mae:.4f}")

    return model, scaler, mae

# Usage:
# df = pd.read_csv('data.csv', index_col='date', parse_dates=True)
# model, scaler, mae = train_lstm_forecaster(df['value'], look_back=30)
```

---

### Exercise 4: Build Anomaly Detection System

```python
"""
Production-ready time series anomaly detection with seasonal baselines.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict

class SeasonalAnomalyDetector:
    """
    Anomaly detector that learns hour-of-day and day-of-week patterns.
    """

    def __init__(self, z_threshold=3.0, min_samples=20):
        self.z_threshold = z_threshold
        self.min_samples = min_samples
        # Store baselines by (hour, day_of_week)
        self.baselines = defaultdict(lambda: {'values': [], 'mean': None, 'std': None})

    def fit(self, series):
        """
        Learn normal patterns from historical data.

        series: pd.Series with DatetimeIndex
        """
        for timestamp, value in series.items():
            key = (timestamp.hour, timestamp.dayofweek)
            self.baselines[key]['values'].append(value)

        # Calculate statistics for each time slot
        for key, data in self.baselines.items():
            values = np.array(data['values'])
            if len(values) >= self.min_samples:
                # Use robust statistics (median and MAD) for outlier resistance
                data['mean'] = np.median(values)
                mad = np.median(np.abs(values - data['mean']))
                data['std'] = 1.4826 * mad  # Scale MAD to approximate std

                # Fallback to regular std if MAD is 0
                if data['std'] < 1e-6:
                    data['std'] = np.std(values)
            else:
                data['mean'] = None
                data['std'] = None

        print(f"Fitted on {len(series)} points")
        print(f"Unique time slots learned: {len(self.baselines)}")

        return self

    def detect(self, timestamp, value):
        """
        Check if a value is anomalous given its timestamp.

        Returns (is_anomaly, details_dict)
        """
        key = (timestamp.hour, timestamp.dayofweek)
        baseline = self.baselines[key]

        if baseline['mean'] is None:
            return False, {
                'status': 'insufficient_history',
                'message': f'Not enough data for {timestamp.hour}:00 on day {timestamp.dayofweek}'
            }

        z_score = (value - baseline['mean']) / (baseline['std'] + 1e-10)

        is_anomaly = abs(z_score) > self.z_threshold

        return is_anomaly, {
            'status': 'anomaly' if is_anomaly else 'normal',
            'value': value,
            'expected': baseline['mean'],
            'z_score': z_score,
            'threshold': self.z_threshold,
            'timestamp': timestamp
        }

    def detect_batch(self, series):
        """
        Run detection on a batch of data, returning all anomalies.
        """
        anomalies = []
        for timestamp, value in series.items():
            is_anomaly, details = self.detect(timestamp, value)
            if is_anomaly:
                anomalies.append(details)

        print(f"Found {len(anomalies)} anomalies in {len(series)} points")
        print(f"Anomaly rate: {len(anomalies)/len(series)*100:.2f}%")

        return anomalies

# Usage example:
# train_data = df['metric']['2024-01-01':'2024-06-30']
# detector = SeasonalAnomalyDetector(z_threshold=3.0)
# detector.fit(train_data)
#
# test_data = df['metric']['2024-07-01':'2024-07-31']
# anomalies = detector.detect_batch(test_data)
# for a in anomalies[:5]:
#     print(f"{a['timestamp']}: value={a['value']:.2f}, expected={a['expected']:.2f}, z={a['z_score']:.2f}")
```

---

## Summary

```
TIME SERIES FORECASTING TOOLKIT:
────────────────────────────────

┌───────────────────────────────────────────────────────────┐
│                    CLASSICAL METHODS                       │
├────────────────┬──────────────────────────────────────────┤
│ ARIMA/SARIMA   │ Statistical, interpretable, good baseline│
│ Prophet        │ Easy to use, handles holidays, robust    │
│ Exponential    │ Simple, fast, good for benchmarking      │
│ Smoothing      │                                          │
└────────────────┴──────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────┐
│                  DEEP LEARNING METHODS                     │
├────────────────┬──────────────────────────────────────────┤
│ LSTM/GRU       │ Sequential, good for medium-length deps  │
│ Transformer    │ Parallel, great for long dependencies    │
│ TFT            │ State-of-art, interpretable attention    │
│ N-BEATS        │ Pure DL, no hand-crafted features        │
└────────────────┴──────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────┐
│                   ENSEMBLE / HYBRID                        │
├────────────────┬──────────────────────────────────────────┤
│ LightGBM+Lags  │ Often wins competitions! Simple & fast   │
│ Stacking       │ Combine multiple model predictions       │
│ Weighted Avg   │ Average classical + DL forecasts         │
└────────────────┴──────────────────────────────────────────┘


DECISION FLOWCHART:
───────────────────
                 Start
                   │
      ┌────────────┴────────────┐
      │   How many series?      │
      └────────────┬────────────┘
                   │
          ┌───────┴───────┐
         <10            >100
          │               │
          ▼               ▼
       ARIMA/         Global
       Prophet        Model
          │               │
    ┌─────┴─────┐   ┌─────┴─────┐
    │Seasonality│   │  >10k pts │
    └─────┬─────┘   └─────┬─────┘
        Yes│No          Yes│No
          │  │            │  │
          ▼  ▼            ▼  ▼
     SARIMA AR       Transformer LightGBM
     Prophet          TFT        +Lags
```

---

##  Historical Context

Understanding where time series methods came from helps appreciate their design decisions and limitations.

### The Classical Era (1920s-1970s)

Time series forecasting began with simple moving averages in the 1920s, used primarily for economic forecasting and quality control in manufacturing. The field was transformed in the 1950s when Robert Brown developed exponential smoothing while working at the U.S. Navy's Office of Operations Research. Brown needed to forecast demand for submarine spare parts—a problem where recent data should matter more than old data. His exponentially weighted moving average became the foundation for modern forecasting.

The next revolution came in 1970 when George Box and Gwilym Jenkins published their seminal book on ARIMA models. Box was a statistician at the University of Wisconsin, and Jenkins worked at the University of Lancaster. Their methodology—identify, estimate, diagnose, forecast—remained the dominant paradigm for three decades. Box famously noted, "All models are wrong, but some are useful," capturing the pragmatic philosophy that still guides forecasting today.

**Did You Know?** The Box-Jenkins methodology was originally developed for predicting gas furnace temperatures in chemical plants. The autocorrelation techniques they refined for this industrial application became the foundation for forecasting everything from stock prices to weather patterns.

### The Machine Learning Era (2000s-2010s)

The rise of machine learning brought new approaches to time series. Recurrent Neural Networks (RNNs) were proposed as early as 1986 by David Rumelhart, but the vanishing gradient problem limited their practical use. Sepp Hochreiter and Jürgen Schmidhuber solved this in 1997 with Long Short-Term Memory (LSTM) networks, but computing power wasn't sufficient to train them effectively until the 2010s.

Meanwhile, practical forecasters discovered that gradient boosting with hand-crafted features often outperformed neural networks. The M Competitions (Makridakis Competitions), running since 1982, provided rigorous benchmarks. In the 2018 M4 competition, a hybrid approach combining exponential smoothing with neural networks won—showing that classical and modern methods could complement each other.

### The Transformer Era (2017-Present)

The introduction of Transformers in 2017 (Vaswani et al.'s "Attention Is All You Need") revolutionized natural language processing and eventually time series. The attention mechanism solved the fundamental problem that plagued RNNs: how to directly connect distant timesteps without information degrading through sequential processing.

Google's Temporal Fusion Transformer (2020) adapted these ideas specifically for time series, adding variable selection networks to handle the many exogenous variables common in forecasting problems. Amazon's DeepAR and Facebook's Prophet (2017) democratized sophisticated forecasting, making it accessible to practitioners without deep statistical training.

Today, we're in an exciting period where classical methods, gradient boosting, and deep learning each have their place. The key insight from decades of research: no single method dominates. The best practitioners understand the strengths of each approach and choose based on their specific problem, data, and constraints.

---

## Further Reading

### Papers
- "Time Series Analysis: Forecasting and Control" (Box & Jenkins, 1970) - The foundational text that defined modern time series analysis
- "Time Series Forecasting with Prophet" (Taylor & Letham, 2017) - Facebook's accessible forecasting framework
- "Temporal Fusion Transformers" (Lim et al., 2020) - State-of-the-art deep learning for interpretable forecasting
- "N-BEATS: Neural Basis Expansion Analysis" (Oreshkin et al., 2020) - Pure deep learning without hand-crafted features
- "Deep Learning for Time Series Forecasting" (Lim & Zohren, 2021) - Comprehensive survey of modern methods
- "The M5 Accuracy Competition: Results, Findings and Conclusions" (Makridakis et al., 2022) - Empirical insights from the largest forecasting competition

### Libraries
- **statsmodels**: ARIMA, exponential smoothing, and classical statistical methods
- **Prophet**: Facebook's forecasting library, excellent for daily data with seasonality
- **GluonTS**: Amazon's deep learning time series toolkit with DeepAR and other models
- **Darts**: Unified interface for classical, ML, and deep learning methods
- **sktime**: scikit-learn compatible time series with consistent API
- **pytorch-forecasting**: PyTorch-based deep learning models including TFT
- **NeuralProphet**: Prophet-like interface with neural network backends

---

## Next Steps

You now understand time series forecasting from classical ARIMA to modern transformers!

**Up Next**: Module 39 - AutoML & Feature Stores

---

_Module 38 Complete!_
_"The best forecast is the one that's useful, not the one that's most complex."_
