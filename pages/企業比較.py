import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="企業比較", layout="wide")
st.title("企業比較")

# 初期設定されたティッカー
default_tickers = ["4063.T", "3407.T", "4188.T", "4183.T", "4005.T"]

# 追加ティッカーの入力欄
ticker_input = st.text_area(
    "追加で企業コードをカンマ区切りで入力してください（例：9984, 7203）", value=""
)
# 入力をリストに変換
additional_tickers = [f"{code.strip()}.T" for code in ticker_input.split(',') if code.strip()]

for ticker in additional_tickers:
    info = yf.Ticker(ticker).info
    name = info.get('shortName', ticker) 
    st.write(f"{ticker}：{name}")


# 初期ティッカー + 入力ティッカーを統合（重複排除）
all_tickers = list(dict.fromkeys(default_tickers + additional_tickers))  # 順序を保ったまま重複削除

# Tickerごとに企業名を取得
ticker_name_dict = {}
for ticker_symbol in all_tickers:
    try:
        info = yf.Ticker(ticker_symbol).info
        name = info.get('shortName', ticker_symbol)  # 取得できない場合はティッカーで代用
        ticker_name_dict[ticker_symbol] = name
    except Exception as e:
        ticker_name_dict[ticker_symbol] = ticker_symbol
        st.warning(f"{ticker_symbol} の企業名取得でエラー: {e}")


# 結果を格納するリスト
all_financials = []

for ticker_symbol in all_tickers:
    ticker = yf.Ticker(ticker_symbol)
    try:
        # 財務データ取得
        financials = ticker.financials.T[['Total Revenue', 'Gross Profit']]
        financials = financials.dropna()  # 欠損行を除外
        financials['Gross Margin'] = financials['Gross Profit'] / financials['Total Revenue'] * 100
        financials['Ticker'] = ticker_symbol
        financials['Date'] = financials.index
        all_financials.append(financials)
    except Exception as e:
        print(f"{ticker_symbol}のデータ取得でエラー: {e}")

# リストをDataFrameに結合
combined_df = pd.concat(all_financials).reset_index(drop=True)

# 売上高増加率（前年比）を計算
combined_df.sort_values(by=['Ticker', 'Date'], inplace=True)
combined_df['Revenue Growth Rate'] = combined_df.groupby('Ticker')['Total Revenue'].pct_change() * 100

# 平均値の計算
mean_df = combined_df.groupby('Ticker')[['Gross Margin', 'Revenue Growth Rate']].mean().reset_index()

# 企業名列を追加
mean_df['Company Name'] = mean_df['Ticker'].map(ticker_name_dict)

# 散布図表示
if not mean_df.empty:
    fig = px.scatter(mean_df,
                     x='Revenue Growth Rate',
                     y='Gross Margin',
                     color='Company Name',
                     hover_name='Ticker',
                     title='売上高増加率と売上総利益率（粗利率）_4年平均値',
                     labels={
                         'Revenue Growth Rate': '売上高増加率（%）',
                         'Gross Margin': '粗利率（%）'
                     })
    fig.update_traces(marker=dict(size=10), selector=dict(mode='markers'))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("有効なデータがありません。")


# 列名を日本語に変換
mean_df_ = mean_df.rename(columns={
    'Ticker': '企業コード',
    'Gross Margin': '粗利率_平均（％）',
    'Revenue Growth Rate':'売上高増加率_平均（％）',
    'Company Name':'企業名'
})

st.dataframe(mean_df_)