import streamlit as st
from streamlit_drawable_canvas import st_canvas
import pdfplumber
import pandas as pd
import io
from PIL import Image
import re
import base64

def pil_to_base64(img):
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    base64_img = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{base64_img}"

st.set_page_config(page_title="PDF a Excel - Zonas de datos", layout="wide")
st.title("PDF a Excel: Selecciona zonas de datos manualmente")

st.markdown("""
1. **Sube tu PDF**
2. **Selecciona visualmente** las zonas que contienen datos (dibuja uno o más rectángulos)
3. **Extrae y descarga el Excel**
""")

uploaded_file = st.file_uploader("Sube tu archivo PDF", type="pdf")

if not uploaded_file:
    st.info("Sube un PDF para empezar.")
else:
    pdf_bytes = uploaded_file.read()
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        first_page = pdf.pages[0]
        img_wrapper = first_page.to_image(resolution=150)
        page_image = img_wrapper.original

        # Siempre RGB para máxima compatibilidad
        buffer_img = io.BytesIO()
        page_image.save(buffer_img, format="PNG")
        buffer_img.seek(0)
        page_image = Image.open(buffer_img).convert("RGB")
        page_width, page_height = page_image.size

        # Convertimos a base64 para fondo canvas
        page_image_base64 = pil_to_base64(page_image)

    st.markdown("Dibuja **rectángulos** sobre las áreas que contienen datos.")
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.2)",  # Naranja translúcido
        stroke_width=2,
        stroke_color="#ff8800",
        background_color="#fff",
        background_image=page_image_base64,  # <-- Base64 string, nunca numpy
        update_streamlit=True,
        height=page_height,
        width=page_width,
        drawing_mode="rect",
        key="canvas"
    )

    # Procesado de zonas seleccionadas
    if canvas_result.json_data:
        zonas = []
        for obj in canvas_result.json_data["objects"]:
            if obj["type"] == "rect":
                left = obj["left"]
                top = obj["top"]
                width = obj["width"]
                height = obj["height"]
                zonas.append((left, top, left + width, top + height))

        if zonas:
            st.success(f"{len(zonas)} zona(s) seleccionada(s). Puedes continuar.")
            if st.button("Extraer datos y generar Excel"):
                with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                    datos = []
                    regex_tramo = re.compile(r'(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+)\s+(\d{2}:\s*\d{2}:\s*\d{2}\.\d*)')
                    for zona in zonas:
                        crop = pdf.pages[0].crop(zona)
                        texto = crop.extract_text() or ""
                        segmento = ""
                        for linea in texto.split("\n"):
                            may = linea.upper()
                            for seg in {"PRÓLOGO", "SS1", "SS2", "REGULARIDAD", "EXCEPCIONALES"}:
                                if seg in may:
                                    segmento = seg
                                    break
                            match = regex_tramo.search(linea)
                            if match and segmento:
                                desde, hasta, media, _ = match.groups()
                                label = segmento
                                if segmento.upper() == "EXCEPCIONALES":
                                    label = f"{segmento}-EX"
                                datos.append({
                                    "Segmento": label,
                                    "Desde (km)": float(desde.replace(",", ".")),
                                    "Hasta (km)": float(hasta.replace(",", ".")),
                                    "Velocidad Media (km/h)": int(media)
                                })

                if datos:
                    df = pd.DataFrame(datos, columns=["Segmento", "Desde (km)", "Hasta (km)", "Velocidad Media (km/h)"])
                    df["Desde (km)"] = df["Desde (km)"].map(lambda x: f"{x:.2f}")
                    df["Hasta (km)"] = df["Hasta (km)"].map(lambda x: f"{x:.2f}")
                    st.dataframe(df)
                    buffer = io.BytesIO()
                    df.to_excel(buffer, index=False, engine="openpyxl")
                    buffer.seek(0)
                    st.download_button(
                        label="⬇️ Descargar Excel",
                        data=buffer,
                        file_name="resultado.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.error("No se extrajo ningún dato. Ajusta las zonas o revisa el formato del PDF.")
        else:
            st.warning("Dibuja al menos una zona antes de continuar.")
    else:
        st.info("Dibuja con el ratón las zonas de datos sobre la imagen del PDF.")
