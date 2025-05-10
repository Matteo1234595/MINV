
# MINV Pro App - Versione Completa con Analisi Azienda e Consulenza
import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from reportlab.pdfgen import canvas
from io import BytesIO

st.set_page_config(page_title="MINV Pro App", layout="wide")
st.title("📊 MINV Pro App")

menu = st.sidebar.selectbox("Seleziona sezione", ["Analisi azienda", "Consulenza AI"])

if menu == "Analisi azienda":
    st.subheader("📊 Analisi azienda – Dati, grafici e PDF")

    ticker = st.text_input("Inserisci ticker (es: ENI.MI, STM.MI)", value="ENI.MI")
    if ticker:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            st.markdown(f"### 🧾 Dati fondamentali: {info.get('longName', ticker)}")

            def format_color(label, val, positive=True):
                try:
                    valf = float(val)
                    color = "green" if (valf > 0 if positive else valf < 0) else "red"
                    return f"<span style='color:{color}'><b>{label}: {valf:.2f}</b></span>"
                except:
                    return f"<b>{label}: {val}</b>"

            pe = info.get("trailingPE", "N/A")
            roe = info.get("returnOnEquity", 0) * 100 if info.get("returnOnEquity") else "N/A"
            debt = info.get("debtToEquity", "N/A")
            fcf = info.get("freeCashflow", "N/A")
            dy = info.get("dividendYield", 0) * 100 if info.get("dividendYield") else "N/A"
            price = info.get("currentPrice", "N/A")

            st.markdown(format_color("Prezzo", price), unsafe_allow_html=True)
            st.markdown(format_color("P/E", pe), unsafe_allow_html=True)
            st.markdown(format_color("ROE (%)", roe), unsafe_allow_html=True)
            st.markdown(format_color("Debt/Equity", debt, positive=False), unsafe_allow_html=True)
            st.markdown(format_color("Free Cash Flow", fcf), unsafe_allow_html=True)
            st.markdown(format_color("Dividendo (%)", dy), unsafe_allow_html=True)

            st.markdown("### 📈 Grafici")
            for label, period in [("6 mesi", "6mo"), ("1 anno", "1y")]:
                hist = stock.history(period=period)
                if not hist.empty:
                    st.line_chart(hist["Close"])
                    media = hist["Close"].mean()
                    if isinstance(price, (int, float)):
                        diff = (price - media) / media * 100 if media else 0
                        if diff < -10:
                            st.success(f"🟢 {label}: Prezzo sotto media di {abs(diff):.1f}%")
                        elif diff > 10:
                            st.error(f"🔴 {label}: Prezzo sopra media di {abs(diff):.1f}%")
                        else:
                            st.info(f"🟡 {label}: Prezzo nella norma")

            st.markdown("### 📰 Notizie recenti")
            try:
                url = f"https://news.google.com/rss/search?q={ticker}+borsa&hl=it&gl=IT&ceid=IT:it"
                rss = requests.get(url)
                soup = BeautifulSoup(rss.content, "xml")
                for item in soup.find_all("item")[:5]:
                    st.markdown(f"- {item.title.text}")
            except:
                st.warning("⚠️ Nessuna notizia trovata.")

            st.markdown("### 📥 Scarica PDF dei dati")
            if st.button("Crea PDF"):
                buffer = BytesIO()
                pdf = canvas.Canvas(buffer)
                pdf.setFont("Helvetica", 12)
                pdf.drawString(50, 800, f"Analisi fondamentale: {ticker}")
                y = 780
                for label, val in [("Prezzo", price), ("P/E", pe), ("ROE", roe), ("Debito/Equity", debt), ("FCF", fcf), ("Dividendo", dy)]:
                    pdf.drawString(50, y, f"{label}: {val}")
                    y -= 20
                pdf.save()
                buffer.seek(0)
                st.download_button("📄 Scarica PDF", data=buffer, file_name=f"{ticker}_analisi.pdf")
        except Exception as e:
            st.error(f"⚠️ Errore nel recupero dei dati per {ticker}: {e}")

elif menu == "Consulenza AI":
    st.subheader("💡 Consulente Finanziario Intelligente")
    profilo = st.radio("Profilo Cliente", ["Conservativo", "Bilanciato", "Dinamico"])
    capitale = st.number_input("Capitale disponibile (€)", min_value=1000, step=1000)
    orizzonte = st.slider("Orizzonte (anni)", 1, 30, 5)

    if st.button("Genera Piano di Investimento"):
        st.markdown("### 🧠 Piano suggerito:")
        if profilo == "Conservativo":
            st.success("✅ 70% ETF Obbligazionari | 20% ETF Bilanciati | 10% Cash")
            st.write("Esempi: iShares Euro Govt Bond 3-7yr, Vanguard Global Bond")
        elif profilo == "Bilanciato":
            st.success("✅ 50% ETF Azionari Globali | 30% Obbligazionari | 20% ETF Bilanciati")
            st.write("Esempi: VWCE, Xtrackers Global Government Bond")
        elif profilo == "Dinamico":
            st.success("✅ 80% Azioni (ETF e singoli titoli) | 20% Cash o obbligazioni ad alto rischio")
            st.write("Esempi: Nasdaq 100 ETF, Azioni STM, ENI, Amazon")
