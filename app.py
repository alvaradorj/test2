import streamlit as st
from streamlit_drawable_canvas import st_canvas
import fitz  # PyMuPDF
from PIL import Image
import io

st.set_page_config(page_title="Selector de zona en PDF", layout="centered")
st.title("Selector visual de zona en PDF")

uploaded_pdf = st.file_uploader("Carga un PDF", type=["pdf"])

if uploaded_pdf:
    # Intentar abrir el PDF
    try:
        pdf_doc = fitz.open(stream=uploaded_pdf.read(), filetype="pdf")
    except Exception as e:
        st.error(f"No se pudo abrir el PDF: {e}")
        st.stop()

    num_pages = pdf_doc.page_count
    if num_pages == 0:
        st.error("El PDF no tiene páginas.")
        st.stop()

    page_num = st.number_input("Selecciona la página", min_value=1, max_value=num_pages, value=1)

    # Renderizar la página a imagen
    page = pdf_doc.load_page(page_num - 1)
    zoom = 2  # Mayor zoom = mejor calidad, pero más consumo de RAM
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)

    try:
        img_bytes = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
    except Exception as e:
        st.error(f"Error al renderizar la página: {e}")
        st.stop()

    width, height = image.size

    st.write(f"Imagen renderizada tamaño: {width} x {height} px")
    st.write("Dibuja un recuadro sobre la imagen para seleccionar zona:")

    # Mostrar el canvas sólo si la imagen está bien cargada
    if image is not None:
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

        # Si se dibuja un rectángulo, mostrar las coordenadas
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
                pdf_x0 = x / zoom
                pdf_y0 = y / zoom
                pdf_x1 = (x + w) / zoom
                pdf_y1 = (y + h) / zoom
                st.info(f"Coordenadas en PDF (pt): x0={pdf_x0:.1f}, y0={pdf_y0:.1f}, x1={pdf_x1:.1f}, y1={pdf_y1:.1f}")
            else:
                st.warning("Dibuja un recuadro para ver las coordenadas.")
    else:
        st.error("No se pudo cargar la imagen de la página seleccionada.")
else:
    st.info("Sube un archivo PDF para comenzar.")
