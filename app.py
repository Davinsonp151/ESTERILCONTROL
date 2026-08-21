import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime, timedelta
from io import BytesIO
from dotenv import load_dotenv

# --- CARGA DE SEGURIDAD ---
load_dotenv()

# --- CONFIGURACIÓN DE LA PESTAÑA DEL NAVEGADOR ---
st.set_page_config(
    page_title="EsterilControl",
    page_icon="assets/logo_esterilcontrol.jpg",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- IMPORTACIÓN DE GENERADORES EXTERNOS ---
from reports.pdf_generator import generar_pdf_informe, generar_orden_entrega

# --- GESTIÓN DE TEMA (CLARO / OSCURO) ---
if "tema_app" not in st.session_state:
    st.session_state.tema_app = "Claro"

# Estilos CSS dinámicos optimizados
if st.session_state.tema_app == "Oscuro":
    css_estilos = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
        html, body, [class*="css"], .stText, .stMarkdown, h1, h2, h3, h4, h5, h6 {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
            color: #f8fafc !important;
        }
        .stApp { background-color: #0f172a !important; }
        header[data-testid="stHeader"] { background-color: rgba(15, 23, 42, 0) !important; }
        section[data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 1px solid #334155; }
        section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] p { color: #f8fafc !important; }
        h1 { font-size: 1.5rem !important; color: #f8fafc !important; }
        h2 { font-size: 1.3rem !important; color: #f8fafc !important; }
        h3 { font-size: 1.1rem !important; color: #f8fafc !important; }
        div[data-testid="stMetric"] {
            background-color: #1e293b !important;
            border: 1px solid #334155 !important;
            padding: 15px !important;
            border-radius: 12px !important;
        }
        div[data-testid="stMetricValue"] { font-size: 1.3rem !important; color: #f8fafc !important; }
        div[data-testid="stMetricLabel"] { font-size: 0.75rem !important; color: #94a3b8 !important; }
        .stButton button {
            background-color: #334155 !important;
            color: #f8fafc !important;
            border: 1px solid #475569 !important;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.85rem !important;
        }
        .stButton button:hover { background-color: #475569 !important; color: #ffffff !important; }
        .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] { color: #f8fafc !important; background-color: #1e293b !important; }
        p, span, label { color: #e2e8f0 !important; }
    </style>
    """
else:
    css_estilos = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
        html, body, [class*="css"], .stText, .stMarkdown, h1, h2, h3, h4, h5, h6 {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
            color: #1e293b !important;
        }
        .stApp { background-color: #f8fafc !important; }
        header[data-testid="stHeader"] { background-color: rgba(248, 250, 252, 0) !important; }
        section[data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #e2e8f0; }
        h1 { font-size: 1.5rem !important; color: #0f172a !important; }
        h2 { font-size: 1.3rem !important; color: #0f172a !important; }
        h3 { font-size: 1.1rem !important; color: #0f172a !important; }
        div[data-testid="stMetric"] {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            padding: 15px !important;
            border-radius: 12px !important;
        }
        div[data-testid="stMetricValue"] { font-size: 1.3rem !important; color: #0f172a !important; }
        div[data-testid="stMetricLabel"] { font-size: 0.75rem !important; color: #64748b !important; }
        .stButton button { border-radius: 8px; font-weight: 600; font-size: 0.85rem !important; }
    </style>
    """

st.markdown(css_estilos, unsafe_allow_html=True)

LOGO_PATH = "assets/logo_esterilcontrol.jpg"
DB_CICLOS_FILE = "ciclos_db.json"
DB_IB_FILE = "ib_db.json"
CONFIG_MAESTRA_FILE = "sistema_config.json"

LISTA_HORAS_BASE = [f"{h:02d}" for h in range(1, 13)]
LISTA_MINUTOS = [f"{m:02d}" for m in range(60)]
LISTA_AM_PM = ["a.m.", "p.m."]

def obtener_hora_minuto_actual():
    now = datetime.now()
    hora = now.hour
    minuto = now.minute
    ampm = "p.m." if hora >= 12 else "a.m."
    h_12 = hora % 12
    h_12 = 12 if h_12 == 0 else h_12
    return f"{h_12:02d}", f"{minuto:02d}", ampm

# --- CONFIGURACIÓN DE USUARIOS Y PERMISOS MAESTROS ---
if "usuarios_db" not in st.session_state:
    st.session_state.usuarios_db = {
        "admin": {"nombre": "Administrador", "pass": os.getenv("ADMIN_PASS", "admin123"), "rol": "admin", "activo": True},
        "supervisor": {"nombre": "Davinson Peña (Supervisor)", "pass": os.getenv("SUPER_PASS", "super123"), "rol": "supervisor", "activo": True},
        "visitante": {"nombre": "Visitante / Auditor", "pass": os.getenv("VISIT_PASS", "visit123"), "rol": "visitante", "activo": True}
    }

OWNER_USER = os.getenv("OWNER_USER", "Davinson")
if "owner_pass" not in st.session_state:
    st.session_state.owner_pass = os.getenv("OWNER_PASS", "Davinson151")

# Permisos globales de módulos por rol
if "permisos_roles" not in st.session_state:
    st.session_state.permisos_roles = {
        "admin": {"Ciclos / Cargas": True, "Control de Incubación": True, "Liberación": True, "Informes": True},
        "supervisor": {"Ciclos / Cargas": True, "Control de Incubación": True, "Liberación": True, "Informes": True},
        "visitante": {"Ciclos / Cargas": True, "Control de Incubación": True, "Liberación": True, "Informes": True}
    }

if "app_bloqueada_general" not in st.session_state:
    st.session_state.app_bloqueada_general = False

# Cargar configuraciones de sistema adicionales si existen
if os.path.exists(CONFIG_MAESTRA_FILE):
    try:
        with open(CONFIG_MAESTRA_FILE, "r", encoding="utf-8") as f:
            cfg_cargada = json.load(f)
            if "app_bloqueada_general" in cfg_cargada:
                st.session_state.app_bloqueada_general = cfg_cargada["app_bloqueada_general"]
            if "permisos_roles" in cfg_cargada:
                st.session_state.permisos_roles = cfg_cargada["permisos_roles"]
            if "usuarios_db" in cfg_cargada:
                for u_k, u_v in cfg_cargada["usuarios_db"].items():
                    if u_k in st.session_state.usuarios_db:
                        st.session_state.usuarios_db[u_k]["pass"] = u_v.get("pass", st.session_state.usuarios_db[u_k]["pass"])
                        st.session_state.usuarios_db[u_k]["activo"] = u_v.get("activo", True)
    except:
        pass

def guardar_config_maestra():
    data_cfg = {
        "app_bloqueada_general": st.session_state.app_bloqueada_general,
        "permisos_roles": st.session_state.permisos_roles,
        "usuarios_db": st.session_state.usuarios_db
    }
    with open(CONFIG_MAESTRA_FILE, "w", encoding="utf-8") as f:
        json.dump(data_cfg, f, ensure_ascii=False, indent=4)

# --- FUNCIONES DE PERSISTENCIA DE DATOS ---
def cargar_datos_disco():
    ciclos = []
    ibs = []
    if os.path.exists(DB_CICLOS_FILE):
        try:
            with open(DB_CICLOS_FILE, "r", encoding="utf-8") as f:
                ciclos = json.load(f)
        except:
            ciclos = []
            
    if os.path.exists(DB_IB_FILE):
        try:
            with open(DB_IB_FILE, "r", encoding="utf-8") as f:
                ibs = json.load(f)
        except:
            ibs = []
    return ciclos, ibs

def guardar_datos_disco():
    with open(DB_CICLOS_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.ciclos_db, f, ensure_ascii=False, indent=4)
    with open(DB_IB_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.ib_db, f, ensure_ascii=False, indent=4)

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario_actual" not in st.session_state:
    st.session_state.usuario_actual = None
if "rol_actual" not in st.session_state:
    st.session_state.rol_actual = None

if "ciclos_db" not in st.session_state or "ib_db" not in st.session_state:
    c_car, ib_car = cargar_datos_disco()
    st.session_state.ciclos_db = c_car
    st.session_state.ib_db = ib_car

def mostrar_logo(width=180):
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=width)
    elif os.path.exists("logo_esterilcontrol.jpg"):
        st.image("logo_esterilcontrol.jpg", width=width)
    else:
        st.title("🌀 EsterilControl")


# ==========================================
# INTERRUPTOR DE EMERGENCIA GENERAL (KILL SWITCH)
# ==========================================
if st.session_state.app_bloqueada_general and st.session_state.rol_actual != "dueno":
    col_izq, col_centro, col_der = st.columns([1, 1.5, 1])
    with col_centro:
        st.write("")
        st.write("")
        mostrar_logo(width=220)
        st.markdown("<h2 style='text-align: center; color: #dc3545;'>⚠️ APLICACIÓN DETENIDA</h2>", unsafe_allow_html=True)
        st.warning("El sistema se encuentra temporalmente pausado por mantenimiento o directriz del Dueño. No hay acceso disponible en este momento.")
        
        st.markdown("---")
        st.markdown("#### ¿Eres el Dueño? Inicia sesión para restaurar el sistema:")
        u_m = st.text_input("Usuario Maestro", key="master_unlock_user")
        p_m = st.text_input("Contraseña Maestra", type="password", key="master_unlock_pass")
        if st.button("🔓 Desbloquear Aplicación", type="primary", use_container_width=True):
            if u_m.strip() == OWNER_USER and p_m == st.session_state.owner_pass:
                st.session_state.app_bloqueada_general = False
                guardar_config_maestra()
                st.session_state.autenticado = True
                st.session_state.usuario_actual = "Davinson (Dueño del Sistema)"
                st.session_state.rol_actual = "dueno"
                st.success("¡Sistema desbloqueado con éxito!")
                st.rerun()
            else:
                st.error("Credenciales maestras incorrectas.")
    st.stop()


# ==========================================
# 1. PANTALLA DE LOGIN
# ==========================================
if not st.session_state.autenticado:
    col_izq, col_centro, col_der = st.columns([1, 1.5, 1])

    with col_centro:
        st.write("")
        st.write("")
        col_img1, col_img2, col_img3 = st.columns([1, 2, 1])
        with col_img2:
            mostrar_logo(width=220)
        
        st.markdown("<h3 style='text-align: center;'><strong>EsterilControl</strong></h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray; font-size: 0.9rem;'>AM Medical S.A.S. - Control de Esterilización EtO</p>", unsafe_allow_html=True)

        user_input = st.text_input("Usuario", placeholder="Ingresa tu usuario")
        pass_input = st.text_input("Contraseña", type="password", placeholder="••••••••")

        if st.button("Iniciar Sesión", type="primary", use_container_width=True):
            user_clean = user_input.strip()
            user_clean_lower = user_clean.lower()
            
            if user_clean == OWNER_USER and pass_input == st.session_state.owner_pass:
                st.session_state.autenticado = True
                st.session_state.usuario_actual = "Davinson (Dueño del Sistema)"
                st.session_state.rol_actual = "dueno"
                st.rerun()
            elif user_clean_lower in st.session_state.usuarios_db:
                u_data = st.session_state.usuarios_db[user_clean_lower]
                if not u_data.get("activo", True):
                    st.error("Este usuario ha sido inhabilitado temporalmente por el Dueño.")
                elif u_data["pass"] == pass_input:
                    st.session_state.autenticado = True
                    st.session_state.usuario_actual = u_data["nombre"]
                    st.session_state.rol_actual = u_data["rol"]
                    st.rerun()
                else:
                    st.error("Credenciales de acceso incorrectas.")
            else:
                st.error("Credenciales de acceso incorrectas.")

# ==========================================
# 2. APLICACIÓN PRINCIPAL
# ==========================================
else:
    top_c1, top_c2 = st.columns([10, 1])
    with top_c2:
        tooltip_txt = "Cambiar a Modo Claro" if st.session_state.tema_app == "Oscuro" else "Cambiar a Modo Oscuro"
        icono_btn = "☀️" if st.session_state.tema_app == "Oscuro" else "🌙"
        if st.button(icono_btn, help=tooltip_txt, key="btn_toggle_tema_top"):
            st.session_state.tema_app = "Claro" if st.session_state.tema_app == "Oscuro" else "Oscuro"
            st.rerun()

    with st.sidebar:
        mostrar_logo(width=140)
        st.caption("AM Medical - Control EtO")
        st.markdown(f"**Usuario:** {st.session_state.usuario_actual}")
        st.markdown(f"**Rol:** `{st.session_state.rol_actual.upper()}`")
        
        st.markdown("---")

        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.autenticado = False
            st.rerun()

        st.markdown("---")
        
        lista_nav_base = ["Panel de control", "Ciclos / Cargas", "Control de Incubación", "Liberación", "Informes"]
        
        if st.session_state.rol_actual == "dueno":
            lista_nav = lista_nav_base + ["Configuración Admin", "🔑 Configuración Maestro (Dueño)"]
        else:
            rol_key = st.session_state.rol_actual
            permisos_rol = st.session_state.permisos_roles.get(rol_key, {})
            
            lista_nav = ["Panel de control"]
            for mod in ["Ciclos / Cargas", "Control de Incubación", "Liberación", "Informes"]:
                if permisos_rol.get(mod, True):
                    lista_nav.append(mod)
            
            if st.session_state.rol_actual == "admin":
                lista_nav.append("Configuración Admin")

        opcion = st.radio("Navegación", lista_nav)

    st.title("Control de ésteres")

    # --- PANEL DE CONTROL ---
    if opcion == "Panel de control":
        st.subheader("Panel de Control General (En Vivo)")
        
        df_c = pd.DataFrame(st.session_state.ciclos_db)
        mes_actual = datetime.now().month
        anio_actual = datetime.now().year
        nombre_mes = datetime.now().strftime("%B").capitalize()

        total_ciclos_mes = 0
        activos_hoy = 0
        if not df_c.empty:
            df_c["fecha_dt"] = pd.to_datetime(df_c["fecha"], errors="coerce")
            df_mes = df_c[(df_c["fecha_dt"].dt.month == mes_actual) & (df_c["fecha_dt"].dt.year == anio_actual)]
            total_ciclos_mes = len(df_mes)
            activos_hoy = len(df_c[df_c["fecha"] == str(datetime.now().date())])

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("CICLOS HOY", str(activos_hoy))
        c2.metric(f"CICLOS {nombre_mes.upper()}", str(total_ciclos_mes))
        c3.metric("EN CUARENTENA", str(len([x for x in st.session_state.ciclos_db if x.get('carga_liberada', 'No') == 'No'])))
        c4.metric("TOTAL HISTÓRICO", str(len(st.session_state.ciclos_db)))
        c5.metric("ESTADO SISTEMA", "Activo", "Discoteca local")
        
        st.markdown("---")
        st.subheader(f"Últimos Ciclos Procesados y Alertas")
        
        if not df_c.empty:
            df_c = df_c.sort_values(by=["fecha", "n_ciclo"], ascending=[False, False])
            
            for index, row in df_c.iterrows():
                n_c_fmt = f"{int(row['n_ciclo']):05d}"
                estado_lib = row.get('carga_liberada', 'No')
                res_ib_val = row.get('res_ib', 'Negativo')
                
                color_fondo = "#1e293b" if st.session_state.tema_app == "Oscuro" else "#f8f9fa"
                borde_tarjeta = "#334155" if st.session_state.tema_app == "Oscuro" else "#ddd"
                texto_color = "#f8fafc" if st.session_state.tema_app == "Oscuro" else "#1e293b"

                badge_estado = "🟡 En Proceso / Cuarentena"
                if "Rechazado" in estado_lib or res_ib_val == "Positivo":
                    badge_estado = f"🔴 {estado_lib} (¡Alerta IB Positivo!)" if res_ib_val == "Positivo" else f"🔴 {estado_lib}"
                elif estado_lib == "Sí":
                    badge_estado = "🟢 Liberado y Conforme"

                st.markdown(f"""
                <div style="background-color: {color_fondo}; padding: 12px 16px; border-radius: 10px; margin-bottom: 10px; border: 1px solid {borde_tarjeta}; font-size: 0.88rem; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                    <span style="color: {texto_color};"><b>Ciclo N° {n_c_fmt}</b> | Fecha: {row['fecha']} | Equipo: {row['equipo']} | Unidades: {row['tot_unidades']} | IB: <b>{res_ib_val}</b> | Estado: <b>{badge_estado}</b></span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No hay ciclos registrados todavía.")

    # --- CICLOS / CARGAS ---
    elif opcion == "Ciclos / Cargas":
        st.subheader("Control de Ciclos")
        
        if st.session_state.rol_actual in ["admin", "supervisor", "dueno"]:
            with st.expander("➕ REGISTRAR NUEVO CICLO DE ESTERILIZACIÓN", expanded=False):
                
                fc1, fc2, fc3, fc4 = st.columns(4)
                with fc1:
                    n_ciclo = st.number_input("N° CICLO:", value=len(st.session_state.ciclos_db) + 1, step=1)
                with fc2:
                    fecha_c = st.date_input("FECHA:", datetime.now())
                
                h_act, m_act, ampm_act = obtener_hora_minuto_actual()
                
                with fc3:
                    st.markdown("**HORA INICIO:**")
                    hi_col1, hi_col2, hi_col3 = st.columns(3)
                    idx_h_def = LISTA_HORAS_BASE.index(h_act) if h_act in LISTA_HORAS_BASE else 0
                    idx_m_def = LISTA_MINUTOS.index(m_act) if m_act in LISTA_MINUTOS else 0
                    idx_ampm_def = LISTA_AM_PM.index(ampm_act) if ampm_act in LISTA_AM_PM else 0
                    
                    with hi_col1:
                        sel_hi_h = st.selectbox("H", LISTA_HORAS_BASE, index=idx_h_def, key="reg_hi_h")
                    with hi_col2:
                        sel_hi_m = st.selectbox("M", LISTA_MINUTOS, index=idx_m_def, key="reg_hi_m")
                    with hi_col3:
                        sel_hi_ap = st.selectbox("AM/PM", LISTA_AM_PM, index=idx_ampm_def, key="reg_hi_ap")
                    
                    hora_i_final = f"{sel_hi_h}:{sel_hi_m} {sel_hi_ap}"

                with fc4:
                    st.markdown("**HORA FIN:**")
                    hf_tipo = st.selectbox("Estado Fin", ["En curso", "Hora Específica"], key="reg_hf_tipo")
                    
                    if hf_tipo == "Hora Específica":
                        hf_col1, hf_col2, hf_col3 = st.columns(3)
                        with hf_col1:
                            sel_hf_h = st.selectbox("H", LISTA_HORAS_BASE, index=idx_h_def, key="reg_hf_h")
                        with hf_col2:
                            sel_hf_m = st.selectbox("M", LISTA_MINUTOS, index=idx_m_def, key="reg_hf_m")
                        with hf_col3:
                            sel_hf_ap = st.selectbox("AM/PM", LISTA_AM_PM, index=idx_ampm_def, key="reg_hf_ap")
                        hora_f_final = f"{sel_hf_h}:{sel_hf_m} {sel_hf_ap}"
                    else:
                        hora_f_final = ""

                eq1, op1 = st.columns(2)
                with eq1:
                    equipo = st.selectbox("EQUIPO:", ["HDX-6 EO", "HDX-2 EO"])
                with op1:
                    operador = st.text_input("OPERADOR / RESPONSABLE:", st.session_state.usuario_actual)

                st.markdown("#### 🌡️ PARÁMETROS FÍSICOS DE CÁMARA:")
                pf1, pf2, pf3, pf4 = st.columns(4)
                with pf1:
                    temp = st.number_input("TEMP (°C):", value=30.9)
                with pf2:
                    humedad = st.number_input("HUMEDAD (%Rh):", value=52.5)
                with pf3:
                    presion_camara = st.text_input("PRESIÓN CÁMARA:", "-49kPa")
                with pf4:
                    t_exp = st.number_input("TIEMPO EXP (min):", value=120)

                pf5, pf6 = st.columns(2)
                with pf5:
                    aireacion = st.text_input("N° AIREACIONES:", "2N2A")
                with pf6:
                    resultado = st.selectbox("RESULTADO DE PROCESO:", ["Aprobado", "No Conforme"])

                st.markdown("#### 📦 DETALLE DE CARGA (Unidades, Peso y Lotes):")
                
                def calcular_fila(nombre, peso_unit):
                    col_u, col_p, col_l = st.columns([1.5, 1, 1.5])
                    with col_u:
                        u = st.number_input(f"Unid. {nombre}", min_value=0, value=0, key=f"u_{nombre}")
                    with col_p:
                        p_tot = round(u * peso_unit, 2)
                        st.text(f"Peso: {p_tot} kg")
                    with col_l:
                        l = st.text_input(f"Lote {nombre}", "0" if u == 0 else "LT080327", key=f"l_{nombre}")
                    return u, p_tot, l

                u_lap, p_lap, l_lap = calcular_fila("Paq. Laparotomía (1.06kg)", 1.06)
                u_hemo, p_hemo, l_hemo = calcular_fila("U. Hemodinamia (0.12kg)", 0.12)
                u_cir, p_cir, l_cir = calcular_fila("Cirugía Valledupar (0.14kg)", 0.14)
                u_sab, p_sab, l_sab = calcular_fila("Sábanas Estériles (1.25kg)", 1.25)
                u_adult, p_adult, l_adult = calcular_fila("Paquete Central Adulto (1.10kg)", 1.10)
                u_neuro, p_neuro, l_neuro = calcular_fila("Neurointervencionismo (1.25kg)", 1.25)
                u_apos, p_apos, l_apos = calcular_fila("Apósitos Estériles (0.02kg)", 0.02)

                tot_unidades = u_lap + u_hemo + u_cir + u_sab + u_adult + u_neuro + u_apos
                tot_peso = round(p_lap + p_hemo + p_cir + p_sab + p_adult + p_neuro + p_apos, 2)
                
                st.markdown("#### 🧺 CANASTAS EN CARGA:")
                can1, can2 = st.columns(2)
                with can1:
                    canastas_grandes = st.number_input("Canastas Grandes (Máx 36):", min_value=0, max_value=36, value=0)
                with can2:
                    canastas_pequenas = st.number_input("Canastas Pequeñas (Máx 12):", min_value=0, max_value=12, value=0)

                ocupacion_eq = round(((canastas_grandes + canastas_pequenas) / (36 + 12)) * 100, 1)
                ocupacion_eq = min(ocupacion_eq, 100.0)

                st.info(f"📊 **TOTALES:** Unidades = {tot_unidades} | Peso = {tot_peso} kg | Ocupación = {ocupacion_eq}% ({canastas_grandes} Grandes, {canastas_pequenas} Pequeñas)")

                inf_final_col1, inf_final_col2 = st.columns(2)
                with inf_final_col1:
                    estado_cumplimiento = st.selectbox("ESTADO CUMPLIMIENTO:", ["CUMPLE", "NO CUMPLE"])
                with inf_final_col2:
                    observaciones = st.text_input("TIPO DE CARGA / OBSERVACIONES:", "Textil")

                if st.button("💾 Guardar Ciclo en Sistema", type="primary"):
                    if hora_f_final:
                        try:
                            fecha_lib = (datetime.combine(fecha_c, datetime.now().time()) + timedelta(hours=49)).strftime("%Y-%m-%d %H:%M")
                        except:
                            fecha_lib = "Pendiente"
                    else:
                        fecha_lib = "Pendiente (En curso)"

                    nuevo_registro = {
                        "n_ciclo": int(n_ciclo),
                        "fecha": str(fecha_c),
                        "hora_inicio": hora_i_final,
                        "hora_fin": hora_f_final,
                        "equipo": equipo,
                        "operador": operador,
                        "temp": temp,
                        "humedad": humedad,
                        "conc_eto": "99.0%",
                        "presion_camara": presion_camara,
                        "t_exp": t_exp,
                        "aireacion": aireacion,
                        "resultado": resultado,
                        "q_lap": u_lap, "p_lap": p_lap, "l_lap": l_lap,
                        "q_hemo": u_hemo, "p_hemo": p_hemo, "l_hemo": l_hemo,
                        "q_cir": u_cir, "p_cir": p_cir, "l_cir": l_cir,
                        "q_sab": u_sab, "p_sab": p_sab, "l_sab": l_sab,
                        "q_adult": u_adult, "p_adult": p_adult, "l_adult": l_adult,
                        "q_neuro": u_neuro, "p_neuro": p_neuro, "l_neuro": l_neuro,
                        "q_apos": u_apos, "p_apos": p_apos, "l_apos": l_apos,
                        "tot_unidades": tot_unidades,
                        "tot_peso": tot_peso,
                        "canastas_grandes": canastas_grandes,
                        "canastas_pequenas": canastas_pequenas,
                        "ocupacion": ocupacion_eq,
                        "estado_cumplimiento": estado_cumplimiento,
                        "fecha_liberacion": fecha_lib,
                        "carga_liberada": "No",
                        "res_ib": "Negativo",
                        "observaciones": observaciones
                    }
                    st.session_state.ciclos_db.append(nuevo_registro)
                    
                    existe_ib = any(int(ib.get('ciclo', 0)) == int(n_ciclo) for ib in st.session_state.ib_db)
                    if not existe_ib:
                        st.session_state.ib_db.append({
                            "ciclo": int(n_ciclo),
                            "tipo": "BT10 EO ATCC 9372",
                            "lote": "A50300",
                            "resultado": "Negativo",
                            "fecha_incubacion": str(fecha_c),
                            "responsable": operador,
                            "observaciones": "Conforme (Automático)"
                        })

                    guardar_datos_disco()
                    st.success(f"¡Ciclo N° {f'{n_ciclo:05d}'} y su control biológico automático guardados con éxito!")
                    st.rerun()
        else:
            st.info("👁️ **Modo Visitante / Auditor:** Solo lectura.")

        st.markdown("---")
        st.subheader("Historial y Gestión de Ciclos Registrados")
        
        if st.session_state.ciclos_db:
            ciclos_ordenados = sorted(st.session_state.ciclos_db, key=lambda x: (x['fecha'], x['n_ciclo']), reverse=True)
            for idx, c in enumerate(ciclos_ordenados):
                cod_c_fmt = f"{int(c['n_ciclo']):05d}"
                estado_h_fin = c['hora_fin'] if c['hora_fin'] else "⚠️ EN CURSO"
                
                with st.expander(f"🔹 CICLO N° {cod_c_fmt} | Fecha: {c['fecha']} | Fin: {estado_h_fin} | Equipo: {c['equipo']} | Unidades: {c['tot_unidades']}", key=f"exp_ciclo_{idx}_{c['n_ciclo']}"):
                    
                    st.markdown("#### ⚙️ Datos Técnicos del Ciclo")
                    dc1, dc2, dc3, dc4 = st.columns(4)
                    dc1.metric("Temperatura", f"{c['temp']} °C")
                    dc2.metric("Humedad", f"{c.get('humedad', 52.5)} %Rh")
                    dc3.metric("Presión Cámara", c.get('presion_camara', '-49kPa'))
                    dc4.metric("Tiempo Exposición", f"{c['t_exp']} Min")

                    dc5, dc6, dc7, dc8 = st.columns(4)
                    dc5.metric("Concentración EtO", c.get('conc_eto', '99.0%'))
                    dc6.metric("Aireaciones", c.get('aireacion', '2N2A'))
                    dc7.metric("Resultado", c['resultado'])
                    dc8.metric("Responsable", c['operador'])

                    st.markdown("---")
                    st.markdown("#### 📦 Datos de la Carga y Ocupación")
                    
                    cc1, cc2, cc3 = st.columns(3)
                    cc1.metric("Peso Total de Carga", f"{c['tot_peso']} kg")
                    cc2.metric("Unidades Totales", f"{c['tot_unidades']} U")
                    cc3.metric("Ocupación de Cámara", f"{c['ocupacion']}%")

                    st.write(f"**Canastas Utilizadas:** {c['canastas_grandes']} Canastas Grandes / {c['canastas_pequenas']} Canastas Pequeñas")
                    st.write(f"**Tipo de Carga / Observaciones:** {c['observaciones']}")

                    st.markdown("##### Desglose de Ítems Esterilizados:")
                    items_detalle = [
                        ("Paquete Laparotomía", c.get('q_lap', 0), c.get('l_lap', '0')),
                        ("Unidad Hemodinamia", c.get('q_hemo', 0), c.get('l_hemo', '0')),
                        ("Cirugía Valledupar", c.get('q_cir', 0), c.get('l_cir', '0')),
                        ("Sábanas Estériles", c.get('q_sab', 0), c.get('l_sab', '0')),
                        ("Paquete Central Adulto", c.get('q_adult', 0), c.get('l_adult', '0')),
                        ("Neurointervencionismo", c.get('q_neuro', 0), c.get('l_neuro', '0')),
                        ("Apósitos Estériles", c.get('q_apos', 0), c.get('l_apos', '0')),
                    ]
                    
                    df_det = pd.DataFrame(items_detalle, columns=["Ítem / Material", "Cantidad (U)", "Lote"])
                    df_det = df_det[df_det["Cantidad (U)"] > 0]
                    if not df_det.empty:
                        st.dataframe(df_det, use_container_width=True, hide_index=True)
                    else:
                        st.info("No hay ítems registrados en este ciclo.")

                    if not c.get('hora_fin') and st.session_state.rol_actual in ["admin", "supervisor", "dueno"]:
                        st.markdown("---")
                        st.write("⚙️ **Finalizar Ciclo en Curso:**")
                        
                        col_fin_btn, col_fin_sel = st.columns([1, 2])
                        
                        with col_fin_btn:
                            st.write("")
                            if st.button(f"⏱️ Ciclo terminado", key=f"btn_fin_{idx}_{c['n_ciclo']}", type="primary"):
                                h_act_s, m_act_s, ampm_act_s = obtener_hora_minuto_actual()
                                hora_actual_exacta = f"{h_act_s}:{m_act_s} {ampm_act_s}"
                                c['hora_fin'] = hora_actual_exacta
                                c['fecha_liberacion'] = (datetime.now() + timedelta(hours=49)).strftime("%Y-%m-%d %H:%M")
                                guardar_datos_disco()
                                st.success(f"¡Ciclo finalizado con la hora actual ({hora_actual_exacta})!")
                                st.rerun()

                        with col_fin_sel:
                            st.markdown("O selecciona hora exacta manual:")
                            h_m_col1, h_m_col2, h_m_col3, h_m_col4 = st.columns([1, 1, 1, 1.2])
                            with h_m_col1:
                                sh_h = st.selectbox("H", LISTA_HORAS_BASE, key=f"hist_sh_h_{idx}_{c['n_ciclo']}")
                            with h_m_col2:
                                sh_m = st.selectbox("M", LISTA_MINUTOS, key=f"hist_sh_m_{idx}_{c['n_ciclo']}")
                            with h_m_col3:
                                sh_ap = st.selectbox("AM/PM", LISTA_AM_PM, key=f"hist_sh_ap_{idx}_{c['n_ciclo']}")
                            with h_m_col4:
                                st.write("")
                                if st.button("Guardar Hora", key=f"btn_guardar_h_{idx}_{c['n_ciclo']}"):
                                    hora_manual_formada = f"{sh_h}:{sh_m} {sh_ap}"
                                    c['hora_fin'] = hora_manual_formada
                                    c['fecha_liberacion'] = (datetime.now() + timedelta(hours=49)).strftime("%Y-%m-%d %H:%M")
                                    guardar_datos_disco()
                                    st.success(f"¡Hora fin actualizada a {hora_manual_formada}!")
                                    st.rerun()

                    if st.session_state.rol_actual in ["admin", "dueno"]:
                        st.markdown("---")
                        if st.button(f"🗑️ Eliminar Ciclo N° {cod_c_fmt}", key=f"del_ciclo_{idx}_{c['n_ciclo']}"):
                            st.session_state.ciclos_db = [x for x in st.session_state.ciclos_db if x['n_ciclo'] != c['n_ciclo']]
                            st.session_state.ib_db = [x for x in st.session_state.ib_db if int(x.get('ciclo', 0)) != int(c['n_ciclo'])]
                            guardar_datos_disco()
                            st.rerun()
        else:
            st.info("No hay ciclos guardados actualmente.")

    # --- CONTROL DE INCUBACIÓN ---
    elif opcion == "Control de Incubación":
        st.subheader("Control de Indicadores Biológicos (IB)")
        
        if st.session_state.rol_actual in ["admin", "supervisor", "dueno"]:
            with st.expander("➕ REGISTRO HISTÓRICO / ADICIONAL DE INDICADOR BIOLÓGICO", expanded=False):
                ib_c1, ib_c2, ib_c3 = st.columns(3)
                with ib_c1:
                    ciclo_asoc = st.number_input("Asociar a N° Ciclo", value=1, step=1)
                    tipo_ib = st.text_input("Tipo Indicador", "BT10 EO ATCC 9372")
                with ib_c2:
                    lote_ib = st.text_input("Lote IB", "A50300")
                    res_lectura = st.selectbox("Resultado (48h)", ["Negativo", "Positivo"])
                with ib_c3:
                    fecha_incubacion = st.date_input("Fecha de Incubación", datetime.now())
                    resp_ib = st.text_input("Responsable", st.session_state.usuario_actual)
                
                obs_ib = st.text_input("Observaciones IB", "Conforme")

                if st.button("💾 Guardar / Actualizar Indicador Biológico Manual", type="primary"):
                    encontrado = False
                    for ib in st.session_state.ib_db:
                        if int(ib.get('ciclo', 0)) == int(ciclo_asoc):
                            ib['tipo'] = tipo_ib
                            ib['lote'] = lote_ib
                            ib['resultado'] = res_lectura
                            ib['fecha_incubacion'] = str(fecha_incubacion)
                            ib['responsable'] = resp_ib
                            ib['observaciones'] = obs_ib
                            encontrado = True
                    
                    if not encontrado:
                        st.session_state.ib_db.append({
                            "ciclo": int(ciclo_asoc),
                            "tipo": tipo_ib,
                            "lote": lote_ib,
                            "resultado": res_lectura,
                            "fecha_incubacion": str(fecha_incubacion),
                            "responsable": resp_ib,
                            "observaciones": obs_ib
                        })

                    for c in st.session_state.ciclos_db:
                        if int(c['n_ciclo']) == int(ciclo_asoc):
                            c['res_ib'] = res_lectura
                    
                    guardar_datos_disco()
                    st.success("¡Indicador biológico guardado correctamente!")
                    st.rerun()

        st.markdown("---")
        st.subheader("Visualización Interactiva por Desglose de Indicadores Biológicos")
        
        if st.session_state.ciclos_db:
            ib_unicos = {}
            for ib in st.session_state.ib_db:
                ib_unicos[int(ib.get('ciclo', 0))] = ib
            st.session_state.ib_db = list(ib_unicos.values())

            ibs_existentes = [int(ib.get('ciclo', 0)) for ib in st.session_state.ib_db]
            for c in st.session_state.ciclos_db:
                if int(c['n_ciclo']) not in ibs_existentes:
                    st.session_state.ib_db.append({
                        "ciclo": int(c['n_ciclo']),
                        "tipo": "BT10 EO ATCC 9372",
                        "lote": "A50300",
                        "resultado": c.get('res_ib', 'Negativo'),
                        "fecha_incubacion": c['fecha'],
                        "responsable": c['operador'],
                        "observaciones": "Creado automáticamente"
                    })

            ib_ordenados = sorted(st.session_state.ib_db, key=lambda x: int(x.get('ciclo', 0)), reverse=True)
            
            for idx_ib, ib in enumerate(ib_ordenados):
                c_num = int(ib.get('ciclo', 0))
                res_actual = ib.get('resultado', 'Negativo')
                icono_estado = "🟢 Negativo (Conforme)" if res_actual == "Negativo" else "🔴 Positivo (¡Alerta!)"
                
                with st.expander(f"🧬 INDICADOR BIOLÓGICO - CICLO N° {c_num:05d} | Resultado: {icono_estado} | Lote: {ib.get('lote', '-')}", key=f"exp_ib_{idx_ib}_{c_num}"):
                    
                    if st.session_state.rol_actual in ["admin", "supervisor", "dueno"]:
                        with st.form(key=f"form_upd_ib_{idx_ib}_{c_num}"):
                            ib_col1, ib_col2, ib_col3 = st.columns(3)
                            with ib_col1:
                                nuevo_tipo = st.text_input("Tipo Indicador", ib.get('tipo', 'BT10 EO ATCC 9372'), key=f"n_tipo_{idx_ib}_{c_num}")
                                nuevo_lote = st.text_input("Lote IB", ib.get('lote', 'A50300'), key=f"n_lote_{idx_ib}_{c_num}")
                            with ib_col2:
                                nuevo_res = st.selectbox("Resultado (48h)", ["Negativo", "Positivo"], index=0 if ib.get('resultado', 'Negativo') == "Negativo" else 1, key=f"n_res_{idx_ib}_{c_num}")
                                nuevo_resp = st.text_input("Responsable", ib.get('responsable', st.session_state.usuario_actual), key=f"n_resp_{idx_ib}_{c_num}")
                            with ib_col3:
                                nueva_obs = st.text_input("Observaciones", ib.get('observaciones', ''), key=f"n_obs_{idx_ib}_{c_num}")
                                st.write("")
                                btn_act_ib = st.form_submit_button("💾 Actualizar Indicador")
                            
                            if btn_act_ib:
                                ib['tipo'] = nuevo_tipo
                                ib['lote'] = nuevo_lote
                                ib['resultado'] = nuevo_res
                                ib['responsable'] = nuevo_resp
                                ib['observaciones'] = nueva_obs
                                
                                for c in st.session_state.ciclos_db:
                                    if int(c['n_ciclo']) == c_num:
                                        c['res_ib'] = nuevo_res
                                        
                                guardar_datos_disco()
                                st.success("¡Indicador biológico actualizado con éxito!")
                                st.rerun()

                        if st.session_state.rol_actual in ["admin", "dueno"]:
                            if st.button(f"🗑️ Eliminar Registro IB Ciclo {c_num:05d}", key=f"del_ib_{idx_ib}_{c_num}"):
                                st.session_state.ib_db = [x for x in st.session_state.ib_db if int(x.get('ciclo', 0)) != c_num]
                                guardar_datos_disco()
                                st.warning(f"Registro IB del ciclo {c_num:05d} eliminado.")
                                st.rerun()
                    else:
                        st.write(f"**Tipo:** {ib.get('tipo')}")
                        st.write(f"**Lote:** {ib.get('lote')}")
                        st.write(f"**Resultado:** {ib.get('resultado')}")
                        st.write(f"**Fecha Incubación:** {ib.get('fecha_incubacion')}")
                        st.write(f"**Responsable:** {ib.get('responsable')}")
                        st.write(f"**Observaciones:** {ib.get('observaciones')}")
        else:
            st.info("No hay ciclos ni indicadores biológicos para mostrar.")

    # --- LIBERACIÓN ---
    elif opcion == "Liberación":
        st.subheader("Liberación de Carga (Validación Estricta por Control Biológico)")
        if st.session_state.ciclos_db:
            # Reemplaza el bucle simple por esta línea con orden inverso:
            ciclos_ordenados_lib = sorted(st.session_state.ciclos_db, key=lambda x: (str(x.get('fecha', '')), int(x.get('n_ciclo', 0))), reverse=True)
            
            for idx_l, c in enumerate(ciclos_ordenados_lib):
                c_num_int = int(c['n_ciclo'])
                cod_c_fmt = f"{c_num_int:05d}"
                
                ib_asoc = next((ib for ib in st.session_state.ib_db if int(ib.get('ciclo', 0)) == c_num_int), None)
                res_ib_ciclo = ib_asoc.get('resultado', 'Negativo') if ib_asoc else c.get('res_ib', 'Negativo')
                
                estado_carga_actual = c.get('carga_liberada', 'No')
                
                color_borde = "#0052cc"
                if "Rechazado" in estado_carga_actual or res_ib_ciclo == "Positivo":
                    color_borde = "#dc3545"
                elif estado_carga_actual == "Sí":
                    color_borde = "#28a745"

                bg_card_lib = "#1e293b" if st.session_state.tema_app == "Oscuro" else "#f8f9fa"
                text_card_lib = "#f8fafc" if st.session_state.tema_app == "Oscuro" else "#1e293b"

                with st.container():
                    st.markdown(f"""
                    <div style="background-color: {bg_card_lib}; padding: 14px; border-radius: 10px; border-left: 6px solid {color_borde}; margin-bottom: 8px; font-size: 0.9rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                        <h4 style="color: {text_card_lib}; margin-bottom: 5px;">📦 Ciclo N° {cod_c_fmt} | Fecha: {c['fecha']} (Fin: {c['hora_fin'] if c['hora_fin'] else 'En curso'})</h4>
                        <p style="color: {text_card_lib}; margin-bottom: 3px;"><b>Estado Carga:</b> <code>{estado_carga_actual}</code> | <b>Control Biológico (IB):</b> <span style="color: {'red' if res_ib_ciclo == 'Positivo' else 'green'}; font-weight: bold;">{res_ib_ciclo}</span></p>
                        <p style="color: {text_card_lib}; margin-bottom: 0px;"><b>Fecha Prevista Liberación (49h):</b> {c.get('fecha_liberacion', 'Pendiente')} | <b>Unidades:</b> {c['tot_unidades']} | <b>Peso:</b> {c['tot_peso']} kg</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if c.get('hora_fin') and st.session_state.rol_actual in ["admin", "supervisor", "dueno"]:
                        if estado_carga_actual == "Sí":
                            if st.session_state.rol_actual in ["admin", "dueno"]:
                                if st.button(f"↩️ Quitar Liberación (Admin) - Ciclo {cod_c_fmt}", key=f"btn_quitar_lib_{c_num_int}", type="secondary"):
                                    c['carga_liberada'] = "No"
                                    guardar_datos_disco()
                                    st.success(f"¡Carga del Ciclo N° {cod_c_fmt} regresada a cuarentena!")
                                    st.rerun()
                            else:
                                st.info("🔒 Carga liberada. Solo administración puede revertirla.")
                        else:
                            if res_ib_ciclo == "Negativo":
                                if st.button(f"✅ Aprobar y Liberar Ciclo {cod_c_fmt}", key=f"btn_aprobar_lib_{c_num_int}", type="primary"):
                                    c['carga_liberada'] = "Sí"
                                    guardar_datos_disco()
                                    st.success(f"¡Carga del Ciclo N° {cod_c_fmt} liberada con éxito!")
                                    st.rerun()
                            else:
                                st.warning("⚠️ Bloqueado: El IB es Positivo.")

                        if estado_carga_actual == "Rechazado (IB Positivo)":
                            if st.session_state.rol_actual in ["admin", "dueno"]:
                                if st.button(f"↩️ Quitar Rechazo IB (Admin) - Ciclo {cod_c_fmt}", key=f"btn_quitar_rej_ib_{c_num_int}", type="secondary"):
                                    c['carga_liberada'] = "No"
                                    guardar_datos_disco()
                                    st.success(f"¡Rechazo IB retirado para el Ciclo N° {cod_c_fmt}!")
                                    st.rerun()
                            else:
                                st.info("🔒 Rechazado por IB. Requiere administración.")
                        else:
                            if st.button(f"🔴 Rechazar por Control Biológico - Ciclo {cod_c_fmt}", key=f"btn_hacer_rej_ib_{c_num_int}"):
                                c['carga_liberada'] = "Rechazado (IB Positivo)"
                                guardar_datos_disco()
                                st.error(f"¡Ciclo {cod_c_fmt} marcado como rechazado por IB positivo!")
                                st.rerun()

                        if estado_carga_actual == "Rechazado (Daños / Falla)":
                            if st.session_state.rol_actual in ["admin", "dueno"]:
                                if st.button(f"↩️ Quitar Rechazo Daños (Admin) - Ciclo {cod_c_fmt}", key=f"btn_quitar_rej_dan_{c_num_int}", type="secondary"):
                                    c['carga_liberada'] = "No"
                                    guardar_datos_disco()
                                    st.success(f"¡Rechazo por daños retirado para el Ciclo N° {cod_c_fmt}!")
                                    st.rerun()
                            else:
                                st.info("🔒 Rechazado por daños. Requiere administración.")
                        else:
                            if st.button(f"⚠️ Rechazar por Daños / Novedad - Ciclo {cod_c_fmt}", key=f"btn_hacer_rej_dan_{c_num_int}"):
                                c['carga_liberada'] = "Rechazado (Daños / Falla)"
                                guardar_datos_disco()
                                st.error(f"¡Ciclo {cod_c_fmt} marcado como rechazado por daños!")
                                st.rerun()
                    
                    st.markdown("---")
        else:
            st.info("No hay ciclos registrados.")

    # --- INFORMES ---
    elif opcion == "Informes":
        st.subheader("Módulo de Informes Oficiales (CIR-FT-01)")
        
        if st.session_state.ciclos_db:
            ciclos_opciones = [f"EL CONTROL DEL PROCESO DE ESTERILIZACIÓN - {int(c['n_ciclo']):05d}" for c in st.session_state.ciclos_db]
            ciclo_seleccionado_str = st.selectbox("Selecciona el ciclo para generar el formato oficial:", ciclos_opciones)
            
            cod_extraido = ciclo_seleccionado_str.split(" - ")[1]
            n_ciclo_sel = int(cod_extraido)
            c_sel = next((x for x in st.session_state.ciclos_db if int(x['n_ciclo']) == n_ciclo_sel), None)

            if c_sel:
                datos_para_pdf = {
                    "metodo": "Óxido de Etileno",
                    "equipo": c_sel.get('equipo', 'HDX-6 EO'),
                    "esterilizador": c_sel.get('equipo', 'HDX-6 EO'),
                    "n_cic": f"{int(c_sel['n_ciclo']):05d}",
                    "fecha_inicio": c_sel.get('fecha', ''),
                    "hora_inicio": c_sel.get('hora_inicio', ''),
                    "hora_fin": c_sel.get('hora_fin', 'En curso'),
                    "temperatura": f"{c_sel.get('temp', 30.9)} °C",
                    "presion": c_sel.get('presion_camara', '-49kPa'),
                    "tiempo_exposicion": f"{c_sel.get('t_exp', 120)} Min",
                    "tipo_carga": c_sel.get('observaciones', 'Textil'),
                    "control_carga": c_sel.get('estado_cumplimiento', 'CUMPLE'),
                    "operador": c_sel.get('operador', 'Administrador'),
                    "estado": c_sel.get('resultado', 'Aprobado'),
                    "items": [
                        {"nombre": "Paquete Laparotomía", "cantidad": c_sel.get('q_lap', 0), "lote": c_sel.get('l_lap', '0')},
                        {"nombre": "Unidad Hemodinamia", "cantidad": c_sel.get('q_hemo', 0), "lote": c_sel.get('l_hemo', '0')},
                        {"nombre": "Cirugía Valledupar", "cantidad": c_sel.get('q_cir', 0), "lote": c_sel.get('l_cir', '0')},
                        {"nombre": "Sábanas Estériles", "cantidad": c_sel.get('q_sab', 0), "lote": c_sel.get('l_sab', '0')},
                        {"nombre": "Paquete Central Adulto", "cantidad": c_sel.get('q_adult', 0), "lote": c_sel.get('l_adult', '0')},
                        {"nombre": "Neurointervencionismo", "cantidad": c_sel.get('q_neuro', 0), "lote": c_sel.get('l_neuro', '0')},
                        {"nombre": "Apósitos Estériles", "cantidad": c_sel.get('q_apos', 0), "lote": c_sel.get('l_apos', '0')},
                    ]
                }

                datos_para_pdf["items"] = [
                    item for item in datos_para_pdf["items"] if item["cantidad"] > 0
                ]
                
                docx_buffer = generar_pdf_informe(datos_para_pdf)
                
                st.download_button(
                    label=f"📥 Descargar EL CONTROL DEL PROCESO DE ESTERILIZACIÓN - {int(c_sel['n_ciclo']):05d}.docx",
                    data=docx_buffer,
                    file_name=f"Informe_Ciclo_{int(c_sel['n_ciclo']):05d}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    type="primary"
                )

                st.markdown("---")
                st.subheader("🖨️ Orden de Entrega")
                
                if c_sel.get('carga_liberada') == 'Sí':
                    st.success("Carga liberada con éxito. Ya puede descargar la orden de entrega en Word.")
                    
                    def parse_q(val):
                        try:
                            return int(val) if val not in [None, ""] else 0
                        except:
                            return 0

                    items_cargados = [
                        {"nombre": "Paquete Laparotomía", "lote": str(c_sel.get('l_lap', '')), "cantidad": parse_q(c_sel.get('q_lap')), "obs": "Conforme"},
                        {"nombre": "Unidad Hemodinamia", "lote": str(c_sel.get('l_hemo', '')), "cantidad": parse_q(c_sel.get('q_hemo')), "obs": "Conforme"},
                        {"nombre": "Cirugía Valledupar", "lote": str(c_sel.get('l_cir', '')), "cantidad": parse_q(c_sel.get('q_cir')), "obs": "Conforme"},
                        {"nombre": "Sábanas Estériles", "lote": str(c_sel.get('l_sab', '')), "cantidad": parse_q(c_sel.get('q_sab')), "obs": "Conforme"},
                        {"nombre": "Paquete Central Adulto", "lote": str(c_sel.get('l_adult', '')), "cantidad": parse_q(c_sel.get('q_adult')), "obs": "Conforme"},
                        {"nombre": "Neurointervencionismo", "lote": str(c_sel.get('l_neuro', '')), "cantidad": parse_q(c_sel.get('q_neuro')), "obs": "Conforme"},
                        {"nombre": "Apósitos Estériles", "lote": str(c_sel.get('l_apos', '')), "cantidad": parse_q(c_sel.get('q_apos')), "obs": "Conforme"},
                    ]

                    items_filtrados = [item for item in items_cargados if item["cantidad"] > 0]

                    datos_orden = {
                        "fecha": c_sel.get('fecha', ''),
                        "n_orden": "0000",
                        "destino": "AM MEDICAL",
                        "ciclo_esteril": f"{int(c_sel['n_ciclo']):05d}",
                        "resp_entrega": "Davinson Peña",
                        "resp_recepcion": "Jorge Espejero",
                        "items": items_filtrados
                    }
                    
                    docx_orden = generar_orden_entrega(datos_orden)
                    
                    st.download_button(
                        label=f"📥 Descargar Orden de Entrega - Ciclo {n_ciclo_sel:05d}.docx",
                        data=docx_orden,
                        file_name=f"Orden_Entrega_{n_ciclo_sel:05d}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                else:
                    st.warning("⚠️ La orden de entrega se encuentra bloqueada y solo estará disponible una vez que el ciclo haya sido aprobado y liberado.")
        else:   
            st.info("Registra al menos un ciclo para poder visualizar y descargar los formatos oficiales.")

    # --- CONFIGURACIÓN ADMIN ---
    elif opcion == "Configuración Admin" and (st.session_state.rol_actual in ["admin", "dueno"]):
        st.subheader("⚙️ Panel de Configuración Administrativa")
        with st.form("form_cambio_pass_admin"):
            user_a_cambiar = st.selectbox("Seleccionar Usuario", [u for u in st.session_state.usuarios_db.keys()])
            nueva_pass_val = st.text_input("Nueva Contraseña", type="password")
            if st.form_submit_button("Actualizar Contraseña"):
                if nueva_pass_val.strip():
                    st.session_state.usuarios_db[user_a_cambiar]["pass"] = nueva_pass_val.strip()
                    guardar_config_maestra()
                    st.success("¡Contraseña actualizada con éxito!")

    # --- CONFIGURACIÓN MAESTRO (DUEÑO) ---
    elif opcion == "🔑 Configuración Maestro (Dueño)" and st.session_state.rol_actual == "dueno":
        st.subheader("🔐 Panel de Control Maestro (Dueño del Sistema)")
        st.info("Bienvenido al núcleo de control absoluto. Todas las operaciones críticas y de gestión de permisos requieren confirmación con tu contraseña de Dueño.")
        
        tab_m1, tab_m2, tab_m3, tab_m4, tab_m5 = st.tabs([
            "🗑️ Borrar Historial", 
            "🛑 Interruptor de Emergencia", 
            "🔑 Gestión de Credenciales y Usuarios", 
            "🛡️ Control de Módulos por Rol",
            "📂 Importación Excel"
        ])

        # TAB 1: Borrar Historial con confirmación de contraseña
        with tab_m1:
            st.markdown("### Zona de Peligro: Borrar Base de Datos")
            st.warning("Borrar el historial eliminará permanentemente todos los ciclos y registros de indicadores biológicos guardados.")
            
            pass_conf_1 = st.text_input("Digita tu contraseña de Dueño para confirmar:", type="password", key="pass_borrar_historial")
            if st.button("🗑️ Borrar Todo el Historial de Ciclos e Indicadores", type="primary"):
                if pass_conf_1 == st.session_state.owner_pass:
                    st.session_state.ciclos_db = []
                    st.session_state.ib_db = []
                    guardar_datos_disco()
                    st.success("¡Se ha vaciado todo el registro de ciclos e indicadores biológicos exitosamente!")
                    st.rerun()
                else:
                    st.error("Contraseña de Dueño incorrecta. Operación cancelada por seguridad.")

        # TAB 2: Interruptor de Emergencia (Kill Switch)
        with tab_m2:
            st.markdown("### Bloqueo Global de la Aplicación")
            st.write(f"Estado actual de bloqueo general: **{'BLOQUEADA 🛑' if st.session_state.app_bloqueada_general else 'ACTIVA 🟢'}**")
            
            pass_conf_2 = st.text_input("Digita tu contraseña de Dueño para alternar el estado:", type="password", key="pass_kill_switch")
            
            col_ks1, col_ks2 = st.columns(2)
            with col_ks1:
                if st.button("🛑 Activar Bloqueo Global (Pausar App)", type="primary"):
                    if pass_conf_2 == st.session_state.owner_pass:
                        st.session_state.app_bloqueada_general = True
                        guardar_config_maestra()
                        st.warning("¡Aplicación bloqueada para todos los demás usuarios!")
                        st.rerun()
                    else:
                        st.error("Contraseña de Dueño incorrecta.")
            with col_ks2:
                if st.button("🟢 Desactivar Bloqueo (Restaurar Acceso)", type="secondary"):
                    if pass_conf_2 == st.session_state.owner_pass:
                        st.session_state.app_bloqueada_general = False
                        guardar_config_maestra()
                        st.success("¡Aplicación restaurada para todos los usuarios!")
                        st.rerun()
                    else:
                        st.error("Contraseña de Dueño incorrecta.")

        # TAB 3: Gestión y Restauración de Credenciales y Usuarios
        with tab_m3:
            st.markdown("### Restauración de Credenciales y Estado de Usuarios")
            u_sel_master = st.selectbox("Seleccionar rol o usuario a gestionar:", list(st.session_state.usuarios_db.keys()), key="select_user_master_gest")
            
            dat_u = st.session_state.usuarios_db[u_sel_master]
            st.write(f"**Nombre asociado:** {dat_u['nombre']}")
            st.write(f"**Estado actual:** {'Activo ✅' if dat_u.get('activo', True) else 'Inhabilitado ❌'}")
            
            nueva_p_master = st.text_input("Nueva contraseña para este usuario:", type="password", key="new_pass_master_user")
            nuevo_estado_activo = st.checkbox("Usuario Activo (Permitir ingreso)", value=dat_u.get('activo', True), key="chk_activo_master_user")
            
            pass_conf_3 = st.text_input("Digita tu contraseña de Dueño para aplicar los cambios:", type="password", key="pass_gest_cred")
            
            if st.button("💾 Guardar Cambios de Usuario", type="primary"):
                if pass_conf_3 == st.session_state.owner_pass:
                    st.session_state.usuarios_db[u_sel_master]["pass"] = nueva_p_master.strip() if nueva_p_master.strip() else dat_u["pass"]
                    st.session_state.usuarios_db[u_sel_master]["activo"] = nuevo_estado_activo
                    guardar_config_maestra()
                    st.success(f"¡Credenciales y estado del usuario `{u_sel_master}` actualizados correctamente!")
                    st.rerun()
                else:
                    st.error("Contraseña de Dueño incorrecta.")

        # TAB 4: Control de Permisos Individuales por Rol
        with tab_m4:
            st.markdown("### Bloqueo o Habilitación de Módulos por Rol")
            st.write("Selecciona qué módulos puede visualizar cada rol dentro del sistema.")
            
            rol_a_configurar = st.selectbox("Seleccionar Rol:", ["admin", "supervisor", "visitante"], key="rol_permiso_select")
            
            permisos_actuales = st.session_state.permisos_roles.get(rol_a_configurar, {})
            
            p_ciclos = st.checkbox("Módulo: Ciclos / Cargas", value=permisos_actuales.get("Ciclos / Cargas", True), key="perm_ciclos")
            p_inc = st.checkbox("Módulo: Control de Incubación", value=permisos_actuales.get("Control de Incubación", True), key="perm_inc")
            p_lib = st.checkbox("Módulo: Liberación", value=permisos_actuales.get("Liberación", True), key="perm_lib")
            p_inf = st.checkbox("Módulo: Informes", value=permisos_actuales.get("Informes", True), key="perm_inf")
            
            pass_conf_4 = st.text_input("Digita tu contraseña de Dueño para guardar permisos:", type="password", key="pass_permisos_rol")
            
            if st.button("💾 Aplicar Restricciones de Módulos", type="primary"):
                if pass_conf_4 == st.session_state.owner_pass:
                    st.session_state.permisos_roles[rol_a_configurar] = {
                        "Ciclos / Cargas": p_ciclos,
                        "Control de Incubación": p_inc,
                        "Liberación": p_lib,
                        "Informes": p_inf
                    }
                    guardar_config_maestra()
                    st.success(f"¡Permisos para el rol `{rol_a_configurar}` actualizados con éxito!")
                    st.rerun()
                else:
                    st.error("Contraseña de Dueño incorrecta.")

        # TAB 5: Importación Masiva de Excel (Mejorada y Robusta)
        with tab_m5:
            st.markdown("### 📂 Importación Masiva y Sincronización de Base de Datos (Excel)")
            st.info("Sube tu archivo Excel de control. El sistema detectará automáticamente las columnas y pestañas disponibles, permitiéndote fusionar o reemplazar los registros de manera segura.")

            excel_file_subido = st.file_uploader("Selecciona el archivo Excel (.xlsx)", type=["xlsx"], key="excel_migracion_robusta")
            
            if excel_file_subido is not None:
                try:
                    xls_obj = pd.ExcelFile(excel_file_subido)
                    hojas_disponibles = xls_obj.sheet_names
                    
                    st.success(f"Archivo cargado con éxito. Pestañas detectadas: `{', '.join(hojas_disponibles)}`")
                    
                    col_h1, col_h2 = st.columns(2)
                    with col_h1:
                        hoja_ciclos_sel = st.selectbox("Pestaña de Ciclos:", hojas_disponibles, index=0)
                    with col_h2:
                        modo_importacion = st.radio("Modo de Importación:", ["Sobrescribir toda la base de datos", "Añadir / Fusionar con registros actuales"], index=0)

                    df_prev = pd.read_excel(xls_obj, sheet_name=hoja_ciclos_sel)
                    st.markdown(f"**Vista previa de columnas encontradas ({len(df_prev)} filas):**")
                    st.dataframe(df_prev.head(3), use_container_width=True)
                    
                    cols_disponibles = [str(c).strip() for c in df_prev.columns]
                    
                    st.markdown("---")
                    st.markdown("#### 🗺️ Mapeo Inteligente de Columnas")
                    st.write("Verifica o selecciona a qué campo del sistema corresponde cada columna de tu Excel:")
                    
                    def buscar_columna_sugerida(lista_opciones, posibles_nombres):
                        for p in posibles_nombres:
                            for col in lista_opciones:
                                if p.lower() in col.lower():
                                    return col
                        return lista_opciones[0] if lista_opciones else None

                    map_c1, map_c2, map_c3 = st.columns(3)
                    with map_c1:
                        col_map_n = st.selectbox("Columna N° Ciclo", cols_disponibles, index=cols_disponibles.index(buscar_columna_sugerida(cols_disponibles, ["ciclo", "n° ciclo", "numero", "id"])) if cols_disponibles else 0)
                        col_map_f = st.selectbox("Columna Fecha", cols_disponibles, index=cols_disponibles.index(buscar_columna_sugerida(cols_disponibles, ["fecha", "date"])) if cols_disponibles else 0)
                    with map_c2:
                        col_map_eq = st.selectbox("Columna Equipo", cols_disponibles, index=cols_disponibles.index(buscar_columna_sugerida(cols_disponibles, ["equipo", "esterilizador"])) if cols_disponibles else 0)
                        col_map_op = st.selectbox("Columna Operador", cols_disponibles, index=cols_disponibles.index(buscar_columna_sugerida(cols_disponibles, ["operador", "responsable"])) if cols_disponibles else 0)
                    with map_c3:
                        col_map_uni = st.selectbox("Columna Unidades Totales", cols_disponibles, index=cols_disponibles.index(buscar_columna_sugerida(cols_disponibles, ["unidades", "paquetes", "cantidad", "tot"])) if cols_disponibles else 0)
                        col_map_obs = st.selectbox("Columna Observaciones", cols_disponibles, index=cols_disponibles.index(buscar_columna_sugerida(cols_disponibles, ["observacion", "tipo", "carga"])) if cols_disponibles else 0)

                except Exception as ex:
                    st.error(f"Error al leer la estructura del archivo Excel: {ex}")
                    df_prev = None

            pass_import = st.text_input("Digita tu contraseña de Dueño para confirmar la importación:", type="password", key="pass_imp_dueno")

            if st.button("🚀 Ejecutar Migración / Importación de Base de Datos", type="primary", key="btn_migrar"):
                if pass_import == st.session_state.owner_pass:
                    if excel_file_subido is not None and 'df_prev' in locals() and df_prev is not None:
                        try:
                            nuevos_ciclos = []
                            nuevos_ibs = []
                            
                            # Si es fusión, conservamos los registros existentes
                            if modo_importacion == "Añadir / Fusionar con registros actuales":
                                nuevos_ciclos = list(st.session_state.ciclos_db)
                                nuevos_ibs = list(st.session_state.ib_db)
                                max_n_existente = max([int(x.get('n_ciclo', 0)) for x in nuevos_ciclos], default=0)
                            else:
                                max_n_existente = 0

                            for idx_r, row in df_prev.iterrows():
                                try:
                                    n_cic_val = int(row[col_map_n]) if col_map_n in row and pd.notna(row[col_map_n]) else (max_n_existente + idx_r + 1)
                                except:
                                    n_cic_val = max_n_existente + idx_r + 1

                                fecha_val = str(row[col_map_f])[:10] if col_map_f in row and pd.notna(row[col_map_f]) else str(datetime.now().date())
                                equipo_val = str(row[col_map_eq]) if col_map_eq in row and pd.notna(row[col_map_eq]) else "HDX-6 EO"
                                operador_val = str(row[col_map_op]) if col_map_op in row and pd.notna(row[col_map_op]) else st.session_state.usuario_actual
                                
                                try:
                                    tot_u_val = int(float(row[col_map_uni])) if col_map_uni in row and pd.notna(row[col_map_uni]) else 0
                                except:
                                    tot_u_val = 0

                                obs_val = str(row[col_map_obs]) if col_map_obs in row and pd.notna(row[col_map_obs]) else "Textil / Importado"

                                registro_importado = {
                                    "n_ciclo": n_cic_val,
                                    "fecha": fecha_val,
                                    "hora_inicio": "08:00 a.m.",
                                    "hora_fin": "04:00 p.m.",
                                    "equipo": equipo_val,
                                    "operador": operador_val,
                                    "temp": 30.9,
                                    "humedad": 52.5,
                                    "conc_eto": "99.0%",
                                    "presion_camara": "-49kPa",
                                    "t_exp": 120,
                                    "aireacion": "2N2A",
                                    "resultado": "Aprobado",
                                    "q_lap": tot_u_val if "lap" in obs_val.lower() else 0, "p_lap": 0.0, "l_lap": "LT080327",
                                    "q_hemo": 0, "p_hemo": 0.0, "l_hemo": "0",
                                    "q_cir": 0, "p_cir": 0.0, "l_cir": "0",
                                    "q_sab": 0, "p_sab": 0.0, "l_sab": "0",
                                    "q_adult": 0, "p_adult": 0.0, "l_adult": "0",
                                    "q_neuro": 0, "p_neuro": 0.0, "l_neuro": "0",
                                    "q_apos": 0, "p_apos": 0.0, "l_apos": "0",
                                    "tot_unidades": tot_u_val,
                                    "tot_peso": round(tot_u_val * 1.05, 2),
                                    "canastas_grandes": min(tot_u_val, 10),
                                    "canastas_pequenas": 2,
                                    "ocupacion": 75.0,
                                    "estado_cumplimiento": "CUMPLE",
                                    "fecha_liberacion": "Completada",
                                    "carga_liberada": "Sí",
                                    "res_ib": "Negativo",
                                    "observaciones": obs_val
                                }
                                
                                # Evitar duplicados exactos de n_ciclo si es fusión
                                if modo_importacion == "Añadir / Fusionar con registros actuales":
                                    nuevos_ciclos = [c for c in nuevos_ciclos if int(c['n_ciclo']) != int(n_cic_val)]
                                
                                nuevos_ciclos.append(registro_importado)

                                # Crear o actualizar indicador biológico asociado
                                ib_existente_idx = next((i for i, ib in enumerate(nuevos_ibs) if int(ib.get('ciclo', 0)) == int(n_cic_val)), -1)
                                ib_nuevo_item = {
                                    "ciclo": int(n_cic_val),
                                    "tipo": "BT10 EO ATCC 9372",
                                    "lote": "A50300",
                                    "resultado": "Negativo",
                                    "fecha_incubacion": fecha_val,
                                    "responsable": operador_val,
                                    "observaciones": "Importado desde Excel"
                                }
                                if ib_existente_idx != -1:
                                    nuevos_ibs[ib_existente_idx] = ib_nuevo_item
                                else:
                                    nuevos_ibs.append(ib_nuevo_item)

                            st.session_state.ciclos_db = nuevos_ciclos
                            st.session_state.ib_db = nuevos_ibs
                            guardar_datos_disco()

                            st.success(f"¡Importación completada con éxito! Se procesaron {len(df_prev)} registros correctamente.")
                            st.balloons()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error durante el procesamiento y guardado de los datos: {e}")
                    else:
                        st.warning("Por favor, sube un archivo Excel válido antes de ejecutar la importación.")
                else:
                    st.error("Contraseña de Dueño incorrecta.")