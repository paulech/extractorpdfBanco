import streamlit as st
import pandas as pd
import pdfplumber
import re
from io import BytesIO

st.set_page_config(page_title="Extractor Bancario PDF → Excel", layout="centered")
st.title("🔍 Extractor de Datos de Extractos Bancarios")
st.markdown("Bro!!! Carga tu PDF bancario (Galicia, BBVA, etc.), y descargá un Excel con los movimientos organizados y totalizados por concepto.")

uploaded_file = st.file_uploader("📄 Subí tu archivo PDF", type="pdf")

if uploaded_file:
    def str_to_float(num_str):
        return float(num_str.replace('.', '').replace(',', '.')) if num_str else 0.0

    date_amount_line = re.compile(r"^(\d{2}/\d{2}/\d{2})\s+(.*?)\s+([\-0-9\.,]+)\s+([\-0-9\.,]+)$")

    transactions = []

    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            for line in text.split("\n"):
                match = date_amount_line.match(line.strip())
                if match:
                    fecha, descripcion, monto_str, saldo_str = match.groups()
                    monto = str_to_float(monto_str)
                    saldo = str_to_float(saldo_str)
                    transactions.append({
                        "Fecha": fecha,
                        "Descripción": descripcion.strip(),
                        "Crédito": monto if monto > 0 else 0.0,
                        "Débito": -monto if monto < 0 else 0.0,
                        "Saldo": saldo,
                        "Concepto": " ".join(descripcion.strip().split()[:3])
                    })

    df = pd.DataFrame(transactions)
    resumen_concepto = df.groupby("Concepto")[["Crédito", "Débito"]].sum().sort_values(by="Crédito", ascending=False)
    resumen_descripcion = df.groupby("Descripción")[["Crédito", "Débito"]].sum().sort_values(by="Crédito", ascending=False)

    st.subheader("🔢 Vista previa de transacciones")
    st.dataframe(df.head(50))

    st.subheader("📊 Total por Concepto")
    st.dataframe(resumen_concepto)

    st.subheader("📋 Total por Descripción (Top 50)")
    st.dataframe(resumen_descripcion.head(50))

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Transacciones")
        resumen_concepto.to_excel(writer, sheet_name="Resumen Concepto")
        resumen_descripcion.to_excel(writer, sheet_name="Resumen Descripción")

    st.download_button(
        label="📥 Descargar Excel completo",
        data=output.getvalue(),
        file_name="Extracto_Procesado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
