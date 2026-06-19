---
title: "Time Series Forecasting"
slug: ai-ml-engineering/machine-learning/module-1.12-time-series-forecasting
sidebar:
  order: 12
---

> **AI/ML Engineering Track** | Complexity: `[COMPLEX]` | Time: 90-120 minutes
>
> **Prerequisites**: [Module 1.3: Model Evaluation, Validation, Leakage & Calibration](../module-1.3-model-evaluation-validation-leakage-and-calibration/), [Module 1.4: Feature Engineering & Preprocessing](../module-1.4-feature-engineering-and-preprocessing/), [Module 1.6: XGBoost & Gradient Boosting](../module-1.6-xgboost-gradient-boosting/), and comfort with pandas indexes, regression metrics, and train/test splits.

---

## Learning Outcomes

By the end of this module, you will be able to:

- Diagnose why a forecasting problem needs time-aware validation, stationarity checks, and leakage controls before model choice.
- Decompose a temporal signal into trend, seasonality, cyclicality, and residual behavior, then use ACF and PACF patterns to propose ARIMA or SARIMA orders.
- Build statistical forecasts with ARIMA, SARIMA, exponential smoothing, and Prophet while explaining when each family is a reasonable baseline.
- Reframe forecasting as supervised regression with lag, rolling, calendar, Fourier, and holiday features for tree-based models.
- Design walk-forward backtests that compare statistical and machine-learning forecasters against naive or seasonal-naive baselines using horizon-aware metrics.

## Why This Module Matters

Forecasting looks like ordinary regression until time becomes part of the contract. In a normal tabular split, shuffling rows often improves the estimate of average generalization. In forecasting, shuffling rows destroys the question. You do not ask whether the model can predict a randomly hidden observation from the same period. You ask whether it can stand at a decision date, see only the past, and make a useful statement about the future.

That one change explains most forecasting failures. A model can look brilliant if it sees target values from next week while building rolling averages for today. A scaler can leak if it estimates the full-period mean before the split. A cross-validation routine can lie if one fold trains on data from the future and evaluates on older observations. Time series work is therefore less about choosing one fashionable algorithm and more about preserving the arrow of time from raw data through evaluation.

Hypothetical scenario: an operations team forecasts daily support tickets for staffing. Their first notebook uses random k-fold validation and centered rolling features, so the validation error looks comfortably low. When the schedule goes live, weekends and holidays are under-staffed because the model learned patterns using information that would not have existed at scheduling time. The fix is not only a different model. The fix is a forecasting protocol that makes impossible information impossible to use.

> **The Sealed Calendar Analogy**
>
> A forecasting model is like a planner with sealed calendar pages. When you stand on March 31, every page after March 31 is sealed. You may know recurring holidays, planned promotions, and the calendar structure, but you may not peek at April demand, April residuals, or April rolling averages. Good forecasting engineering is the discipline of keeping those pages sealed in code.

> **Landscape snapshot - as of 2026-06. Library versions move fast; verify against the project's release notes before relying on specifics.**
>
> - `statsmodels` **0.14.6** includes `statsmodels.tsa` ARIMA, SARIMAX, and `ExponentialSmoothing`.
> - `prophet` **1.3.0** is the maintained successor to the original `fbprophet`; Python imports use `from prophet import Prophet`.
> - Tree-based forecasting commonly uses XGBoost **3.3.0**, LightGBM **4.6.0**, or scikit-learn **1.9.0** estimators such as `HistGradientBoostingRegressor`.

## What Makes Time Series Different

A time series is a sequence where order carries information. Yesterday's temperature, last month's revenue, and last year's holiday spike are not independent row labels attached after the fact. They help define what the next value can plausibly be. This dependence is called autocorrelation: nearby values, and sometimes values one seasonal period apart, tend to be related.

Temporal ordering changes the basic modeling assumptions. In ordinary supervised learning, you can often assume rows are exchangeable enough for random splitting. In forecasting, rows are not exchangeable because the training set must represent what was known before the forecast origin. A feature computed from the entire series can silently smuggle future information into the past even when the final train/test split looks chronological.

The cardinal rule is simple: the future must never leak into the past. Every transformation, imputation, scaling step, feature, model selection decision, and metric calculation must be written as if the model were running on the forecast date. If a value would not be available to the production system at that date, it cannot be used during validation.

Time series structure is usually discussed through four components. Trend is the long-run direction, such as atmospheric CO2 rising over decades or active users growing during adoption. Seasonality is a repeating pattern with a known or stable period, such as hourly traffic cycles, weekly staffing rhythms, or annual demand spikes. Cyclicality is a broader rise-and-fall pattern whose length is not fixed, such as business cycles or commodity regimes. Residual behavior is what remains after the structured parts are removed.

Those components matter because they suggest different interventions. A strong trend may need differencing, damping, or explicit trend terms. A regular seasonal pattern may need seasonal differencing, Fourier features, seasonal smoothing, or a seasonal-naive baseline. A noisy residual pattern may reveal that the useful signal is exhausted, and a more complex model is only fitting noise more elegantly.

```text
observed series
    |
    +-- trend: long-run movement
    +-- seasonality: repeated calendar pattern
    +-- cyclicality: irregular regime movement
    +-- residual: unexplained remainder
```

The most useful first plot is rarely a model plot. Start with the raw series, the train/test boundary, and a seasonal view by hour, week, month, or product cycle. Many expensive modeling mistakes become obvious when you can see that the validation window covers a different regime, that timestamps are missing, or that the target has a hard floor near zero.

## Forecast Origins and Data Availability

The most important timestamp in a forecasting project is the forecast origin. That is the moment where the model stands and makes a claim about the future. If a retailer forecasts demand every Sunday night for the next two weeks, then Sunday night is the forecast origin. If a platform team forecasts CPU capacity every morning for the next day, then each morning is a new origin. Write this down explicitly because it defines which data is allowed.

Availability is not the same as timestamp. A source record may have an event timestamp of Monday but arrive in the warehouse on Wednesday. A financial adjustment may describe last month but be posted after the forecast was made. A monitoring metric may be timestamped correctly but delayed by an exporter outage. Forecasting pipelines need both event time and availability time when late-arriving data can change what the model would have known.

This distinction matters during feature engineering. Suppose a feature named `last_known_inventory` is computed by joining the latest inventory snapshot before the target date. That sounds safe until you learn that snapshots are corrected retroactively after reconciliation. A backtest using corrected snapshots may outperform production because production would have seen the uncorrected version. The leakage is subtle because every row still has a date before the target.

Good forecasting datasets therefore include an availability contract. For each column, document whether it is observed history, scheduled future information, slowly updated metadata, or a target-derived artifact. Observed history must be cut off at the origin. Scheduled future information can extend into the horizon only if it is genuinely known. Target-derived artifacts usually need special suspicion because they often encode future outcomes under a harmless business name.

When that contract is missing, model review becomes guesswork. Reviewers argue about algorithms while the real uncertainty is whether the feature table could have existed at forecast time. A simple availability table prevents many of these arguments. It also makes the project easier to operationalize, because the production feature job can be tested against the same "known by origin" rule used in backtesting.

## Stationarity, Differencing, ACF, and PACF

Many classical time series methods assume some form of stationarity. A stationary series has statistical behavior that is stable over time: its mean, variance, and autocorrelation structure do not drift wildly as the window moves. Real business and infrastructure series are often not stationary in their raw form, but a transformed version may be close enough to model responsibly.

Differencing is the most common transformation. A first difference models the change from one observation to the next rather than the level itself. Seasonal differencing models the change from one seasonal position to the corresponding previous seasonal position, such as this January minus last January. Differencing can remove trend or seasonal persistence, but unnecessary differencing can also erase useful signal and make forecasts unstable.

Two standard tests help frame the stationarity question. The Augmented Dickey-Fuller test uses a null hypothesis of a unit root, so a low p-value is evidence against non-stationarity. The KPSS test reverses the framing by using a stationarity null, so a low p-value suggests the series is not stationary under the selected level or trend assumption. The tests are not magic judges; they are structured evidence to combine with plots and domain knowledge.

ACF and PACF plots help identify autoregressive and moving-average structure after appropriate transformation. The autocorrelation function shows correlation between the series and lagged versions of itself. The partial autocorrelation function estimates the relationship at a lag after accounting for shorter lags. In practice, ACF and PACF are diagnostic tools, not vending machines for perfect `(p, d, q)` orders.

```python
import warnings

import numpy as np
from statsmodels.datasets import co2
from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.stattools import acf, adfuller, kpss, pacf

series = (
    co2.load_pandas()
    .data["co2"]
    .resample("MS")
    .mean()
    .interpolate("time")
    .asfreq("MS")
)

decomposition = STL(series, period=12, robust=True).fit()
differenced = series.diff().dropna()

adf_stat, adf_pvalue, *_ = adfuller(differenced, autolag="AIC")
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    kpss_stat, kpss_pvalue, *_ = kpss(differenced, regression="c", nlags="auto")

acf_values = acf(differenced, nlags=12, fft=True)
pacf_values = pacf(differenced, nlags=12, method="ywm")

print("ADF p-value:", round(adf_pvalue, 4))
print("KPSS p-value:", round(kpss_pvalue, 4))
print("First seasonal ACF value:", round(float(acf_values[12]), 3))
print("First seasonal PACF value:", round(float(pacf_values[12]), 3))
print("STL residual rows:", decomposition.resid.dropna().shape[0])
```

Use this kind of diagnostic block before model selection. If the raw series has a clear trend and the first difference looks stable, an ARIMA model with `d=1` may be reasonable. If there is a strong spike at lag 12 on monthly data, a seasonal order or seasonal features should be considered. If the residuals retain strong autocorrelation after fitting, the model has not captured the temporal structure you claimed it captured.

## Reading Diagnostics Conservatively

Diagnostics should narrow the candidate set, not replace judgment. ACF and PACF plots are especially easy to over-read because they feel precise. Real operational data often has calendar effects, interventions, missing periods, and regime changes that make textbook patterns messy. If the ACF tails off slowly, that may indicate trend, seasonal persistence, or an unmodeled level shift. The next move is to test a simpler transformation and inspect residuals, not to add every possible lag.

Stationarity tests deserve the same restraint. ADF and KPSS can disagree because they ask different null-hypothesis questions and depend on lag choices, trend settings, and sample length. A low p-value is evidence, not a deployment approval. If plots show a structural break, the right answer may be a regime-aware split or a shorter training window rather than another round of differencing. The purpose is to understand the signal well enough to validate models honestly.

Residual diagnostics are the bridge between modeling and engineering. After fitting a statistical model, plot residuals over time, inspect residual ACF, and check whether errors cluster around known calendar or business events. If residuals still have strong seasonal autocorrelation, the model missed repeating structure. If residual variance grows with the level, a transformation or multiplicative model may be more appropriate. If residuals deteriorate in the most recent window, older history may no longer represent current behavior.

This conservative reading also helps compare statistical and machine-learning approaches. A tree model may beat SARIMA because it captures nonlinear calendar interactions. SARIMA may beat a tree model because the tree lacks enough history to learn long seasonal cycles. Diagnostics give you language to explain the difference. Without them, a forecast comparison becomes a leaderboard with no causal story, and the team has little guidance when the next regime change arrives.

## Classical Statistical Forecasting

Classical statistical methods remain the durable core of forecasting because they make temporal assumptions explicit. They are fast, interpretable, and strong baselines for many univariate problems. Even when a tree-based or deep-learning model eventually wins, a disciplined statistical baseline tells you whether that extra complexity bought real forecasting value.

### ARIMA and SARIMA

ARIMA stands for autoregressive integrated moving average. The `p` term controls autoregressive lag terms, the `d` term controls differencing, and the `q` term controls moving-average error terms. A SARIMA model adds seasonal `P`, `D`, and `Q` terms plus a seasonal period `s`, so monthly data with annual seasonality commonly uses `s=12`.

Autoregressive terms say that the current value relates to past values. Differencing says the model should learn changes rather than levels. Moving-average terms say that the current value relates to past forecast errors. The combined model is compact, but each term encodes a different belief about how the signal behaves.

Order identification usually starts with plots, differencing experiments, and ACF/PACF diagnostics. If the raw series trends upward, test a first difference. If monthly residuals still show annual structure, consider seasonal differencing or seasonal AR/MA terms. Then compare a small set of plausible orders with information criteria, residual diagnostics, and honest backtests. Avoid searching a huge order grid until one lucky specification wins a validation split by noise.

`statsmodels.tsa.arima.model.ARIMA` provides a direct interface for ARIMA-type models, including seasonal components. For many production teams, `SARIMAX` is also important because it can include exogenous regressors, but the same temporal validation rule applies to those regressors. Future exogenous values must either be known at forecast time or forecast by another leakage-safe process.

```python
from statsmodels.datasets import co2
from statsmodels.tsa.arima.model import ARIMA

series = (
    co2.load_pandas()
    .data["co2"]
    .resample("MS")
    .mean()
    .interpolate("time")
    .asfreq("MS")
)

train = series.iloc[:-12]
test = series.iloc[-12:]

model = ARIMA(
    train,
    order=(1, 1, 1),
    seasonal_order=(1, 0, 1, 12),
    enforce_stationarity=False,
    enforce_invertibility=False,
)
fitted = model.fit()
forecast = fitted.get_forecast(steps=len(test))

print(forecast.predicted_mean.head())
print(forecast.conf_int().head())
```

`auto_arima` from `pmdarima` is a useful convenience when you want a structured search over ARIMA orders. Treat it as a helper, not as an exemption from diagnostics. You still choose the seasonal period, inspect residuals, verify assumptions, and backtest against simple baselines. Automation can propose candidates, but it cannot know whether your validation window matches the operational decision.

```python
from pmdarima import auto_arima
from statsmodels.datasets import co2

series = (
    co2.load_pandas()
    .data["co2"]
    .resample("MS")
    .mean()
    .interpolate("time")
    .asfreq("MS")
)
train = series.iloc[:-12]

candidate = auto_arima(
    train,
    seasonal=True,
    m=12,
    information_criterion="aic",
    stepwise=True,
    suppress_warnings=True,
)

print(candidate.order)
print(candidate.seasonal_order)
```

### Exponential Smoothing and Holt-Winters

Exponential smoothing methods forecast by updating level, trend, and seasonal components as new observations arrive. Recent observations receive more weight than older observations, which makes these models intuitive for operational series that evolve gradually. Holt-Winters extends the idea to trend and seasonality, giving you a compact baseline for many business and capacity-planning forecasts.

The additive versus multiplicative choice matters. Additive seasonality assumes the seasonal swing has roughly constant size, such as plus or minus a fixed number of requests. Multiplicative seasonality assumes the seasonal swing scales with the level, such as December demand being a percentage lift over baseline demand. Multiplicative components require positive data and can behave badly near zero.

```python
from statsmodels.datasets import co2
from statsmodels.tsa.holtwinters import ExponentialSmoothing

series = (
    co2.load_pandas()
    .data["co2"]
    .resample("MS")
    .mean()
    .interpolate("time")
    .asfreq("MS")
)

train = series.iloc[:-12]
test = series.iloc[-12:]

model = ExponentialSmoothing(
    train,
    trend="add",
    seasonal="add",
    seasonal_periods=12,
    initialization_method="estimated",
)
fitted = model.fit(optimized=True)
forecast = fitted.forecast(len(test))

print(forecast.head())
```

Exponential smoothing is often easier to explain than ARIMA because the components map directly to planning language. Level answers "where are we now." Trend answers "how fast are we moving." Seasonality answers "where are we inside the recurring cycle." That clarity is valuable when forecasts support staffing, purchasing, budget, or reliability decisions.

### Prophet

Prophet models a time series as an additive combination of trend, seasonality, holidays, and error. It is designed for analyst-friendly forecasting workflows where calendar effects, missing observations, changepoints, and holiday regressors matter. It can work well when a series has strong multiple seasonalities and a reasonable amount of history for each recurring pattern.

Prophet is not a universal upgrade over ARIMA, exponential smoothing, or tree-based regression. It can struggle when the signal has weak seasonality, very short history, unstable regimes, or high-frequency dependencies that are better expressed through lags. It also needs the same leakage-safe evaluation as every other forecasting method. A convenient API does not make future target values available at prediction time.

```python
import pandas as pd
from prophet import Prophet
from statsmodels.datasets import co2

series = (
    co2.load_pandas()
    .data["co2"]
    .resample("MS")
    .mean()
    .interpolate("time")
    .asfreq("MS")
)

df = series.reset_index()
df.columns = ["ds", "y"]

train = df.iloc[:-12]

model = Prophet(
    yearly_seasonality=True,
    weekly_seasonality=False,
    daily_seasonality=False,
)
model.fit(train)

future = model.make_future_dataframe(periods=12, freq="MS")
forecast = model.predict(future)

print(forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail())
```

Prophet's holiday support is useful when the calendar contains known future events. A holiday flag for next year's public holiday is legitimate because you know that calendar before the forecast. A flag derived from next year's observed demand spike is leakage because it uses the target to explain itself. The difference is not the column name; the difference is whether the information is genuinely known at the forecast origin.

## Machine-Learning Forecasting as Supervised Regression

Machine-learning forecasting reframes the problem as supervised regression. Instead of fitting an explicit stochastic time-series model, you create rows where features summarize what was known at each timestamp and the target is a future value. This framing lets you use familiar tools such as gradient-boosted trees, random forests, regularized linear models, and scikit-learn pipelines.

The feature design carries the forecasting logic. Lag features expose recent target history, such as `lag_1`, `lag_7`, or `lag_12`. Rolling features summarize recent history, such as a trailing mean, trailing maximum, trailing standard deviation, or trailing count. Calendar features expose known future structure, such as hour, day of week, month, quarter, or end-of-month flags. Fourier features encode smooth seasonal patterns without creating one dummy column per calendar value.

Holiday flags are allowed when the holiday calendar is known before prediction. Price, weather, promotion, inventory, or staffing features require more care. If the future value is known at forecast time because it is scheduled, you may use it. If it would only be known later, you must either exclude it or forecast it separately inside the same backtest.

Tree-based models are popular because they handle nonlinear interactions between lag values, rolling summaries, and calendar effects. XGBoost, LightGBM, and scikit-learn's histogram gradient boosting can learn rules such as "January demand is high only when the last quarter was already high" without requiring you to hand-write the interaction. That strength is also a risk, because a powerful model will happily exploit leakage if you give it a leaked feature.

Global models train across many related series in one model. Instead of fitting one model per store, product, metric, or region, you include a series identifier and train on all histories together. A global model can share signal across sparse series and learn common seasonal behavior, but it also needs careful backtesting so that each series is evaluated only on future timestamps.

```text
forecast origin: 2026-03-31

allowed features for 2026-04:
  - lagged target values through 2026-03
  - trailing rolling means ending at 2026-03
  - known calendar facts for 2026-04
  - scheduled future events known before 2026-04

not allowed features for 2026-04:
  - centered rolling means that include 2026-04
  - scaler parameters fitted on the full year
  - imputed values learned from the validation period
  - future target-derived flags created after observing demand
```

The safest implementation habit is to shift before you roll. A trailing rolling mean for target forecasting should usually start from `y.shift(1).rolling(window).mean()`, not from `y.rolling(window).mean()`. The first version uses only completed observations. The second version includes the current target in the feature row, which is direct target leakage for one-step forecasting.

Feature leakage also appears through preprocessing. A standard scaler fitted on the full series learns the validation-period mean and variance. A target encoder fitted before the split learns validation outcomes for categories that should still be unseen. An imputer fitted across the full timeline can learn future seasonal levels. These errors are not fixed by choosing a different regressor, because the regressor receives already-contaminated features. Time-aware pipelines fit preprocessing inside each training window.

Calendar and Fourier features are safer because their future values are known. The model can know that a future timestamp is a Monday, a month end, or part of a smooth yearly cycle. This is one reason tree-based forecasting often combines target lags with calendar features. The lag features carry recent state, while calendar features let the model condition that state on recurring context. The model still needs a chronological backtest because known future calendar does not protect against leaked target history.

Global models need careful identifiers. A series ID can help the model learn that one store is usually larger than another, but a high-cardinality identifier can also let the model memorize series-specific averages without adapting to recent behavior. Add identifiers deliberately, compare against local baselines, and inspect performance by segment. Aggregate metrics can hide that the global model works for large stable series while failing for small, intermittent, or recently launched series.

Recursive tree forecasts deserve special scrutiny. At horizon one, every lag comes from observed history. At horizon two, some lag values may come from the model's own horizon-one prediction. By horizon twelve, a monthly recursive forecast can be standing on a stack of previous predictions. This is not leakage, but it is a source of error accumulation. Your backtest should implement recursion the same way production will, otherwise the reported horizon accuracy is not meaningful.

Direct forecasting avoids that specific feedback loop by training horizon-specific targets. A direct six-month model learns to predict six months ahead from features known at the origin. It may be more stable at long horizons, but it needs enough examples for each horizon and more operational machinery. Many teams compare recursive, direct, and hybrid strategies on the same folds, then choose the simplest strategy that performs reliably at the horizon that matters.

## Backtesting and Evaluation Without Leakage

Forecasting validation should replay history. Pick several forecast origins, train using data available up to each origin, forecast the next horizon, and score the forecast against the observations that later arrived. This is called walk-forward validation, rolling-origin evaluation, or backtesting. The core idea is the same: your validation procedure should look like production forecasting repeated at earlier dates.

Random k-fold validation is invalid for most forecasting tasks because it lets later observations influence models evaluated on earlier observations. `TimeSeriesSplit` is a safer scikit-learn primitive because each split trains on earlier rows and tests on later rows. Expanding-window validation grows the training set over time. Sliding-window validation keeps a fixed-width training window so old regimes eventually fall out.

```text
expanding window:
  train [====] test [--]
  train [========] test [--]
  train [============] test [--]

sliding window:
  train [====] test [--]
       train [====] test [--]
            train [====] test [--]
```

Multi-step forecasting adds another design choice. A recursive strategy trains a one-step model, predicts the next step, appends that prediction to history, and repeats. It is simple, but errors compound because later steps depend on earlier predictions. A direct strategy trains a separate model for each horizon, such as one model for one month ahead and another model for six months ahead. It can reduce error accumulation, but it increases model count and data requirements.

Metrics should match the decision. MAE is easy to explain and robust to occasional large errors. RMSE penalizes large misses more strongly, which matters when a few severe under-forecasts are costly. MAPE is intuitive as a percentage, but it breaks down near zero and can overweight tiny denominators. sMAPE tries to soften that problem, but it still has edge cases when both actual and predicted values are near zero.

MASE compares a model against a naive baseline using scaled absolute error. For seasonal data, the denominator often comes from a seasonal-naive forecast such as "use the value from the same month last year." This makes MASE useful across series with different units because it asks whether the model improves over a simple rule that a serious forecaster should beat.

Baselines are not optional. A naive baseline uses the most recent value. A seasonal-naive baseline uses the value from the previous season. A moving-average baseline uses recent history. If a complex model cannot beat these baselines in a leakage-safe backtest, the correct conclusion is not "tune harder" by default. The correct conclusion is that the added complexity has not yet earned its operational cost.

Backtest results should be read by horizon, segment, and time period. A single average error can hide that the model is excellent one step ahead but weak at longer horizons. It can also hide that a model performs well for high-volume series while failing for low-volume series where decisions are still important. Reporting a table by fold and horizon makes this visible. A plot of error over forecast origin often reveals regime changes faster than another aggregate metric.

Do not let the validation window become a new test set by repeated manual tuning. If you inspect every backtest fold, change features, rerun, and keep the best version, you are still adapting to validation evidence. That may be acceptable during development, but you need a final untouched holdout period or a later live shadow evaluation before claiming generalization. Forecasting projects are especially vulnerable because the most recent period is tempting to reuse many times.

Retraining cadence belongs in evaluation too. A model retrained daily may adapt quickly but cost more to operate and expose the pipeline to more data-quality incidents. A model retrained monthly may be stable but stale after sudden demand shifts. Your backtest can simulate cadence by refitting at each origin, every few origins, or with a fixed window. The best cadence is not just the lowest error; it is the one the team can run reliably when data arrives late and forecasts are needed on schedule.

Finally, compare models by decision impact, not only by metric decimals. A small RMSE improvement may not matter if staffing decisions are rounded to whole shifts. A slightly worse MAE may be preferable if prediction intervals are better calibrated and the model is easier to explain. Forecasting supports decisions under uncertainty, so the winning model is the one that improves the decision process under a realistic operating contract.

## Choosing a Forecasting Workflow

Start with the forecast contract before choosing a library. Write down the decision date, the horizon, the update frequency, the unit of action, and the metric that changes the downstream decision. A forecast for next hour's queue length, next month's inventory order, and next quarter's hiring plan may all use temporal data, but they have different latency, uncertainty, aggregation, and failure-cost requirements.

Then build a ladder of baselines. Use naive, seasonal-naive, and moving-average forecasts first because they reveal whether the series contains easy persistence or seasonal structure. Add exponential smoothing or SARIMA when the signal looks mostly univariate and interpretable. Add tree-based regression when known calendar effects, lag interactions, many related series, or exogenous drivers are likely to matter. Each rung should beat the previous rung in the same walk-forward protocol.

Finally, make the production feature boundary explicit. Store which raw fields are available at the forecast origin, which future calendar fields are scheduled, and which fields would require a separate upstream forecast. This boundary is more durable than any single model choice. It prevents subtle leakage when the project later adds promotions, weather, prices, inventory, or incident labels to improve accuracy.

## Practical Concerns

Missing timestamps are different from missing values. If an hourly system has no row for 03:00, you need to know whether the metric was genuinely absent, the collector failed, or the value should be zero. Resampling to a regular frequency makes gaps visible, but filling them requires domain rules. Forward fill, interpolation, and zero fill each encode a different claim about the world.

Irregular sampling complicates lag features and seasonal periods. A lag of one row is not the same as a lag of one hour when event timing is irregular. Some problems should be resampled to a regular grid before forecasting. Others are better modeled as event processes, survival problems, or point processes rather than forced into a fixed interval forecast.

Multiple and hierarchical series introduce reconciliation questions. Store-level forecasts may need to sum to regional forecasts, and product-level forecasts may need to sum to category forecasts. You can fit independent local models, global models across related series, or hierarchical approaches that reconcile forecasts across levels. The right choice depends on data volume, similarity across series, and the business decision attached to each level.

Prediction intervals are often more useful than point forecasts. Staffing, inventory, capacity planning, and SLO risk decisions need ranges because being slightly wrong is normal. ARIMA and exponential smoothing can provide model-based intervals. Tree-based models often use quantile losses, bootstrapped residuals, conformal prediction, or simulation around recursive forecasts. The interval method should be validated with coverage checks, not merely plotted.

Ecosystems such as `sktime` and `darts` provide forecasting abstractions, model wrappers, backtesting utilities, and probabilistic forecast interfaces. They are peers in the Python forecasting ecosystem rather than a strict ranking. Learn the concepts in this module first, because the same leakage rules, baselines, horizon choices, and metric tradeoffs apply whichever library owns the API.

Forecast monitoring should separate data freshness, feature validity, point error, interval coverage, and decision impact. A forecast can fail because the data feed stopped, because a holiday table was not updated, because the model drifted, or because the downstream planner changed how forecasts are consumed. These failures require different responses. One alert named "forecast bad" is too vague to drive a useful operational action.

Coverage monitoring is especially important when teams publish prediction intervals. If an eighty percent interval only contains the actual value half the time, the interval is underestimating uncertainty. If it contains the actual value nearly all the time, it may be too wide to guide decisions. Coverage should be checked by horizon and segment because long-horizon intervals often degrade before short-horizon intervals, and sparse series may have very different error behavior.

Forecasts also need a fallback plan. If the model job fails at the forecast origin, the system should still produce a reasonable baseline such as seasonal naive, last known plan, or a conservative capacity rule. This fallback is not glamorous, but it prevents a modeling incident from becoming an operations incident. The fallback should be backtested and documented so teams understand what happens when the preferred model is unavailable.

Retraining should be boring by design. Store the training window, forecast origin, model parameters, feature definitions, package versions, and validation summary with each model artifact. When a forecast changes unexpectedly, these records let you distinguish model behavior from data changes and dependency changes. Without that lineage, teams waste time comparing screenshots, rerunning notebooks, and guessing which version generated a decision.

Human override deserves a clear contract too. Planners often know one-off events that are not represented in historical data, such as a migration freeze, a facility closure, or a planned campaign. Overrides can improve decisions, but they should be recorded separately from model forecasts. Mixing them into the target history without annotation teaches future models that the override was observed demand, which can create confusing feedback loops.

A mature forecasting workflow therefore has three products, not one. It produces a point forecast for the expected path, an uncertainty estimate for planning risk, and an audit trail explaining what information was available at the origin. The model is only one part of that workflow. The engineering discipline around data availability, validation, fallbacks, and monitoring is what makes the forecast usable repeatedly.

The final practical habit is to keep a forecast review notebook or report that starts from the business decision rather than the model class. Each review should show the forecast origin, horizon, baseline comparison, interval coverage, largest misses, and any data-quality anomalies for that period. This turns model maintenance into a repeatable operating review. It also helps new team members understand why a simple seasonal baseline may stay in production, why a more accurate model was rejected, or why a retraining rule changed after a regime shift.

Treat every large miss as a classification exercise before treating it as a modeling failure. Some misses are predictable because a known feature was unavailable, some are data incidents, some are structural breaks, and some are ordinary irreducible noise. Labeling misses this way turns error analysis into a backlog. The team can then decide whether to improve data contracts, add known-event features, adjust retraining cadence, or simply widen intervals around inherently volatile periods. This keeps model work connected to the operational cause of error.

## Did You Know?

- **A seasonal-naive baseline can be hard to beat**: monthly, weekly, and daily series often contain enough recurring structure that "same period last season" is a serious benchmark rather than a toy.
- **ADF and KPSS ask opposite stationarity questions**: ADF looks for evidence against a unit root, while KPSS looks for evidence against stationarity under the chosen regression setting.
- **Centered windows are usually leakage in forecasting**: a centered rolling mean for today's target uses observations after today, so it belongs in analysis plots more often than in production features.
- **Forecast intervals need their own validation**: a model can have acceptable point error while its intervals are too narrow, which creates false confidence for capacity and risk decisions.

## Common Mistakes

| Mistake | Problem | Solution |
|---|---|---|
| Randomly shuffling time series rows before validation | The model trains on future observations and reports an error estimate that cannot happen in production. | Use chronological holdouts, `TimeSeriesSplit`, or explicit walk-forward backtests with forecast origins. |
| Computing rolling features before shifting the target | The current target leaks into its own feature row, especially with means, maxima, and standard deviations. | Build target-derived features from shifted history, such as `y.shift(1).rolling(window).mean()`. |
| Fitting scalers or imputers on the full dataset | Validation-period distribution information changes training-period transformations and inflates backtest scores. | Fit transformations inside each fold using training data only, preferably through a time-aware pipeline. |
| Treating `auto_arima` as final model selection | Automated order search can optimize information criteria without proving operational forecast quality. | Use it to propose candidates, then inspect residuals and compare against baselines in walk-forward validation. |
| Ignoring the forecast horizon | A model that works one step ahead may fail badly twelve steps ahead because recursive errors compound. | Score the exact horizon the business needs and compare direct, recursive, and baseline strategies. |
| Using MAPE when actuals approach zero | Percentage errors explode or become undefined, making the metric unstable and sometimes misleading. | Prefer MAE, RMSE, sMAPE with caution, or MASE against a meaningful naive baseline. |
| Filling missing timestamps without diagnosis | A fill rule can convert collector outages, true zeros, and irregular events into the same artificial pattern. | Reindex to the expected frequency, inspect gaps, and document the domain-specific fill rule. |
| Shipping point forecasts without intervals | Planners cannot see uncertainty, so they may treat a fragile forecast as a promise. | Add prediction intervals and validate empirical coverage across backtest folds. |

## Quiz

1. A team builds a daily demand model with `TimeSeriesSplit`, but creates a feature using `sales.rolling(7, center=True).mean()` before splitting. What is wrong?

<details><summary>Answer</summary>

The centered rolling window uses observations on both sides of each timestamp, so feature rows near the forecast date contain future target information. The split object cannot repair leakage that was already created before validation. The feature should be based on shifted trailing history, such as `sales.shift(1).rolling(7).mean()`, inside the training window for each fold.

</details>

2. A monthly series has a strong upward trend and a repeating annual pattern. After first differencing, the ACF still spikes at lag 12. Which model family and terms would you investigate first?

<details><summary>Answer</summary>

A SARIMA candidate is reasonable because the series has both nonseasonal trend behavior and seasonal dependence. First differencing suggests `d=1`, while the lag-12 ACF spike suggests seasonal AR, seasonal MA, or seasonal differencing terms with `s=12`. You would compare a small set of plausible `(p, d, q)(P, D, Q, 12)` orders, inspect residuals, and backtest against a seasonal-naive baseline.

</details>

3. Why is random k-fold cross-validation usually invalid for time series forecasting?

<details><summary>Answer</summary>

Random k-fold validation breaks temporal ordering. Some folds train on observations that happen after the validation observations, which means the model benefits from future regimes, future transformations, and future target patterns. Forecasting validation must replay the production situation by training on the past and evaluating on later timestamps.

</details>

4. A staffing forecast has actual ticket counts near zero on quiet nights. The model team reports excellent MAPE for normal days but extreme percentage errors overnight. What should they change?

<details><summary>Answer</summary>

MAPE is unstable near zero because a small absolute miss can become a huge percentage error or undefined value. The team should evaluate with MAE or RMSE for absolute staffing impact, consider sMAPE only with caution, and use MASE against a naive or seasonal-naive baseline so the score remains interpretable across different volume levels.

</details>

5. When is a holiday feature legitimate, and when does it become leakage?

<details><summary>Answer</summary>

A holiday feature is legitimate when it comes from a calendar known before the forecast origin, such as next year's public holidays or a scheduled business closure. It becomes leakage when the feature is derived from future observed target behavior, such as labeling a demand spike as a holiday-like event only after seeing the validation period.

</details>

6. A tree-based forecaster beats ARIMA one step ahead but loses badly at a six-month horizon. What design issue should you investigate?

<details><summary>Answer</summary>

The first suspect is horizon strategy. A recursive tree model can compound its own errors because each later prediction depends on earlier predicted values. The team should score each horizon separately and compare recursive forecasting with direct horizon-specific models, seasonal-naive baselines, and possibly simpler statistical models that encode seasonal structure more directly.

</details>

7. A product team has thousands of short store-product series. Why might a global model be useful, and what extra validation concern does it create?

<details><summary>Answer</summary>

A global model can share information across related series, which helps when individual histories are too short for reliable local models. The validation concern is that every series still needs chronological evaluation. The model may learn across series, but it must not train on future timestamps for the same series being evaluated, and aggregate metrics should not hide failure on sparse or high-value series.

</details>

## Hands-On Exercise

**Task**: Build an ARIMA/SARIMA forecaster and a tree-based recursive forecaster on bundled CO2 data, then compare both against a seasonal-naive baseline with walk-forward validation.

This lab uses `statsmodels.datasets.co2`, so it does not download external data. It assumes the forecasting libraries are installed in your environment. If you are using the project virtual environment, install any missing optional packages with an explicit venv command such as `.venv/bin/python -m pip install statsmodels scikit-learn pandas numpy`.

### Steps

- [ ] Load the bundled monthly CO2 series and make the timestamp index regular.
- [ ] Define a seasonal-naive baseline that repeats the last observed annual cycle.
- [ ] Fit a SARIMA-style `statsmodels` ARIMA model inside each walk-forward fold.
- [ ] Fit a recursive `HistGradientBoostingRegressor` using lag, rolling, and calendar features from training history only.
- [ ] Score all three approaches with MAE, RMSE, and MASE across identical forecast horizons.
- [ ] Inspect whether either learned model beats the seasonal-naive baseline enough to justify its complexity.

```python
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import TimeSeriesSplit
from statsmodels.datasets import co2
from statsmodels.tsa.arima.model import ARIMA


def load_monthly_co2():
    series = (
        co2.load_pandas()
        .data["co2"]
        .resample("MS")
        .mean()
        .interpolate("time")
        .asfreq("MS")
    )
    return series.loc["1970":].astype(float)


def seasonal_naive(train, steps, season_length=12):
    last_season = train.iloc[-season_length:].to_numpy()
    repeats = int(np.ceil(steps / season_length))
    return np.tile(last_season, repeats)[:steps]


def make_training_frame(y):
    frame = pd.DataFrame({"y": y})
    frame["lag_1"] = frame["y"].shift(1)
    frame["lag_12"] = frame["y"].shift(12)
    frame["roll_3"] = frame["y"].shift(1).rolling(3).mean()
    frame["roll_12"] = frame["y"].shift(1).rolling(12).mean()
    month = frame.index.month
    frame["month_sin"] = np.sin(2 * np.pi * month / 12)
    frame["month_cos"] = np.cos(2 * np.pi * month / 12)
    return frame.dropna()


def make_future_row(history, timestamp):
    values = np.asarray(history, dtype=float)
    month = timestamp.month
    return pd.DataFrame(
        {
            "lag_1": [values[-1]],
            "lag_12": [values[-12]],
            "roll_3": [values[-3:].mean()],
            "roll_12": [values[-12:].mean()],
            "month_sin": [np.sin(2 * np.pi * month / 12)],
            "month_cos": [np.cos(2 * np.pi * month / 12)],
        },
        index=[timestamp],
    )


def recursive_tree_forecast(train, test_index):
    training_frame = make_training_frame(train)
    X_train = training_frame.drop(columns="y")
    y_train = training_frame["y"]

    model = HistGradientBoostingRegressor(
        max_iter=200,
        learning_rate=0.05,
        l2_regularization=0.01,
        random_state=7,
    )
    model.fit(X_train, y_train)

    history = list(train.to_numpy())
    predictions = []
    for timestamp in test_index:
        row = make_future_row(history, timestamp)
        prediction = float(model.predict(row)[0])
        predictions.append(prediction)
        history.append(prediction)
    return np.asarray(predictions)


def arima_forecast(train, steps):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fitted = ARIMA(
            train,
            order=(1, 1, 1),
            seasonal_order=(1, 0, 1, 12),
            enforce_stationarity=False,
            enforce_invertibility=False,
        ).fit()
    return np.asarray(fitted.forecast(steps=steps))


def rmse(y_true, y_pred):
    errors = np.asarray(y_true) - np.asarray(y_pred)
    return float(np.sqrt(np.mean(errors**2)))


def mase(y_true, y_pred, train, season_length=12):
    train_values = np.asarray(train, dtype=float)
    denominator = np.mean(
        np.abs(train_values[season_length:] - train_values[:-season_length])
    )
    return float(mean_absolute_error(y_true, y_pred) / denominator)


series = load_monthly_co2()
horizon = 12
splitter = TimeSeriesSplit(n_splits=4, test_size=horizon)

rows = []
for fold, (train_idx, test_idx) in enumerate(splitter.split(series), start=1):
    train = series.iloc[train_idx]
    test = series.iloc[test_idx]

    forecasts = {
        "seasonal_naive": seasonal_naive(train, len(test)),
        "arima_sarima": arima_forecast(train, len(test)),
        "tree_recursive": recursive_tree_forecast(train, test.index),
    }

    for model_name, prediction in forecasts.items():
        rows.append(
            {
                "fold": fold,
                "model": model_name,
                "MAE": mean_absolute_error(test, prediction),
                "RMSE": rmse(test, prediction),
                "MASE": mase(test, prediction, train),
            }
        )

results = pd.DataFrame(rows)
print(results.groupby("model")[["MAE", "RMSE", "MASE"]].mean().round(3))
```

### Success Criteria

- [ ] The code prints one aggregate metric row for `seasonal_naive`, `arima_sarima`, and `tree_recursive`.
- [ ] The ARIMA model is fitted separately inside each fold and never sees validation observations during fitting.
- [ ] The tree forecaster uses lagged and trailing features only, then recursively feeds its own predictions for multi-step forecasting.
- [ ] Your written interpretation names the best model, the baseline gap, and whether the improvement justifies the added complexity.

### Verification

```bash
.venv/bin/python time_series_backtest.py
```

The exact numeric scores can differ across library versions and optimization settings. The important verification is structural: the same walk-forward folds score all models, the seasonal-naive baseline is present, and the learned models never train on their validation windows.

## Sources

- [statsmodels PyPI project page](https://pypi.org/project/statsmodels/) - release metadata and high-level package scope.
- [statsmodels Time Series Analysis user guide](https://www.statsmodels.org/stable/tsa.html) - `statsmodels.tsa` model families and forecasting tools.
- [statsmodels ARIMA API](https://www.statsmodels.org/stable/generated/statsmodels.tsa.arima.model.ARIMA.html) - ARIMA and seasonal ARIMA interface details.
- [statsmodels ExponentialSmoothing API](https://www.statsmodels.org/stable/generated/statsmodels.tsa.holtwinters.ExponentialSmoothing.html) - Holt-Winters level, trend, and seasonal parameters.
- [statsmodels STL decomposition API](https://www.statsmodels.org/stable/generated/statsmodels.tsa.seasonal.STL.html) - seasonal-trend decomposition reference.
- [statsmodels ADF/KPSS stationarity notebook](https://www.statsmodels.org/stable/examples/notebooks/generated/stationarity_detrending_adf_kpss.html) - stationarity test interpretation examples.
- [statsmodels ACF API](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.acf.html) and [PACF API](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.pacf.html) - autocorrelation and partial autocorrelation functions.
- [pmdarima `auto_arima` documentation](https://alkaline-ml.com/pmdarima/modules/generated/pmdarima.arima.auto_arima.html) - automated ARIMA order search behavior.
- [Prophet PyPI project page](https://pypi.org/project/prophet/) and [Prophet quick start](https://facebook.github.io/prophet/docs/quick_start.html) - package metadata and Python usage.
- [Prophet GitHub release notes](https://github.com/facebook/prophet) - maintained project repository and changelog.
- [scikit-learn `TimeSeriesSplit` documentation](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html) - time-ordered cross-validation behavior.
- [scikit-learn `HistGradientBoostingRegressor` documentation](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingRegressor.html) - histogram gradient boosting regressor API.
- [scikit-learn 1.9 release notes](https://scikit-learn.org/stable/whats_new/v1.9.html) - versioned library reference for the dated snapshot.
- [XGBoost release notes](https://xgboost.readthedocs.io/en/stable/changes/index.html) - versioned release reference for tree-based forecasting options.
- [LightGBM documentation](https://lightgbm.readthedocs.io/en/latest/) - gradient boosting framework reference.
- [sktime forecasting API](https://www.sktime.net/en/latest/api_reference/forecasting.html) and [Darts documentation](https://unit8co.github.io/darts/) - Python forecasting ecosystem references.

## Next Module

Next, continue to [Module 2.1: Class Imbalance & Cost-Sensitive Learning](../module-2.1-class-imbalance-and-cost-sensitive-learning/) to handle target distributions where rare outcomes and asymmetric costs change what "good" model behavior means.
