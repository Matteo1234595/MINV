import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from io import BytesIO
from reportlab.pdfgen import canvas

st.set_page_config(page_title="MINV – Market Investment AI", layout="wide")

st.image("https://cdn.pixabay.com/photo/2017/08/10/07/32/stock-2619124_1280.jpg", use_container_width=True)
if st.toggle("🌙 Tema scuro"):
    st.markdown('<style>body, .stApp {background-color: #1e1e1e; color: white;}</style>', unsafe_allow_html=True)

st.title("💼 MINV – Market Investment AI")

menu = st.sidebar.selectbox("📊 Seleziona sezione", [
    "Dashboard", "Analisi azienda", "Portafoglio simulato",
    "Consulenza personalizzata", "Screener azioni italiane", "AI Consulente"
])

def format_val(val):
    if val is None: return "N/A"
    if isinstance(val, (int, float)):
        if abs(val) >= 1e9: return f"{val/1e9:.2f}B"
        if abs(val) >= 1e6: return f"{val/1e6:.2f}M"
        return f"{val:.2f}"
    return val

if menu == "Dashboard":
    st.subheader("🌐 Indici di mercato")
    indices = {
        "FTSE MIB": "^FTSEMIB.MI",
        "NASDAQ 100": "^NDX",
        "S&P 500": "^GSPC",
        "DAX": "^GDAXI"
    }
    col1, col2 = st.columns(2)
    for i, (name, ticker) in enumerate(indices.items()):
        try:
            data = yf.Ticker(ticker).history(period="5d")
            if not data.empty:
                last = data["Close"].iloc[-1]
                first = data["Close"].iloc[0]
                pct = ((last - first) / first) * 100
                (col1 if i % 2 == 0 else col2).metric(name, f"{last:.2f}", f"{pct:+.2f}%")
        except:
            (col1 if i % 2 == 0 else col2).metric(name, "N/D", "N/D")

elif menu == "Analisi azienda":
    ticker = st.text_input("Ticker (es: ENI.MI, AAPL)", "ENI.MI")
    if ticker:
        stock = yf.Ticker(ticker)
        info = stock.info
        st.subheader(f"📊 Analisi per {ticker}")
        try:
            st.write("**Prezzo attuale:**", format_val(info.get("currentPrice")))
            st.write("**P/E:**", format_val(info.get("trailingPE")))
            st.write("**ROE:**", format_val(info.get("returnOnEquity", 0)*100))
            st.write("**Debito/Equity:**", format_val(info.get("debtToEquity")))
            st.write("**FCF:**", format_val(info.get("freeCashflow")))
            st.write("**Dividendo (%):**", format_val(info.get("dividendYield", 0)*100))
        except:
            st.warning("❌ Errore nel recupero dei dati.")

elif menu == "Portafoglio simulato":
    st.subheader("📈 Simula portafoglio")
    tickers = st.text_input("Titoli separati da virgola", "ENI.MI, UCG.MI").split(",")
    capitale = st.number_input("Capitale (€)", 1000, 1_000_000, 10000, 1000)
    if st.button("Simula"):
        col1, col2 = st.columns(2)
        for i, t in enumerate([x.strip().upper() for x in tickers]):
            try:
                h = yf.Ticker(t).history(period="6mo")
                rendimento = (h["Close"].iloc[-1] - h["Close"].iloc[0]) / h["Close"].iloc[0]
                quota = capitale / len(tickers)
                finale = quota * (1 + rendimento)
                (col1 if i % 2 == 0 else col2).metric(t, f"{finale:.2f} €", f"{rendimento*100:+.2f}%")
            except:
                st.warning(f"Errore su {t}")

elif menu == "Consulenza personalizzata":
    st.subheader("🧑‍💼 Piano operativo su misura")
    with st.form("profilo"):
        eta = st.number_input("Età", 18, 100, 40)
        capitale = st.number_input("Capitale (€)", 1000, 1000000, 20000)
        rischio = st.selectbox("Rischio", ["Basso", "Medio", "Alto"])
        orizzonte = st.selectbox("Orizzonte", ["1-3 anni", "3-5 anni", "5+ anni"])
        esegui = st.form_submit_button("Genera piano")
    if esegui:
        st.write("### 📌 Allocazione suggerita")
        az, obb, liq = 0.5, 0.4, 0.1
        if rischio == "Basso": az, obb, liq = 0.2, 0.6, 0.2
        elif rischio == "Alto": az, obb, liq = 0.7, 0.2, 0.1
        tot = az + obb + liq
        az, obb, liq = az/tot, obb/tot, liq/tot
        st.write(f"- Azioni: {az*100:.1f}% → €{az*capitale:,.2f}")
        st.write(f"- Obbligazioni: {obb*100:.1f}% → €{obb*capitale:,.2f}")
        st.write(f"- Liquidità: {liq*100:.1f}% → €{liq*capitale:,.2f}")
        st.markdown("### 🛒 Cosa acquistare")
        if rischio == "Basso":
            st.write("- ETF: iShares Euro Gov Bond 1-3Y (IBGL.DE)")
        elif rischio == "Medio":
            st.write("- ETF: Vanguard FTSE All-World (VWCE.DE)")
        else:
            st.write("- Azioni suggerite: STM.MI, LUX.MI, UCG.MI")
            st.write("- ETF tematico: iShares Digitalisation (DGTL.DE)")
        st.markdown("### 📘 Spiegazione completa")
        st.write("Il piano è calibrato su orizzonte, rischio e capitale. L’allocazione mira a bilanciare crescita e protezione.")

elif menu == "Screener azioni italiane":
    st.subheader("🔎 Classifica azioni italiane")
    titoli = ["ENI.MI", "UCG.MI", "STM.MI", "ATL.MI", "LUX.MI", "ISP.MI"]
    rows = []
    for t in titoli:
        try:
            i = yf.Ticker(t).info
            rows.append({
                "Ticker": t,
                "P/E": round(i.get("trailingPE", 0), 2),
                "ROE %": round(i.get("returnOnEquity", 0)*100, 2),
                "Dividendo %": round(i.get("dividendYield", 0)*100, 2)
            })
        except:
            continue
    if rows:
        st.dataframe(pd.DataFrame(rows).set_index("Ticker").sort_values("ROE %", ascending=False))

elif menu == "AI Consulente":
    st.subheader("🤖 AI Consulente")
    nome = st.text_input("Nome cliente", "Mario")
    capitale = st.number_input("Capitale disponibile (€)", 1000, 1_000_000, 30000)
    rischio = st.selectbox("Rischio", ["Basso", "Medio", "Alto"])
    if st.button("Genera raccomandazione"):
        st.write(f"### 👤 Profilo: {nome}")
        if rischio == "Basso":
            st.write("- Obiettivo: protezione del capitale")
            st.write("- Suggerimento: ETF IBGL.DE (obbligazioni), 30% in liquidità")
        elif rischio == "Medio":
            st.write("- Obiettivo: equilibrio tra rendimento e rischio")
            st.write("- Suggerimento: ETF VWCE.DE (mondo), IEAC.DE (obbligazionario), 10% cash")
        else:
            st.write("- Obiettivo: crescita a lungo termine")
            st.write("- Suggerimento: Azioni STM.MI, LUX.MI, ETF tematici (DGTL.DE)")
        st.write("Tutti i prodotti sono a replica fisica e liquidità elevata.")