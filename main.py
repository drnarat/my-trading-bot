import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
from datetime import datetime

# ============================================================
# 1. STYLE & CSS (GLASSMORPHISM DESIGN)
# ============================================================
def apply_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&family=IBM+Plex+Mono&display=swap');
        
        /* Global Background */
        html, body, [class*="css"] {
            font-family: 'Sarabun', sans-serif;
            background-color: #0d0d14;
            color: #e2e8f0;
        }

        /* Modern Card Layout */
        .stock-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(5px);
        }
        
        .buy-border { border-left: 6px solid #00b894; }
        .sell-border { border-left: 6px solid #d63031; }
        .watch-border { border-left: 6px solid #fdcb6e; }

        /* Typography */
        .symbol-text { font-family: 'IBM Plex Mono', monospace; font-size: 1.3rem; font-weight: 700; color: #fff; }
        .price-text { font-family: 'IBM Plex Mono', monospace; font-size: 1.2rem; font-weight: 700; }
        .signal-badge { padding: 4px 12px; border-radius: 10px; font-size: 0.8rem; font-weight: 700; }
        
        /* Dashboard Stats */
        .stat-box {
            text-align: center;
            background: rgba(108, 99, 255, 0.1);
            padding: 15px;
            border-radius: 15px;
            border: 1px solid rgba(108, 99, 255, 0.2);
        }
    </style>
    """, unsafe_allow_html=True)

# ============================================================
# 2. CORE LOGIC (DATA & ANALYSIS)
# ============================================================
class StockAnalyzer:
    @staticmethod
    def fetch_data(symbol, market):
        """ดึงข้อมูลจาก Yahoo Finance (เป็นหลัก)"""
        ticker = f"{symbol}.BK" if market == "SET" else symbol
        df = yf.download(ticker, period="150d", interval="1d", progress=False)
        
        if df.empty: return None
        
        # แก้ไขปัญหา Multi-index ของ yfinance
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df

    @staticmethod
    def calculate_indicators(df):
        """คำนวณ Indicators ทั้งหมดในที่เดียว"""
        df.ta.rsi(length=14, append=True)
        df.ta.macd(append=True)
        df.ta.sma(length=20, append=True)
        df.ta.sma(length=50, append=True)
        df.ta.atr(length=14, append=True)
        
        # Bollinger Bands แบบปลอดภัย
        bb = ta.bbands(df['Close'], length=20, std=2)
        df['BBP'] = (df['Close'] - bb.iloc[:, 0]) / (bb.iloc[:, 2] - bb.iloc[:, 0] + 1e-9)
        return df

    @staticmethod
    def generate_signal(df):
        """วิเคราะห์สัญญาณซื้อขายจากคะแนน 0-100"""
        c = df.iloc[-1]
        score = 50
        reasons = []

        # RSI Logic
        if c['RSI_14'] < 35: score += 15; reasons.append("RSI Oversold (โซนซื้อ)")
        elif c['RSI_14'] > 70: score -= 15; reasons.append("RSI Overbought (โซนขาย)")

        # Trend Logic
        if c['Close'] > c['SMA_20'] > c['SMA_50']: score += 20; reasons.append("Bullish Trend (ขาขึ้นแข็งแกร่ง)")
        
        # Volume Spike
        vol_avg = df['Volume'].tail(20).mean()
        if c['Volume'] > vol_avg * 1.5: score += 10; reasons.append("Volume Spike (แรงซื้อเข้า)")

        # Result Mapping
        if score >= 65: return score, "🟢 BUY", "buy", reasons
        if score <= 35: return score, "🔴 SELL", "sell", reasons
        return score, "🟡 WATCH", "watch", reasons

# ============================================================
# 3. UI RENDERING (MOBILE-FIRST)
# ============================================================
def main():
    apply_custom_css()
    
    # Header Section
    st.markdown("""
        <div style="text-align: center; padding-bottom: 20px;">
            <h1 style="margin-bottom: 0;">📈 Scanner Pro</h1>
            <p style="color: #8892b0; font-size: 0.9rem;">Smart Trading Companion</p>
        </div>
    """, unsafe_allow_html=True)

    # Market Selection Tab
    market_choice = st.selectbox("เลือกตลาดหุ้น", ["SET (Thai)", "US Tech (USA)", "CN Tech (China)"])
    market_key = market_choice.split(" ")[0]

    universe = {
        "SET": ["ADVANC", "CPALL", "PTT", "KBANK", "AOT", "DELTA", "GULF", "SCB"],
        "US": ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL", "META", "AMD"],
        "CN": ["BABA", "JD", "PDD", "NIO", "XPEV", "LI", "BILI"]
    }

    if st.button("🔍 Start Scanning", use_container_width=True):
        results = []
        analyzer = StockAnalyzer()
        
        progress_bar = st.progress(0)
        stocks = universe[market_key]
        
        for idx, sym in enumerate(stocks):
            df = analyzer.fetch_data(sym, market_key)
            if df is not None:
                df = analyzer.calculate_indicators(df)
                score, rec, cls, reasons = analyzer.generate_signal(df)
                
                c = df.iloc[-1]
                chg = (c['Close'] / df.iloc[-2]['Close'] - 1) * 100
                
                # Render Card for each stock
                st.markdown(f"""
                <div class="stock-card {cls}-border">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div>
                            <div class="symbol-text">{sym}</div>
                            <div style="color: #8892b0; font-size: 0.8rem;">Score: <b>{score}</b></div>
                        </div>
                        <div style="text-align: right;">
                            <div class="price-text">{c['Close']:,.2f}</div>
                            <div style="color: {'#00b894' if chg >= 0 else '#d63031'}; font-weight: bold;">{chg:+.2f}%</div>
                        </div>
                    </div>
                    <div style="margin-top: 15px; display: flex; justify-content: space-between; align-items: center;">
                        <span class="signal-badge" style="background: rgba(108,99,255,0.15); color: #6c63ff;">{rec}</span>
                        <div style="font-size: 0.75rem; color: #8892b0;">RSI: {c['RSI_14']:.1f}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander(f"📖 ดูเหตุผลวิเคราะห์สำหรับ {sym}"):
                    for r in reasons:
                        st.write(f"• {r}")
                    st.line_chart(df['Close'].tail(30))
            
            progress_bar.progress((idx + 1) / len(stocks))
        
        st.success(f"สแกนสำเร็จ {len(stocks)} รายการ")

if __name__ == "__main__":
    main()
