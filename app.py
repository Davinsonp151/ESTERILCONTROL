import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime, timedelta
from io import BytesIO

# --- IMPORTACIÓN DEL NUEVO GENERADOR EXTERNO ---
from reports.pdf_generator import generar_pdf_informe

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="EsterilControl - AM Medical",
    page_icon="🔵",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
        html, body, [class*="css"], .stText, .stMarkdown, h1, h2, h3, h4, h5, h6 {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }
        h1 { font-size: 1.5rem !important; }
        h2 { font-size: 1.3rem !important; }
        h3 { font-size: 1.1rem !important; }
        h4 { font-size: 0.95rem !important; }
        
        div[data-testid="stMetricValue"] {
            font-size: 1.25rem !important;
        }
        div[data-testid="stMetricLabel"] {
            font-size: 0.75rem !important;
        }
        
        .stButton button {
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.85rem !important;
        }
    </style>
""", unsafe_allow_html=True)

LOGO_PATH = "assets/logo_esterilcontrol.jpg"
DB_CICLOS_FILE = "ciclos_db.json"
DB_IB_FILE = "ib_db.json"

# --- GESTIÓN DE USUARIOS EN SESSION STATE ---
if "usuarios_db" not in st.session_state:
    st.session_state.usuarios_db = {
        "admin": {"nombre": "Administrador", "pass": "admin123", "rol": "admin"},
        "supervisor": {"nombre": "Davinson Peña (Supervisor)", "pass": "super123", "rol": "supervisor"},
        "visitante": {"nombre": "Visitante / Auditor", "pass": "visit123", "rol": "visitante"}
    }

OWNER_USER = "Davinson"
if "owner_pass" not in st.session_state:
    st.session_state.owner_pass = "Davinson151"

# --- FUNCIONES DE PERSISTENCIA ---
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
            elif user_clean_lower in st.session_state.usuarios_db and st.session_state.usuarios_db[user_clean_lower]["pass"] == pass_input:
                st.session_state.autenticado = True
                st.session_state.usuario_actual = st.session_state.usuarios_db[user_clean_lower]["nombre"]
                st.session_state.rol_actual = st.session_state.usuarios_db[user_clean_lower]["rol"]
                st.rerun()
            else:
                st.error("Credenciales de acceso incorrectas.")

# ==========================================
# 2. APLICACIÓN PRINCIPAL
# ==========================================
else:
    with st.sidebar:
        mostrar_logo(width=140)
        st.caption("AM Medical - Control EtO")
        st.markdown(f"**Usuario:** {st.session_state.usuario_actual}")
        st.markdown(f"**Rol:** `{st.session_state.rol_actual.upper()}`")
        
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.autenticado = False
            st.rerun()

        st.markdown("---")
        
        lista_nav = ["Panel de control", "Ciclos / Cargas", "Control de Incubación", "Liberación", "Informes"]
        if st.session_state.rol_actual in ["admin", "dueno"]:
            lista_nav.append("Configuración Admin")
        if st.session_state.rol_actual == "dueno":
            lista_nav.append("🔑 Configuración Maestro (Dueño)")

        opcion = st.radio("Navegación", lista_nav)

    st.title("EsterilControl")

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
        c5.metric("ESTADO SISTEMA", "Activo", "Disco Local")
        
        st.markdown("---")
        st.subheader(f"Últimos Ciclos Procesados")
        
        if not df_c.empty:
            df_c = df_c.sort_values(by=["fecha", "n_ciclo"], ascending=[False, False])
            cols_ver = ["n_ciclo", "fecha", "hora_inicio", "hora_fin", "equipo", "operador", "tot_unidades", "tot_peso", "ocupacion", "carga_liberada"]
            st.dataframe(df_c[[col for col in cols_ver if col in df_c.columns]], use_container_width=True)
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
                with fc3:
                    hora_i = st.text_input("HORA INICIO (Ej: 11:03 AM):", "11:03 AM")
                with fc4:
                    hora_f = st.text_input("HORA FIN (Ej: 5:26 PM):", "")

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
                    hora_fin_val = hora_f.strip()
                    if hora_fin_val:
                        try:
                            fecha_lib = (datetime.combine(fecha_c, datetime.now().time()) + timedelta(hours=49)).strftime("%Y-%m-%d %H:%M")
                        except:
                            fecha_lib = "Pendiente"
                    else:
                        fecha_lib = "Pendiente"

                    nuevo_registro = {
                        "n_ciclo": int(n_ciclo),
                        "fecha": str(fecha_c),
                        "hora_inicio": hora_i.strip(),
                        "hora_fin": hora_fin_val,
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
                    guardar_datos_disco()
                    st.success(f"¡Ciclo N° {f'{n_ciclo:05d}'} registrado y guardado con éxito!")
                    st.rerun()
        else:
            st.info("👁️ **Modo Visitante / Auditor:** Solo lectura.")

        st.markdown("---")
        st.subheader("Historial y Gestión de Ciclos Registrados")
        
        if st.session_state.ciclos_db:
            ciclos_ordenados = sorted(st.session_state.ciclos_db, key=lambda x: (x['fecha'], x['n_ciclo']), reverse=True)
            for idx, c in enumerate(ciclos_ordenados):
                cod_c_fmt = f"{int(c['n_ciclo']):05d}"
                
                with st.expander(f"🔹 CICLO N° {cod_c_fmt} | Fecha: {c['fecha']} | Equipo: {c['equipo']} | Unidades: {c['tot_unidades']} | Peso: {c['tot_peso']} kg"):
                    
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

                    if not c['hora_fin'] and st.session_state.rol_actual in ["admin", "supervisor", "dueno"]:
                        st.markdown("---")
                        col_fin1, col_fin2 = st.columns([2, 1])
                        with col_fin1:
                            input_hf_manual = st.text_input(f"Asignar Hora Fin para Ciclo {cod_c_fmt}", value="5:26 PM", key=f"txt_hf_{c['n_ciclo']}")
                        with col_fin2:
                            st.write("")
                            if st.button(f"⏱️ Finalizar Ciclo", key=f"btn_fin_{c['n_ciclo']}", type="primary"):
                                c['hora_fin'] = input_hf_manual.strip()
                                c['fecha_liberacion'] = (datetime.now() + timedelta(hours=49)).strftime("%Y-%m-%d %H:%M")
                                guardar_datos_disco()
                                st.success("¡Ciclo finalizado!")
                                st.rerun()

                    if st.session_state.rol_actual in ["admin", "dueno"]:
                        st.markdown("---")
                        if st.button(f"🗑️ Eliminar Ciclo N° {cod_c_fmt}", key=f"del_ciclo_{c['n_ciclo']}"):
                            st.session_state.ciclos_db = [x for x in st.session_state.ciclos_db if x['n_ciclo'] != c['n_ciclo']]
                            guardar_datos_disco()
                            st.rerun()
        else:
            st.info("No hay ciclos guardados actualmente.")

    # --- CONTROL DE INCUBACIÓN ---
    elif opcion == "Control de Incubación":
        st.subheader("Control de Indicadores Biológicos")
        
        if st.session_state.rol_actual in ["admin", "supervisor", "dueno"]:
            with st.expander("➕ REGISTRAR RESULTADO DE INDICADOR BIOLÓGICO", expanded=False):
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

                if st.button("💾 Guardar Indicador Biológico", type="primary"):
                    st.session_state.ib_db.append({
                        "ciclo": ciclo_asoc,
                        "tipo": tipo_ib,
                        "lote": lote_ib,
                        "resultado": res_lectura,
                        "fecha_incubacion": str(fecha_incubacion),
                        "responsable": resp_ib,
                        "observaciones": obs_ib,
                        "fecha_registro": str(datetime.now().date())
                    })
                    for c in st.session_state.ciclos_db:
                        if c['n_ciclo'] == ciclo_asoc:
                            c['res_ib'] = res_lectura
                    
                    guardar_datos_disco()
                    st.success("¡Indicador biológico guardado correctamente!")
                    st.rerun()

        st.markdown("---")
        st.subheader("Historial de Indicadores Biológicos")
        if st.session_state.ib_db:
            st.dataframe(pd.DataFrame(st.session_state.ib_db), use_container_width=True)
        else:
            st.info("No hay indicadores biológicos registrados.")

    # --- LIBERACIÓN ---
    elif opcion == "Liberación":
        st.subheader("Liberación de Carga")
        if st.session_state.ciclos_db:
            for c in st.session_state.ciclos_db:
                cod_c_fmt = f"{int(c['n_ciclo']):05d}"
                st.markdown(f"""
                <div style="background-color: #f8f9fa; padding: 12px; border-radius: 8px; border-left: 4px solid #0052cc; margin-bottom: 10px; font-size: 0.9rem;">
                    <h4>📦 Ciclo N° {cod_c_fmt} | Fecha: {c['fecha']} (Fin: {c['hora_fin'] if c['hora_fin'] else 'En Proceso'})</h4>
                    <p><b>Estado Carga Liberada:</b> <code>{c.get('carga_liberada', 'No')}</code> | <b>Fecha Prevista Liberación (49h):</b> {c.get('fecha_liberacion', 'Pendiente')}</p>
                    <p><b>Control Biológico:</b> {c.get('res_ib', 'Negativo')} | <b>Unidades:</b> {c['tot_unidades']} | <b>Peso:</b> {c['tot_peso']} kg</p>
                </div>
                """, unsafe_allow_html=True)
                
                if c.get('carga_liberada', 'No') == 'No' and c['hora_fin']:
                    if st.session_state.rol_actual in ["admin", "supervisor", "dueno"]:
                        if st.button(f"✅ Aprobar y Liberar Carga Ciclo {cod_c_fmt}", key=f"lib_btn_{c['n_ciclo']}", type="primary"):
                            c['carga_liberada'] = "Sí"
                            guardar_datos_disco()
                            st.success(f"¡Carga del Ciclo N° {cod_c_fmt} liberada!")
                            st.rerun()
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
                # ADAPTADOR DE DATOS PARA EL PDF OFICIAL (Con la llave "lote" corregida)
                datos_para_pdf = {
                    "metodo": "Óxido de Etileno",
                    "equipo": c_sel.get('equipo', 'HDX-6 EO'),
                    "esterilizador": c_sel.get('equipo', 'HDX-6 EO'),
                    "n_cic": f"{int(c_sel['n_ciclo']):05d}",
                    "fecha_inicio": c_sel.get('fecha', ''),
                    "hora_inicio": c_sel.get('hora_inicio', ''),
                    "hora_fin": c_sel.get('hora_fin', 'En Proceso'),
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

                # Filtramos solo los ítems que tengan cantidad mayor a 0
                datos_para_pdf["items"] = [
                    item for item in datos_para_pdf["items"] if item["cantidad"] > 0
                ]
                
                # LLAMADA AL NUEVO GENERADOR EXTERNO CON DATOS ADAPTADOS
                pdf_buffer = generar_pdf_informe(datos_para_pdf)
                
                st.download_button(
                    label=f"📥 Descargar EL CONTROL DEL PROCESO DE ESTERILIZACIÓN - {int(c_sel['n_ciclo']):05d}.docx",
                    data=pdf_buffer,
                    file_name=f"Informe_Ciclo_{int(c_sel['n_ciclo']):05d}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    type="primary"
                )
        else:
            st.info("Registra al menos un ciclo para poder visualizar y descargar el formato oficial.")

    # --- CONFIGURACIÓN ADMIN ---
    elif opcion == "Configuración Admin" and st.session_state.rol_actual in ["admin", "dueno"]:
        st.subheader("⚙️ Panel de Configuración Administrativa")
        with st.form("form_cambio_pass_admin"):
            user_a_cambiar = st.selectbox("Seleccionar Usuario", list(st.session_state.usuarios_db.keys()))
            nueva_pass_val = st.text_input("Nueva Contraseña", type="password")
            if st.form_submit_button("Actualizar Contraseña"):
                if nueva_pass_val.strip():
                    st.session_state.usuarios_db[user_a_cambiar]["pass"] = nueva_pass_val.strip()
                    st.success("¡Contraseña actualizada con éxito!")

    # --- CONFIGURACIÓN MAESTRO (DUEÑO) ---
    elif opcion == "🔑 Configuración Maestro (Dueño)" and st.session_state.rol_actual == "dueno":
        st.subheader("🔐 Panel Maestro (Modo Dueño Oculto)")
        if st.button("🗑️ Borrar Todo el Historial de Ciclos", type="primary"):
            st.session_state.ciclos_db = []
            guardar_datos_disco()
            st.warning("Se ha vaciado todo el registro de ciclos.")
            st.rerun()