import streamlit as st
from streamlit_drawable_canvas import st_canvas
import pdfplumber
import io

st.title("Canvas TEST con imagen PDF de fondo")

uploaded_file = st.file_uploader("Sube tu PDF", type="pdf")
if uploaded_file:
    pdf_bytes = uploaded_file.read()
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        page = pdf.pages[0]
        img = page.to_image(resolution=150).original.convert("RGB")
        st.image(img, caption="Previsualización directa", use_container_width=True)
        st.write(type(img), img.mode, img.size)
        width, height = img.size

    st.markdown("Canvas visual con imagen PDF")
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.2)",
        stroke_width=2,
        stroke_color="#ff8800",
        background_color="#fff",
        background_image=img,  # <--- DIRECTAMENTE el objeto PIL.Image
        update_streamlit=True,
        height=height,
        width=width,
        drawing_mode="rect",
        key="canvas_test"
    )
