
import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from reportlab.pdfgen import canvas
from io import BytesIO

st.set_page_config(page_title="MINV Pro App", layout="wide")
st.title("📊 MINV Pro App")

menu = st.sidebar.selectbox("Seleziona sezione", ['Dashboard mercato', 'Analisi azienda', 'Consulenza AI', 'Simulatore portafoglio', 'Screener azioni italiane'])

if menu == "Dashboard mercato":
    st.subheader("📈 Dashboard Mercato")
    st.write("Contenuto dashboard...")

elif menu == "Analisi azienda":
    st.subheader("📊 Analisi azienda – vedi app.py principale")

elif menu == "Consulenza AI":
    st.subheader("💡 Consulenza AI – piano personalizzato")
    st.write("Contenuto della sezione AI...")

elif menu == "Simulatore portafoglio":
    st.subheader("💼 Simulatore di Portafoglio")
    st.write("Contenuto del simulatore...")

elif menu == "Screener azioni italiane":
    st.subheader("🔎 Screener Azioni Italiane")
    st.write("Contenuto dello screener...")
