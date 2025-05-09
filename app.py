
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
    "Dashboard", "Analisi azienda", "Portafoglio simulato", "Consulenza personalizzata"
])

def get_news(query):
    try:
        url = f"https://news.google.com/rss/search?q={query}+borsa&hl=it&gl=IT&ceid=IT:it"
        feed = requests.get(url)
        soup = BeautifulSoup(feed.content, "xml")
        items = soup.findAll("item")[:5]
        return [item.title.text for item in items]
    except:
        return []

def format_val(val):
    if val is None: return "N/A"
    if isinstance(val, (int, float)):
        if abs(val) >= 1e9: return f"{val/1e9:.2f}B"
        if abs(val) >= 1e6: return f"{val/1e6:.2f}M"
        return f"{val:.2f}"
    return val

def create_pdf(data_dict):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.setFont("Helvetica", 12)
    y = 800
    for key, value in data_dict.items():
        pdf.drawString(40, y, f"{key}: {format_val(value)}")
        y -= 20
    pdf.save()
    buffer.seek(0)
    return buffer

if menu == "Consulenza personalizzata":
    st.subheader("🧑‍💼 Piano di investimento personalizzato")

    with st.form("form_cliente"):
        eta = st.number_input("Età del cliente", 18, 100, 40)
        capitale = st.number_input("Capitale disponibile (€)", 1000, 1000000, 20000, step=1000)
        rischio = st.selectbox("Propensione al rischio", ["Basso", "Medio", "Alto"])
        orizzonte = st.selectbox("Orizzonte temporale", ["Breve (1-3 anni)", "Medio (3-5 anni)", "Lungo (5+ anni)"])
        submit = st.form_submit_button("Calcola piano")

    if submit:
        st.markdown("### 📊 Risultato del piano")

        if rischio == "Basso":
            azioni = 0.2
            obbligazioni = 0.6
            liquidità = 0.2
        elif rischio == "Medio":
            azioni = 0.4
            obbligazioni = 0.4
            liquidità = 0.2
        else:
            azioni = 0.7
            obbligazioni = 0.2
            liquidità = 0.1

        if orizzonte == "Breve (1-3 anni)":
            azioni *= 0.7
            obbligazioni *= 1.1
        elif orizzonte == "Lungo (5+ anni)":
            azioni *= 1.2
            obbligazioni *= 0.9

        totale = azioni + obbligazioni + liquidità
        azioni /= totale
        obbligazioni /= totale
        liquidità /= totale

        st.success(f"🔵 Azioni consigliate: {azioni*100:.1f}%")
        st.info(f"🟠 Obbligazioni consigliate: {obbligazioni*100:.1f}%")
        st.warning(f"🟢 Liquidità consigliata: {liquidità*100:.1f}%")

        st.markdown("#### 📌 Suggerimento azioni italiane oggi")
        titoli_italiani = ["ENI.MI", "UCG.MI", "ISP.MI", "STM.MI", "SRG.MI", "ATL.MI", "MONC.MI"]
        for t in titoli_italiani:
            try:
                data = yf.Ticker(t).history(period="6mo")
                if not data.empty:
                    variazione = (data["Close"].iloc[-1] - data["Close"].iloc[0]) / data["Close"].iloc[0]
                    colore = "🟢" if variazione > 0 else "🔴"
                    st.markdown(f"- {colore} {t}: rendimento 6 mesi = {variazione*100:.2f}%")
            except:
                st.markdown(f"- ⚠️ {t}: errore nel recupero dati")

