# Sistema de Orientación Laboral para Aspirantes a Vacantes Públicas CNSC

**Proyecto:** Modelo Predictivo para la Recomendación de Oportunidades Laborales en el Ámbito Gubernamental  
**Autores:** Diana Vásquez · Germán Mahecha  
**Maestría:** Ciencia de Datos

---

## Descripción

Este repositorio contiene un prototipo orientado al ciudadano/aspirante que permite registrar información de formación académica y experiencia laboral para identificar oportunidades OPEC históricas compatibles con su perfil.

El sistema integra reglas de elegibilidad, procesamiento de variables y un modelo predictivo entrenado con información histórica. La salida principal es un **índice de compatibilidad**, utilizado para ordenar las oportunidades y apoyar la exploración del ciudadano.

> **Advertencia:** el índice de compatibilidad es una orientación basada en información histórica. No corresponde a una probabilidad de selección, no garantiza superar la Verificación de Requisitos Mínimos (VRM) y no reemplaza la validación oficial de la CNSC.

El catálogo utilizado en el prototipo corresponde a información histórica de 2024 y se emplea con fines académicos y demostrativos.

## Contenido del repositorio

| Archivo | Descripción |
|---|---|
| `app.py` | Interfaz ciudadana desarrollada en Streamlit |
| `motor_inferencia.py` | Motor de validación, transformación y generación de recomendaciones |
| `paquete_modelo_cnsc_v1.joblib` | Modelo predictivo y transformaciones congeladas |
| `catalogo_opec_prototipo.csv` | Catálogo histórico OPEC usado para la demostración |
| `catalogo_opec_prototipo.joblib` | Versión serializada del catálogo para inferencia |
| `metadata_modelo.json` | Versión, alcance, métricas y metadatos del modelo |
| `contrato_entrada.json` | Estructura esperada del perfil ciudadano |
| `contrato_salida.json` | Estructura de salida del motor de recomendación |
| `ejemplo_perfil.json` | Ejemplo de perfil de entrada |
| `test_motor.py` | Pruebas funcionales del motor con datos nuevos y errores controlados |
| `requirements.txt` | Dependencias de Python |
| `ejecutar.bat` | Script de instalación, validación y ejecución para Windows |
| `Dockerfile` | Definición del contenedor del aplicativo |
| `.dockerignore` | Exclusiones para construcción del contenedor |

## Requisitos previos

- Windows 10/11 para ejecución mediante `ejecutar.bat`.
- Python 3.11 recomendado.
- Conexión a internet para la instalación inicial de dependencias.

## Instalación y ejecución

### Opción 1 — Windows

```bat
git clone https://github.com/DianaVF2025/proyectoMCD-ciudadano.git
cd proyectoMCD-ciudadano
ejecutar.bat
```

El script realiza:

1. Verificación de Python.
2. Comprobación de archivos requeridos.
3. Creación del entorno virtual.
4. Instalación de dependencias.
5. Ejecución de pruebas funcionales.
6. Apertura de la interfaz Streamlit en `http://localhost:8501`.

### Opción 2 — Ejecución manual

```bash
git clone https://github.com/DianaVF2025/proyectoMCD-ciudadano.git
cd proyectoMCD-ciudadano
python -m venv venv
```

Windows:

```bat
venv\Scripts\activate
pip install -r requirements.txt
python test_motor.py
streamlit run app.py
```

Mac/Linux:

```bash
source venv/bin/activate
pip install -r requirements.txt
python test_motor.py
streamlit run app.py
```

## Flujo funcional

```text
Perfil del ciudadano
        │
        ▼
Formación académica
        │
        ▼
Experiencia laboral
        │
        ▼
Validación y normalización
        │
        ▼
Comparación con requisitos OPEC
        │
        ▼
Motor predictivo
        │
        ▼
Índice de compatibilidad
        │
        ▼
Ranking de oportunidades laborales
```

## Enfoque del prototipo

El aplicativo fue reorientado al ciudadano. El usuario registra su propio perfil y recibe un conjunto ordenado de oportunidades OPEC históricas compatibles. Esta arquitectura reemplaza el enfoque anterior, en el cual una entidad seleccionaba una vacante y el sistema priorizaba candidatos históricos.

La recomendación combina información del perfil, requisitos de las OPEC y el componente predictivo. El resultado se presenta como orientación y no como decisión administrativa ni como mecanismo de selección oficial.

## Pruebas

Antes de iniciar la interfaz, `ejecutar.bat` ejecuta `test_motor.py`. Las pruebas verifican el comportamiento del motor frente a perfiles nuevos y condiciones de error controladas.

Para ejecutarlas manualmente:

```bash
python test_motor.py
```

## Docker

```bash
docker build -t orientador-cnsc .
docker run --rm -p 8501:8501 orientador-cnsc
```

La aplicación quedará disponible en:

```text
http://localhost:8501
```

## Alcance académico

El prototipo forma parte de un proyecto de Maestría en Ciencia de Datos orientado al análisis y diseño de un modelo predictivo para la recomendación de oportunidades laborales en el sector público colombiano.

La información incluida se utiliza con fines de investigación, validación técnica y demostración académica. El sistema no sustituye los procesos, criterios ni decisiones oficiales de la Comisión Nacional del Servicio Civil (CNSC).
