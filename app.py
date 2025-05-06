import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup

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

def colored(label, value, positive=True):
    if value == "N/A": return f"**{label}:** {value}"
    color = "green" if (value > 0 if positive else value < 0) else "red"
    return f"<span style='color:{color}'><strong>{label}: {format_val(value)}</strong></span>"

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
        st.markdown(colored("Prezzo", price), unsafe_allow_html=True)
        st.markdown(colored("P/E", pe), unsafe_allow_html=True)
        st.markdown(colored("ROE (%)", roe), unsafe_allow_html=True)
        st.markdown(colored("Debt/Equity", debt, positive=False), unsafe_allow_html=True)
        st.markdown(colored("Free Cash Flow", fcf), unsafe_allow_html=True)
        st.markdown(colored("Dividendo %", dy), unsafe_allow_html=True)

        st.subheader("📈 Prezzo con media mobile")
        for label, period in [("6 mesi", "6mo"), ("1 anno", "1y")]:
            hist = stock.history(period=period)
            if not hist.empty:
                st.line_chart(hist["Close"])
                media = hist["Close"].mean()
                diff = (price - media) / media * 100 if media else 0
                if diff < -10:
                    st.success(f"🟢 {label}: Prezzo sotto la media di {abs(diff):.1f}%")
                elif diff > 10:
                    st.error(f"🔴 {label}: Prezzo sopra la media di {abs(diff):.1f}%")
                else:
                    st.info(f"🟡 {label}: Prezzo nella media (±10%)")

        st.subheader("🤖 AI: Tendenza stimata")
        ai_data = stock.history(period="1mo")
        if not ai_data.empty and len(ai_data) >= 5:
            ai_data["MA5"] = ai_data["Close"].rolling(window=5).mean()
            p_now = ai_data["Close"].iloc[-1]
            p_ma = ai_data["MA5"].iloc[-1]
            if p_now > p_ma:
                st.info("📈 Probabile tendenza al rialzo (MA5)")
            else:
                st.warning("📉 Probabile tendenza al ribasso (MA5)")

        st.subheader("📰 Notizie recenti")
        for news in get_news(ticker): st.markdown(f"- {news}")

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