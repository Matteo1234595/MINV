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
                from reportlab.pdfgen import canvas
                from io import BytesIO
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
    st.subheader("🧑‍⚖️ Consulenza personalizzata – Guida operativa")

    with st.form("profilo_cliente"):
        eta = st.number_input("Età", 18, 100, 40)
        capitale = st.number_input("Capitale disponibile (€)", 1000, 1000000, 20000)
        rischio = st.selectbox("Rischio", ["Basso", "Medio", "Alto"])
        orizzonte = st.selectbox("Durata dell’investimento", ["1-3 anni", "3-5 anni", "5+ anni"])
        obiettivo = st.selectbox("Obiettivo", ["Protezione", "Crescita controllata", "Massima crescita"])
        invia = st.form_submit_button("📊 Crea piano dettagliato")

    if invia:
        st.write("### 📘 Strategia consigliata per profilo:")
        st.markdown(f"- **Età:** {eta} anni")
        st.markdown(f"- **Rischio:** {rischio}")
        st.markdown(f"- **Orizzonte:** {orizzonte}")
        st.markdown(f"- **Obiettivo:** {obiettivo}")
        st.markdown("---")

        if rischio == "Basso":
            st.markdown("**PASSO 1:** Investi 70% (€{:.2f}) su ETF obbligazionari come:".format(capitale * 0.7))
            st.markdown("- iShares Euro Government Bond 1-3yr (IBGL.DE)")
            st.markdown("**PASSO 2:** Mantieni 30% (€{:.2f}) su liquidità (conto deposito 2–3%).".format(capitale * 0.3))
            st.info("✔️ Piano a rischio minimo con protezione del capitale.")
        elif rischio == "Medio":
            st.markdown("**PASSO 1:** Investi 50% (€{:.2f}) su ETF azionario globale:".format(capitale * 0.5))
            st.markdown("- Vanguard FTSE All-World (VWCE.DE)")
            st.markdown("**PASSO 2:** Investi 30% (€{:.2f}) su ETF obbligazionario:".format(capitale * 0.3))
            st.markdown("- iShares Euro Corp Bond (IEAC.DE)")
            st.markdown("**PASSO 3:** Mantieni 20% cash per flessibilità.")
            st.info("✔️ Diversificazione ed equilibrio tra crescita e stabilità.")
        else:
            st.markdown("**PASSO 1:** Acquista le seguenti azioni italiane con buone prospettive:")
            azioni = ["STM.MI", "LUX.MI", "UCG.MI"]
            for t in azioni:
                try:
                    h = yf.Ticker(t).history(period="6mo")
                    rend = (h["Close"].iloc[-1] - h["Close"].iloc[0]) / h["Close"].iloc[0]
                    st.markdown(f"- **{t}** → rendimento 6 mesi: **{rend*100:.2f}%**")
                except:
                    st.markdown(f"- **{t}** → dati non disponibili")

            st.markdown("**PASSO 2:** Aggiungi ETF tematico:")
            st.markdown("- iShares Digitalisation (DGTL.DE)")
            st.markdown("**PASSO 3:** Tieni 10% (€{:.2f}) in cash per opportunità future.".format(capitale * 0.1))
            st.info("✔️ Strategia aggressiva per crescita a lungo termine.")

        st.markdown("### 🔁 Ribilanciamento e monitoraggio")
        st.markdown("- **Controllo trimestrale** del portafoglio")
        st.markdown("- **Ribilancia** se una componente supera il +10% rispetto al peso iniziale")
        st.markdown("- Rivedi strategia se cambiano obiettivi o orizzonte temporale")
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
    st.subheader("🤖 AI Consulente – Guida passo-passo")

    capitale = st.number_input("Capitale da investire (€)", 1000, 1_000_000, 20000)
    rischio = st.selectbox("Tolleranza al rischio", ["Basso", "Medio", "Alto"])
    orizzonte = st.selectbox("Durata investimento", ["1-3 anni", "3-5 anni", "5+ anni"])
    obiettivo = st.selectbox("Obiettivo primario", ["Stabilità", "Crescita controllata", "Massimo rendimento"])

    if st.button("🚀 Avvia raccomandazione"):
        st.write("### ✅ Piano consigliato con azioni concrete")
        if rischio == "Basso":
            st.markdown("**PASSO 1:** Destina **70% del capitale (€{:.2f})** su ETF obbligazionari come:".format(capitale * 0.7))
            st.markdown("- iShares Euro Government Bond 1-3yr (**IBGL.DE**) – ETF a bassa volatilità")
            st.markdown("**PASSO 2:** Mantieni **30% (€{:.2f})** in conto deposito o liquidità.".format(capitale * 0.3))
            st.info("✔️ Obiettivo: massima protezione del capitale con rendimento modesto (1.5–3%)")
        elif rischio == "Medio":
            st.markdown("**PASSO 1:** Investi **50% (€{:.2f})** su ETF globale:".format(capitale * 0.5))
            st.markdown("- Vanguard FTSE All-World (**VWCE.DE**)")
            st.markdown("**PASSO 2:** Allocare **30% (€{:.2f})** su ETF obbligazionario:".format(capitale * 0.3))
            st.markdown("- iShares Euro Corp Bond (**IEAC.DE**)")
            st.markdown("**PASSO 3:** Lascia 20% liquido.")
            st.info("✔️ Obiettivo: crescita moderata e diversificazione geografica")
        else:
            st.markdown("**PASSO 1:** Compra i seguenti titoli con performance recente positiva:")
            azioni = ["STM.MI", "LUX.MI", "UCG.MI"]
            for t in azioni:
                try:
                    h = yf.Ticker(t).history(period="6mo")
                    rend = (h["Close"].iloc[-1] - h["Close"].iloc[0]) / h["Close"].iloc[0]
                    st.markdown(f"- **{t}** – Rendimento 6 mesi: **{rend*100:.2f}%**")
                except:
                    st.markdown(f"- **{t}** – dati non disponibili")
            st.markdown("**PASSO 2:** Acquista ETF tematico:")
            st.markdown("- iShares Digitalisation (**DGTL.DE**)")
            st.markdown("**PASSO 3:** Tieni il 10% pronto per opportunità.")
            st.info("✔️ Obiettivo: massimo potenziale di rendimento con elevata esposizione al rischio")

        st.write("### 📌 Azioni da evitare o vendere")
        st.markdown("- Titoli con perdita >10% ultimi 6 mesi")
        st.markdown("- ETF difensivi se non coerenti col profilo")

        st.write("### 📋 Ricorda:")
        st.markdown("Effettua un controllo ogni **3 mesi** e **ribilancia** se una categoria supera il +10% rispetto al target.")