import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import time

# --- 1. SETTING & UI CONFIG ---
st.set_page_config(page_title="Pro Quant Dashboard", layout="wide")

# Custom CSS เพื่อปรับขนาดตัวอักษรและสี
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("📟 Pro Quant Dashboard (V25)")
st.divider()

# --- 2. SIDEBAR CONTROL ---
with st.sidebar:
    st.header("⚙️ Strategy Settings")
    market = st.selectbox("เลือกตลาด", ["Thai Active Stocks", "US Big Tech", "Crypto"])
    
    with st.expander("🛠 ปรับจูน Indicator", expanded=False):
        buy_rsi = st.slider("Buy RSI Level", 20, 45, 35)
        min_val = st.number_input("Min Value (M)", value=10.0)
        vol_ratio = st.slider("Vol Spike Ratio", 1.0, 3.0, 1.5)
    
    start_btn = st.button("🚀 Start Deep Scan", use_container_width=True)

# Data Mapping
market_data = {
    "Thai Active Stocks": ["ADVANC", "AOT", "CPALL", "PTT", "DELTA", "KBANK", "SCB", "GULF", "PTTEP", "SCC", "BDMS", "BBL", "BGRIM", "BH", "CBG", "CRC", "EA", "GPSC", "HMPRO", "IVL"],
    "US Big Tech": ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA", "META", "AMZN", "NFLX", "AMD", "SMCI"],
    "Crypto": ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD"]
}

# --- 3. ANALYTICAL ENGINE ---
def analyze_data(ticker_list, is_thai):
    symbols = [f"{s}.BK" for s in ticker_list] if is_thai else ticker_list
    data = yf.download(symbols, period="100d", group_by='ticker', progress=False)
    results = []

    for s in symbols:
        try:
            df = data[s].dropna()
            if len(df) < 35: continue
            
            # Technicals
            df['RSI'] = ta.rsi(df['Close'], length=14)
            macd = ta.macd(df['Close'])
            df = pd.concat([df, macd], axis=1)
            df['EMA5'] = ta.ema(df['Close'], length=5)
            df['EMA20'] = ta.ema(df['Close'], length=20)
            df['Vol_Avg'] = df['Volume'].rolling(window=5).mean()
            df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)

            c, p = df.iloc[-1], df.iloc[-2]
            
            # Reasoning Logic
            reasons = []
            score = 0
            if c['RSI'] < buy_rsi: score += 25; reasons.append("📉 RSI ต่ำ (ราคาถูก)")
            if c['MACD_12_26_9'] > c['MACDs_12_26_9'] and p['MACD_12_26_9'] <= p['MACDs_12_26_9']: 
                score += 25; reasons.append("🔥 MACD ตัดขึ้น")
            if c['Volume'] > (c['Vol_Avg'] * vol_ratio): score += 25; reasons.append("⚡ Volume เข้า")
            if c['EMA5'] > c['EMA20'] and p['EMA5'] <= p['EMA20']: score += 25; reasons.append("📈 แนวโน้มกลับตัว")

            val = (c['Close'] * c['Volume']) / 1_000_000
            if is_thai and val < min_val: continue

            results.append({
                "Symbol": s.replace(".BK", ""),
                "Price": round(c['Close'], 2),
                "Score": score,
                "Action": "🟢 STRONG BUY" if score >= 75 else "🔵 ACCUMULATE" if score >= 50 else "🔴 SELL/WAIT" if c['RSI'] > 70 else "Wait",
                "Analysis": " | ".join(reasons) if reasons else "รอสัญญาณ",
                "TP": round(c['Close'] + (c['ATR'] * 2), 2),
                "SL": round(c['Close'] - (c['ATR'] * 1.5), 2),
                "Value(M)": round(val, 2),
                "RSI": round(c['RSI'], 2)
            })
        except: continue
    return pd.DataFrame(results)

# --- 4. MAIN DISPLAY ---
if start_btn:
    with st.spinner("🔍 กำลังจัดระเบียบข้อมูลและวิเคราะห์..."):
        df_res = analyze_data(market_data[market], market == "Thai Active Stocks")
        
        if not df_res.empty:
            df_sorted = df_res.sort_values("Score", ascending=False)
            
            # --- SECTION 1: TOP PICKS ---
            st.subheader("🔥 Top 3 Opportunities")
            top_cols = st.columns(3)
            for i, (_, row) in enumerate(df_sorted.head(3).iterrows()):
                with top_cols[i]:
                    st.metric(label=row['Symbol'], value=f"{row['Price']:,}", delta=f"Score: {row['Score']}")
                    st.markdown(f"**Action:** `{row['Action']}`")
                    st.caption(f"🎯 TP: {row['TP']} | 🛡️ SL: {row['SL']}")

            st.divider()

            # --- SECTION 2: FULL REPORT ---
            st.subheader("📋 Full Analysis Report")
            
            # การจัดคอลัมน์ให้ชัดเจนโดยใช้ Column Config
            st.dataframe(
                df_sorted,
                use_container_width=True,
                column_order=("Symbol", "Action", "Price", "Score", "Analysis", "RSI", "TP", "SL", "Value(M)"),
                column_config={
                    "Symbol": st.column_config.TextColumn("หุ้น", help="ชื่อย่อหลักทรัพย์"),
                    "Action": st.column_config.TextColumn("คำแนะนำ"),
                    "Price": st.column_config.NumberColumn("ราคาล่าสุด", format="%.2f"),
                    "Score": st.column_config.ProgressColumn("คะแนนความมั่นใจ", min_value=0, max_value=100),
                    "Analysis": st.column_config.TextColumn("เหตุผลประกอบ", width="large"),
                    "RSI": st.column_config.NumberColumn("RSI", format="%.1f"),
                    "TP": st.column_config.NumberColumn("เป้ากำไร", format="%.2f"),
                    "SL": st.column_config.NumberColumn("จุดตัดขาดทุน", format="%.2f"),
                    "Value(M)": st.column_config.NumberColumn("มูลค่า (ล้าน)", format="%.1f"),
                },
                hide_index=True
            )
        else:
            st.warning("ไม่พบหุ้นที่เข้าเกณฑ์ในขณะนี้")
else:
    st.info("👈 ปรับการตั้งค่าที่แถบด้านข้างแล้วกด **Start Deep Scan** เพื่อเริ่มวิเคราะห์")
