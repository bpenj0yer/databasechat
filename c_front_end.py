import b_backend
import streamlit as st
from streamlit_chat import message

st.title("Pene")
st.write("Haz preguntas sobre la base de datos y obtén respuestas analizadas.")

if 'preguntas' not in st.session_state:
    st.session_state.preguntas = []
if 'respuestas' not in st.session_state:
    st.session_state.respuestas = []

def click():
    if st.session_state.user != '':
        pregunta = st.session_state.user
        try:
            # Llamar al flujo completo en el backend
            respuesta = b_backend.procesar_pregunta(pregunta)
            st.session_state.preguntas.append(pregunta)
            st.session_state.respuestas.append(respuesta)
        except Exception as e:
            # Capturar errores inesperados
            st.session_state.respuestas.append(f"Error: {str(e)}")
        st.session_state.user = ''

with st.form('formulario'):
    query = st.text_input('¿En qué puedo ayudarte?', key='user')
    submit_button = st.form_submit_button('Enviar', on_click=click)

if st.session_state.preguntas:
    for i in range(len(st.session_state.preguntas) - 1, -1, -1):
        message(st.session_state.preguntas[i], is_user=True, key=f"q{i}")
        message(st.session_state.respuestas[i], is_user=False, key=f"r{i}")
