# Lanzar con streamlit run c_front_end.py en el terminal

import b_backend
import streamlit as st
from streamlit_chat import message

st.title("ChatGPT database")
st.write("Puedes hacerme a mí todas las preguntas y dejar trabajar al equipo de Data Science!!")

if 'preguntas' not in st.session_state:
    st.session_state.preguntas = []
if 'respuestas' not in st.session_state:
    st.session_state.respuestas = []

def click():
    if st.session_state.user != '':
        pregunta = st.session_state.user
        respuesta = b_backend.consulta(pregunta)

        st.session_state.preguntas.append(pregunta)
        st.session_state.respuestas.append(respuesta)

        # Limpiar el input de usuario después de enviar la pregunta
        st.session_state.user = ''

with st.form('my-form'):
   query = st.text_input('¿En qué te puedo ayudar?', key='user', help='Pulsa Enviar para hacer la pregunta')
   submit_button = st.form_submit_button('Enviar', on_click=click)

if st.session_state.preguntas:
    for i in range(len(st.session_state.respuestas)-1, -1, -1):
        message(st.session_state.respuestas[i], key=str(i))
