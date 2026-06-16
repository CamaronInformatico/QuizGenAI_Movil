import re
import json
import threading
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup
from kivy.utils import get_color_from_hex
import google.generativeai as genai
import mysql.connector

# ==============================================================================
# CONFIGURACIÓN DE LA IA (GEMINI)
# ==============================================================================
GENAI_API_KEY = "TU_API_KEY_AQUI"
genai.configure(api_key=GENAI_API_KEY)

# ==============================================================================
# CONEXIÓN A LA BASE DE DATOS
# ==============================================================================
# NOTA PARA EL APK: '127.0.0.1' apunta al propio celular. Para producción en Android 
# necesitarás cambiarlo por la dirección IP pública de tu servidor MySQL.
try:
    cn = mysql.connector.connect(
        user='root',
        password='180507',
        host='127.0.0.1', 
        database='quizgen_ia',
        port=3306
    )
    cursor = cn.cursor()
    print("Conexión exitosa a MySQL")
except Exception as e:
    cn = None
    cursor = None
    print(f"Error de conexión inicial (Normal si estás probando local): {e}")

# Crear tabla si existe conexión
if cursor:
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS preguntas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            pregunta TEXT NOT NULL,
            opcion_a TEXT NOT NULL,
            opcion_b TEXT NOT NULL,
            opcion_c TEXT NOT NULL,
            opcion_d TEXT NOT NULL,
            respuesta_correcta VARCHAR(2) NOT NULL,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cn.commit()
    except Exception as e:
        print("Error creando tabla preguntas:", e)

# ==============================================================================
# PALETA DE COLORES (TEMAS)
# ==============================================================================
TEMAS = {
    "claro": {"fondo": "#F5F7FA", "texto": "#2D3436", "primario": "#4A90E2", "input_bg": "#FFFFFF"},
    "oscuro": {"fondo": "#2D3436", "texto": "#F5F7FA", "primario": "#0BC376", "input_bg": "#636E72"}
}

# ==============================================================================
# VISTAS Y PANTALLAS (KIVY MOBILE ARCHITECTURE)
# ==============================================================================

class PantallaLogin(Screen):
    def on_pre_enter(self):
        self.colores = App.get_running_app().colores
        self.dibujar_pantalla()

    def dibujar_pantalla(self):
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=30, spacing=15)
        
        layout.add_widget(Label(text="Iniciar Sesión", font_size=24, bold=True, color=get_color_from_hex(self.colores["texto"])))
        
        layout.add_widget(Label(text="Correo electrónico:", size_hint_y=None, height=30, color=get_color_from_hex(self.colores["texto"])))
        self.entrada_correo = TextInput(multiline=False, write_tab=False, size_hint_y=None, height=40, background_color=get_color_from_hex(self.colores["input_bg"]))
        layout.add_widget(self.entrada_correo)
        
        self.lbl_error = Label(text="", color=[0.9, 0.3, 0.3, 1], size_hint_y=None, height=20)
        layout.add_widget(self.lbl_error)
        
        layout.add_widget(Label(text="Contraseña:", size_hint_y=None, height=30, color=get_color_from_hex(self.colores["texto"])))
        self.entrada_pass = TextInput(password=True, multiline=False, write_tab=False, size_hint_y=None, height=40, background_color=get_color_from_hex(self.colores["input_bg"]))
        layout.add_widget(self.entrada_pass)
        
        btn_ingresar = Button(text="Ingresar", background_color=get_color_from_hex(self.colores["primario"]), size_hint_y=None, height=45)
        btn_ingresar.bind(on_press=self.verificar_login)
        layout.add_widget(btn_ingresar)
        
        btn_registro = Button(text="Registrarse", background_color=get_color_from_hex("#9B59B6"), size_hint_y=None, height=45)
        btn_registro.bind(on_press=lambda x: setattr(self.manager, 'current', 'registro'))
        layout.add_widget(btn_registro)
        
        self.add_widget(layout)

    def verificar_login(self, instance):
        correo = self.entrada_correo.text.strip()
        contrasena = self.entrada_pass.text
        self.lbl_error.text = ""
        
        if not correo or not contrasena:
            App.get_running_app().mostrar_popup("Atención", "Por favor llena todos los campos.")
            return
            
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', correo):
            self.lbl_error.text = "correo electrónico inválido"
            App.get_running_app().mostrar_popup("Error de Formato", "Ingresa un correo electrónico válido.")
            return
            
        if cursor is None:
            # Simulación bypass si no hay Base de Datos externa conectada para poder probar la UI en el móvil
            App.get_running_app().usuario_id = 1
            App.get_running_app().mostrar_popup("Modo Demo", "Conexión local no disponible. Entrando en modo de prueba.")
            self.manager.current = 'inicio'
            return

        try:
            sql = "SELECT id, nombre FROM usuarios WHERE correo = %s AND contrasena = %s"
            cursor.execute(sql, (correo, contrasena))
            usuario = cursor.fetchone()
            if usuario:
                App.get_running_app().usuario_id = usuario[0]
                App.get_running_app().mostrar_popup("Éxito", f"¡Bienvenido(a)!")
                self.manager.current = 'inicio'
            else:
                App.get_running_app().mostrar_popup("Error", "Correo o contraseña incorrectos.")
        except Exception as e:
            App.get_running_app().mostrar_popup("Error BD", f"Detalle: {e}")

class PantallaRegistro(Screen):
    def on_pre_enter(self):
        self.colores = App.get_running_app().colores
        self.dibujar_pantalla()

    def dibujar_pantalla(self):
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=30, spacing=10)
        
        layout.add_widget(Label(text="Crear Cuenta", font_size=24, bold=True, color=get_color_from_hex(self.colores["texto"])))
        
        layout.add_widget(Label(text="Nombre completo:", color=get_color_from_hex(self.colores["texto"])))
        self.entrada_nombre = TextInput(multiline=False, size_hint_y=None, height=40)
        layout.add_widget(self.entrada_nombre)
        
        layout.add_widget(Label(text="Correo electrónico:", color=get_color_from_hex(self.colores["texto"])))
        self.entrada_correo = TextInput(multiline=False, size_hint_y=None, height=40)
        layout.add_widget(self.entrada_correo)
        
        layout.add_widget(Label(text="Contraseña:", color=get_color_from_hex(self.colores["texto"])))
        self.entrada_pass = TextInput(password=True, multiline=False, size_hint_y=None, height=40)
        layout.add_widget(self.entrada_pass)
        
        btn_guardar = Button(text="Guardar Registro", background_color=get_color_from_hex("#00B894"), size_hint_y=None, height=45)
        btn_guardar.bind(on_press=self.registrar_usuario)
        layout.add_widget(btn_guardar)
        
        btn_volver = Button(text="Volver al Login", background_color=get_color_from_hex("#E74C3C"), size_hint_y=None, height=45)
        btn_volver.bind(on_press=lambda x: setattr(self.manager, 'current', 'login'))
        layout.add_widget(btn_volver)
        
        self.add_widget(layout)

    def registrar_usuario(self, instance):
        if not self.entrada_nombre.text or not self.entrada_correo.text or not self.entrada_pass.text:
            App.get_running_app().mostrar_popup("Atención", "Por favor llena todos los campos.")
            return
        App.get_running_app().mostrar_popup("Éxito", "Usuario Registrado (Modo Demo/Local).")
        self.manager.current = 'login'

class PantallaInicio(Screen):
    def on_pre_enter(self):
        self.colores = App.get_running_app().colores
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=30, spacing=15)
        
        layout.add_widget(Label(text="Bienvenido Alumn@", font_size=24, bold=True, color=get_color_from_hex(self.colores["texto"])))
        layout.add_widget(Label(text="¿Qué deseas hacer hoy?", color=get_color_from_hex(self.colores["texto"])))
        
        btn1 = Button(text="Crear Quiz", background_color=get_color_from_hex("#4A90E2"), size_hint_y=None, height=50)
        btn1.bind(on_press=lambda x: setattr(self.manager, 'current', 'crear_quiz'))
        layout.add_widget(btn1)
        
        btn2 = Button(text="Resolver Quiz", background_color=get_color_from_hex("#00B894"), size_hint_y=None, height=50)
        btn2.bind(on_press=lambda x: setattr(self.manager, 'current', 'biblioteca'))
        layout.add_widget(btn2)
        
        btn3 = Button(text="Configuración", background_color=get_color_from_hex("#6C5CE7"), size_hint_y=None, height=50)
        btn3.bind(on_press=lambda x: setattr(self.manager, 'current', 'configuracion'))
        layout.add_widget(btn3)
        
        self.add_widget(layout)

class CrearQuiz(Screen):
    def on_pre_enter(self):
        self.colores = App.get_running_app().colores
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=30, spacing=15)
        
        layout.add_widget(Label(text="Crear Quiz", font_size=22, bold=True, color=get_color_from_hex(self.colores["texto"])))
        
        layout.add_widget(Label(text="Nombre del Quiz:", color=get_color_from_hex(self.colores["texto"])))
        layout.add_widget(TextInput(multiline=False, size_hint_y=None, height=40))
        
        btn_manual = Button(text="Crear Manualmente", background_color=get_color_from_hex("#4A90E2"), size_hint_y=None, height=50)
        btn_manual.bind(on_press=lambda x: setattr(self.manager, 'current', 'editor_preguntas'))
        layout.add_widget(btn_manual)
        
        btn_volver = Button(text="Volver", background_color=get_color_from_hex("#E74C3C"), size_hint_y=None, height=50)
        btn_volver.bind(on_press=lambda x: setattr(self.manager, 'current', 'inicio'))
        layout.add_widget(btn_volver)
        
        self.add_widget(layout)

class EditorPreguntas(Screen):
    def on_pre_enter(self):
        self.colores = App.get_running_app().colores
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=20, spacing=8)
        
        layout.add_widget(Label(text="Editor de Preguntas", font_size=20, bold=True, color=get_color_from_hex(self.colores["texto"])))
        
        self.entry_p = TextInput(hint_text="Pregunta", size_hint_y=None, height=40)
        self.op_a = TextInput(hint_text="Opción A", size_hint_y=None, height=40)
        self.op_b = TextInput(hint_text="Opción B", size_hint_y=None, height=40)
        self.op_c = TextInput(hint_text="Opción C", size_hint_y=None, height=40)
        self.op_d = TextInput(hint_text="Opción D", size_hint_y=None, height=40)
        self.resp = TextInput(hint_text="Respuesta Correcta (A/B/C/D)", size_hint_y=None, height=40)
        
        layout.add_widget(self.entry_p)
        layout.add_widget(self.op_a)
        layout.add_widget(self.op_b)
        layout.add_widget(self.op_c)
        layout.add_widget(self.op_d)
        layout.add_widget(self.resp)
        
        btn_save = Button(text="Guardar Pregunta", background_color=get_color_from_hex("#00B894"), size_hint_y=None, height=45)
        btn_save.bind(on_press=self.guardar)
        layout.add_widget(btn_save)
        
        btn_back = Button(text="Volver", background_color=get_color_from_hex("#E74C3C"), size_hint_y=None, height=45)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'crear_quiz'))
        layout.add_widget(btn_back)
        
        self.add_widget(layout)

    def guardar(self, instance):
        App.get_running_app().mostrar_popup("Éxito", "Pregunta guardada en caché local.")
        self.manager.current = 'inicio'

class BibliotecaQuizzes(Screen):
    def on_pre_enter(self):
        self.colores = App.get_running_app().colores
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=30, spacing=15)
        
        layout.add_widget(Label(text="Selecciona tu Carrera", font_size=22, bold=True, color=get_color_from_hex(self.colores["texto"])))
        
        self.carreras = ["Ing. en Sistemas", "Cuidados P. Dependientes", "Ing. en Mecatronica", "Admin. Hotelera y Gast."]
        self.spinner = Spinner(text=self.carreras[0], values=self.carreras, size_hint_y=None, height=50)
        layout.add_widget(self.spinner)
        
        btn_start = Button(text="Iniciar Evaluación", background_color=get_color_from_hex("#00B894"), size_hint_y=None, height=50)
        btn_start.bind(on_press=self.preparar_evaluacion)
        layout.add_widget(btn_start)
        
        btn_volver = Button(text="Volver", background_color=get_color_from_hex("#E74C3C"), size_hint_y=None, height=50)
        btn_volver.bind(on_press=lambda x: setattr(self.manager, 'current', 'inicio'))
        layout.add_widget(btn_volver)
        
        self.add_widget(layout)

    def preparar_evaluacion(self, instance):
        App.get_running_app().carrera_seleccionada = self.spinner.text
        self.manager.current = 'resolver_quiz'

class ResolverQuiz(Screen):
    def on_pre_enter(self):
        self.colores = App.get_running_app().colores
        self.banco = App.get_running_app().banco_preguntas.get(App.get_running_app().carrera_seleccionada, [])
        self.indice = 0
        self.aciertos = 0
        self.mostrar_pregunta()

    def mostrar_pregunta(self):
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        if self.indice >= len(self.banco):
            total = len(self.banco)
            porcentaje = int((self.aciertos / total) * 100) if total > 0 else 0
            layout.add_widget(Label(text=f"Resultados\n\nAciertos: {self.aciertos}/{total}\nCalificación: {porcentaje}%", font_size=20, halign="center", color=get_color_from_hex(self.colores["texto"])))
            
            btn_fin = Button(text="Volver al inicio", background_color=get_color_from_hex("#4A90E2"), size_hint_y=None, height=50)
            btn_fin.bind(on_press=lambda x: setattr(self.manager, 'current', 'inicio'))
            layout.add_widget(btn_fin)
            self.add_widget(layout)
            return

        p = self.banco[self.indice]
        layout.add_widget(Label(text=f"Pregunta {self.indice + 1} de {len(self.banco)}", color=get_color_from_hex(self.colores["texto"])))
        layout.add_widget(Label(text=p["pregunta"], font_size=16, bold=True, halign="center", color=get_color_from_hex(self.colores["texto"])))
        
        self.seleccion = None
        grid = GridLayout(cols=1, spacing=10, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))
        
        for opcion in p["opciones"]:
            btn_op = Button(text=opcion, size_hint_y=None, height=40, background_color=get_color_from_hex("#34495E"))
            btn_op.bind(on_press=lambda btn: self.seleccionar_opcion(btn))
            grid.add_widget(btn_op)
            
        layout.add_widget(grid)
        
        btn_resp = Button(text="Responder", background_color=get_color_from_hex("#00B894"), size_hint_y=None, height=50)
        btn_resp.bind(on_press=self.verificar_respuesta)
        layout.add_widget(btn_resp)
        
        self.add_widget(layout)

    def seleccionar_opcion(self, btn):
        self.seleccion = btn.text
        App.get_running_app().mostrar_popup("Selección", f"Elegiste: {btn.text}")

    def verificar_respuesta(self, instance):
        if not self.seleccion:
            App.get_running_app().mostrar_popup("Atención", "Selecciona una respuesta primero.")
            return
        
        p = self.banco[self.indice]
        if self.seleccion == p["respuesta"]:
            self.aciertos += 1
            App.get_running_app().mostrar_popup("Correcto", "¡Buen trabajo!")
        else:
            App.get_running_app().mostrar_popup("Incorrecto", f"La correcta era: {p['respuesta']}\n\n{p['feedback']}")
            
        self.indice += 1
        self.mostrar_pregunta()

class Configuracion(Screen):
    def on_pre_enter(self):
        self.colores = App.get_running_app().colores
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=30, spacing=15)
        
        layout.add_widget(Label(text="Configuración de Tema", font_size=22, bold=True, color=get_color_from_hex(self.colores["texto"])))
        
        btn_claro = Button(text="Tema Claro", background_color=get_color_from_hex("#0AA6B8"), size_hint_y=None, height=50)
        btn_claro.bind(on_press=lambda x: App.get_running_app().cambiar_tema("claro"))
        layout.add_widget(btn_claro)
        
        btn_oscuro = Button(text="Tema Oscuro", background_color=get_color_from_hex("#34495E"), size_hint_y=None, height=50)
        btn_oscuro.bind(on_press=lambda x: App.get_running_app().cambiar_tema("oscuro"))
        layout.add_widget(btn_oscuro)
        
        btn_volver = Button(text="Volver al Menú", background_color=get_color_from_hex("#E74C3C"), size_hint_y=None, height=50)
        btn_volver.bind(on_press=lambda x: setattr(self.manager, 'current', 'inicio'))
        layout.add_widget(btn_volver)
        
        self.add_widget(layout)

# ==============================================================================
# APLICACIÓN PRINCIPAL
# ==============================================================================
class QuizGenIAMovilApp(App):
    def build(self):
        self.usuario_id = None
        self.tema_actual = "claro"
        self.colores = TEMAS[self.tema_actual]
        self.carrera_seleccionada = ""
        
        # BANCO DE PREGUNTAS INTEGRADO
        self.banco_preguntas = {
            "Ing. en Sistemas": [
                {"pregunta": "¿Cuál es una característica clave del modelo en Cascada?", "opciones": ["Iterativo", "Secuencial", "Continuo", "Extremo"], "respuesta": "Secuencial", "feedback": "Requieres terminar una fase antes de pasar a la siguiente."},
                {"pregunta": "¿Estructura para evaluar casos en Python 3.10+?", "opciones": ["While", "For", "Match-Case", "If-Else"], "respuesta": "Match-Case", "feedback": "Permite evaluar múltiples estructuras de limpio."}
            ],
            "Ing. en Mecatronica": [
                {"pregunta": "¿Qué disciplinas se integran en la Mecatrónica?", "opciones": ["Informática y redes", "Mecánica, electrónica y control", "Química y biología"], "respuesta": "Mecánica, electrónica y control", "feedback": "Sinergia para sistemas automatizados."}
            ]
        }
        
        sm = ScreenManager()
        sm.add_widget(PantallaLogin(name='login'))
        sm.add_widget(PantallaRegistro(name='registro'))
        sm.add_widget(PantallaInicio(name='inicio'))
        sm.add_widget(CrearQuiz(name='crear_quiz'))
        sm.add_widget(EditorPreguntas(name='editor_preguntas'))
        sm.add_widget(BibliotecaQuizzes(name='biblioteca'))
        sm.add_widget(ResolverQuiz(name='resolver_quiz'))
        sm.add_widget(Configuracion(name='configuracion'))
        
        return sm

    def cambiar_tema(self, nuevo_tema):
        self.tema_actual = nuevo_tema
        self.colores = TEMAS[nuevo_tema]
        if self.root:
            pantalla_actual = self.root.current_screen
            if hasattr(pantalla_actual, 'dibujar_pantalla'):
                pantalla_actual.dibujar_pantalla()
            else:
                pantalla_actual.on_pre_enter()

    def mostrar_popup(self, titulo, texto):
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        layout.add_widget(Label(text=texto, halign="center"))
        btn_cerrar = Button(text="Entendido", size_hint_y=None, height=40, background_color=get_color_from_hex(self.colores["primario"]))
        layout.add_widget(btn_cerrar)
        
        popup = Popup(title=titulo, content=layout, size_hint=(0.8, 0.4))
        btn_cerrar.bind(on_press=popup.dismiss)
        popup.open()

if __name__ == "__main__":
    QuizGenIAMovilApp().run()