import streamlit as st

from app.context.examples import ESTIMATION_EXAMPLES
from app.services.llm_service import (
    LLMServiceError,
    StreamMetrics,
    build_system_prompt,
    stream_estimation,
)

st.set_page_config(page_title="Estimador CAG", page_icon="🧮")
st.title("🧮 Estimador de Software (CAG)")
st.caption(
    "Pega la transcripción de una reunión con el cliente y recibe una estimación "
    "de software generada por IA, apoyada en ejemplos de referencia (CAG)."
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_metrics" not in st.session_state:
    st.session_state.last_metrics = None

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

transcription = st.chat_input("Pega aquí la transcripción de la reunión...")

if transcription:
    st.session_state.messages.append({"role": "user", "content": transcription})
    with st.chat_message("user"):
        st.markdown(transcription)

    with st.chat_message("assistant"):
        metrics = StreamMetrics()
        try:
            estimation = st.write_stream(stream_estimation(transcription, metrics))
        except LLMServiceError as exc:
            estimation = f"⚠️ No se pudo generar la estimación: {exc}"
            st.markdown(estimation)
        else:
            st.session_state.last_metrics = metrics
            if metrics.truncated:
                st.warning("La respuesta se truncó por el límite de tokens.")

    st.session_state.messages.append({"role": "assistant", "content": estimation})

with st.sidebar:
    st.header("Contexto CAG")

    with st.expander("System prompt activo", expanded=False):
        st.text_area(
            "system_prompt",
            value=build_system_prompt(),
            height=300,
            disabled=True,
            label_visibility="collapsed",
        )

    with st.expander(f"Ejemplos de referencia ({len(ESTIMATION_EXAMPLES)})", expanded=False):
        for i, example in enumerate(ESTIMATION_EXAMPLES, start=1):
            st.markdown(f"**Ejemplo {i}**")
            st.caption(example["meeting_summary"])
            st.markdown(example["estimation"])
            st.divider()

    st.header("Métricas de la última llamada")
    metrics = st.session_state.last_metrics
    if metrics is None:
        st.caption("Todavía no se ha generado ninguna estimación.")
    else:
        st.metric("Modelo", f"{metrics.provider} / {metrics.model}")
        col1, col2 = st.columns(2)
        col1.metric("Tokens entrada", metrics.input_tokens)
        col2.metric("Tokens salida", metrics.output_tokens)
        st.metric("Tiempo de respuesta", f"{metrics.elapsed_seconds:.2f} s")

