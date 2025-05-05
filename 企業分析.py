# ============================================
# Streamlit × yfinance 企業分析 Webアプリ
# ============================================

# ------------------------------------------------------------

import time
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

from requests.exceptions import HTTPError


st.set_page_config(page_title="企業分析アプリ", layout="wide")

raw_input = st.text_input("企業コード (例: 3405)", value="3405")
num = f"{raw_input.strip()}.T"
ticker = yf.Ticker(num) 

try:
    company_name = ticker.info["longName"]
    st.subheader(f"{num}：{company_name}")
except KeyError:
    st.subheader(f"{num}：企業名を取得できませんでした。")

financials = ticker.financials.T[['Total Revenue', 'Gross Profit']]
financials['Gross Margin'] = financials["Gross Profit"] / financials["Total Revenue"]*100

# 列名を日本語に変換
financials_ = financials.rename(columns={
    'Total Revenue': '売上高',
    'Gross Profit': '売上総利益（粗利）',
    'Gross Margin': '粗利率（％）'
})

# 表示
st.dataframe(financials_)

# 年月の表示を列名（日付→年表記など）に変換（例: 2021-12-31 → 2021）
financials.index = pd.to_datetime(financials.index).year.astype(int)

# プロット作成
fig = make_subplots(specs=[[{"secondary_y": True}]])

# 売上高
fig.add_trace(
    go.Bar(
        x=financials.index,
        y=financials["Total Revenue"],
        name="売上高",
    ),
    secondary_y=False,
)

# 売上総利益
fig.add_trace(
    go.Bar(
        x=financials.index,
        y=financials["Gross Profit"],
        name="売上総利益",
    ),
    secondary_y=False,
)

# 粗利率（%）
fig.add_trace(
    go.Scatter(
        x=financials.index,
        y=financials["Gross Margin"],
        name="粗利率（%）",
        mode="lines+markers",
        line=dict(dash="solid", color='red')
    ),
    secondary_y=True,
)

# レイアウト調整
fig.update_layout(
    title_text="売上高・売上総利益・粗利率の推移",
    barmode='group',
    xaxis_title="年度",
    legend_title="項目",
    height=600
)

fig.update_xaxes(
    tickmode='linear',
    dtick=1,
    tickformat='d'
)

fig.update_yaxes(title_text="金額（円）", secondary_y=False)
fig.update_yaxes(title_text="粗利率（%）", secondary_y=True)

st.plotly_chart(fig, use_container_width=True)


# 株価データ取得・整形
hist = ticker.history(period="max")
hist.reset_index(inplace=True)

# タイムゾーン情報を削除（重要！）
hist["Date"] = hist["Date"].dt.tz_localize(None)

# 期間指定（2年前～今日）
today = pd.to_datetime("today")
default_start = today - pd.DateOffset(years=2)

start_date = st.date_input("表示開始日", value=default_start.date())
end_date = st.date_input("表示終了日", value=today.date())

# 期間でフィルタ
mask = (hist["Date"] >= pd.to_datetime(start_date)) & (hist["Date"] <= pd.to_datetime(end_date))
hist_filtered = hist.loc[mask].copy()

# 移動平均線の計算
hist_filtered["MA25"] = hist_filtered["Close"].rolling(window=25).mean()
hist_filtered["MA50"] = hist_filtered["Close"].rolling(window=50).mean()

# プロット作成
fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                    vertical_spacing=0.03, row_heights=[0.7, 0.3])

# ローソク足
fig.add_trace(
    go.Candlestick(
        x=hist_filtered["Date"],
        open=hist_filtered["Open"],
        high=hist_filtered["High"],
        low=hist_filtered["Low"],
        close=hist_filtered["Close"],
        name="ローソク足"
    ),
    row=1, col=1
)

# 移動平均線
fig.add_trace(
    go.Scatter(
        x=hist_filtered["Date"],
        y=hist_filtered["MA25"],
        mode="lines",
        line=dict(color='blue', width=1),
        name="MA25"
    ),
    row=1, col=1
)
fig.add_trace(
    go.Scatter(
        x=hist_filtered["Date"],
        y=hist_filtered["MA50"],
        mode="lines",
        line=dict(color='green', width=1),
        name="MA50"
    ),
    row=1, col=1
)

# 出来高
fig.add_trace(
    go.Bar(
        x=hist_filtered["Date"],
        y=hist_filtered["Volume"],
        name="出来高"
    ),
    row=2, col=1
)

# レイアウト
fig.update_layout(
    title=f"{company_name} の株価チャート",
    height=700,
    showlegend=True,
    xaxis_rangeslider_visible=True  # ここでスライダー表示
)

st.plotly_chart(fig, use_container_width=True)

st.dataframe(hist[::-1])  # 一番下の行が先頭に表示される