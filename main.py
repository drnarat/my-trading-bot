st.markdown("""
<style>
    /* การออกแบบ Card แบบใหม่ที่ดูแพงขึ้น */
    .st-emotion-cache-1kyxreq { /* Container ของ Card */
        padding: 0;
    }
    .modern-card {
        background: rgba(26, 26, 46, 0.8);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(108, 99, 255, 0.2);
        border-radius: 20px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        transition: transform 0.2s;
    }
    .modern-card:active {
        transform: scale(0.98);
    }
    .trend-up { color: #00b894; font-weight: 700; }
    .trend-down { color: #d63031; font-weight: 700; }
    
    /* ตกแต่ง Score Ring ให้เหมือน Dashboard รถสปอร์ต */
    .score-circle {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: conic-gradient(#6c63ff calc(var(--score) * 1%), #1a1a2e 0);
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
    }
    .score-circle::after {
        content: attr(data-score);
        width: 50px;
        height: 50px;
        background: #1a1a2e;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'IBM Plex Mono';
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)
