from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
import re
import streamlit as st

# Configuración de la base de datos y OpenAI
DB_USER = st.secrets["DB_USER"]
DB_PASSWORD = st.secrets["DB_PASSWORD"]
DB_HOST = st.secrets["DB_HOST"]
DB_NAME = st.secrets["DB_NAME"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# Crear el motor de conexión SQLAlchemy
engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")

# Configurar LLM y prompts
llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini", openai_api_key=OPENAI_API_KEY)

# Primer Prompt: Generar la consulta SQL
sql_prompt_template = """
Eres un asistente de análisis de datos y consultas SQL para una tabla llamada `Respuestas`. Esta tabla contiene información sobre trabajadores que respondieron un formulario. Las columnas disponibles son:

- `id`: Identificador único.
- `empresa`: Nombre de la empresa.
- `nombre`: Nombre del trabajador.
- `genero`: Género del trabajador (por ejemplo, "Masculino", "Femenino", u "Otro").
- `edad`: Edad del trabajador.
- `estudios`: Nivel educativo del trabajador.
- `correo`: Correo electrónico.
- `antigüedad`: Antigüedad laboral en años.
- `sueldo`: Sueldo mensual.
- `horas`: Horas trabajadas por semana.
- `posicion`: Puesto laboral.

**Instrucciones**:
1. Lee cuidadosamente la pregunta del usuario.
2. Genera una consulta SQL válida que seleccione las columnas completas necesarias para responder la pregunta.
3. Si la pregunta menciona comparación, estadísticas o relaciones entre datos, selecciona las columnas relevantes completas (sin realizar cálculos en SQL).
4. Devuelve solo la consulta SQL sin ninguna explicación adicional.
5. No quiero que des ningún cálculo en la respuesta, sino directamente la columna necesaria. Pero si en la pregunta pide una columna con una indicación concreta, sí que puedes filtrarlo.
    Por ejemplo, si te pido la media de sueldo en una empresa concreta, no hace falta que des como respuesta todas las empresas y todos los sueldos, sino solo los sueldos de los trabajadores de esa empresa,

Ejemplos:
- Pregunta: ¿Cuál es la diferencia de sueldo entre hombres y mujeres?
  Consulta: SELECT genero, sueldo FROM Respuestas;
- Pregunta: ¿Qué empresas tienen trabajadores con más de 10 años de antigüedad?
  Consulta: SELECT empresa, antigüedad FROM Respuestas;
- Pregunta: ¿Cuál es el promedio de edad de los trabajadores?
  Consulta: SELECT edad FROM Respuestas;

Pregunta del usuario: {question}
"""
sql_prompt = PromptTemplate(template=sql_prompt_template, input_variables=["question"])

# Segundo Prompt: Crear una respuesta directa y analítica
response_prompt_template = """
Eres un asistente de datos. Responde de forma directa y concisa a la pregunta del usuario utilizando los datos proporcionados.

Pregunta del usuario: {question}
Datos obtenidos (en formato tabla):
{data}

Tu respuesta debe:
1. Ser breve y directa.
2. Incluir solo la información necesaria para responder la pregunta.
3. Evitar explicaciones adicionales o análisis que no se hayan solicitado.

Ejemplo:
- Pregunta: ¿Cuántas empresas hay?
  Respuesta: Hay un total de 4 empresas diferentes (TechCorp, Innovatech, FutureTech y MegaCorp).

  Si la tabla es excesivamente larga, no la incluyas en la respuesta porque puede afectar a la facilidad de comprensión.

Debes ser capaz de justificar la respuesta, pero sin dar datos innecesarios. Por ejemplo si te pregunto una diferencia salarial entre géneros, no hace falta que me digas cuánto ha cobrado cada persona de la tabla, pero si me puedes dar una media de cada género o un porcentaje de diferencia.
"""
response_prompt = PromptTemplate(template=response_prompt_template, input_variables=["question", "data"])

# Función para generar la consulta SQL
def generar_consulta_sql(pregunta):
    return llm.predict(sql_prompt.format(question=pregunta))

# Función para procesar la consulta SQL
def ejecutar_consulta(consulta_sql):
    try:
        with engine.connect() as connection:
            consulta_text = text(consulta_sql)
            resultado = connection.execute(consulta_text)
            
            # Obtener nombres de las columnas
            columnas = resultado.keys()
            
            # Crear DataFrame con los resultados
            datos = [list(row) for row in resultado]
            df = pd.DataFrame(datos, columns=columnas)
            
            return df
    except SQLAlchemyError as e:
        return f"Error al ejecutar la consulta: {str(e)}"

# Función para generar la respuesta final
def generar_respuesta_elaborada(pregunta, datos):
    datos_str = datos.to_string(index=False) if isinstance(datos, pd.DataFrame) else datos
    return llm.predict(response_prompt.format(question=pregunta, data=datos_str))

# Función principal para manejar el flujo completo
def procesar_pregunta(pregunta_usuario):
    try:
        # Generar la consulta SQL
        consulta_sql = generar_consulta_sql(pregunta_usuario)
        print("Consulta SQL generada:", consulta_sql)
        
        # Validar la consulta generada
        consulta_sql = re.search(r"(SELECT .* FROM .*;)", consulta_sql, re.IGNORECASE)
        if not consulta_sql:
            return "Error: No se pudo generar una consulta válida. Verifica tu pregunta."
        consulta_sql = consulta_sql.group(0)
        
        # Ejecutar la consulta y obtener los datos
        datos_obtenidos = ejecutar_consulta(consulta_sql)
        if isinstance(datos_obtenidos, str):  # Si ocurrió un error
            return datos_obtenidos

        print("Datos obtenidos:", datos_obtenidos)

        # Generar una respuesta elaborada
        respuesta = generar_respuesta_elaborada(pregunta_usuario, datos_obtenidos)
        return respuesta
    except Exception as e:
        return f"Error procesando la pregunta: {str(e)}"
