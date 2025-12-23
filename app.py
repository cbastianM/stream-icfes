import streamlit as st
from streamlit import fragment
import pandas as pd
from datetime import datetime
import time
import hashlib
import json
import os
from pathlib import Path

# Configuración de la página
st.set_page_config(
    page_title="Stream Interactivo - Aula Virtual",
    page_icon="🎓",
    layout="wide"
)

# Directorio para datos compartidos
DATA_DIR = Path("shared_data")
DATA_DIR.mkdir(exist_ok=True)

# Funciones para manejo de datos compartidos
def save_shared_data(key, data):
    """Guardar datos compartidos en archivo JSON"""
    file_path = DATA_DIR / f"{key}.json"
    with open(file_path, 'w') as f:
        json.dump(data, f)

def load_shared_data(key, default=None):
    """Cargar datos compartidos desde archivo JSON"""
    file_path = DATA_DIR / f"{key}.json"
    if file_path.exists():
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except:
            return default
    return default

def clear_all_shared_data():
    """Limpiar todos los archivos de datos compartidos"""
    if DATA_DIR.exists():
        for file in DATA_DIR.glob("*.json"):
            try:
                file.unlink()
            except:
                pass

# CSS personalizado
st.markdown("""
<style>
    .chat-message {
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
        background-color: rgba(240, 242, 246, 0.1);
        border: 1px solid rgba(128, 128, 128, 0.2);
        color: inherit;
    }
    .teacher-message {
        background-color: rgba(33, 150, 243, 0.15);
        border-left: 4px solid #2196f3;
        color: inherit;
    }
    .chat-message strong {
        color: inherit;
    }
    .chat-message small {
        color: rgba(128, 128, 128, 0.8);
    }
    .poll-option {
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
        background-color: rgba(232, 234, 240, 0.1);
    }
    .stButton>button {
        width: 100%;
    }
    .user-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: bold;
    }
    .teacher-badge {
        background-color: #ff9800;
        color: white;
    }
    .student-badge {
        background-color: #4caf50;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar session state
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'polls' not in st.session_state:
    st.session_state.polls = []
if 'current_poll' not in st.session_state:
    st.session_state.current_poll = None
if 'poll_votes' not in st.session_state:
    st.session_state.poll_votes = {}  # {user_id: {poll_id: option_voted}}
if 'vdo_link' not in st.session_state:
    st.session_state.vdo_link = ""
if 'teacher_password' not in st.session_state:
    st.session_state.teacher_password = "maestro123"  # Cambiar por una contraseña segura
if 'connected_students' not in st.session_state:
    st.session_state.connected_students = {}  # {user_id: {'username': str, 'last_activity': datetime}}

# Función para generar ID único de usuario
def generate_user_id(username, user_type):
    # Usar solo el nombre de usuario para que sea consistente entre sesiones
    return hashlib.md5(f"{username}_{user_type}".encode()).hexdigest()[:8]

# Pantalla de login
if st.session_state.user_type is None:
    st.title("🎓 Aula Virtual - Stream Interactivo")
    st.markdown("### Bienvenido")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("---")
        user_type = st.radio("Selecciona tu rol:", ["👨‍🎓 Estudiante", "👨‍🏫 Maestro"])
        
        username = st.text_input("Nombre de usuario:", placeholder="Ingresa tu nombre")
        
        if user_type == "👨‍🏫 Maestro":
            password = st.text_input("Contraseña del maestro:", type="password")
        
        if st.button("🚀 Ingresar", use_container_width=True):
            if username:
                if user_type == "👨‍🏫 Maestro":
                    if password == st.session_state.teacher_password:
                        st.session_state.user_type = "maestro"
                        st.session_state.username = username
                        st.session_state.user_id = generate_user_id(username, "maestro")
                        st.success("¡Bienvenido Maestro!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Contraseña incorrecta")
                else:
                    st.session_state.user_type = "estudiante"
                    st.session_state.username = username
                    st.session_state.user_id = generate_user_id(username, "estudiante")
                    
                    # Registrar estudiante conectado en archivo compartido
                    connected = load_shared_data('connected_students', {})
                    connected[st.session_state.user_id] = {
                        'username': username,
                        'last_activity': datetime.now().isoformat()
                    }
                    save_shared_data('connected_students', connected)
                    
                    st.success("¡Bienvenido Estudiante!")
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("Por favor ingresa tu nombre")
        
        st.markdown("---")
        st.info("💡 Los estudiantes pueden ver el stream y participar en encuestas.\n\n👨‍🏫 Los maestros pueden controlar el stream y crear encuestas.")

# Aplicación principal
else:
    # Actualizar actividad del estudiante al cargar la página
    if st.session_state.user_type == "estudiante":
        # Cargar estudiantes conectados
        connected = load_shared_data('connected_students', {})
        
        if st.session_state.user_id not in connected:
            # Re-registrar al estudiante si no está en la lista
            connected[st.session_state.user_id] = {
                'username': st.session_state.username,
                'last_activity': datetime.now().isoformat()
            }
        else:
            # Actualizar actividad (heartbeat)
            connected[st.session_state.user_id]['last_activity'] = datetime.now().isoformat()
        
        # Guardar cambios
        save_shared_data('connected_students', connected)
    
    # Heartbeat automático para estudiantes - actualizar cada 10 segundos
    if st.session_state.user_type == "estudiante":
        @fragment(run_every="10s")
        def student_heartbeat():
            connected = load_shared_data('connected_students', {})
            if st.session_state.user_id in connected:
                connected[st.session_state.user_id]['last_activity'] = datetime.now().isoformat()
                save_shared_data('connected_students', connected)
        
        student_heartbeat()
    
    # Header con información del usuario
    col_header1, col_header2, col_header3 = st.columns([2, 2, 1])
    
    with col_header1:
        st.title("🎓 Aula Virtual")
    
    with col_header2:
        badge_class = "teacher-badge" if st.session_state.user_type == "maestro" else "student-badge"
        role_emoji = "👨‍🏫" if st.session_state.user_type == "maestro" else "👨‍🎓"
        st.markdown(f"""
        <div style='text-align: right; padding-top: 20px;'>
            <span class='user-badge {badge_class}'>{role_emoji} {st.session_state.user_type.upper()}</span>
            <br><strong>{st.session_state.username}</strong>
        </div>
        """, unsafe_allow_html=True)
    
    with col_header3:
        if st.button("🚪 Salir"):
            # Si es maestro, limpiar toda la caché antes de salir
            if st.session_state.user_type == "maestro":
                clear_all_shared_data()
                st.success("🗑️ Sesión cerrada y datos limpiados")
                time.sleep(1)
            
            st.session_state.user_type = None
            st.session_state.username = None
            st.session_state.user_id = None
            st.rerun()
        
        # Botón de actualizar para estudiantes
        if st.session_state.user_type == "estudiante":
            if st.button("🔄 Actualizar"):
                st.rerun()
    
    st.markdown("---")
    
    # Panel lateral - Solo para maestros
    if st.session_state.user_type == "maestro":
        with st.sidebar:
            st.header("⚙️ Panel de Control del Maestro")
            
            # Link de VDO.Ninja
            st.subheader("📹 Configuración del Stream")
            
            # Cargar link guardado
            saved_link = load_shared_data('vdo_link', '')
            
            vdo_link = st.text_input(
                "Link de VDO.Ninja",
                value=saved_link,
                placeholder="https://vdo.ninja/...",
                help="Pega aquí tu link de VDO.Ninja"
            )
            
            if st.button("💾 Guardar Link"):
                save_shared_data('vdo_link', vdo_link)
                st.session_state.vdo_link = vdo_link
                st.success("Link guardado y compartido con todos!")
            
            st.divider()
            
            # Lanzar pregunta
            st.subheader("📊 Lanzar Pregunta")
            
            # Mostrar si hay una encuesta activa
            current_poll_status = load_shared_data('current_poll', None)
            if current_poll_status and current_poll_status.get('active', False):
                st.warning(f"⚠️ Ya hay una pregunta activa desde las {current_poll_status['timestamp']}")
            
            if st.button("🚀 Lanzar Pregunta ABCD", use_container_width=True):
                new_poll = {
                    'id': int(datetime.now().timestamp()),
                    'question': 'Pregunta',
                    'options': ['A', 'B', 'C', 'D'],
                    'votes': {'A': 0, 'B': 0, 'C': 0, 'D': 0},
                    'timestamp': datetime.now().strftime("%H:%M:%S"),
                    'active': True,
                    'voters': []
                }
                
                # Guardar encuesta en archivo compartido
                save_shared_data('current_poll', new_poll)
                save_shared_data('poll_votes', {})
                
                st.session_state.current_poll = new_poll
                st.success("¡Pregunta lanzada y visible para todos los estudiantes!")
                time.sleep(1)
                st.rerun()
            
            # Verificar si hay encuesta activa desde archivo compartido
            shared_poll = load_shared_data('current_poll', None)
            if shared_poll and shared_poll.get('active', False):
                if st.button("❌ Cerrar Encuesta Actual"):
                    shared_poll['active'] = False
                    save_shared_data('current_poll', shared_poll)
                    st.session_state.current_poll = None
                    st.success("Encuesta cerrada")
                    st.rerun()
            
            st.divider()
            
            # Estudiantes conectados (con auto-refresh)
            @fragment(run_every="5s")
            def mostrar_estudiantes_conectados():
                st.subheader("👥 Estudiantes Conectados")
                
                # Cargar estudiantes conectados
                connected_students = load_shared_data('connected_students', {})
                
                # Limpiar estudiantes inactivos (más de 30 segundos sin actividad)
                # Cambiado de 5 minutos a 30 segundos para ser más preciso
                current_time = datetime.now()
                inactive_students = []
                active_students = {}
                
                for user_id, data in connected_students.items():
                    try:
                        last_activity = datetime.fromisoformat(data['last_activity'])
                        time_diff = (current_time - last_activity).total_seconds()
                        
                        # Si tiene más de 30 segundos de inactividad, marcar como inactivo
                        if time_diff > 30:
                            inactive_students.append(user_id)
                        else:
                            active_students[user_id] = data
                    except:
                        inactive_students.append(user_id)
                
                # Guardar solo estudiantes activos
                if inactive_students:
                    save_shared_data('connected_students', active_students)
                    connected_students = active_students
                
                # Mostrar lista de estudiantes
                num_students = len(connected_students)
                st.metric("Total de estudiantes", num_students)
                
                if num_students > 0:
                    st.markdown("**Lista de estudiantes:**")
                    for user_id, data in connected_students.items():
                        # Mostrar tiempo desde última actividad
                        try:
                            last_activity = datetime.fromisoformat(data['last_activity'])
                            seconds_ago = int((current_time - last_activity).total_seconds())
                            st.text(f"👨‍🎓 {data['username']} (hace {seconds_ago}s)")
                        except:
                            st.text(f"👨‍🎓 {data['username']}")
                else:
                    st.info("No hay estudiantes conectados")
                
                # Botón para limpiar manualmente estudiantes inactivos
                if st.button("🔄 Actualizar Lista", use_container_width=True):
                    st.rerun()
            
            mostrar_estudiantes_conectados()
            
            st.divider()
            
            # Estadísticas de encuesta actual
            st.subheader("📈 Estadísticas de Encuesta")
            shared_poll = load_shared_data('current_poll', None)
            if shared_poll and shared_poll.get('active', False):
                total_votes = len(shared_poll.get('voters', []))
                st.metric("Estudiantes que han votado", total_votes)
                if num_students > 0:
                    participation = (total_votes / num_students) * 100
                    st.metric("Participación", f"{participation:.1f}%")
            else:
                st.info("No hay encuesta activa")
            
            st.divider()
            
            # Moderación
            st.subheader("🛡️ Moderación")
            if st.button("🗑️ Limpiar Chat"):
                save_shared_data('messages', [])
                st.success("Chat limpiado")
                st.rerun()
            
            st.divider()
            
            # Limpieza completa de sesión
            st.subheader("⚠️ Gestión de Sesión")
            st.warning("Esto eliminará todos los datos: chat, encuestas, estudiantes conectados y configuración del stream.")
            
            if st.button("🔄 Reiniciar Sesión Completa", type="primary", use_container_width=True):
                clear_all_shared_data()
                st.success("✅ Sesión reiniciada. Todos los datos han sido eliminados.")
                time.sleep(2)
                st.rerun()
    
    # Layout principal
    # Stream en la parte superior (ancho completo)
    st.header("📹 Stream en Vivo")
    
    # Cargar link compartido
    shared_vdo_link = load_shared_data('vdo_link', '')
    
    if shared_vdo_link:
        # Incrustar iframe de VDO.Ninja con aspect ratio 16:9
        # Calcular altura basada en el ancho (16:9)
        iframe_html = f"""
        <div style="position: relative; width: 100%; padding-bottom: 56.25%; /* 16:9 aspect ratio */">
            <iframe 
                src="{shared_vdo_link}" 
                style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none; border-radius: 10px;"
                allow="camera; microphone; display-capture; autoplay; clipboard-write"
                allowfullscreen>
            </iframe>
        </div>
        """
        st.markdown(iframe_html, unsafe_allow_html=True)
    else:
        st.info("👨‍🏫 El maestro aún no ha configurado el stream")
        # Placeholder con aspect ratio 16:9
        st.markdown("""
        <div style="position: relative; width: 100%; padding-bottom: 56.25%; background-color: #1f1f1f; border-radius: 10px; display: flex; align-items: center; justify-content: center;">
            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: white; font-size: 24px; text-align: center;">
                Esperando Stream
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Chat y Encuestas debajo del stream en dos columnas
    col1, col2 = st.columns(2)
    # Columna izquierda - Chat
    with col1:
        st.subheader("💬 Chat en Vivo")
        
        # Fragmento que se auto-actualiza cada 2 segundos
        @fragment(run_every="2s")
        def mostrar_chat():
            # Cargar mensajes compartidos
            shared_messages = load_shared_data('messages', [])
            
            # Contenedor de mensajes
            chat_container = st.container(height=400)
            
            with chat_container:
                for msg in shared_messages[-50:]:  # Últimos 50 mensajes
                    # Verificar si el mensaje tiene el campo 'type', si no, asignar 'estudiante' por defecto
                    msg_type = msg.get('type', 'estudiante')
                    msg_class = "teacher-message" if msg_type == "maestro" else "chat-message"
                    badge_class = "teacher-badge" if msg_type == "maestro" else "student-badge"
                    role_emoji = "👨‍🏫" if msg_type == "maestro" else "👨‍🎓"
                    
                    st.markdown(f"""
                    <div class="chat-message {msg_class}">
                        <span class='user-badge {badge_class}'>{role_emoji}</span>
                        <strong>{msg['user']}</strong> <small>{msg['time']}</small><br>
                        {msg['text']}
                    </div>
                    """, unsafe_allow_html=True)
        
        mostrar_chat()
        
        # Input de chat
        with st.form(key='chat_form', clear_on_submit=True):
            message = st.text_input("Mensaje", placeholder="Escribe un mensaje...", label_visibility="collapsed")
            submit = st.form_submit_button("Enviar")
            
            if submit and message:
                # Cargar mensajes actuales
                shared_messages = load_shared_data('messages', [])
                
                # Agregar nuevo mensaje
                new_message = {
                    'user': st.session_state.username,
                    'type': st.session_state.user_type,
                    'text': message,
                    'time': datetime.now().strftime("%H:%M:%S")
                }
                shared_messages.append(new_message)
                
                # Guardar mensajes
                save_shared_data('messages', shared_messages)
                
                # Actualizar actividad del estudiante
                if st.session_state.user_type == "estudiante":
                    connected = load_shared_data('connected_students', {})
                    if st.session_state.user_id in connected:
                        connected[st.session_state.user_id]['last_activity'] = datetime.now().isoformat()
                        save_shared_data('connected_students', connected)
                
                st.rerun()
    
    # Columna derecha - Encuestas
    with col2:
        st.subheader("📊 Encuestas")
        
        # Fragmento que se auto-actualiza cada 3 segundos para estudiantes
        @fragment(run_every="3s" if st.session_state.user_type == "estudiante" else None)
        def mostrar_encuestas():
            # Cargar encuesta compartida
            shared_poll = load_shared_data('current_poll', None)
            
            if shared_poll and shared_poll.get('active', False):
                poll = shared_poll
                
                st.markdown(f"### {poll['question']}")
                st.caption(f"Creada a las {poll['timestamp']}")
                
                # Cargar votos compartidos
                all_votes = load_shared_data('poll_votes', {})
                
                # Verificar si el usuario ya votó
                user_has_voted = st.session_state.user_id in poll.get('voters', [])
                
                if st.session_state.user_type == "estudiante":
                    if not user_has_voted:
                        st.info("🗳️ Selecciona una opción para votar (solo puedes votar una vez)")
                        
                        # Opciones de votación
                        for option in poll['options']:
                            if st.button(option, key=f"vote_{poll['id']}_{option}", use_container_width=True):
                                # Registrar voto
                                poll['votes'][option] += 1
                                poll['voters'].append(st.session_state.user_id)
                                
                                # Guardar voto del usuario
                                all_votes[st.session_state.user_id] = {
                                    'poll_id': poll['id'],
                                    'option': option
                                }
                                
                                # Guardar en archivos compartidos
                                save_shared_data('current_poll', poll)
                                save_shared_data('poll_votes', all_votes)
                                
                                # Actualizar actividad del estudiante
                                connected = load_shared_data('connected_students', {})
                                if st.session_state.user_id in connected:
                                    connected[st.session_state.user_id]['last_activity'] = datetime.now().isoformat()
                                    save_shared_data('connected_students', connected)
                                
                                st.success(f"✅ ¡Voto registrado para: {option}!")
                                time.sleep(1)
                                st.rerun()
                    else:
                        # Mostrar qué opción votó el estudiante
                        user_vote = all_votes.get(st.session_state.user_id, {})
                        voted_option = user_vote.get('option', '')
                        st.success(f"✅ Ya has votado por: **{voted_option}**")
                        st.info("No puedes cambiar tu voto")
                
                st.divider()
                
                # Resultados (visible para todos)
                st.subheader("📊 Resultados en Vivo")
                total_votes = sum(poll['votes'].values())
                
                if total_votes > 0:
                    for option, votes in poll['votes'].items():
                        percentage = (votes / total_votes) * 100
                        
                        # Mostrar barra de progreso y estadísticas
                        col_opt, col_num = st.columns([3, 1])
                        with col_opt:
                            st.progress(percentage / 100)
                            st.caption(f"{option}")
                        with col_num:
                            st.metric("", f"{votes}", f"{percentage:.1f}%")
                    
                    st.caption(f"Total de votos: {total_votes}")
                else:
                    st.info("Aún no hay votos")
            
            else:
                st.info("No hay encuestas activas en este momento")
                if st.session_state.user_type == "estudiante":
                    st.caption("Espera a que el maestro lance una encuesta")
        
        mostrar_encuestas()
    
    # Footer
    st.markdown("---")
    
    # Indicador de actualización para estudiantes
    if st.session_state.user_type == "estudiante":
        col_f1, col_f2, col_f3 = st.columns([1, 2, 1])
        with col_f2:
            st.info("💡 Presiona 🔄 Actualizar en la esquina superior para ver nuevas encuestas")
    
    footer_text = "👨‍🏫 **Panel del Maestro:** Controla el stream y crea encuestas desde el panel lateral" if st.session_state.user_type == "maestro" else "👨‍🎓 **Modo Estudiante:** Disfruta del stream y participa en las encuestas"
    st.markdown(f"""
    <div style='text-align: center; color: #666;'>
        <p>{footer_text}</p>
    </div>
    """, unsafe_allow_html=True)
