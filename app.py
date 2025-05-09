
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
    "Screener azioni italiane", "AI Consulente",
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



elif menu == "Consulenza personalizzata":
    st.subheader("🧑‍💼 Piano di investimento professionale")

    with st.form("form_cliente"):
        eta = st.number_input("Età del cliente", 18, 100, 40)
        capitale = st.number_input("Capitale disponibile (€)", 1000, 1000000, 20000, step=1000)
        rischio = st.selectbox("Propensione al rischio", ["Basso", "Medio", "Alto"])
        orizzonte = st.selectbox("Orizzonte temporale", ["Breve (1-3 anni)", "Medio (3-5 anni)", "Lungo (5+ anni)"])
        submit = st.form_submit_button("Calcola piano")

    if submit:
        st.markdown("### 🧩 Piano di allocazione suggerito")

        if rischio == "Basso":
            azioni = 0.2
            obbligazioni = 0.6
            liquidità = 0.2
        elif rischio == "Medio":
            azioni = 0.5
            obbligazioni = 0.3
            liquidità = 0.2
        else:
            azioni = 0.7
            obbligazioni = 0.2
            liquidità = 0.1

        if orizzonte == "Breve (1-3 anni)":
            azioni *= 0.7
            obbligazioni *= 1.2
        elif orizzonte == "Lungo (5+ anni)":
            azioni *= 1.3
            obbligazioni *= 0.9

        tot = azioni + obbligazioni + liquidità
        azioni /= tot
        obbligazioni /= tot
        liquidità /= tot

        p_azioni = capitale * azioni
        p_obblig = capitale * obbligazioni
        p_liquidi = capitale * liquidità

        st.success(f"📈 Azioni: {azioni*100:.1f}% – €{p_azioni:,.2f}")
        st.info(f"💵 Obbligazioni: {obbligazioni*100:.1f}% – €{p_obblig:,.2f}")
        st.warning(f"💶 Liquidità: {liquidità*100:.1f}% – €{p_liquidi:,.2f}")

        st.markdown("---")
        st.markdown("### 📌 Piano operativo consigliato (Azioni)")

        titoli_italiani = {
            "ENI.MI": "Energia e dividendi solidi",
            "UCG.MI": "Banca con buona redditività",
            "STM.MI": "Tecnologia con crescita",
            "ATL.MI": "Infrastrutture difensive",
            "LUX.MI": "Consumi di lusso in crescita"
        }

        suggeriti = []
        for ticker, descrizione in titoli_italiani.items():
            try:
                h = yf.Ticker(ticker).history(period="6mo")
                if not h.empty:
                    rendimento = (h["Close"].iloc[-1] - h["Close"].iloc[0]) / h["Close"].iloc[0]
                    if rendimento > 0:
                        suggeriti.append((ticker, rendimento, descrizione))
            except:
                pass

        if suggeriti:
            for ticker, rendimento, note in sorted(suggeriti, key=lambda x: -x[1])[:3]:
                st.markdown(f"**🟢 {ticker}** – {note} — rendimento 6 mesi: **{rendimento*100:.2f}%**")
        else:
            st.markdown("⚠️ Nessun titolo italiano in trend positivo rilevato oggi.")

        st.markdown("---")
        st.markdown("### 🛠️ Strategia consigliata:")
        if rischio == "Basso":
            st.markdown("- Investire in **ETF obbligazionari** a breve scadenza")
            st.markdown("- Mantenere una parte liquida per emergenze")
        elif rischio == "Medio":
            st.markdown("- Diversificare con **ETF azionari globali** e obbligazioni corporate")
            st.markdown("- Ribilanciamento annuale")
        else:
            st.markdown("- Puntare su **growth stock** e settori in trend")
            st.markdown("- Usare ETF tematici e tecnologie")
            st.markdown("- Valutare strumenti derivati solo con capitali superiori a €50k")

        st.markdown("---")
        st.markdown("### 📉 Rischio stimato:")
        rischio_val = {"Basso": "🟢 Basso (volatilità ridotta)", "Medio": "🟡 Medio (bilanciato)", "Alto": "🔴 Alto (oscillazioni elevate)"}
        st.markdown(rischio_val[rischio])


elif menu == "Screener azioni italiane":
    st.subheader("🔢 Screener azioni italiane per fondamentali")
    titoli = {
        "ENI.MI": "Energia",
        "UCG.MI": "Banca",
        "STM.MI": "Tecnologia",
        "ATL.MI": "Infrastrutture",
        "ISP.MI": "Banca",
        "LUX.MI": "Lusso"
    }

    risultati = []
    for ticker, settore in titoli.items():
        try:
            info = yf.Ticker(ticker).info
            pe = info.get("trailingPE", 0)
            roe = info.get("returnOnEquity", 0) * 100 if info.get("returnOnEquity") else 0
            dy = info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0
            fcf = info.get("freeCashflow", 0)
            risultati.append({
                "Ticker": ticker,
                "Settore": settore,
                "P/E": round(pe, 2),
                "ROE%": round(roe, 2),
                "Dividendo%": round(dy, 2),
                "FCF": fcf
            })
        except:
            continue

    if risultati:
        df = pd.DataFrame(risultati)
        df["Score"] = (df["ROE%"] > 10).astype(int) + (df["Dividendo%"] > 2).astype(int) + (df["P/E"] > 0).astype(int)
        st.dataframe(df.sort_values("Score", ascending=False).set_index("Ticker"))

elif menu == "AI Consulente":
    st.subheader("🤖 Consulente AI (demo locale)")
    nome = st.text_input("Nome cliente")
    capitale = st.number_input("Capitale disponibile (€)", 1000, 1000000, 20000, step=500)
    rischio = st.selectbox("Rischio", ["Basso", "Medio", "Alto"])
    orizzonte = st.selectbox("Orizzonte temporale", ["1-3 anni", "3-5 anni", "5+ anni"])

    if st.button("Ottieni raccomandazione"):
        st.markdown(f"### 🧠 Raccomandazione per {nome}")
        if rischio == "Basso":
            st.write("- Puntare su ETF obbligazionari, mantenere il 20% liquido.")
        elif rischio == "Medio":
            st.write("- Mix di ETF azionari globali e obbligazioni.")
        else:
            st.write("- Azioni di crescita (STM.MI, LUX.MI), ETF tematici tecnologici.")
        st.write(f"Capitale consigliato per investimento attivo: €{capitale * 0.8:,.2f}")
