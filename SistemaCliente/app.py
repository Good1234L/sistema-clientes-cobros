import streamlit as st
import pandas as pd
import json
import os
import hashlib

# Configuración de la página
st.set_page_config(page_title="Sistema de Gestión de Clientes", page_icon="💡", layout="wide")

# ==========================================
# SEGURIDAD Y ROLES
# ==========================================
CONFIG_FILE = "security_config.json"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def cargar_usuarios():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    default_usuarios = {
        "admin": {"password": hash_password("admin123"), "rol": "Administrador"},
        "operador": {"password": hash_password("ope123"), "rol": "Operador"},
        "soporte": {"password": hash_password("sop123"), "rol": "Soporte"}
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(default_usuarios, f, ensure_ascii=False, indent=4)
    return default_usuarios

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario_actual = None
    st.session_state.rol_actual = None

usuarios_db = cargar_usuarios()

if not st.session_state.autenticado:
    st.title("🔐 Acceso al Sistema de Cobros")
    with st.form("login_form"):
        user_input = st.text_input("Usuario:")
        pass_input = st.text_input("Contraseña:", type="password")
        btn_login = st.form_submit_button("🔑 Iniciar Sesión")
        
        if btn_login:
            user_input = user_input.strip().lower()
            if user_input in usuarios_db and usuarios_db[user_input]["password"] == hash_password(pass_input):
                st.session_state.autenticado = True
                st.session_state.usuario_actual = user_input
                st.session_state.rol_actual = usuarios_db[user_input]["rol"]
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
    st.stop()

# ==========================================
# BACKEND: Almacenamiento local en JSON
# ==========================================
DB_FILE = "clientes_db.json"

def cargar_datos():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def guardar_datos(clientes):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(clientes, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Error al guardar en el backend: {e}")

if "clientes" not in st.session_state:
    st.session_state.clientes = cargar_datos()

# ==========================================
# FRONTEND: Estilos y Diseño Web
# ==========================================
st.sidebar.title("🔒 Panel de Control")
st.sidebar.info(f"**Usuario:** {st.session_state.usuario_actual}\n\n**Rol:** {st.session_state.rol_actual}")
if st.sidebar.button("Cerrar Sesión"):
    st.session_state.autenticado = False
    st.rerun()

st.markdown("""
    <style>
    .main { background-color: #f4f6f9; }
    .stButton>button {
        background-color: #2563eb;
        color: white;
        border-radius: 8px;
        font-weight: bold;
        border: none;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover { background-color: #1d4ed8; color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("💡 Sistema de Registro, Cobros y Modificación")
st.markdown("---")

col_form, col_info = st.columns([1.2, 1.8], gap="large")

with col_form:
    st.subheader("📝 Registrar Nuevo Cliente")
    if st.session_state.rol_actual in ["Administrador", "Operador"]:
        with st.form("form_cliente", clear_on_submit=True):
            nombre = st.text_input("Nombre del cliente (Solo letras):")
            costo = st.number_input("Costo actual ($)", min_value=0.0, format="%.2f")
            deuda = st.number_input("Deuda pendiente ($)", min_value=0.0, format="%.2f")
            alumbrado_fijo = 0.18
            st.info(f"💡 Alumbrado público fijo: ${alumbrado_fijo}")
            en_corte = st.checkbox("⚠️ Marcar cliente en corte (Suspensión)")
            enviar = st.form_submit_button("💾 Guardar y Calcular Total")
            
            if enviar:
                nombre_limpio = nombre.strip()
                if not nombre_limpio:
                    st.error("⚠️ El nombre no puede estar vacío.")
                elif not all(c.isalpha() or c.isspace() for c in nombre_limpio):
                    st.error("⚠️ Error: El nombre solo debe contener letras.")
                else:
                    estado_cliente = "🔴 En Corte" if en_corte else "🟢 Activo"
                    total = costo + deuda + alumbrado_fijo
                    nuevo_id = len(st.session_state.clientes) + 1
                    cliente = {
                        "ID": nuevo_id,
                        "Nombre": nombre_limpio,
                        "Costo": costo,
                        "Deuda": deuda,
                        "Alumbrado Fijo": alumbrado_fijo,
                        "Total": total,
                        "Estado": estado_cliente
                    }
                    st.session_state.clientes.append(cliente)
                    guardar_datos(st.session_state.clientes)
                    st.success(f"¡Cliente guardado exitosamente con el ID #{nuevo_id}!")
                    st.rerun()
    else:
        st.warning("⚠️ Tu perfil de Soporte no tiene permisos para registrar clientes.")

with col_info:
    st.subheader("📊 Panel de Métricas")
    if st.session_state.clientes:
        total_clientes = len(st.session_state.clientes)
        df_temp = pd.DataFrame(st.session_state.clientes)
        recaudacion_total = df_temp["Total"].sum()
        cortados = len(df_temp[df_temp["Estado"] == "🔴 En Corte"])
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Clientes", total_clientes)
        m2.metric("En Corte", cortados)
        m3.metric("Recaudación Total", f"${recaudacion_total:,.2f}")
    else:
        st.info("ℹ️ Ingresa tu primer cliente para ver las estadísticas.")

# Tabla general, búsqueda y exportación
if st.session_state.clientes:
    st.markdown("---")
    st.subheader("📋 Lista General de Clientes")
    df_clientes = pd.DataFrame(st.session_state.clientes)
    st.dataframe(df_clientes, use_container_width=True)
    
    col_descarga, col_busqueda = st.columns([1, 1], gap="medium")
    with col_descarga:
        st.markdown("### 📥 Exportar Datos")
        csv_data = df_clientes.to_csv(index=False).encode('utf-8')
        st.download_button(label="Descargar reporte en formato Excel (CSV)", data=csv_data, file_name="reporte_clientes_cortes.csv", mime="text/csv")
        
    with col_busqueda:
        st.markdown("### 🔍 Buscar Cliente")
        busqueda = st.text_input("Filtrar por Nombre o ID asignado:").strip()
        if busqueda:
            encontrados = []
            for c in st.session_state.clientes:
                if busqueda.isdigit() and c['ID'] == int(busqueda):
                    encontrados.append(c)
                elif busqueda.lower() in c['Nombre'].lower():
                    encontrados.append(c)
            if encontrados:
                st.success(f"Coincidencias encontradas: {len(encontrados)}")
                st.dataframe(pd.DataFrame(encontrados), use_container_width=True)
            else:
                st.warning("No se encontró ningún registro.")

# ==========================================
# SECCIÓN: MODIFICAR (Solo Admin/Operador)
# ==========================================
if st.session_state.clientes:
    st.markdown("---")
    st.subheader("✏️ Modificar o Corregir Datos de un Cliente")
    if st.session_state.rol_actual in ["Administrador", "Operador"]:
        ids_disponibles = [c["ID"] for c in st.session_state.clientes]
        id_a_modificar = st.selectbox("Selecciona el número de ID del cliente a corregir:", ids_disponibles)
        cliente_actual = next((c for c in st.session_state.clientes if c["ID"] == id_a_modificar), None)
        
        if cliente_actual:
            with st.form(f"form_editar_{id_a_modificar}"):
                nuevo_nombre = st.text_input("Corregir Nombre:", value=cliente_actual["Nombre"])
                nuevo_costo = st.number_input("Corregir Costo actual ($):", min_value=0.0, value=float(cliente_actual["Costo"]), format="%.2f")
                nueva_deuda = st.number_input("Corregir Deuda pendiente ($):", min_value=0.0, value=float(cliente_actual["Deuda"]), format="%.2f")
                estado_actual_bool = True if "En Corte" in cliente_actual["Estado"] else False
                nuevo_corte = st.checkbox("⚠️ Marcar cliente en corte (Suspensión)", value=estado_actual_bool)
                btn_actualizar = st.form_submit_button("🔄 Guardar Cambios")
                
                if btn_actualizar:
                    nombre_limpio = nuevo_nombre.strip()
                    if not nombre_limpio:
                        st.error("⚠️ El nombre no puede estar vacío.")
                    elif not all(c.isalpha() or c.isspace() for c in nombre_limpio):
                        st.error("⚠️ Error: El nombre solo debe contener letras.")
                    else:
                        alumbrado_fijo = 0.18
                        nuevo_total = nuevo_costo + nueva_deuda + alumbrado_fijo
                        nuevo_estado = "🔴 En Corte" if nuevo_corte else "🟢 Activo"
                        
                        for c in st.session_state.clientes:
                            if c["ID"] == id_a_modificar:
                                c["Nombre"] = nombre_limpio
                                c["Costo"] = nuevo_costo
                                c["Deuda"] = nueva_deuda
                                c["Total"] = nuevo_total
                                c["Estado"] = nuevo_estado
                                break
                        guardar_datos(st.session_state.clientes)
                        st.success(f"✅ ¡Cliente ID #{id_a_modificar} actualizado correctamente!")
                        st.rerun()
    else:
        st.warning("⚠️ Tu perfil de Soporte no tiene permisos para modificar datos.")
