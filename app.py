import streamlit as st
from streamlit_drawable_canvas import st_canvas
import fitz  # PyMuPDF
from PIL import Image
import io

st.set_page_config(page_title="Selector de zona en PDF", layout="centered")

st.title("Selector visual de zona en PDF")

# 1. Cargar PDF
uploaded_pdf = st.file_uploader("Carga un PDF", type=["pdf"])

if uploaded_pdf:
    pdf_doc = fitz.open(stream=uploaded_pdf.read(), filetype="pdf")
    num_pages = pdf_doc.page_count

    # 2. Selección de página
    page_num = st.number_input("Selecciona la página", min_value=1, max_value=num_pages, value=1)

    # 3. Renderizar la página a imagen
    page = pdf_doc.load_page(page_num - 1)
    zoom = 2  # calidad de imagen (más grande, mejor definición)
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("png")
    image = Image.open(io.BytesIO(img_bytes))
    width, height = image.size

    st.write(f"Imagen renderizada tamaño: {width} x {height} px")
    st.write("Dibuja un recuadro sobre la imagen para seleccionar zona:")

    # 4. Canvas para dibujar
    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.1)", 
        stroke_width=3,
        stroke_color="#FF0000",
        background_image=image,
        update_streamlit=True,
        height=height,
        width=width,
        drawing_mode="rect",
        key="canvas",
    )

    # 5. Obtener y mostrar las coordenadas
    if canvas_result.json_data is not None:
        objects = canvas_result.json_data.get("objects", [])
        if objects:
            obj = objects[-1]  # último rectángulo dibujado
            x = obj["left"]
            y = obj["top"]
            w = obj["width"]
            h = obj["height"]
            st.success(f"Coordenadas en imagen (px): x={x:.1f}, y={y:.1f}, ancho={w:.1f}, alto={h:.1f}")

            # Convertir a coordenadas de PDF (píxeles -> puntos PDF)
            # PyMuPDF renderiza la imagen a una escala de "zoom"
            pdf_x0 = x / zoom
            pdf_y0 = y / zoom
            pdf_x1 = (x + w) / zoom
            pdf_y1 = (y + h) / zoom
            st.info(f"Coordenadas en PDF (pt): x0={pdf_x0:.1f}, y0={pdf_y0:.1f}, x1={pdf_x1:.1f}, y1={pdf_y1:.1f}")

            st.write("Estas coordenadas puedes usarlas para extraer esa zona con PyMuPDF u otras librerías.")
        else:
            st.warning("Dibuja un recuadro para ver las coordenadas.")

else:
    st.info("Sube un archivo PDF para comenzar.")
