import streamlit as st
import pdfplumber
from PIL import Image
import pandas as pd
import io
import re

st.title("PDF a Excel: Extracción de zonas múltiples y consecutivas")

uploaded_file = st.file_uploader("Sube tu archivo PDF", type="pdf")

def coords_img2pdf(x0, y0, x1, y1, img_width, img_height, pdf_width, pdf_height):
    x0_pdf = x0 * pdf_width / img_width
    x1_pdf = x1 * pdf_width / img_width
    y0_pdf = pdf_height - (y0 * pdf_height / img_height)
    y1_pdf = pdf_height - (y1 * pdf_height / img_height)
    return (x0_pdf, min(y0_pdf, y1_pdf), x1_pdf, max(y0_pdf, y1_pdf))

if uploaded_file:
    pdf_bytes = uploaded_file.read()
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        num_pages = len(pdf.pages)
        st.info(f"El PDF tiene {num_pages} páginas.")

        page_number = st.number_input("Selecciona la página (empezando en 1)", min_value=1, max_value=num_pages, value=1)
        page = pdf.pages[page_number-1]
        img = page.to_image(resolution=150).original.convert("RGB")
        st.image(img, caption=f"Página {page_number}", use_container_width=True)
        img_width, img_height = img.size
        pdf_width, pdf_height = page.width, page.height
        st.write(f"Tamaño de la imagen: {img_width}px x {img_height}px")
        st.write(f"Tamaño del PDF: {pdf_width} x {pdf_height}")

        # Botón para descargar la imagen de la página y facilitar medición en Paint/GIMP
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        st.download_button(
            "Descargar imagen de la página para inspección",
            data=img_bytes.getvalue(),
            file_name=f"pagina_{page_number}.png"
        )

    st.subheader("Define las zonas y los grupos")

    if "zonas" not in st.session_state:
        st.session_state["zonas"] = []

    grupo_opciones = ["Nuevo grupo"] + [f"Grupo {i+1}" for i in range(len(st.session_state["zonas"]))]
    grupo_seleccionado = st.selectbox("¿A qué grupo pertenece esta zona?", grupo_opciones)
    x0 = st.slider("x0 (izquierda)", 0, img_width, 0, 1)
    y0 = st.slider("y0 (arriba)", 0, img_height, 0, 1)
    x1 = st.slider("x1 (derecha)", 0, img_width, img_width, 1)
    y1 = st.slider("y1 (abajo)", 0, img_height, img_height, 1)

    # Previsualización del recorte de la imagen
    crop_img = img.crop((x0, y0, x1, y1))
    st.image(crop_img, caption="Previsualización del recorte", use_container_width=True)

    # Previsualización del texto PDF real
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        page = pdf.pages[page_number-1]
        pdf_crop_coords = coords_img2pdf(x0, y0, x1, y1, img_width, img_height, pdf_width, pdf_height)
        try:
            crop = page.crop(pdf_crop_coords)
            texto_crop = crop.extract_text() or ""
        except Exception as e:
            texto_crop = f"Error en las coordenadas seleccionadas: {e}"
        st.text_area("Texto extraído en la zona seleccionada:", texto_crop, height=120)

    if st.button("Añadir zona"):
        nueva_zona = {
            "pagina": page_number-1,
            "coords": (x0, y0, x1, y1)
        }
        if grupo_seleccionado == "Nuevo grupo":
            st.session_state["zonas"].append([nueva_zona])
        else:
            idx = int(grupo_seleccionado.split(" ")[1]) - 1
            st.session_state["zonas"][idx].append(nueva_zona)
        st.success(f"Zona añadida a {grupo_seleccionado}.")

    if st.session_state["zonas"]:
        st.markdown("#### Zonas añadidas (por grupos):")
        for i, grupo in enumerate(st.session_state["zonas"]):
            st.markdown(f"**Grupo {i+1}:**")
            for z in grupo:
                st.markdown(f"- Página {z['pagina']+1} | x0={z['coords'][0]}, y0={z['coords'][1]}, x1={z['coords'][2]}, y1={z['coords'][3]}")

        if st.button("Limpiar todas las zonas"):
            st.session_state["zonas"] = []
            st.experimental_rerun()

    if st.session_state["zonas"] and st.button("Extraer datos de todas las zonas y descargar Excel"):
        datos_finales = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for grupo in st.session_state["zonas"]:
                texto_acumulado = ""
                for zona in grupo:
                    page = pdf.pages[zona["pagina"]]
                    pdf_crop_coords = coords_img2pdf(*zona["coords"], img_width, img_height, page.width, page.height)
                    crop = page.crop(pdf_crop_coords)
                    texto_acumulado += (crop.extract_text() or "") + "\n"
                datos = []
                regex_tramo = re.compile(r'(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+)\s+(\d{2}:\s*\d{2}:\s*\d{2}\.\d*)')
                segmento = ""
                for linea in texto_acumulado.split("\n"):
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
                datos_finales.extend(datos)

        if datos_finales:
            df = pd.DataFrame(datos_finales, columns=["Segmento", "Desde (km)", "Hasta (km)", "Velocidad Media (km/h)"])
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
            st.warning("No se encontraron datos en las zonas/grupos seleccionados.")

else:
    st.info("Sube un PDF para empezar.")
