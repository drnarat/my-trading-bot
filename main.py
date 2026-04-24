import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import numpy as np
from datetime import datetime
import time

# ============================================================
# PAGE CONFIG & CSS (จากตัวอย่างที่คุณให้มา)
# ============================================================
st.set_page_config(page_title="📈 Stock Scanner Pro", page_icon="📈", layout="centered")

# ใส่ CSS ทั้งหมดที่คุณให้มาใน st.markdown(""" <style> ... </style> """)
# [เพื่อประหยัดพื้นที่ ผมจะขอข้ามส่วน CSS ในตัวอย่างนี้ แต่คุณต้องใส่กลับเข้าไปในโค้ดจริงนะครับ]

# ============================================================
# GLOBAL CONFIG & MARKETS
# ============================================================
MARKETS = {
    "SET": {
        "flag": "🇹🇭", "name": "ตลาดหุ้นไทย", "desc": "SET50, SET100", "currency": "฿", "tag_class": "tag-th",
        "stocks": ["ADVANC", "AOT", "CPALL", "PTT", "DELTA", "KBANK", "SCB", "GULF", "PTTEP", "SCC"]
    },
    "US": {
        "flag": "🇺🇸", "name": "US Tech", "desc": "NASDAQ, NYSE", "currency": "$", "tag_class": "tag-us",
        "stocks": ["AAPL", "MSFT", "NVDA", "GOOGL", "TSLA", "META", "AMZN", "NFLX"]
    }
}

# ============================================================
# DATA & INDICATOR ENGINE (ใช้ pandas_ta เพื่อความแม่นยำ)
# ============================================================
def get_real_data(symbol, is_thai=True):
    ticker = f"{symbol}.BK" if is_thai else symbol
    df = yf.download(ticker, period="150d", interval="1d", progress=False)
    if df.empty: return None
    
    # คำนวณ Indicators ทั้งหมด
    df['RSI'] = ta.rsi(df['Close'], length=14)
    macd = ta.macd(df['Close'])
    df = pd.concat([df, macd], axis=1)
    df['SMA20'] = ta.sma(df['Close'], length=20)
    df['SMA50'] = ta.sma(df['Close'], length=50)
    df['SMA200'] = ta.sma(df['Close'], length=200)
    df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
    df['EMA5'] = ta.ema(df['Close'], length=5)
    df['EMA20'] = ta.ema(df['Close'], length=20)
    
    # Bollinger Bands
    bb = ta.bbands(df['Close'], length=20, std=2)
    df['BBU'] = bb['BBU_20_2.0']
    df['BBL'] = bb['BBL_20_2.0']
    df['BBP'] = (df['Close'] - df['BBL']) / (df['BBU'] - df['BBL'])
    
    # Volume Average
    df['Vol_Avg'] = df['Volume'].rolling(window=20).mean()
    df['Vol_R'] = df['Volume'] / df['Vol_Avg']
    
    return df

def get_score_and_reasons(df):
    c = df.iloc[-1]
    p = df.iloc[-2]
    score = 50
    bs, ss, ns = [], [], []
    
    # RSI Logic
    if c['RSI'] < 35: score += 15; bs.append(f"RSI {c['RSI']:.1f} ต่ำ (Oversold)")
    elif c['RSI'] > 70: score -= 15; ss.append(f"RSI {c['RSI']:.1f} สูง (Overbought)")
    
    # MACD Logic
    if c['MACD_12_26_9'] > c['MACDs_12_26_9'] and p['MACD_12_26_9'] <= p['MACDs_12_26_9']:
        score += 15; bs.append("MACD เกิด Golden Cross")
    elif c['MACD_12_26_9'] < c['MACDs_12_26_9']:
        score -= 10; ss.append("MACD อยู่ในโซนขาลง")
        
    # EMA Cross
    if c['EMA5'] > c['EMA20'] and p['EMA5'] <= p['EMA20']:
        score += 15; bs.append("แนวโน้มระยะสั้นตัดขึ้น (EMA5/20)")
        
    # Volume Spike
    if c['Vol_R'] > 1.5:
        score += 10; bs.append(f"Volume เข้าผิดปกติ {c['Vol_R']:.1f}x")
        
    # Final Recommendation
    if score >= 70: rec, cls = "🟢 ซื้อ", "buy"
    elif score <= 35: rec, cls = "🔴 ขาย", "sell"
    elif score >= 55: rec, cls = "🟡 เฝ้าระวัง", "watch"
    else: rec, cls = "⚪ ถือ", "neutral"
    
    # TP/SL based on ATR
    atr = c['ATR']
    t1 = c['Close'] + (atr * 2)
    sl = c['Close'] - (atr * 1.5)
    
    return dict(score=score, rec=rec, cls=cls, bs=bs, ss=ss, ns=ns, t1=t1, sl=sl)

# ============================================================
# MAIN UI ROUTING
# ============================================================
if "view" not in st.session_state: st.session_state.view = "scan"
if "market" not in st.session_state: st.session_state.market = "SET"

# Header Section
st.markdown("""
<div class="app-header">
    <h1>📈 Stock Scanner Pro V26</h1>
    <div class="sub"><span class="live-dot"></span> 15+ Indicators · Yahoo Finance Real-time</div>
</div>
""", unsafe_allow_html=True)

if st.session_state.view == "scan":
    # Market Selector
    m_cols = st.columns(2)
    for i, (k, v) in enumerate(MARKETS.items()):
        if m_cols[i].button(f"{v['flag']} {k}\n{v['name']}", use_container_width=True):
            st.session_state.market = k
            
    m_key = st.session_state.market
    m_info = MARKETS[m_key]
    
    if st.button(f"🔍 เริ่มสแกน {m_info['name']} ({len(m_info['stocks'])} หุ้น)", use_container_width=True):
        results = []
        prog = st.progress(0)
        for idx, sym in enumerate(m_info['stocks']):
            df = get_real_data(sym, is_thai=(m_key=="SET"))
            if df is not None:
                analysis = get_score_and_reasons(df)
                c = df.iloc[-1]
                results.append({
                    "Symbol": sym, "Price": c['Close'], "RSI": c['RSI'], 
                    "Score": analysis['score'], "Action": analysis['rec'], 
                    "Cls": analysis['cls'], "TP": analysis['t1'], "SL": analysis['sl'],
                    "Change": (c['Close']/df.iloc[-2]['Close']-1)*100
                })
            prog.progress((idx+1)/len(m_info['stocks']))
        st.session_state.last_results = results
        prog.empty()

    # Display Results as Cards
    if "last_results" in st.session_state:
        for res in st.session_state.last_results:
            chg_color = "change-up" if res['Change'] >= 0 else "change-dn"
            st.markdown(f"""
            <div class="stock-card {res['Cls']}">
                <div class="sc-top">
                    <div><div class="sc-symbol">{res['Symbol']}</div></div>
                    <div>
                        <div class="sc-price">{m_info['currency']}{res['Price']:.2f}</div>
                        <div class="sc-change {chg_color}">{res['Change']:.2f}%</div>
                    </div>
                </div>
                <div class="sc-bars">
                    <div class="sc-bar-item"><div class="sc-bar-label">RSI</div><div class="sc-bar-val">{res['RSI']:.0f}</div></div>
                    <div class="sc-bar-item"><div class="sc-bar-label">Score</div><div class="sc-bar-val">{res['Score']}</div></div>
                </div>
                <div class="sc-bottom">
                    <span class="signal-chip chip-{res['Cls']}">{res['Action']}</span>
                    <div style="font-size:0.7rem; color:#8892b0;">🎯 TP: {res['TP']:.2f} | 🛡️ SL: {res['SL']:.2f}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"🔎 วิเคราะห์ {res['Symbol']} เจาะลึก", key=f"btn_{res['Symbol']}"):
                st.session_state.detail_sym = res['Symbol']
                st.session_state.view = "detail"
                st.rerun()

elif st.session_state.view == "detail":
    if st.button("← กลับไปหน้าสแกน"):
        st.session_state.view = "scan"
        st.rerun()
    st.write(f"### กำลังแสดงบทวิเคราะห์เจาะลึกของ {st.session_state.detail_sym}")
    # (ส่วนนี้คุณสามารถใส่รายละเอียด Indicator รายตัวตาม HTML/CSS ที่คุณมีได้เลยครับ)
