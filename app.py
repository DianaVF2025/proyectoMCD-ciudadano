from pathlib import Path
import json
import re
import unicodedata

import pandas as pd
import streamlit as st

from motor_inferencia import MotorRecomendacionCNSC, ADVERTENCIA

st.set_page_config(page_title="Orientador de oportunidades laborales públicas", page_icon="🧭", layout="wide")
BASE_DIR = Path(__file__).resolve().parent

@st.cache_resource
def cargar_motor():
    return MotorRecomendacionCNSC(BASE_DIR / "paquete_modelo_cnsc_v1.joblib")

def normalizar_para_coincidencia(valor):
    texto = unicodedata.normalize("NFKD", str(valor or "").lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", texto).strip()

def nueva_formacion(): return {"nivel": "PROFESIONAL", "titulo": ""}
def nueva_experiencia(): return {"cargo": "", "empresa": "", "funciones": "", "tipo": "Profesional", "fecha_inicio": "", "fecha_fin": ""}

def inicializar_estado():
    if "formaciones" not in st.session_state: st.session_state.formaciones = [nueva_formacion()]
    if "experiencias" not in st.session_state: st.session_state.experiencias = [nueva_experiencia()]

def render_formaciones():
    st.subheader("1. Formación académica"); st.caption("Registre al menos una formación. Puede agregar varias.")
    niveles=["BACHILLER","TECNICO PROFESIONAL","TECNOLOGICO","PROFESIONAL","ESPECIALIZACION PROFESIONAL","MAESTRIA","DOCTORADO"]
    for i,f in enumerate(st.session_state.formaciones):
        with st.container(border=True):
            c1,c2=st.columns([1,2]); actual=f.get("nivel","PROFESIONAL")
            f["nivel"]=c1.selectbox("Nivel",niveles,index=niveles.index(actual) if actual in niveles else 3,key=f"nivel_{i}")
            f["titulo"]=c2.text_input("Título o programa académico",value=f.get("titulo",""),placeholder="Ej. Ingeniería Industrial, Matemáticas o Medicina Veterinaria",key=f"titulo_{i}")
            if len(st.session_state.formaciones)>1 and st.button("Eliminar formación",key=f"del_form_{i}"): st.session_state.formaciones.pop(i); st.rerun()
    if st.button("+ Agregar otra formación"): st.session_state.formaciones.append(nueva_formacion()); st.rerun()

def render_experiencias():
    st.subheader("2. Experiencia laboral"); st.caption("Registre cargo, entidad, funciones y fechas. La relación de la experiencia con una OPEC depende de sus requisitos y no la determina el ciudadano.")
    tipos=["Profesional","Docente","Laboral","Otra"]
    for i,e in enumerate(st.session_state.experiencias):
        with st.container(border=True):
            c1,c2=st.columns(2); e["cargo"]=c1.text_input("Cargo",value=e.get("cargo",""),key=f"cargo_{i}"); e["empresa"]=c2.text_input("Entidad / empresa",value=e.get("empresa",""),key=f"empresa_{i}")
            e["funciones"]=st.text_area("Funciones principales",value=e.get("funciones",""),help="Describa las funciones para permitir el contraste informativo con los requisitos de experiencia.",key=f"funciones_{i}")
            c3,c4,c5=st.columns(3); actual=e.get("tipo","Profesional"); actual=actual if actual in tipos else "Profesional"
            e["tipo"]=c3.selectbox("Naturaleza general de la experiencia",tipos,index=tipos.index(actual),help="No clasifique la experiencia como relacionada o específica.",key=f"tipo_{i}")
            e["fecha_inicio"]=c4.text_input("Fecha de inicio",value=e.get("fecha_inicio",""),placeholder="AAAA-MM-DD",key=f"inicio_{i}"); e["fecha_fin"]=c5.text_input("Fecha de finalización",value=e.get("fecha_fin",""),placeholder="AAAA-MM-DD o vacío si continúa",key=f"fin_{i}")
            if st.button("Eliminar experiencia",key=f"del_exp_{i}"): st.session_state.experiencias.pop(i); st.rerun()
    if st.button("+ Agregar otra experiencia"): st.session_state.experiencias.append(nueva_experiencia()); st.rerun()

def construir_perfil():
    fs=[{"nivel":f["nivel"],"titulo":f["titulo"].strip()} for f in st.session_state.formaciones if f.get("titulo","").strip()]; es=[]
    for e in st.session_state.experiencias:
        cargo,func=e.get("cargo","").strip(),e.get("funciones","").strip()
        if cargo or func: es.append({"cargo":cargo,"empresa":e.get("empresa","").strip(),"funciones":func,"tipo":e.get("tipo","Profesional"),"fecha_inicio":e.get("fecha_inicio","").strip(),"fecha_fin":e.get("fecha_fin","").strip() or None})
    return {"formaciones":fs,"experiencias":es}

def obtener_rutas_originales(motor,opec):
    c=motor.catalogo[motor.catalogo["opec"].astype(str)==str(opec)]
    if c.empty:return []
    rutas=c.iloc[0].get("rutas_requisitos",[])
    if isinstance(rutas,str):
        try:rutas=json.loads(rutas)
        except json.JSONDecodeError:return []
    return rutas if isinstance(rutas,list) else []

def componentes_alternativas(motor,opec):
    salida=[]
    for i,ruta in enumerate(obtener_rutas_originales(motor,opec),start=1):
        for clave,etiqueta in (("requisito_principal","Requisito"),("requisito_alternativo","Alternativa")):
            req=(ruta or {}).get(clave,{}) or {}; estudio=str(req.get("estudio") or "").strip(); exp=str(req.get("experiencia") or "").strip(); meses=req.get("tiempomin")
            if estudio or exp or meses not in (None,""):salida.append({"numero":i,"tipo":etiqueta,"estudio":estudio,"experiencia":exp,"meses":meses})
    return salida

def coincidencia_componente(c,formaciones):
    req=normalizar_para_coincidencia(c.get("estudio",""))
    return any((t:=normalizar_para_coincidencia(f.get("titulo",""))) and t in req for f in formaciones)

def coincidencia_directa_titulo(motor,opec,formaciones):return any(coincidencia_componente(c,formaciones) for c in componentes_alternativas(motor,opec))

def aplicar_priorizacion_formacion(resultado,motor,formaciones,top_n):
    if resultado.empty:return resultado
    df=resultado.copy(); df["coincidencia_titulo_directa"]=df["opec"].apply(lambda x:coincidencia_directa_titulo(motor,x,formaciones)); df=pd.concat([df[df["coincidencia_titulo_directa"]],df[~df["coincidencia_titulo_directa"]]],ignore_index=True).head(top_n).copy(); df["posicion"]=range(1,len(df)+1); return df

def mostrar_alternativas_perfil(motor,opec,formaciones,meses_ciudadano):
    comps=componentes_alternativas(motor,opec); identificados=[c for c in comps if coincidencia_componente(c,formaciones)]
    st.markdown("#### 2. Análisis complementario de requisitos")
    st.caption("Este análisis ayuda a interpretar la oportunidad frente al perfil declarado. Es independiente del índice de compatibilidad histórica y no modifica su valor.")
    if identificados:
        st.success(f"Se identificó coincidencia académica directa en {len(identificados)} alternativa(s) registrada(s).")
        for c in identificados:
            with st.container(border=True):
                st.markdown(f"**Alternativa {c['numero']} · {c['tipo']}**")
                if c["estudio"]:st.write(f"**Formación académica:** Coincidencia directa identificada\n\n{c['estudio']}")
                if c["experiencia"]:st.write(f"**Experiencia solicitada:** {c['experiencia']}")
                if c["meses"] not in (None,""):
                    try:
                        req=float(c["meses"]); st.write(f"**Experiencia total registrada:** {meses_ciudadano:.1f} meses  |  **Tiempo mínimo registrado en esta alternativa:** {req:.1f} meses")
                        if req==0:st.info("La alternativa registra 0 meses como tiempo mínimo de experiencia. Esto no determina el cumplimiento de los demás requisitos.")
                        elif meses_ciudadano>=req:st.info("El tiempo total registrado alcanza el mínimo indicado. Si se exige experiencia relacionada o específica, todavía deben contrastarse las funciones reportadas con el requisito.")
                        else:st.warning(f"El tiempo total registrado ({meses_ciudadano:.1f} meses) es inferior al mínimo indicado ({req:.1f} meses). Si además se exige experiencia relacionada o específica, también deben revisarse las funciones.")
                    except (TypeError,ValueError):pass
    else:st.info("No se identificó coincidencia textual directa entre la formación declarada y las alternativas académicas registradas para esta oportunidad.")
    with st.expander("Ver todas las alternativas de requisitos registradas"):
        if not comps:st.write("No se encontraron requisitos para esta oportunidad en el catálogo histórico.")
        for c in comps:
            marca=" · coincidencia académica identificada" if coincidencia_componente(c,formaciones) else ""
            st.markdown(f"**Alternativa {c['numero']} · {c['tipo']}{marca}**")
            if c["estudio"]:st.write(f"Estudios: {c['estudio']}")
            if c["experiencia"]:st.write(f"Experiencia: {c['experiencia']}")
            if c["meses"] not in (None,""):st.write(f"Tiempo mínimo registrado: {c['meses']} meses")
            st.divider()

def mostrar_resultados(resultado,motor,formaciones):
    if resultado.empty:st.warning("No se encontraron oportunidades para el perfil registrado.");return
    df=resultado.copy(); df["indice_compatibilidad_pct"]=(df["indice_compatibilidad"]*100).round(1); df["experiencia_ciudadano_meses"]=df["experiencia_ciudadano_meses"].round(1)
    if "coincidencia_titulo_directa" not in df:df["coincidencia_titulo_directa"]=False
    cantidad=int(df["coincidencia_titulo_directa"].sum()); st.success(f"Se muestran {len(df)} oportunidades orientadas por el modelo. En {cantidad} se identificó además coincidencia académica directa en al menos una alternativa registrada.")
    st.info("**Cómo leer los resultados:** el índice de compatibilidad histórica es el resultado principal del modelo aprobado. El análisis de formación y experiencia se muestra por separado para ayudar a interpretar cada oportunidad antes de postularse.")
    vista=df[["posicion","opec","descripcion","indice_compatibilidad_pct","coincidencia_titulo_directa"]].rename(columns={"posicion":"Posición","opec":"OPEC","descripcion":"Descripción","indice_compatibilidad_pct":"Índice de compatibilidad histórica (%)","coincidencia_titulo_directa":"Análisis académico"}); vista["Análisis académico"]=vista["Análisis académico"].map({True:"Coincidencia identificada",False:"Sin coincidencia directa"})
    st.subheader("Oportunidades orientadas por compatibilidad"); st.caption("El índice conserva exactamente la salida del modelo predictivo aprobado. No corresponde a un porcentaje de cumplimiento de requisitos."); st.dataframe(vista,use_container_width=True,hide_index=True)
    st.subheader("Detalle e interpretación")
    titulos=", ".join(f.get("titulo","") for f in formaciones if f.get("titulo","").strip())
    for _,rec in df.iterrows():
        with st.expander(f"#{int(rec['posicion'])} · OPEC {rec['opec']} · Compatibilidad histórica {rec['indice_compatibilidad_pct']:.1f}%"):
            st.markdown("#### 1. Índice de compatibilidad histórica")
            c1,c2=st.columns([1,1]); c1.metric("Compatibilidad histórica",f"{rec['indice_compatibilidad_pct']:.1f}%"); c2.metric("Experiencia total registrada",f"{rec['experiencia_ciudadano_meses']:.1f} meses")
            st.write("Este índice es generado por el **modelo predictivo aprobado** a partir de patrones históricos y múltiples características del perfil y de la oportunidad.")
            st.warning("**Importante:** este valor no significa que el ciudadano cumpla ese porcentaje de los requisitos, ni corresponde a una probabilidad de selección.")
            with st.expander("¿Por qué una oportunidad puede tener mayor o menor compatibilidad histórica?"):
                st.write("El modelo considera conjuntamente múltiples variables históricas, entre ellas características de la experiencia registrada, duración y brechas de experiencia, características académicas y medidas de similitud textual. El valor final surge de la combinación aprendida por el modelo y no se atribuye a una sola variable.")
                st.write("Por esta razón, una oportunidad puede presentar un índice histórico alto sin coincidencia académica directa, mientras otra puede presentar coincidencia académica y un índice histórico menor. El análisis de requisitos que aparece a continuación permite interpretar esa diferencia.")
            st.write(f"**Formación declarada:** {titulos}"); st.write(f"**Descripción de la oportunidad:** {rec.get('descripcion','')}")
            mostrar_alternativas_perfil(motor,rec["opec"],formaciones,float(rec["experiencia_ciudadano_meses"]))
            st.markdown("#### 3. Orientación para el ciudadano")
            if bool(rec["coincidencia_titulo_directa"]):st.success("Se identificó al menos una alternativa académica que contiene directamente la formación declarada. Revise también las condiciones de experiencia y los demás requisitos antes de postularse.")
            else:st.warning("No se identificó coincidencia académica directa con la formación declarada. Aunque el modelo muestre compatibilidad histórica, revise cuidadosamente los requisitos académicos antes de considerar la postulación.")
            st.caption("El análisis complementario no recalcula ni modifica el índice de compatibilidad histórica. La verificación oficial de requisitos corresponde a la convocatoria."); st.caption(rec.get("advertencia",ADVERTENCIA))

def main():
    inicializar_estado();motor=cargar_motor();st.title("🧭 Orientador de oportunidades laborales públicas")
    st.write("Registre su formación y experiencia para consultar oportunidades. El resultado principal es el **índice de compatibilidad histórica generado por el modelo predictivo aprobado**; adicionalmente, el prototipo presenta un análisis complementario de los requisitos para facilitar su interpretación.")
    st.warning("La compatibilidad histórica orienta la búsqueda de oportunidades. No equivale a porcentaje de cumplimiento de requisitos, probabilidad de selección ni verificación oficial de la CNSC.")
    with st.sidebar:
        st.header("Acerca del prototipo");st.write("Proyecto académico de Maestría en Ciencia de Datos.");st.write(f"**Modelo:** {motor.metadata.get('nombre_modelo',motor.metadata.get('modelo_seleccionado','No especificado'))}");st.write(f"**Versión:** {motor.metadata.get('version',motor.metadata.get('version_modelo','v1'))}");st.caption("El modelo, sus vectorizadores, variables, umbral y métricas aprobadas permanecen congelados.")
    render_formaciones();render_experiencias();st.subheader("3. Generar orientación");top_n=st.slider("Número de oportunidades a mostrar",1,20,10)
    if st.button("Consultar compatibilidad y oportunidades",type="primary",use_container_width=True):
        try:
            perfil=construir_perfil();resultado_modelo=motor.recomendar(perfil,top_n=len(motor.catalogo));resultado=aplicar_priorizacion_formacion(resultado_modelo,motor,perfil["formaciones"],top_n);mostrar_resultados(resultado,motor,perfil["formaciones"])
        except Exception as exc:st.error(f"No fue posible generar la orientación: {exc}")

if __name__=="__main__":main()
