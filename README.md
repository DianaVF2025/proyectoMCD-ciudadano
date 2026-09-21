# Orientador de oportunidades laborales del sector público colombiano

**Proyecto de Maestría en Ciencia de Datos**  
**Proyecto:** *Realizar un análisis y diseño de un modelo predictivo para la recomendación de oportunidades laborales en el ámbito gubernamental*  
**Autores:** Diana Vásquez · Germán Mahecha

## Prototipo desplegado

**Aplicación web:** https://proyectomcd-ciudadano-kqhpti4jdjkht2npkkquff.streamlit.app/

El prototipo está publicado en Streamlit Community Cloud y puede utilizarse directamente desde el navegador, sin instalación local.

## Descripción

Este repositorio contiene un prototipo orientado al **ciudadano/aspirante**. El usuario registra información básica de su formación académica y experiencia laboral y recibe oportunidades OPEC históricas ordenadas mediante un **índice de compatibilidad histórica** generado por el modelo predictivo aprobado.

La interfaz complementa ese resultado mostrando, de forma separada, información que ayuda a interpretar la recomendación frente a la formación y experiencia declaradas y los requisitos originales disponibles de cada OPEC.

> **Advertencia:** el índice de compatibilidad es una orientación basada en información histórica. No es una probabilidad de selección, no garantiza superar la Verificación de Requisitos Mínimos (VRM) y no reemplaza la verificación oficial de la CNSC.

El catálogo utilizado corresponde a información histórica y se emplea con fines académicos y demostrativos.

## Modelo predictivo aprobado

El prototipo conserva el modelo seleccionado durante la fase experimental del proyecto:

- **Algoritmo:** `HistGradientBoostingClassifier`
- **Artefacto:** `paquete_modelo_cnsc_v1.joblib`
- **Umbral aprobado:** `0.720`
- Se conservan las variables, vectorizadores y transformaciones del modelo aprobado.
- La capa de presentación ciudadana no reentrena ni modifica el modelo.

### Métricas aprobadas de validación temporal

| Métrica | Resultado |
|---|---:|
| Accuracy | 0.7103 |
| Precision | 0.8187 |
| Recall — supera VRM | 0.7417 |
| Recall — no supera VRM | 0.6418 |
| F1 | 0.7783 |
| ROC-AUC | 0.7685 |
| Balanced Accuracy | 0.6917 |
| Umbral | **0.720** |

Estas métricas corresponden a la evaluación aprobada del modelo y no son recalculadas por la aplicación durante la inferencia.

## Flujo del prototipo

```text
Perfil del ciudadano
        ↓
Modelo predictivo aprobado
        ↓
Índice de compatibilidad histórica
        ↓
Oportunidades recomendadas
        ↓
Consulta de formación, experiencia
y requisitos originales de la OPEC
```

El **índice de compatibilidad histórica** constituye la salida del modelo. La información de formación, experiencia y requisitos se presenta como apoyo para la interpretación del ciudadano y no como certificación automática de cumplimiento.

## Contenido del repositorio

| Archivo | Función |
|---|---|
| `app.py` | Interfaz ciudadana desarrollada en Streamlit |
| `motor_inferencia.py` | Preparación de variables e inferencia con el modelo aprobado |
| `paquete_modelo_cnsc_v1.joblib` | Paquete congelado del modelo, vectorizadores y componentes requeridos |
| `catalogo_opec_prototipo.joblib` | Catálogo histórico utilizado por el prototipo |
| `metadata_modelo.json` | Metadatos y especificaciones del modelo |
| `contrato_entrada.json` | Estructura esperada del perfil ciudadano |
| `contrato_salida.json` | Estructura de salida del motor |
| `ejemplo_perfil.json` | Ejemplo de perfil de entrada |
| `test_motor.py` | Pruebas funcionales del motor |
| `requirements.txt` | Dependencias necesarias para la ejecución |
| `ejecutar.bat` | Ejecución local automatizada en Windows |
| `Dockerfile` | Configuración alternativa mediante contenedor |
| `.dockerignore` | Exclusiones utilizadas para construir el contenedor |

## Uso recomendado para revisión académica

Para revisar el resultado funcional no es necesario instalar el proyecto. Se recomienda ingresar directamente a:

**https://proyectomcd-ciudadano-kqhpti4jdjkht2npkkquff.streamlit.app/**

Flujo sugerido de revisión:

1. Registrar la formación académica del aspirante.
2. Registrar su experiencia laboral.
3. Seleccionar **Consultar oportunidades compatibles**.
4. Revisar el índice de compatibilidad histórica de las oportunidades recomendadas.
5. Abrir el detalle de una OPEC para contrastar el perfil registrado con sus requisitos originales.

## Ejecución local

Se recomienda **Python 3.11** para reproducir el entorno utilizado durante las pruebas locales.

### Windows

```bat
git clone https://github.com/DianaVF2025/proyectoMCD-ciudadano.git
cd proyectoMCD-ciudadano
git checkout actualizacion-prototipo-ciudadano
ejecutar.bat
```

### Ejecución manual

```bash
python -m venv venv
```

En Windows:

```bat
venv\Scripts\activate
pip install -r requirements.txt
python test_motor.py
streamlit run app.py
```

En macOS/Linux:

```bash
source venv/bin/activate
pip install -r requirements.txt
python test_motor.py
streamlit run app.py
```

## Alcance y limitaciones

El prototipo tiene alcance **académico y demostrativo**. Está orientado a apoyar la exploración de oportunidades laborales del sector público colombiano a partir de información histórica.

La coincidencia textual entre la formación declarada y los requisitos académicos se presenta separadamente del índice histórico. El aplicativo no establece equivalencias académicas propias, no realiza una clasificación automática por NBC y no debe interpretarse como una validación oficial de requisitos.

La experiencia registrada por el ciudadano se utiliza como información del perfil. La determinación de si una experiencia es relacionada o específica frente a una OPEC requiere revisar las funciones y condiciones particulares de esa oportunidad.

## Reproducibilidad

La versión publicada conserva el modelo predictivo aprobado y sus componentes de inferencia. El archivo `requirements.txt` fija las dependencias principales necesarias para reproducir el prototipo.

Las pruebas funcionales pueden ejecutarse con:

```bash
python test_motor.py
```

## Nota institucional

Este proyecto **no es una herramienta oficial de la Comisión Nacional del Servicio Civil (CNSC)**. Las decisiones sobre admisión, cumplimiento de requisitos, VRM y procesos de selección corresponden exclusivamente a las entidades y procedimientos oficiales aplicables.

---
**Maestría en Ciencia de Datos — Prototipo académico**
