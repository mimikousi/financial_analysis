# -*- coding: utf-8 -*-
"""
中国のGDP推移（名目USD）とGDP成長率（年率％）を1980年〜最新年で取得・可視化
データソース：World Bank API
- 名目GDP（Current US$）: NY.GDP.MKTP.CD
- 実質GDP成長率（Annual %）: NY.GDP.MKTP.KD.ZG
"""

import requests
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import seaborn as sns
sns.set(font='IPAexGothic')
import japanize_matplotlib

# ===== 設定 =====
COUNTRY = "CHN"          # 中国
START_YEAR = 1980
# 取りたい指標
INDICATORS = {
    "gdp_usd": "NY.GDP.MKTP.CD",    # 名目GDP（US$）
    "gdp_growth": "NY.GDP.MKTP.KD.ZG",  # 実質GDP成長率（%）
}

def fetch_worldbank_series(country: str, indicator: str, start_year: int) -> pd.Series:
    """World Bank API から指定国・指標の年次データを取得し、pd.Series(year -> value) で返す"""
    current_year = pd.Timestamp.today().year
    url = (
        f"https://api.worldbank.org/v2/country/{country}"
        f"/indicator/{indicator}?date={start_year}:{current_year}"
        f"&format=json&per_page=20000"
    )
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list) or len(data) < 2 or data[1] is None:
        raise ValueError(f"APIレスポンスが不正です: {data[:1]}")
    rows = data[1]

    # JSONをSeriesへ（年→値）。Noneは落とす。年は昇順に。
    s = (
        pd.DataFrame(rows)[["date", "value"]]
        .dropna(subset=["value"])
        .assign(date=lambda df: df["date"].astype(int))
        .sort_values("date")
        .set_index("date")["value"]
    )
    return s

def main():
    # データ取得
    gdp_usd = fetch_worldbank_series(COUNTRY, INDICATORS["gdp_usd"], START_YEAR)
    gdp_growth = fetch_worldbank_series(COUNTRY, INDICATORS["gdp_growth"], START_YEAR)

    # 見やすさのため、GDPは「兆（1e12）米ドル」に換算
    gdp_trillion = gdp_usd / 1e12

    # 年で内部結合（共通年のみプロット）
    df = pd.concat(
        {"名目GDP（兆US$）": gdp_trillion, "GDP成長率（年率%）": gdp_growth},
        axis=1
    ).dropna()

    # CSV保存（任意）
    df.to_csv("china_gdp_1980_latest.csv", encoding="utf-8-sig")

    # ---- プロット ----
    plt.rcParams["axes.unicode_minus"] = False  # マイナス符号の表示崩れ対策（日本語環境向け）
    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

    # 上：名目GDP（兆US$）
    ax1 = axes[0]
    df["名目GDP（兆US$）"].plot(ax=ax1)
    ax1.set_title("中国の名目GDP推移（1980年〜最新年）")
    ax1.set_ylabel("兆US$")
    ax1.grid(True, alpha=0.3)

    # 目盛り整形（小数1桁程度）
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda v, pos: f"{v:.1f}"))

    # 下：実質GDP成長率（年率%）
    ax2 = axes[1]
    df["GDP成長率（年率%）"].plot(ax=ax2)
    ax2.set_title("中国のGDP成長率推移（1980年〜最新年）")
    ax2.set_ylabel("%")
    ax2.set_xlabel("年")
    ax2.grid(True, alpha=0.3)

    # レイアウト調整と保存
    fig.tight_layout()
    plt.savefig("china_gdp_plots.png", dpi=200, bbox_inches="tight")
    plt.show()

if __name__ == "__main__":
    main()
