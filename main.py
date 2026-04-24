import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf

# ============================================================
# 1. HIGH CONTRAST UI DESIGN (No Pure White)
# ============================================================
def apply_high_contrast_ui():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&family=IBM+Plex+Mono:wght@700&display=swap');
        
        /* พื้นหลังสีน้ำเงินเข้มจัด (Midnight) */
        html, body, [class*="css"] {
            font-family: 'Sarabun', sans-serif;
            background-color: #050510;
            color: #FFBF00; /* ตัวอักษรสีเหลืองอำพัน (Amber) - เห็นชัดที่สุดบนสีมืด */
        }

        /* หัวข้อสีฟ้าสว่าง (Cyan) */
        h1, h2, h3, b, strong {
            color: #00E5FF !important; 
        }

        /* Card ดีไซน์ใหม่ เน้นขอบชัดเจน */
        .stock-card {
            background: #101223;
            border: 2px solid #1E293B;
            border-radius: 12px;
            padding: 18px;
            margin-bottom: 12px;
        }
        
        /* แถบสีข้าง Card เน้นความหนาและสีสด */
        .buy-border { border-left: 8px solid #00FF41; }   /* เขียวนีออน */
        .sell-border { border-left: 8px solid #FF3131; }  /* แดงสด */
        .watch-border { border-left: 8px solid #FFD700; } /* ทอง */

        /* ตัวเลขหุ้นแบบ Mono หนาพิเศษ */
        .symbol-text { 
            font-family: 'IBM Plex Mono', monospace; 
            font-size: 1.4rem; 
            color: #00E5FF;
        }
        .price-text { 
            font-family: 'IBM Plex Mono', monospace; 
            font-size: 1.2rem; 
            color: #FFBF00;
        }
        
        /* ปรับสีปุ่มให้ตัดกับพื้นหลัง */
        .stButton>button {
            background-color: #1E293B;
            color: #00E5FF;
            border: 2px solid #00E5FF;
            font-weight: bold;
        }

        /* ปรับสี Expander */
        .stExpander {
            background-color: #0A0A1A;
            border: 1px solid #1E293B !important;
        }
    </style>
    """, unsafe_allow_html=True)

# ============================================================
# 2. ANALYSIS ENGINE (Clean & Robust)
# ============================================================
def get_stock_analysis(symbol, market):
    ticker = f"{symbol}.BK" if market == "SET" else symbol
    try:
        df = yf.download(ticker, period="150d", interval="1d", progress=False)
        if df.empty or len(df) < 50: return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        df.ta.rsi(length=14, append=True)
        df.ta.sma(length=20, append=True)
        df.ta.sma(length=50, append=True)
        
        c = df.iloc[-1]
        score = 50
        if c['RSI_14'] < 30: score += 20
        elif c['RSI_14'] > 70: score -= 20
        if c['Close'] > c['SMA_20'] > c['SMA_50']: score += 20
        
        rec = "🟢 BUY" if score >= 65 else "🔴 SELL" if score <= 35 else "🟡 WATCH"
        cls = "buy" if score >= 65 else "sell" if score <= 35 else "watch"
        return {"price": c['Close'], "chg": (c['Close']/df.iloc[-2]['Close']-1)*100, 
                "rsi": c['RSI_14'], "score": score, "rec": rec, "cls": cls}
    except:
        return None

# ============================================================
# 3. APP RENDER
# ============================================================
def main():
    apply_high_contrast_ui()
    
    st.markdown('<h1 style="text-align: center;">📊 SCANNER PRO</h1>', unsafe_allow_html=True)
    
    m_choice = st.selectbox("MARKET", ["SET (Thai)", "US Tech (USA)", "CN Tech (China)"])
    m_key = m_choice.split(" ")[0]

    universe = {
        "SET": ["ADVANC", "CPALL", "PTT", "KBANK", "AOT", "DELTA", "GULF", "SCB"],
        "US": ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL", "META", "AMD"],
        "CN": ["BABA", "JD", "PDD", "NIO", "XPEV", "LI", "BILI"]
    }

    if st.button("RUN SCANNER", use_container_width=True):
        for sym in universe[m_key]:
            res = get_stock_analysis(sym, m_key)
            if res:
                st.markdown(f"""
                <div class="stock-card {res['cls']}-border">
                    <div style="display: flex; justify-content: space-between;">
                        <div>
                            <div class="symbol-text">{sym}</div>
                            <div style="color: #64748B; font-size: 0.8rem;">SCORE: {res['score']}</div>
                        </div>
                        <div style="text-align: right;">
                            <div class="price-text">{res['price']:,.2f}</div>
                            <div style="color: {'#00FF41' if res['chg'] >= 0 else '#FF3131'}; font-weight: bold;">
                                {res['chg']:+.2f}%
                            </div>
                        </div>
                    </div>
                    <div style="margin-top: 10px; font-weight: bold; color: #00E5FF;">{res['rec']}</div>
                </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
