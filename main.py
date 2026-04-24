# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import numpy as np
from datetime import datetime

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Stock Scanner Pro V27",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ============================================================
# CSS (UI Design จากตัวอย่างที่คุณให้มา)
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap');
html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; background: #0d0d14; color: #e2e8f0; }
.app-hdr { background: linear-gradient(135deg, #12122a, #1a1035, #0f1f3a); border: 1px solid rgba(108,99,255,0.3); border-radius: 16px; padding: 18px; text-align: center; margin-bottom: 16px; }
.da-hdr { background: linear-gradient(135deg, #12122a, #1a1035); border: 1px solid rgba(108,99,255,0.4); border-radius: 14px; padding: 16px; margin-bottom: 14px; }
.stock-card { background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 14px; padding: 14px; margin-bottom: 10px; }
.stock-card.buy { border-left: 4px solid #00b894; }
.stock-card.sell { border-left: 4px solid #d63031; }
.sring { width: 44px; height: 44px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-family: 'IBM Plex Mono'; }
.sh { border: 2px solid #00b894; color: #00b894; }
.sl { border: 2px solid #d63031; color: #d63031; }
.tus { background: #1a1a3a; color: #6c63ff; border: 1px solid #6c63ff40; padding: 2px 8px; border-radius: 8px; }
.tcn { background: #3a1a1a; color: #d63031; border: 1px solid #d6303140; padding: 2px 8px; border-radius: 8px; }
.ibox { background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 10px; padding: 10px; text-align: center; }
.ind-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# STOCK UNIVERSE (รวมหุ้นจีน US และไทย)
# ============================================================
MARKETS = {
    "SET": {"flag": "🇹🇭", "name": "ตลาดหุ้นไทย", "currency": "฿", "tag": "tth", "stocks": ["KBANK", "PTT", "CPALL", "ADVANC", "AOT"]},
    "US": {"flag": "🇺🇸", "name": "US Tech", "currency": "$", "tag": "tus", "stocks": ["AAPL", "NVDA", "MSFT", "GOOGL", "TSLA"]},
    "CN": {"flag": "🇨🇳", "name": "CN Tech", "currency": "$", "tag": "tcn", "stocks": ["BABA", "JD", "BIDU", "PDD", "NIO", "XPEV", "LI", "BILI"]}
}

# ============================================================
# INDICATORS ENGINE
# ============================================================
def get_data(symbol, mkt_key):
    ticker_sym = f"{symbol}.BK" if mkt_key == "SET" else symbol
    df = yf.download(ticker_sym, period="200d", interval="1d", progress=False)
    if df.empty: return None, None
    
    # คำนวณ Indicators ด้วย pandas_ta
    df.ta.rsi(length=14, append=True)
    df.ta.macd(append=True)
    bb = ta.bbands(df['Close'], length=20, std=2)
    df['BBL'] = bb.iloc[:, 0]; df['BBM'] = bb.iloc[:, 1]; df['BBU'] = bb.iloc[:, 2]
    df['BBP'] = (df['Close'] - df['BBL']) / (df['BBU'] - df['BBL'] + 1e-9)
    df.ta.sma(length=20, append=True); df.ta.sma(length=50, append=True)
    df.ta.atr(length=14, append=True)
    
    # Ichimoku
    ichi, _ = ta.ichimoku(df['High'], df['Low'], df['Close'])
    df = pd.concat([df, ichi], axis=1)
    
    # Fundamental
    info = yf.Ticker(ticker_sym).info
    return df, info

def get_signal(df):
    c = df.iloc[-1]
    score = 50
    reasons = []
    
    if c['RSI_14'] < 30: score += 15; reasons.append("RSI Oversold")
    elif c['RSI_14'] > 70: score -= 15; reasons.append("RSI Overbought")
    
    # Trend Logic
    if c['Close'] > c['SMA_20'] > c['SMA_50']: score += 15; reasons.append("แนวโน้มขาขึ้นสมบูรณ์")
    
    # Ichimoku Logic
    if c['Close'] > c['ISA_9'] and c['Close'] > c['ISB_26']: score += 10; reasons.append("อยู่เหนือเมฆ Ichimoku")
    
    rec = "🟢 ซื้อ" if score >= 65 else "🔴 ขาย" if score <= 35 else "🟡 เฝ้า"
    cls = "buy" if score >= 65 else "sell" if score <= 35 else "watch"
    
    return score, rec, cls, reasons

# ============================================================
# MAIN APP
# ============================================================
st.markdown('<div class="app-hdr"><h1>📈 Stock Scanner Pro V27</h1><div class="sub">15+ Indicators · SET · US Tech · CN Tech</div></div>', unsafe_allow_html=True)

m_key = st.radio("เลือกตลาดหุ้น", list(MARKETS.keys()), horizontal=True)
m_info = MARKETS[m_key]

if st.button(f"🔍 เริ่มสแกน {m_info['name']} ({len(m_info['stocks'])} หุ้น)"):
    for sym in m_info['stocks']:
        df, fund = get_data(sym, m_key)
        if df is not None:
            score, rec, cls, reasons = get_signal(df)
            c = df.iloc[-1]
            chg = (c['Close']/df.iloc[-2]['Close']-1)*100
            
            st.markdown(f"""
            <div class="stock-card {cls}">
                <div style="display:flex; justify-content:space-between;">
                    <div>
                        <span style="font-size:1.2rem; font-weight:700;">{sym}</span>
                        <span class="{m_info['tag']}">{m_info['flag']} {m_key}</span>
                        <div style="font-size:0.8rem; color:#8892b0;">RSI: {c['RSI_14']:.1f}</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:1.2rem; font-weight:700;">{m_info['currency']}{c['Close']:.2f}</div>
                        <div style="color:{'#00b894' if chg>=0 else '#d63031'};">{chg:+.2f}%</div>
                    </div>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:10px;">
                    <div><span style="background:rgba(108,99,255,0.1); padding:4px 10px; border-radius:10px;">{rec}</span></div>
                    <div class="sring {'sh' if score>=65 else 'sl' if score<=35 else ''}">{score}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander(f"📊 วิเคราะห์ {sym} เจาะลึก"):
                st.write(f"**เหตุผล:** {', '.join(reasons)}")
                c1, c2, c3 = st.columns(3)
                c1.metric("P/E (TTM)", f"{fund.get('trailingPE', 'N/A')}")
                c2.metric("Market Cap", f"{fund.get('marketCap', 0)/1e9:.1f}B")
                c3.metric("Dividend Yield", f"{fund.get('dividendYield', 0)*100:.2f}%")
