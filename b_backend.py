from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from sqlalchemy import create_engine, text  # Importamos `text` de SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
import os
import re

# Configurar la clave de API de OpenAI
openai_api_key = os.getenv("OPENAI_API_KEY")

# Leer los datos de conexión desde variables de entorno
usuario = os.getenv("DB_USER")
contraseña = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
nombre_db = os.getenv("DB_NAME")

# Crear el motor de conexión SQLAlchemy
engine = create_engine(f"mysql+pymysql://{usuario}:{contraseña}@{host}/{nombre_db}")

# Crear el modelo de lenguaje usando `gpt-4o-mini`
llm = ChatOpenAI(temperature=0, model_name='gpt-4o-mini')

# Crear el prompt para generar consultas SQL con mayor capacidad de inferencia
prompt_template = """
Eres un asistente de consultas SQL en MySQL. Sigue estos pasos:
1. Lee cuidadosamente la pregunta del usuario e identifica qué información específica necesita.
2. 2. Primero, verifica si el dato solicitado existe como una columna en la tabla `usuarios`. Si es así, genera una consulta SQL simple para obtenerlo.
3. Si el usuario menciona un dato de manera general (como "correo electrónico", "edad", "nombre completo"), infiere cuál columna corresponde en la tabla `usuarios`. Por ejemplo, asocia "correo electrónico" con la columna `email`.
4. Si el dato solicitado no está directamente disponible como columna, intenta derivarlo a partir de otros datos. Usa cálculos o combinaciones cuando sea necesario.
5. Si la pregunta implica una verificación, comparación o un filtro, utiliza condiciones en SQL para obtener solo los resultados relevantes.
6. Si la consulta pide una lista de resultados (por ejemplo, "todos los nombres"), devuelve todos los registros relevantes, no solo el primero.
7. Asegúrate de que la consulta SQL sea precisa y devuelva únicamente los datos necesarios para responder la pregunta.
8. No incluyas explicaciones adicionales ni información fuera de la consulta SQL.

Pregunta del usuario: {question}
"""
prompt = PromptTemplate(template=prompt_template, input_variables=["question"])
chain = LLMChain(llm=llm, prompt=prompt)

# Función para hacer la consulta y obtener el resultado real
def consulta(input_usuario):
    # Generar la consulta SQL basada en la pregunta
    consulta_sql = chain.run({"question": input_usuario})
    print("Consulta generada (antes de limpieza):", consulta_sql)  # Verificar la consulta generada para depuración
    
    # Limpiar la consulta SQL para eliminar texto adicional
    consulta_sql = re.search(r"(SELECT .* FROM .*;)", consulta_sql, re.IGNORECASE)
    if consulta_sql:
        consulta_sql = consulta_sql.group(0)  # Extraer solo la consulta SQL
    else:
        return "Error: No se pudo generar una consulta SQL válida."

    print("Consulta generada (después de limpieza):", consulta_sql)  # Verificar la consulta limpia
    
    # Ejecutar la consulta en la base de datos y obtener el resultado
    try:
        # Envolver la consulta en text() para hacerla ejecutable
        consulta_sql_text = text(consulta_sql)
        
        # Conectar a la base de datos y ejecutar la consulta
        with engine.connect() as connection:
            resultado = connection.execute(consulta_sql_text).fetchall()
        
        # Formatear el resultado para devolverlo como respuesta en español
        if resultado:
            # Si hay múltiples resultados, concatenamos todos
            if len(resultado) > 1:
                respuesta = "Resultados: " + ", ".join([str(row[0]) for row in resultado])
            else:
                respuesta = f"Resultado: {resultado[0][0]}"
        else:
            respuesta = "No se encontraron resultados para la consulta."
    
    except SQLAlchemyError as e:
        respuesta = f"Error al ejecutar la consulta: {str(e)}"
    
    return respuesta
