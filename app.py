
import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from io import BytesIO
from reportlab.pdfgen import canvas

st.set_page_config(page_title="MINV – Market Investment AI", layout="wide")

# Logo e tema
st.image("https://cdn.pixabay.com/photo/2017/08/10/07/32/stock-2619124_1280.jpg", use_container_width=True)
tema_scuro = st.toggle("🌙 Tema scuro", value=False)
if tema_scuro:
    st.markdown('<style>body, .stApp {background-color: #1e1e1e; color: white;}</style>', unsafe_allow_html=True)

st.title("💼 MINV – Market Investment AI")

menu = st.sidebar.selectbox("📊 Seleziona sezione", [
    "Dashboard", "Analisi azienda", "Portafoglio simulato"
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
                delta = last - first
                pct = (delta / first) * 100
                (col1 if i % 2 == 0 else col2).metric(label=name, value=f"{last:.2f}", delta=f"{pct:+.2f}%")
        except:
            (col1 if i % 2 == 0 else col2).metric(label=name, value="N/D", delta="N/D")

    st.markdown("### 📰 Notizie economiche globali")
    for news in get_news("borsa economia"):
        st.markdown(f"- {news}")

elif menu == "Analisi azienda":
    ticker = st.text_input("Inserisci il ticker (es: AAPL, ENI.MI)", value="AAPL")
    if ticker:
        stock = yf.Ticker(ticker)
        info = stock.info
        price = info.get("currentPrice")
        pe = info.get("trailingPE")
        roe = info.get("returnOnEquity", 0) * 100 if info.get("returnOnEquity") else None
        debt = info.get("debtToEquity")
        fcf = info.get("freeCashflow")
        dy = info.get("dividendYield", 0) * 100 if info.get("dividendYield") else None

        st.subheader("📊 Dati fondamentali")
        data = {
            "Ticker": ticker,
            "Prezzo attuale": price,
            "P/E": pe,
            "ROE (%)": roe,
            "Debito/Equity": debt,
            "Free Cash Flow": fcf,
            "Dividendo (%)": dy
        }

        for k, v in data.items():
            st.write(f"**{k}:** {format_val(v)}")

        st.subheader("📥 Scarica dati in PDF")
        if st.button("Download PDF"):
            pdf = create_pdf(data)
            st.download_button("📄 Scarica PDF", data=pdf, file_name=f"{ticker}_analisi.pdf")

elif menu == "Portafoglio simulato":
    st.subheader("💼 Simulatore portafoglio")
    tickers = st.text_input("Ticker separati da virgola", "AAPL, ENI.MI").split(",")
    capitale = st.number_input("Capitale totale (€)", 1000, 1000000, 10000, step=500)

    if st.button("Simula"):
        tickers = [t.strip().upper() for t in tickers if t.strip()]
        col1, col2 = st.columns(2)
        risultati = []
        for i, t in enumerate(tickers):
            try:
                h = yf.Ticker(t).history(period="6mo")
                if not h.empty:
                    rend = (h["Close"].iloc[-1] - h["Close"].iloc[0]) / h["Close"].iloc[0]
                    quota = capitale / len(tickers)
                    finale = quota * (1 + rend)
                    risultati.append({"Ticker": t, "Rendimento %": rend * 100, "Valore Finale €": finale})
                    (col1 if i % 2 == 0 else col2).metric(t, f"{finale:.2f} €", f"{rend*100:+.2f}%")
            except:
                st.warning(f"Errore su {t}")

        if risultati:
            df = pd.DataFrame(risultati).set_index("Ticker")
            st.dataframe(df.style.format({"Rendimento %": "{:.2f}", "Valore Finale €": "€{:.2f}"}))
