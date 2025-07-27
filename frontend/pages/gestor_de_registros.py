import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from backend.database import obtener_registros, eliminar_registro, actualizar_registro, guardar
from backend.models import cargar_modelos, predecir
from backend.loaders import load_all_models
from backend.predictors import predecir
from backend.utils import cultivos as cultivo_dict


st.title("Gestión de registros de predicción")

# Cargar modelos
modelo_fertilidad, modelo_cultivo = cargar_modelos()

# Mostrar predicción pendiente
if "registro_predicho" in st.session_state:
    st.markdown("### ✅ Última predicción no guardada")
    st.json(st.session_state["registro_predicho"])

    col_guardar, col_descartar = st.columns(2)
    if col_guardar.button("💾 Guardar predicción"):
        insertar_registro(st.session_state["registro_predicho"])
        st.success("📥 Predicción guardada correctamente.")
        del st.session_state["registro_predicho"]
        st.rerun()

    if col_descartar.button("🗑️ Descartar predicción"):
        del st.session_state["registro_predicho"]
        st.info("Predicción descartada.")
        st.rerun()

# Obtener datos de Supabase
registros = obtener_registros()

def mostrar_registro(fila):
    with st.expander(f"📄 Registro ID {fila['id']}"):
        col1, col2 = st.columns([3, 1])
        with col1:
            for campo, valor in fila.items():
                if campo != "id":
                    st.write(f"**{campo}**: {valor}")
        with col2:
            if st.button("✏️ Editar", key=f"editar_{fila['id']}"):
                st.session_state[f"editando_{fila['id']}"] = True
            if st.button("🗑️ Eliminar", key=f"eliminar_{fila['id']}"):
                with st.expander("🗑️ Eliminar registro"):
                    st.warning("⚠️ ¿Estás seguro de que deseas eliminar este registro? Esta acción no se puede deshacer.")
                    if st.button("❌ Confirmar eliminación", key=f"confirmar_eliminar_{fila['id']}"):
                        eliminar_registro(fila['id'])
                        st.warning(f"Registro ID {fila['id']} eliminado")
                        st.rerun()

# Mostrar todos los registros
st.markdown("## 📋 Registros actuales")
for fila in registros:
    if st.session_state.get(f"editando_{fila['id']}", False):
        with st.form(f"form_edicion_{fila['id']}"):
            columnas = st.columns(3)
            campos_numericos = [
                "ph", "materia_organica", "conductividad", "nitrogeno", "fosforo", "potasio", "humedad",
                "densidad", "altitud", "temperatura","evapotranspiracion", "mes"
            ]
            campos_categoricos = ["tipo_suelo", "condiciones_clima"]

            datos_actualizados = {}
            for i, campo in enumerate(campos_numericos + campos_categoricos):
                with columnas[i % 3]:
                    valor_actual = fila.get(campo, "")
                    if campo in campos_numericos:
                        datos_actualizados[campo] = st.number_input(
                            campo.replace("_", " ").capitalize(), value=float(valor_actual) if valor_actual != "" else 0.0,
                            format="%.4f", key=f"{campo}_{fila['id']}"
                        )
                    else:
                        datos_actualizados[campo] = st.text_input(
                            campo.replace("_", " ").capitalize(), value=valor_actual,
                            key=f"{campo}_{fila['id']}"
                        )

            submitted = st.form_submit_button("💾 Guardar cambios")
            if submitted:
                # Volver a predecir con nuevos valores
                nueva_fertilidad = predecir(modelo_fertilidad, datos_actualizados)
                nuevo_cultivo = predecir(modelo_cultivo, datos_actualizados)

                # Comparar con los valores antiguos
                cambios = []
                if nueva_fertilidad != fila.get("fertilidad"):
                    cambios.append(f"Fertilidad: {fila.get('fertilidad')} → {nueva_fertilidad}")
                if nuevo_cultivo != fila.get("cultivo"):
                    cambios.append(f"Cultivo: {fila.get('cultivo')} → {nuevo_cultivo}")

                if cambios:
                    st.warning("Se detectaron cambios en la predicción:")
                    for cambio in cambios:
                        st.write(f"- {cambio}")
                    if st.checkbox("✅ Confirmar actualización del registro", key=f"confirmar_{fila['id']}"):
                        datos_actualizados["fertilidad"] = nueva_fertilidad
                        datos_actualizados["cultivo"] = nuevo_cultivo
                        datos_actualizados["prediccion"] = True
                        datos_actualizados["fecha_ingreso"] = datetime.now(pytz.timezone("America/Lima")).isoformat()
                        actualizar_registro(fila['id'], datos_actualizados)
                        st.success("✅ Registro actualizado correctamente.")
                        del st.session_state[f"editando_{fila['id']}"]
                        st.rerun()
                else:
                    st.info("ℹ️ No se detectaron cambios. El registro no fue actualizado.")
                    del st.session_state[f"editando_{fila['id']}"]
    else:
        mostrar_registro(fila)




