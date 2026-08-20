# EsterilControl 🩺⚙️

Aplicación web especializada para el control, manejo y gestión automatizada de ciclos, cargas y paquetes de esterilización industrial (con enfoque en procesos de óxido de etileno - EtO). Diseñada con una interfaz ágil y adaptable para su uso tanto en computadoras como en dispositivos móviles desde planta.

## 🚀 Características principales
- **Gestión de Ciclos:** Control exhaustivo de parámetros de esterilización (temperatura, presión, tiempos de exposición y fases del proceso).
- **Trazabilidad de Paquetes:** Registro detallado de materiales, lotes y cantidades procesadas por ciclo.
- **Generación Automatizada de Documentos:** Creación dinámica de informes técnicos y órdenes de entrega en formato Word/PDF basados en plantillas institucionales personalizadas.
- **Manejo Dinámico de Tablas:** Inyección inteligente de múltiples ítems adaptada a celdas complejas y estructuras con *colspan*.
- **Acceso Multidispositivo:** Interfaz optimizada para equipos de escritorio y visualización móvil directamente en el área de operaciones.
- **Control de Órdenes y Archivos:** Gestión y exportación limpia de comprobantes y registros de entrega para auditorías y control de calidad.

## 🛠️ Tecnologías utilizadas
- **Lenguaje:** Python
- **Framework Web:** Streamlit
- **Procesamiento de Documentos:** python-docx / Manejo de Streams de Bytes
- **Base de Datos:** Almacenamiento local en estructuras JSON sincronizadas

## 📂 Estructura del Proyecto
```text
EsterilControl/
│
├── .streamlit/           # Configuración de diseño y UI de Streamlit
├── assets/               # Recursos gráficos y multimedia
├── database/             # Registros de base de datos local (JSON)
├── reports/              # Plantillas base (.docx) y generador de informes
│   ├── plantilla_base.docx
│   ├── plantilla_orden_entrega.docx
│   └── pdf_generator.py
├── app.py                # Archivo principal de la aplicación web
└── README.md             # Documentación del proyecto