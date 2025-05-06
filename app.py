
import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup

# ⚙️ Configurazione iniziale
st.set_page_config(page_title="MINV - Market Investment AI", layout="wide")

# 🎨 Logo e tema
logo_url = "https://cdn.pixabay.com/photo/2017/08/10/07/32/stock-2619124_1280.jpg"
st.image(logo_url, use_container_width=True)

tema_scuro = st.toggle("🌗 Tema scuro", value=False)
if tema_scuro:
    st.markdown('<style>body, .stApp {background-color: #1e1e1e; color: white;}</style>', unsafe_allow_html=True)

st.title("💼 MINV – Market Investment AI")

menu = st.sidebar.selectbox("📊 Seleziona sezione", [
    "Dashboard", "Analisi azienda"
])

def format_val(val):
    if val is None: return "N/A"
    if isinstance(val, (int, float)):
        abs_val = abs(val)
        if abs_val >= 1e9:
            return f"{val / 1e9:.2f}B"
        elif abs_val >= 1e6:
            return f"{val / 1e6:.2f}M"
        return f"{val:.2f}"
    return val

def colored_text(label, value, positive=True):
    if value == "N/A": return f"**{label}:** {value}"
    color = "green" if (value > 0 if positive else value < 0) else "red"
    return f"<span style='color:{color}'><strong>{label}: {format_val(value)}</strong></span>"

def get_news(company):
    try:
        url = f"https://news.google.com/rss/search?q={company}+borsa+site:ansa.it+OR+site:ilsole24ore.com&hl=it&gl=IT&ceid=IT:it"
        res = requests.get(url)
        soup = BeautifulSoup(res.content, features="xml")
        items = soup.findAll("item")[:5]
        return [item.title.text for item in items]
    except:
        return []

def analizza_titolo(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    name = info.get("longName", ticker)
    price = info.get("currentPrice", None)
    pe = info.get("trailingPE", None)
    roe = info.get("returnOnEquity", None)
    if roe: roe *= 100
    debt = info.get("debtToEquity", None)
    fcf = info.get("freeCashflow", None)
    dy = info.get("dividendYield", None)
    if dy: dy *= 100
    dr = info.get("dividendRate", None)

    st.subheader(f"📊 Fondamentali per {name}")
    st.markdown(colored_text("Prezzo attuale", price), unsafe_allow_html=True)
    st.markdown(colored_text("P/E", pe), unsafe_allow_html=True)
    st.markdown(colored_text("ROE (%)", roe), unsafe_allow_html=True)
    st.markdown(colored_text("Debito/Equity", debt, positive=False), unsafe_allow_html=True)
    st.markdown(colored_text("Free Cash Flow", fcf), unsafe_allow_html=True)
    st.markdown(colored_text("Dividendo %", dy), unsafe_allow_html=True)
    st.markdown(colored_text("Dividendo annuale", dr), unsafe_allow_html=True)

    score = sum([
        pe and 8 < pe < 25,
        roe and roe > 15,
        debt and debt < 100,
        fcf and fcf > 0
    ])
    st.metric("Buffett Score", f"{score}/4")

    st.subheader("📈 Prezzo e media con Alert")
    for label, yf_period in [("6 mesi", "6mo"), ("12 mesi", "1y")]:
        hist = stock.history(period=yf_period)
        if not hist.empty and price:
            st.line_chart(hist["Close"])
            media = hist["Close"].mean()
            diff = (price - media) / media * 100
            if diff < -10:
                st.success(f"🟢 [{label}] Prezzo sottovalutato del {abs(diff):.1f}% rispetto alla media")
            elif diff > 10:
                st.error(f"🔴 [{label}] Prezzo sopravvalutato del {abs(diff):.1f}% rispetto alla media")
            else:
                st.info(f"🟡 [{label}] Prezzo nella norma (±10%) rispetto alla media")

    st.subheader("🤖 AI: previsione prossimi 5 giorni")
    data = stock.history(period="1mo")
    if not data.empty and len(data) >= 10:
        data["MA5"] = data["Close"].rolling(window=5).mean()
        ultimo_prezzo = data["Close"].iloc[-1]
        media_recente = data["MA5"].iloc[-1]
        direzione = "📈 Probabile salita" if ultimo_prezzo > media_recente else "📉 Probabile discesa"
        confidenza = abs((ultimo_prezzo - media_recente) / media_recente) * 100
        st.info(f"{direzione} con confidenza stimata del {confidenza:.1f}%")
    else:
        st.warning("Dati insufficienti per la previsione AI.")

    st.subheader("📰 Notizie recenti")
    for n in get_news(name): st.markdown(f"- {n}")

if menu == "Dashboard":
    st.subheader("📈 Panoramica Mercati Principali")

    indices = {
        "FTSE MIB (Italia)": "^FTSEMIB.MI",
        "NASDAQ 100 (USA)": "^NDX",
        "S&P 500 (USA)": "^GSPC",
        "DAX (Germania)": "^GDAXI"
    }

    col1, col2 = st.columns(2)
    for i, (nome, symbol) in enumerate(indices.items()):
        try:
            data = yf.Ticker(symbol).history(period="5d")
            if not data.empty and "Close" in data.columns:
                last = data["Close"].iloc[-1]
                first = data["Close"].iloc[0]
                delta = last - first
                pct = (delta / first) * 100
                val = f"{last:.2f}"
                dlt = f"{pct:+.2f}%"
            else:
                val = "N/D"
                dlt = "N/D"
        except:
            val = "N/D"
            dlt = "N/D"

        (col1 if i % 2 == 0 else col2).metric(label=nome, value=val, delta=dlt)

    st.markdown("---")
    st.markdown("📰 Ultime notizie economiche globali")
    try:
        url = "https://news.google.com/rss/search?q=borsa+economia+site:reuters.com+OR+site:bloomberg.com&hl=it&gl=IT&ceid=IT:it"
        soup = BeautifulSoup(requests.get(url).content, "xml")
        for item in soup.findAll("item")[:5]:
            st.markdown(f"- {item.title.text}")
    except:
        st.warning("⚠️ Impossibile caricare le notizie globali.")


elif menu == "Portafoglio simulato":
    st.subheader("💼 Portafoglio simulato")
    st.markdown("Aggiungi titoli e importi per vedere la performance teorica negli ultimi 6 mesi.")

    tickers_input = st.text_input("Inserisci ticker separati da virgola (es: AAPL, ENI.MI, UCG.MI)", value="AAPL, ENI.MI")
    capitale_totale = st.number_input("Capitale totale investito (€)", min_value=1000, value=10000, step=500)

    if st.button("Simula portafoglio"):
        tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
        col1, col2 = st.columns(2)
        risultati = []
        for i, t in enumerate(tickers):
            try:
                data = yf.Ticker(t).history(period="6mo")
                if data.empty:
                    st.warning(f"Dati non disponibili per {t}")
                    continue
                rendimento = (data["Close"].iloc[-1] - data["Close"].iloc[0]) / data["Close"].iloc[0]
                quota = capitale_totale / len(tickers)
                valore_finale = quota * (1 + rendimento)
                risultati.append({"Ticker": t, "Rendimento %": rendimento * 100, "Valore finale": valore_finale})
                (col1 if i % 2 == 0 else col2).metric(label=t, value=f"{valore_finale:.2f} €", delta=f"{rendimento*100:+.2f}%")
            except Exception as e:
                st.error(f"Errore su {t}: {e}")

        if risultati:
            df = pd.DataFrame(risultati)
            st.markdown("### 📊 Riepilogo portafoglio")
            st.dataframe(df.set_index("Ticker").style.format({"Rendimento %": "{:.2f}", "Valore finale": "€{:.2f}"}))
