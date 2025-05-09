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
    st.subheader("🧑‍⚖️ Consulenza dettagliata per profilo utente")

    with st.form("profilo_cliente"):
        eta = st.number_input("Età", 18, 100, 45)
        capitale = st.number_input("Capitale disponibile (€)", 1000, 1000000, 25000)
        rischio = st.selectbox("Rischio", ["Basso", "Medio", "Alto"])
        orizzonte = st.selectbox("Orizzonte", ["1-3 anni", "3-5 anni", "5+ anni"])
        obiettivo = st.selectbox("Obiettivo", ["Protezione", "Crescita", "Alta crescita"])
        invia = st.form_submit_button("📊 Genera piano")

    if invia:
        st.write("### 💼 Piano operativo consigliato")
        if rischio == "Basso":
            st.write("- ✅ Obbligazioni europee a breve termine")
            st.write("- ✅ Liquidità su conto deposito")
            st.write("- ✅ ETF: iShares Euro Government Bond 1-3yr (IBGL.DE)")
        elif rischio == "Medio":
            st.write("- ✅ ETF: Vanguard FTSE All-World (VWCE.DE)")
            st.write("- ✅ ETF: iShares Euro Corporate Bond (IEAC.DE)")
            st.write("- ✅ 10% cash per opportunità future")
        else:
            st.write("- ✅ Azioni suggerite:")
            for titolo in ["STM.MI", "LUX.MI", "UCG.MI"]:
                try:
                    hist = yf.Ticker(titolo).history(period="6mo")
                    rend = (hist["Close"].iloc[-1] - hist["Close"].iloc[0]) / hist["Close"].iloc[0]
                    st.markdown(f"  - **{titolo}**: rendimento 6 mesi = {rend*100:.2f}%")
                except:
                    st.markdown(f"  - {titolo}: dati non disponibili")
            st.write("- ✅ ETF: iShares Digitalisation (DGTL.DE)")

        st.write("### 📝 Strategia dettagliata")
        st.write("Distribuzione consigliata:")
        if rischio == "Basso":
            alloc = {"ETF Obbligazionario": 0.6, "Conto deposito": 0.3, "Altro": 0.1}
        elif rischio == "Medio":
            alloc = {"ETF Azionario globale": 0.5, "ETF Obbligazionario": 0.3, "Liquidità": 0.2}
        else:
            alloc = {"Azioni": 0.6, "ETF Tematici": 0.3, "Cash": 0.1}
        for voce, perc in alloc.items():
            st.markdown(f"- **{voce}**: {perc*100:.0f}% → €{capitale * perc:,.2f}")
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
    st.subheader("🤖 AI Consulente – Azione diretta")

    capitale = st.number_input("Capitale investibile (€)", 1000, 1_000_000, 20000)
    rischio = st.selectbox("Profilo rischio", ["Basso", "Medio", "Alto"])
    orizzonte = st.selectbox("Orizzonte", ["1-3 anni", "3-5 anni", "5+ anni"])
    obiettivo = st.selectbox("Obiettivo", ["Rendimento costante", "Crescita equilibrata", "Alta performance"])

    if st.button("🧠 Genera raccomandazione reale"):
        st.write("### ✅ Azioni suggerite da eseguire ora")
        if rischio == "Basso":
            st.write("- Compra **IBGL.DE** – ETF obbligazionario euro breve scadenza")
            st.write("- Mantieni 30% in **liquidità** su conto vincolato")
        elif rischio == "Medio":
            st.write("- Compra **VWCE.DE** – ETF mondo a replica fisica")
            st.write("- Compra **IEAC.DE** – ETF obbligazionario corporate")
        else:
            st.write("- Compra **STM.MI**, **LUX.MI**, **UCG.MI**")
            st.write("- Aggiungi ETF tematico: **DGTL.DE**")
            st.write("- Mantieni 10% liquido per occasioni future")

        st.write("### 🔁 Valuta vendita di:")
        st.write("- Titoli con perdita > 10% negli ultimi 6 mesi")
        st.write("- ETF difensivi se sei in fase di accumulo")

        st.write("### 🧠 Motivazione AI:")
        st.write("Analisi basata su rendimento storico 6 mesi, scenario macroeconomico e coerenza con obiettivi definiti.")