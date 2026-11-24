#!/usr/bin/env python3
from pathlib import Path
import hashlib

import pandas as pd
import streamlit as st
import math
from pysentimiento import create_analyzer
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent
SALES_CSV = ROOT / 'mock_sales.csv'
REVIEWS_CSV = ROOT / 'mock_reviews_large.csv'
LABELS = {'POS': 'positivo', 'NEG': 'negativo', 'NEU': 'neutral'}

# Detecta nuevos csv y vuelve a generar los graficos
def file_cache_key(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

st.set_page_config(page_title='Vintara | IA Analytics', page_icon='📊', layout='wide')
st.title('Vintara | IA Analytics')
st.caption('Módulo de Business Intelligence.')


@st.cache_data
def get_sales_data(file_hash):
    data = pd.read_csv(SALES_CSV)
    data = data[data['order_status'].isin(['delivered', 'completed'])].copy()
    data['order_date'] = pd.to_datetime(data['order_date'])
    data['month'] = data['order_date'].dt.to_period('M').dt.to_timestamp()
    first_month = data['month'].min()
    data['month_index'] = ((data['month'].dt.year - first_month.year) * 12
                           + data['month'].dt.month - first_month.month + 1)
    data = data.groupby(['month', 'month_index', 'product_id', 'product'], as_index=False).agg(
        units=('units', 'sum'), unit_price_crc=('unit_price_crc', 'mean'),
        discount_pct=('discount_pct', 'mean'))
    data['product_code'] = data['product'].astype('category').cat.codes
    month_number = data['month'].dt.month
    radians = month_number * 2 * math.pi / 12
    data['month_sin'] = radians.map(math.sin)
    data['month_cos'] = radians.map(math.cos)
    return data


def make_features(data):
    return data[['month_index', 'product_code', 'unit_price_crc', 'discount_pct', 'month_sin', 'month_cos']]


@st.cache_data
def demand_forecast(file_hash):
    history = get_sales_data(file_hash).sort_values('month_index')
    model = RandomForestRegressor(n_estimators=120, max_depth=5, random_state=42)
    model.fit(make_features(history), history['units'])

    recent = history[history['month_index'] > history['month_index'].max() - 6]
    products = (recent.groupby(['product_id', 'product', 'product_code'], as_index=False)
                .agg(unit_price_crc=('unit_price_crc', 'mean'),
                     discount_pct=('discount_pct', 'mean')))
    last_month = history['month'].max()
    last_index = int(history['month_index'].max())
    forecasts = []
    for offset, month in enumerate(pd.date_range(last_month + pd.offsets.MonthBegin(1), periods=3, freq='MS'), 1):
        future = products.copy()
        future['month'] = month
        future['month_index'] = last_index + offset
        radians = month.month * 2 * math.pi / 12
        future['month_sin'] = math.sin(radians)
        future['month_cos'] = math.cos(radians)
        future['predicted_units'] = model.predict(make_features(future)).clip(min=0).round(0).astype(int)
        forecasts.append(future[['product_id', 'product', 'month', 'predicted_units']])
    return pd.concat(forecasts, ignore_index=True)


def customer_snapshot(sales, cutoff, horizon_days=90):
    history = sales[(sales['order_date'] < cutoff)
                    & (sales['order_date'] >= cutoff - pd.Timedelta(days=365))]
    history = history[history['order_status'].isin(['delivered', 'completed'])]
    if history.empty:
        return pd.DataFrame()
    history = history.sort_values('order_date')
    grouped = history.groupby('customer_id')
    snapshot = grouped.agg(
        orders_12m=('order_id', 'nunique'), units_12m=('units', 'sum'),
        revenue_12m=('revenue_crc', 'sum'), product_variety=('product_id', 'nunique'),
        last_purchase=('order_date', 'max'), avg_discount=('discount_pct', 'mean'),
        customer_segment=('customer_segment', 'last'), province=('province', 'last'))
    snapshot['days_since_purchase'] = (cutoff - snapshot['last_purchase']).dt.days
    future = sales[(sales['order_date'] >= cutoff)
                   & (sales['order_date'] < cutoff + pd.Timedelta(days=horizon_days))
                   & sales['order_status'].isin(['delivered', 'completed'])]
    future_customers = set(future['customer_id'])
    snapshot['repeat_purchase'] = snapshot.index.isin(future_customers).astype(int)
    return snapshot.drop(columns='last_purchase').reset_index()


@st.cache_data
def repurchase_by_segment(file_hash):
    sales = pd.read_csv(SALES_CSV)
    sales['order_date'] = pd.to_datetime(sales['order_date'])
    latest = sales['order_date'].max().normalize()
    horizon_days = 90
    score_cutoff = latest - pd.Timedelta(days=horizon_days - 1)

    first_date = sales['order_date'].min().normalize()
    train_cutoffs = pd.date_range(first_date + pd.Timedelta(days=365),
                                  score_cutoff - pd.Timedelta(days=horizon_days), freq='90D')
    snapshots = [customer_snapshot(sales, cutoff, horizon_days) for cutoff in train_cutoffs]
    training = pd.concat([row for row in snapshots if not row.empty], ignore_index=True)
    scoring = customer_snapshot(sales, score_cutoff, horizon_days)
    if training.empty or scoring.empty or training['repeat_purchase'].nunique() < 2:
        raise ValueError('No hay suficientes casos de recompra para entrenar el modelo mock.')

    numeric = ['orders_12m', 'units_12m', 'revenue_12m', 'product_variety',
               'days_since_purchase', 'avg_discount']
    categorical = ['customer_segment', 'province']
    train_x = pd.get_dummies(training[numeric + categorical], columns=categorical, dtype=float)
    score_x = pd.get_dummies(scoring[numeric + categorical], columns=categorical, dtype=float)
    score_x = score_x.reindex(columns=train_x.columns, fill_value=0)
    model = make_pipeline(StandardScaler(), MLPClassifier(
        hidden_layer_sizes=(16, 8), max_iter=1200, alpha=0.05,
        early_stopping=True, random_state=42))
    model.fit(train_x, training['repeat_purchase'])
    scoring['estimated_probability'] = model.predict_proba(score_x)[:, list(model.classes_).index(1)]
    summary = scoring.groupby('customer_segment', as_index=False).agg(
        estimated_probability=('estimated_probability', 'mean'),
        observed_repeat_rate=('repeat_purchase', 'mean'), customers=('customer_id', 'count'))
    summary['estimated_probability'] *= 100
    summary['observed_repeat_rate'] *= 100
    return summary, score_cutoff, latest


@st.cache_resource
def sentiment_analyzer():
    return create_analyzer(task='sentiment', lang='es')


@st.cache_data
def sentiment_data(file_hash):
    reviews = pd.read_csv(REVIEWS_CSV)
    analyzer = sentiment_analyzer()
    comments = reviews['comment'].astype(str).tolist()
    outputs = []
    for start in range(0, len(comments), 64):
        batch = analyzer.predict(comments[start:start + 64])
        outputs.extend(batch if isinstance(batch, list) else [batch])
    reviews['sentiment'] = [LABELS[result.output] for result in outputs]
    return reviews


st.header('Machine learning')
st.caption('Ventas reales de los últimos 12 meses y demanda estimada para los siguientes tres.')
sales_key = file_cache_key(SALES_CSV)
ml_forecast = demand_forecast(sales_key)
actual_chart = (get_sales_data(sales_key)
                .groupby('month', as_index=False)['units'].sum().tail(12)
                .rename(columns={'units': 'ventas_reales'}))
future_chart = (ml_forecast.groupby('month', as_index=False)['predicted_units'].sum()
                .rename(columns={'predicted_units': 'unidades_estimadas'}))
forecast_chart = actual_chart.merge(future_chart, on='month', how='outer').sort_values('month')
forecast_chart['month'] = forecast_chart['month'].dt.strftime('%Y-%m')
st.line_chart(forecast_chart, x='month', y=['ventas_reales', 'unidades_estimadas'],
              x_label='Mes', y_label='Unidades')

st.header('Deep learning')
st.caption('Red neuronal que estima si un cliente activo volverá a comprar en los siguientes 90 días, según su historial de compras de los últimos 12 meses.')
repurchase, score_cutoff, latest = repurchase_by_segment(sales_key)
st.bar_chart(repurchase, x='customer_segment',
             y=['estimated_probability', 'observed_repeat_rate'],
             x_label='Segmento de cliente', y_label='Clientes con recompra (%)')
lowest = repurchase.loc[repurchase['estimated_probability'].idxmin()]
portfolio_average = repurchase['estimated_probability'].mean()
if lowest['estimated_probability'] < portfolio_average - 5:
    advice = (f"Recomendación: priorizar una campaña de retención para el segmento "
              f"{lowest['customer_segment']}; la probabilidad estimada de recompra es "
              f"{lowest['estimated_probability']:.1f}%, por debajo del promedio de "
              f"{portfolio_average:.1f}%.")
else:
    advice = 'Recomendación: las probabilidades estimadas son parecidas entre segmentos; mantener las acciones de fidelización actuales.'
st.info(advice)
st.caption(f'Comparación temporal: se estima la recompra desde {score_cutoff:%d/%m/%Y}; compras observadas hasta {latest:%d/%m/%Y}.')

st.header('LLMs / análisis de sentimientos')
st.caption('Esta demostración usa pysentimiento para clasificar texto. Es PLN con un modelo preentrenado, no un LLM generativo.')
reviews = sentiment_data(file_cache_key(REVIEWS_CSV))
sentiment_summary = (reviews.groupby(['product', 'sentiment']).size()
                     .unstack(fill_value=0).reindex(columns=['positivo', 'neutral', 'negativo'], fill_value=0))
st.bar_chart(sentiment_summary.reset_index(), x='product', y=['positivo', 'neutral', 'negativo'],
             x_label='Producto', y_label='Comentarios')
negative_pct = reviews.groupby('product')['sentiment'].apply(lambda values: (values == 'negativo').mean() * 100)
priority = negative_pct.idxmax()
if negative_pct[priority] >= 25:
    advice = f'Recomendación: revisar comentarios y experiencia de entrega de {priority}; tiene {negative_pct[priority]:.0f}% de opiniones negativas en esta muestra.'
else:
    advice = 'Recomendación: mantener el seguimiento de comentarios; ningún producto supera 25% de opiniones negativas en esta muestra.'
st.info(advice)
with st.expander('Ver comentarios mock clasificados'):
    st.dataframe(reviews[['product', 'comment', 'sentiment']], use_container_width=True, hide_index=True)
