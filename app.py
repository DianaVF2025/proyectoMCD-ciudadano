from pathlib import Path
import json
import re
import unicodedata

import pandas as pd
import streamlit as st

from motor_inferencia import MotorRecomendacionCNSC, ADVERTENCIA


st.set_page_config(
    page_title="Orientador de oportunidades laborales públicas",
    page_icon="🧭",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent


@st.cache_resource
def cargar_motor():
    """Carga únicamente el paquete congelado aprobado para inferencia."""
    return MotorRecomendacionCNSC(BASE_DIR / "paquete_modelo_cnsc_v1.joblib")


def normalizar_para_coincidencia(valor):
    texto = unicodedata.normalize("NFKD", str(valor or "").lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", texto).strip()


def nueva_formacion():
    return {"nivel": "PROFESIONAL", "titulo": ""}


def nueva_experiencia():
    return {
        "cargo": "",
        "empresa": "",
        "funciones": "",
        "tipo": "Profesional",
        "fecha_inicio": "",
        "fecha_fin": "",
    }


def inicializar_estado():
    if "formaciones" not in st.session_state:
        st.session_state.formaciones = [nueva_formacion()]
    if "experiencias" not in st.session_state:
        st.session_state.experiencias = [nueva_experiencia()]


def render_formaciones():
    st.subheader("1. Formación académica")
    st.caption("Registre al menos una formación. Puede agregar varias.")
    niveles = [
        "BACHILLER", "TECNICO PROFESIONAL", "TECNOLOGICO", "PROFESIONAL",
        "ESPECIALIZACION PROFESIONAL", "MAESTRIA", "DOCTORADO"
    ]

    for i, formacion in enumerate(st.session_state.formaciones):
        with st.container(border=True):
            c1, c2 = st.columns([1, 2])
            nivel_actual = formacion.get("nivel", "PROFESIONAL")
            indice = niveles.index(nivel_actual) if nivel_actual in niveles else niveles.index("PROFESIONAL")
            formacion["nivel"] = c1.selectbox("Nivel", niveles, index=indice, key=f"nivel_{i}")
            formacion["titulo"] = c2.text_input(
                "Título o programa académico",
                value=formacion.get("titulo", ""),
                placeholder="Ej. Ingeniería Industrial, Matemáticas o Administración de Empresas",
                help="Indique el nombre del título obtenido o del programa académico cursado.",
                key=f"titulo_{i}",
            )
            if len(st.session_state.formaciones) > 1 and st.button("Eliminar formación", key=f"del_form_{i}"):
                st.session_state.formaciones.pop(i)
                st.rerun()

    if st.button("+ Agregar otra formación"):
        st.session_state.formaciones.append(nueva_formacion())
        st.rerun()


def render_experiencias():
    st.subheader("2. Experiencia laboral")
    st.caption(
        "La experiencia es opcional. Registre los datos objetivos de cada empleo o actividad: cargo, entidad, "
        "funciones y fechas. La relación de la experiencia con una oportunidad específica no la declara el ciudadano."
    )
    tipos = ["Profesional", "Docente", "Laboral", "Otra"]

    for i, experiencia in enumerate(st.session_state.experiencias):
        with st.container(border=True):
            c1, c2 = st.columns(2)
            experiencia["cargo"] = c1.text_input("Cargo", value=experiencia.get("cargo", ""), placeholder="Ej. Profesional especializado", key=f"cargo_{i}")
            experiencia["empresa"] = c2.text_input("Entidad / empresa", value=experiencia.get("empresa", ""), placeholder="Ej. Entidad pública", key=f"empresa_{i}")
            experiencia["funciones"] = st.text_area(
                "Funciones principales", value=experiencia.get("funciones", ""),
                placeholder="Describa brevemente sus funciones y responsabilidades.",
                help="Las funciones permiten contrastar el contenido de la experiencia con los requisitos históricos de las oportunidades.",
                key=f"funciones_{i}",
            )
            c3, c4, c5 = st.columns(3)
            tipo_actual = experiencia.get("tipo", "Profesional")
            if tipo_actual not in tipos:
                tipo_actual = "Profesional"
            experiencia["tipo"] = c3.selectbox(
                "Naturaleza general de la experiencia", tipos, index=tipos.index(tipo_actual),
                help="Indique únicamente la naturaleza general. La relación o especificidad depende de los requisitos de cada OPEC.",
                key=f"tipo_{i}",
            )
            experiencia["fecha_inicio"] = c4.text_input("Fecha de inicio", value=experiencia.get("fecha_inicio", ""), placeholder="AAAA-MM-DD", key=f"inicio_{i}")
            experiencia["fecha_fin"] = c5.text_input("Fecha de finalización", value=experiencia.get("fecha_fin", ""), placeholder="AAAA-MM-DD o vacío si continúa", key=f"fin_{i}")
            if st.button("Eliminar experiencia", key=f"del_exp_{i}"):
                st.session_state.experiencias.pop(i)
                st.rerun()

    if st.button("+ Agregar otra experiencia"):
        st.session_state.experiencias.append(nueva_experiencia())
        st.rerun()


def construir_perfil():
    formaciones = [
        {"nivel": f["nivel"], "titulo": f["titulo"].strip()}
        for f in st.session_state.formaciones if f.get("titulo", "").strip()
    ]
    experiencias = []
    for e in st.session_state.experiencias:
        cargo = e.get("cargo", "").strip()
        funciones = e.get("funciones", "").strip()
        if cargo or funciones:
            experiencias.append({
                "cargo": cargo,
                "empresa": e.get("empresa", "").strip(),
                "funciones": funciones,
                "tipo": e.get("tipo", "Profesional"),
                "fecha_inicio": e.get("fecha_inicio", "").strip(),
                "fecha_fin": e.get("fecha_fin", "").strip() or None,
            })
    return {"formaciones": formaciones, "experiencias": experiencias}


def obtener_rutas_originales(motor, opec):
    coincidencias = motor.catalogo[motor.catalogo["opec"].astype(str) == str(opec)]
    if coincidencias.empty:
        return []
    rutas = coincidencias.iloc[0].get("rutas_requisitos", [])
    if isinstance(rutas, str):
        try:
            rutas = json.loads(rutas)
        except json.JSONDecodeError:
            return []
    return rutas if isinstance(rutas, list) else []


def textos_estudio_opec(motor, opec):
    textos = []
    for ruta in obtener_rutas_originales(motor, opec):
        for clave in ("requisito_principal", "requisito_alternativo"):
            requisito = (ruta or {}).get(clave, {}) or {}
            estudio = str(requisito.get("estudio") or "").strip()
            if estudio:
                textos.append(estudio)
    return textos


def coincidencia_directa_titulo(motor, opec, formaciones):
    """Identifica solo presencia textual directa; no crea equivalencias ni interpreta NBC."""
    requisitos = [normalizar_para_coincidencia(t) for t in textos_estudio_opec(motor, opec)]
    titulos = [normalizar_para_coincidencia(f.get("titulo", "")) for f in formaciones]
    titulos = [t for t in titulos if t]
    for titulo in titulos:
        for requisito in requisitos:
            if titulo in requisito:
                return True
    return False


def aplicar_priorizacion_formacion(resultado, motor, formaciones, top_n):
    """Capa funcional: no modifica ni recalcula el índice producido por el modelo."""
    if resultado.empty:
        return resultado
    df = resultado.copy()
    df["coincidencia_titulo_directa"] = df["opec"].apply(
        lambda opec: coincidencia_directa_titulo(motor, opec, formaciones)
    )
    coincidentes = df[df["coincidencia_titulo_directa"]].copy()
    no_coincidentes = df[~df["coincidencia_titulo_directa"]].copy()
    ordenado = pd.concat([coincidentes, no_coincidentes], ignore_index=True)
    ordenado = ordenado.head(top_n).copy()
    ordenado["posicion"] = range(1, len(ordenado) + 1)
    return ordenado


def mostrar_requisitos_originales(motor, opec):
    rutas = obtener_rutas_originales(motor, opec)
    st.markdown("#### Requisitos registrados para la oportunidad")
    st.caption(
        "Se presentan los requisitos disponibles en el catálogo histórico. El prototipo no certifica "
        "su cumplimiento ni construye equivalencias académicas propias."
    )
    if not rutas:
        st.write("No se encontraron requisitos para esta oportunidad en el catálogo histórico.")
        return

    for i, ruta in enumerate(rutas, start=1):
        componentes = []
        for clave, etiqueta in (("requisito_principal", "Requisito"), ("requisito_alternativo", "Alternativa")):
            requisito = (ruta or {}).get(clave, {}) or {}
            estudio = str(requisito.get("estudio") or "").strip()
            experiencia = str(requisito.get("experiencia") or "").strip()
            meses = requisito.get("tiempomin")
            if estudio or experiencia or meses not in (None, ""):
                componentes.append((etiqueta, estudio, experiencia, meses))
        if not componentes:
            continue
        if len(rutas) > 1:
            st.markdown(f"**Alternativa de requisitos {i}**")
        for etiqueta, estudio, experiencia, meses in componentes:
            if len(componentes) > 1:
                st.write(f"**{etiqueta}**")
            if estudio:
                st.write(f"Estudios: {estudio}")
            if experiencia:
                st.write(f"Experiencia: {experiencia}")
            if meses not in (None, ""):
                st.write(f"Tiempo mínimo registrado: {meses} meses")


def mostrar_resultados(resultado: pd.DataFrame, motor, formaciones):
    if resultado.empty:
        st.warning("No se encontraron oportunidades para el perfil registrado.")
        return

    df = resultado.copy()
    df["indice_compatibilidad_pct"] = (df["indice_compatibilidad"] * 100).round(1)
    df["experiencia_ciudadano_meses"] = df["experiencia_ciudadano_meses"].round(1)
    if "coincidencia_titulo_directa" not in df:
        df["coincidencia_titulo_directa"] = False

    cantidad = int(df["coincidencia_titulo_directa"].sum())
    st.success(
        f"Se muestran {len(df)} oportunidades priorizadas. En {cantidad} se identificó coincidencia textual "
        "directa entre al menos un título declarado y el requisito académico registrado."
    )
    st.warning(
        "La coincidencia textual es una ayuda de priorización de la interfaz: no certifica cumplimiento, no "
        "interpreta NBC y no modifica el índice de compatibilidad histórica generado por el modelo aprobado."
    )

    vista = df[["posicion", "opec", "descripcion", "coincidencia_titulo_directa", "indice_compatibilidad_pct"]].rename(columns={
        "posicion": "Posición", "opec": "OPEC", "descripcion": "Descripción",
        "coincidencia_titulo_directa": "Coincidencia directa del título",
        "indice_compatibilidad_pct": "Índice histórico (%)",
    })
    vista["Coincidencia directa del título"] = vista["Coincidencia directa del título"].map({True: "Identificada", False: "No identificada"})

    st.subheader("Oportunidades priorizadas")
    st.caption(
        "Primero se presentan las oportunidades con coincidencia textual directa del título declarado. "
        "Dentro de cada grupo se conserva el orden del índice histórico del modelo aprobado."
    )
    st.dataframe(vista, use_container_width=True, hide_index=True)

    st.subheader("Comparación del índice de compatibilidad histórica")
    grafico = df[["opec", "indice_compatibilidad_pct"]].copy()
    grafico["OPEC"] = "OPEC " + grafico["opec"].astype(str)
    grafico = grafico.set_index("OPEC")[["indice_compatibilidad_pct"]]
    grafico.columns = ["Índice histórico (%)"]
    st.bar_chart(grafico, horizontal=True, x_label="Índice de compatibilidad histórica (%)", y_label="Oportunidad OPEC")

    st.subheader("Detalle de las oportunidades")
    titulos_declarados = ", ".join(f.get("titulo", "") for f in formaciones if f.get("titulo", "").strip())
    for _, rec in df.iterrows():
        titulo = f"#{int(rec['posicion'])} · OPEC {rec['opec']} · Índice histórico {rec['indice_compatibilidad_pct']:.1f}%"
        with st.expander(titulo):
            c1, c2 = st.columns(2)
            c1.metric("Índice de compatibilidad histórica", f"{rec['indice_compatibilidad_pct']:.1f}%")
            c2.metric("Experiencia total registrada", f"{rec['experiencia_ciudadano_meses']:.1f} meses")
            st.write(f"**Formación declarada:** {titulos_declarados}")
            if bool(rec["coincidencia_titulo_directa"]):
                st.success("Coincidencia textual directa con el requisito académico: Identificada")
            else:
                st.info("Coincidencia textual directa con el requisito académico: No identificada")
            st.caption(
                "Esta comparación solo busca el título declarado dentro del texto original del requisito. "
                "No determina equivalencias, pertenencia a un NBC ni cumplimiento oficial."
            )
            st.write(f"**Descripción de la oportunidad:** {rec.get('descripcion', '')}")
            mostrar_requisitos_originales(motor, rec["opec"])
            st.warning(
                "Revise los requisitos académicos y de experiencia antes de postularse. El índice histórico y la "
                "coincidencia textual no constituyen una verificación oficial de los requisitos de la convocatoria."
            )
            st.caption(rec.get("advertencia", ADVERTENCIA))


def main():
    inicializar_estado()
    motor = cargar_motor()

    st.title("🧭 Orientador de oportunidades laborales públicas")
    st.write(
        "Ingrese su formación y experiencia. El prototipo utiliza el modelo predictivo aprobado y una capa "
        "funcional de priorización por coincidencia textual directa del título declarado."
    )
    st.warning(
        "El índice de compatibilidad histórica es una herramienta de orientación. No es una probabilidad de "
        "selección, no certifica el cumplimiento de requisitos y no reemplaza la verificación oficial de la CNSC."
    )

    with st.sidebar:
        st.header("Acerca del prototipo")
        st.write("Proyecto académico de Maestría en Ciencia de Datos.")
        st.write(f"**Modelo:** {motor.metadata.get('nombre_modelo', motor.metadata.get('modelo_seleccionado', 'No especificado'))}")
        st.write(f"**Versión:** {motor.metadata.get('version', motor.metadata.get('version_modelo', 'v1'))}")
        st.write(f"**Catálogo:** {motor.metadata.get('catalogo', 'Histórico OPEC 2024')}")
        st.caption("El modelo, sus vectorizadores, variables, umbral y métricas aprobadas permanecen congelados.")

    render_formaciones()
    render_experiencias()

    st.subheader("3. Generar orientación")
    top_n = st.slider("Número de oportunidades a mostrar", min_value=1, max_value=20, value=10)

    if st.button("Priorizar oportunidades", type="primary", use_container_width=True):
        try:
            perfil = construir_perfil()
            # Se solicita el catálogo completo para que la capa funcional pueda priorizar antes de cortar el top N.
            resultado_modelo = motor.recomendar(perfil, top_n=len(motor.catalogo))
            resultado = aplicar_priorizacion_formacion(resultado_modelo, motor, perfil["formaciones"], top_n)
            mostrar_resultados(resultado, motor, perfil["formaciones"])
        except Exception as exc:
            st.error(f"No fue posible generar la orientación: {exc}")


if __name__ == "__main__":
    main()
