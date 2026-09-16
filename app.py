from pathlib import Path
import json

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
        "La experiencia es opcional. Si registra una, indique como mínimo el cargo, tipo de experiencia y "
        "fecha de inicio. Deje la fecha de finalización vacía si actualmente continúa en ese empleo."
    )
    tipos = ["Profesional", "Profesional relacionada", "Relacionada", "Específica", "Docente", "Laboral", "Otra"]

    for i, experiencia in enumerate(st.session_state.experiencias):
        with st.container(border=True):
            c1, c2 = st.columns(2)
            experiencia["cargo"] = c1.text_input("Cargo", value=experiencia.get("cargo", ""), placeholder="Ej. Profesional especializado", key=f"cargo_{i}")
            experiencia["empresa"] = c2.text_input("Entidad / empresa", value=experiencia.get("empresa", ""), placeholder="Ej. Entidad pública", key=f"empresa_{i}")
            experiencia["funciones"] = st.text_area("Funciones principales", value=experiencia.get("funciones", ""), placeholder="Describa brevemente sus funciones y responsabilidades.", key=f"funciones_{i}")
            c3, c4, c5 = st.columns(3)
            tipo_actual = experiencia.get("tipo", "Profesional")
            indice_tipo = tipos.index(tipo_actual) if tipo_actual in tipos else 0
            experiencia["tipo"] = c3.selectbox(
                "Tipo de experiencia laboral", tipos, index=indice_tipo,
                help=("Seleccione la opción que mejor describa la experiencia registrada. Este dato se conserva porque forma parte de las variables de entrada del modelo aprobado."),
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
    formaciones = [{"nivel": f["nivel"], "titulo": f["titulo"].strip()} for f in st.session_state.formaciones if f.get("titulo", "").strip()]
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
    """Recupera las rutas originales del catálogo sin interpretarlas ni modificarlas."""
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


def mostrar_requisitos_originales(motor, opec):
    """Muestra el requisito registrado en el catálogo sin emitir juicio de cumplimiento."""
    rutas = obtener_rutas_originales(motor, opec)
    st.markdown("#### Requisitos originales registrados para la OPEC")
    st.caption(
        "Se presentan como están registrados en el catálogo histórico. El prototipo no determina "
        "si su perfil cumple estos requisitos ni construye equivalencias académicas propias."
    )

    if not rutas:
        st.write("No se encontraron rutas de requisitos para esta oportunidad en el catálogo histórico.")
        return

    for i, ruta in enumerate(rutas, start=1):
        numero_ruta = (ruta or {}).get("numero_ruta", i)
        st.markdown(f"**Opción {numero_ruta}**")
        encontrados = False
        for clave, etiqueta in (
            ("requisito_principal", "Requisito principal"),
            ("requisito_alternativo", "Requisito alternativo"),
        ):
            requisito = (ruta or {}).get(clave, {}) or {}
            estudio = str(requisito.get("estudio") or "").strip()
            experiencia = str(requisito.get("experiencia") or "").strip()
            meses = requisito.get("tiempomin")
            if estudio or experiencia or meses not in (None, ""):
                encontrados = True
                st.write(f"**{etiqueta}**")
                if estudio:
                    st.write(f"Estudios: {estudio}")
                if experiencia:
                    st.write(f"Experiencia: {experiencia}")
                if meses not in (None, ""):
                    st.write(f"Tiempo mínimo registrado: {meses} meses")
        if not encontrados:
            st.write("Sin información de requisitos en esta opción.")


def mostrar_resultados(resultado: pd.DataFrame, motor):
    """Presenta el índice histórico separado de los requisitos originales de la OPEC."""
    if resultado.empty:
        st.warning("No se encontraron oportunidades para el perfil registrado.")
        return

    st.success(
        f"Se muestran {len(resultado)} oportunidades del catálogo histórico, priorizadas según "
        "el índice de compatibilidad histórica generado por el modelo aprobado."
    )
    st.warning(
        "El orden presentado corresponde al índice generado por el modelo predictivo a partir de "
        "información histórica. Antes de postularse, revise los requisitos académicos y de experiencia "
        "de cada oportunidad."
    )

    df = resultado.copy()
    df["indice_compatibilidad_pct"] = (df["indice_compatibilidad"] * 100).round(1)
    df["experiencia_ciudadano_meses"] = df["experiencia_ciudadano_meses"].round(1)

    columnas = ["posicion", "opec", "descripcion", "indice_compatibilidad_pct"]
    vista = df[columnas].rename(columns={
        "posicion": "Posición",
        "opec": "OPEC",
        "descripcion": "Descripción",
        "indice_compatibilidad_pct": "Índice histórico (%)",
    })

    st.subheader("Oportunidades priorizadas según compatibilidad histórica")
    st.caption(
        "El índice permite ordenar las oportunidades según patrones históricos del modelo. "
        "No representa cumplimiento de requisitos ni probabilidad de selección."
    )
    st.dataframe(
        vista,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Posición": st.column_config.NumberColumn(width="small"),
            "OPEC": st.column_config.TextColumn(width="small"),
            "Descripción": st.column_config.TextColumn(width="large"),
            "Índice histórico (%)": st.column_config.NumberColumn(format="%.1f%%", width="medium"),
        },
    )

    st.subheader("Comparación del índice de compatibilidad histórica")
    st.caption(
        "La gráfica muestra únicamente el índice producido por el modelo aprobado. "
        "No debe interpretarse como probabilidad ni como validación de requisitos."
    )
    grafico = df[["opec", "indice_compatibilidad_pct"]].copy()
    grafico["OPEC"] = "OPEC " + grafico["opec"].astype(str)
    grafico = grafico.set_index("OPEC")[["indice_compatibilidad_pct"]]
    grafico.columns = ["Índice histórico (%)"]
    st.bar_chart(grafico, horizontal=True, x_label="Índice de compatibilidad histórica (%)", y_label="Oportunidad OPEC")

    st.subheader("Detalle de las oportunidades")
    st.caption(
        "Abra una oportunidad para consultar por separado el índice histórico y los requisitos "
        "registrados en el catálogo."
    )

    for _, rec in df.iterrows():
        titulo = f"#{int(rec['posicion'])} · OPEC {rec['opec']} · Índice histórico {rec['indice_compatibilidad_pct']:.1f}%"
        with st.expander(titulo):
            c1, c2 = st.columns(2)
            c1.metric("Índice de compatibilidad histórica", f"{rec['indice_compatibilidad_pct']:.1f}%")
            c2.metric("Experiencia registrada por el ciudadano", f"{rec['experiencia_ciudadano_meses']:.1f} meses")

            st.info(
                "El índice refleja patrones históricos identificados por el modelo y no determina "
                "el cumplimiento de los requisitos de la OPEC."
            )
            st.write(f"**Descripción de la oportunidad:** {rec.get('descripcion', '')}")

            mostrar_requisitos_originales(motor, rec["opec"])

            st.warning(
                "Revise los requisitos académicos y de experiencia antes de postularse. "
                "El índice de compatibilidad no constituye una verificación del cumplimiento "
                "de los requisitos establecidos por la convocatoria."
            )

            with st.expander("Ver trazabilidad técnica del cálculo"):
                st.caption(
                    "Información interna utilizada por el motor aprobado. Estos valores no constituyen "
                    "una evaluación oficial del cumplimiento de requisitos."
                )
                st.write(f"**Ruta interna seleccionada por el motor:** Opción {rec.get('numero_ruta', '')}")
                st.write(f"**Tipo de ruta interna:** {rec.get('tipo_ruta', '')}")
                st.write(f"**Requisito de estudio de la ruta interna:** {rec.get('requisito_estudio', '')}")
                st.write(f"**Requisito de experiencia de la ruta interna:** {rec.get('requisito_experiencia', '')}")
                st.write(f"**Meses requeridos en la ruta interna:** {rec.get('meses_requeridos', 0):.1f}")
                st.write(f"**Brecha temporal calculada:** {rec.get('brecha_meses', 0):.1f} meses")
                st.write(f"**Similitud académica interna:** {rec.get('similitud_academica', 0):.3f}")
                st.write(f"**Similitud de experiencia interna:** {rec.get('similitud_experiencia', 0):.3f}")

            st.caption(rec.get("advertencia", ADVERTENCIA))


def main():
    inicializar_estado()
    motor = cargar_motor()

    st.title("🧭 Orientador de oportunidades laborales públicas")
    st.write(
        "Ingrese su formación y experiencia. El prototipo utiliza el modelo predictivo aprobado para "
        "priorizar oportunidades de un catálogo histórico OPEC mediante un índice de compatibilidad histórica."
    )
    st.warning(
        "El índice de compatibilidad histórica es una herramienta de orientación. No es una probabilidad "
        "de selección, no certifica el cumplimiento de requisitos y no reemplaza la verificación oficial "
        "de la CNSC."
    )

    with st.sidebar:
        st.header("Acerca del prototipo")
        st.write("Proyecto académico de Maestría en Ciencia de Datos.")
        st.write(f"**Modelo:** {motor.metadata.get('nombre_modelo', motor.metadata.get('modelo_seleccionado', 'No especificado'))}")
        st.write(f"**Versión:** {motor.metadata.get('version', motor.metadata.get('version_modelo', 'v1'))}")
        st.write(f"**Catálogo:** {motor.metadata.get('catalogo', 'Histórico OPEC 2024')}")
        st.caption(
            "El catálogo utilizado es histórico y se emplea con fines académicos y demostrativos. "
            "La información oficial y vigente debe verificarse en las fuentes de la CNSC."
        )

    render_formaciones()
    render_experiencias()

    st.subheader("3. Consultar oportunidades")
    top_n = st.slider(
        "Número de oportunidades a mostrar",
        min_value=1,
        max_value=50,
        value=10,
        help="Seleccione cuántas oportunidades desea consultar, ordenadas por el índice de compatibilidad histórica.",
    )

    if st.button("Consultar oportunidades", type="primary", use_container_width=True):
        perfil = construir_perfil()
        try:
            resultado = motor.recomendar(perfil, top_n=top_n)
            mostrar_resultados(resultado, motor)
        except Exception as exc:
            st.error(f"No fue posible procesar el perfil: {exc}")

    with st.expander("Ver ejemplo de perfil en JSON"):
        ejemplo = json.loads((BASE_DIR / "ejemplo_perfil.json").read_text(encoding="utf-8"))
        st.json(ejemplo)


if __name__ == "__main__":
    main()
