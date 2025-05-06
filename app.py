
import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from io import BytesIO
from fpdf import FPDF

st.set_page_config(page_title="MINV – Market Investment AI", layout="wide")
st.image("https://cdn.pixabay.com/photo/2017/08/10/07/32/stock-2619124_1280.jpg", use_container_width=True)
if st.toggle("🌙 Tema scuro"):
    st.markdown('<style>body, .stApp {background-color: #1e1e1e; color: white;}</style>', unsafe_allow_html=True)

st.title("💼 MINV – Market Investment AI")

menu = st.sidebar.selectbox("📊 Seleziona sezione", [
    "Dashboard", "Analisi azienda", "Portafoglio simulato"
])

def get_news(query):
    try:
        url = f"https://news.google.com/rss/search?q={query}+borsa&hl=it&gl=IT&ceid=IT:it"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "xml")
        return [item.title.text for item in soup.find_all("item")[:5]]
    except:
        return ["⚠️ Nessuna notizia disponibile al momento."]

def generate_pdf_report(data_dict):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for key, value in data_dict.items():
        pdf.cell(200, 10, txt=f"{key}: {value}", ln=True)
    output = BytesIO()
    pdf.output(output)
    return output

def format_val(val):
    if val is None: return "N/A"
    if isinstance(val, (int, float)):
        if abs(val) >= 1e9: return f"{val/1e9:.2f}B"
        if abs(val) >= 1e6: return f"{val/1e6:.2f}M"
        return f"{val:.2f}"
    return str(val)

def alert_price(price, media, label):
    diff = (price - media) / media * 100
    if diff < -10:
        st.success(f"🟢 {label}: Prezzo sotto media di {abs(diff):.1f}%")
    elif diff > 10:
        st.error(f"🔴 {label}: Prezzo sopra media di {abs(diff):.1f}%")
    else:
        st.info(f"🟡 {label}: Prezzo stabile ({diff:+.1f}%)")

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

    st.markdown("### 📰 Notizie finanziarie globali")
    for news in get_news("borsa economia finanza"):
        st.markdown(f"- {news}")

elif menu == "Analisi azienda":
    ticker = st.text_input("Ticker azienda (es: AAPL, ENI.MI)", value="AAPL")
    if ticker:
        stock = yf.Ticker(ticker)
        info = stock.info
        data = {
            "Nome": info.get("longName", ticker),
            "Prezzo attuale": info.get("currentPrice"),
            "P/E": info.get("trailingPE"),
            "ROE (%)": info.get("returnOnEquity", 0) * 100 if info.get("returnOnEquity") else None,
            "Debito/Equity": info.get("debtToEquity"),
            "Free Cash Flow": info.get("freeCashflow"),
            "Dividendo (%)": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else None
        }

        st.subheader("📊 Dati fondamentali")
        for k, v in data.items():
            st.write(f"**{k}:** {format_val(v)}")

        st.subheader("📈 Prezzo con Allerta")
        for label, period in [("6 mesi", "6mo"), ("1 anno", "1y")]:
            hist = stock.history(period=period)
            if not hist.empty:
                st.line_chart(hist["Close"])
                media = hist["Close"].mean()
                alert_price(data['Prezzo attuale'], media, label)

        st.subheader("🤖 AI: Tendenza stimata")
        ai = stock.history(period="1mo")
        if not ai.empty and len(ai) >= 5:
            ai["MA5"] = ai["Close"].rolling(5).mean()
            p_now = ai["Close"].iloc[-1]
            p_ma = ai["MA5"].iloc[-1]
            if p_now > p_ma:
                st.info("📈 Probabile tendenza al rialzo")
            else:
                st.warning("📉 Probabile tendenza al ribasso")

        st.subheader("📰 Notizie recenti")
        for n in get_news(ticker): st.markdown(f"- {n}")

        if st.button("📥 Scarica dati in PDF"):
            pdf = generate_pdf_report(data)
            st.download_button("Download PDF", data=pdf.getvalue(), file_name=f"{ticker}_analisi.pdf")

elif menu == "Portafoglio simulato":
    st.subheader("💼 Simulatore portafoglio")
    tickers = st.text_input("Tickers (es: AAPL, ENI.MI)", "AAPL, ENI.MI").split(",")
    capitale = st.number_input("Capitale investito (€)", 1000, 1000000, 10000, 500)

    if st.button("Simula"):
        col1, col2 = st.columns(2)
        risultati = []
        for i, t in enumerate([x.strip().upper() for x in tickers]):
            try:
                h = yf.Ticker(t).history(period="6mo")
                if not h.empty:
                    rendimento = (h["Close"].iloc[-1] - h["Close"].iloc[0]) / h["Close"].iloc[0]
                    quota = capitale / len(tickers)
                    finale = quota * (1 + rendimento)
                    risultati.append({"Ticker": t, "Rendimento %": rendimento * 100, "Valore Finale €": finale})
                    (col1 if i % 2 == 0 else col2).metric(t, f"{finale:.2f} €", f"{rendimento*100:+.2f}%")
            except:
                st.warning(f"⚠️ Errore su {t}")

        if risultati:
            df = pd.DataFrame(risultati).set_index("Ticker")
            st.dataframe(df.style.format({"Rendimento %": "{:.2f}", "Valore Finale €": "€{:.2f}"}))
