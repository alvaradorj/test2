import streamlit as st
from streamlit_drawable_canvas import st_canvas
import pdfplumber
import io
import base64

st.title("Canvas TEST con imagen base64")

uploaded_file = st.file_uploader("Sube tu PDF", type="pdf")
if uploaded_file:
    pdf_bytes = uploaded_file.read()
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        page = pdf.pages[0]
        img = page.to_image(resolution=150).original.convert("RGB")
        st.image(img, caption="Previsualización directa", use_container_width=True)
        width, height = img.size

    def pil_to_base64(img):
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        base64_img = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{base64_img}"

    img_base64 = pil_to_base64(img)

    st.markdown("Canvas visual con imagen PDF")
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.2)",
        stroke_width=2,
        stroke_color="#ff8800",
        background_color="#fff",
        background_image_url=img_base64,
        update_streamlit=True,
        height=height,
        width=width,
        drawing_mode="rect",
        key="canvas_test"
    )
