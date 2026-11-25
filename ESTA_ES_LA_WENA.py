
import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import mysql.connector
import hashlib
import hmac
import secrets
import json
from tkinter import filedialog
from datetime import date, datetime

try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    GRAFICAS_DISPONIBLES = True
except ImportError:
    GRAFICAS_DISPONIBLES = False

try:
    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Font, PatternFill
    EXCEL_DISPONIBLE = True
except ImportError:
    EXCEL_DISPONIBLE = False




DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "cecytem"
}

AZUL = "#0D3B66"
AZUL_BOTON = "#1565C0"
AZUL_CLARO = "#E3F2FD"

AZUL_MEDIO = "#2563EB"
AZUL_SUAVE = "#DBEAFE"

FONDO = "#F1F5F9"
PANEL = "#FFFFFF"
GRAFITO = "#0D3B66"
AMARILLO = "#1565C0"
CIAN = "#00E5FF"
MAGENTA = "#FF2BD6"
TEXTO = "#1E293B"
SECUNDARIO = "#64748B"
ENTRADA = "#FFFFFF"
BLANCO = PANEL
AZUL = GRAFITO
AZUL_BOTON = AMARILLO
AZUL_CLARO = "#E3F2FD"
GRIS = SECUNDARIO
ROJO = "#B91C1C"
NARANJA = "#EA580C"


COLORES_ALERTA = {
    "Baja": {"fuerte": "#16A34A", "suave": "#DCFCE7", "texto": "#14532D", "icono": "🟢🔔"},
    "Media": {"fuerte": "#EAB308", "suave": "#FEF9C3", "texto": "#713F12", "icono": "🟡🔔"},
    "Alta": {"fuerte": "#F97316", "suave": "#FFEDD5", "texto": "#7C2D12", "icono": "🟠🔔"},
    "Crítica": {"fuerte": "#DC2626", "suave": "#FEE2E2", "texto": "#7F1D1D", "icono": "🔴🔔"},
}

GRUPOS_BASE = [
    "1A", "1B", "1C",
    "2A", "2B", "2C",
    "3A", "3B", "3C"
]

ESTADOS_ASISTENCIA = [
    "Presente", "Falta", "Retardo", "Justificante"
]


def conectar():
    return mysql.connector.connect(**DB_CONFIG)


def generar_hash_password(password, sal=None):
    """Genera un hash PBKDF2 con sal aleatoria para nuevas contraseñas."""
    sal = sal or secrets.token_hex(16)
    iteraciones = 310000
    resultado = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), sal.encode("utf-8"), iteraciones
    ).hex()
    return f"pbkdf2_sha256${iteraciones}${sal}${resultado}"


def verificar_password(password, guardada):
    """Verifica hashes actuales y formatos anteriores para conservar las cuentas."""
    if guardada is None:
        return False

    guardada = str(guardada)

    if guardada.startswith("pbkdf2_sha256$"):
        try:
            algoritmo, iteraciones, sal, hash_guardado = guardada.split("$", 3)
            iteraciones = int(iteraciones)
            if algoritmo != "pbkdf2_sha256" or not 100000 <= iteraciones <= 2000000:
                return False
            calculado = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), sal.encode("utf-8"), iteraciones
            ).hex()
            return hmac.compare_digest(calculado, hash_guardado.lower())
        except (ValueError, TypeError):
            return False

    
    if hmac.compare_digest(password, guardada):
        return True

    sha = hashlib.sha256(password.encode("utf-8")).hexdigest()
    if hmac.compare_digest(sha, guardada.lower()):
        return True

    if ":" in guardada:
        sal, hash_guardado = guardada.split(":", 1)
        candidatos = [
            hashlib.sha256((password + sal).encode("utf-8")).hexdigest(),
            hashlib.sha256((sal + password).encode("utf-8")).hexdigest()
        ]
        if any(hmac.compare_digest(x, hash_guardado.lower()) for x in candidatos):
            return True

    return False


def crear_tablas():
    """Crea tablas auxiliares sin borrar tablas existentes."""
    conexion = conectar()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS grupos_escolares (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(30) NOT NULL UNIQUE,
                creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS docente_grupos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                docente VARCHAR(100) NOT NULL,
                grupo_id INT NOT NULL,
                UNIQUE KEY asignacion_unica (docente, grupo_id),
                FOREIGN KEY (grupo_id)
                    REFERENCES grupos_escolares(id)
                    ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alumnos_escolares (
                id INT AUTO_INCREMENT PRIMARY KEY,
                grupo_id INT NOT NULL,
                numero_lista INT NOT NULL,
                nombre VARCHAR(150) NOT NULL,
                activo BOOLEAN DEFAULT TRUE,
                UNIQUE KEY alumno_lista (grupo_id, numero_lista),
                FOREIGN KEY (grupo_id)
                    REFERENCES grupos_escolares(id)
                    ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS asistencias_escolares (
                id INT AUTO_INCREMENT PRIMARY KEY,
                alumno_id INT NOT NULL,
                grupo_id INT NOT NULL,
                fecha DATE NOT NULL,
                estado VARCHAR(30) NOT NULL,
                docente VARCHAR(100) NOT NULL,
                observaciones TEXT,
                creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY asistencia_diaria (alumno_id, fecha),
                FOREIGN KEY (alumno_id)
                    REFERENCES alumnos_escolares(id),
                FOREIGN KEY (grupo_id)
                    REFERENCES grupos_escolares(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registros_escolares (
                id INT AUTO_INCREMENT PRIMARY KEY,
                tipo VARCHAR(50) NOT NULL,
                alumno VARCHAR(150) NOT NULL,
                grupo VARCHAR(50),
                fecha DATE NOT NULL,
                hora TIME NULL,
                detalle TEXT,
                accion VARCHAR(150),
                evidencia VARCHAR(500),
                seguimiento BOOLEAN DEFAULT FALSE,
                gravedad VARCHAR(20) NOT NULL DEFAULT 'Baja',
                estado VARCHAR(40) DEFAULT 'Pendiente',
                registrado_por VARCHAR(100) NOT NULL,
                creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'registros_escolares'
              AND COLUMN_NAME = 'gravedad'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                ALTER TABLE registros_escolares
                ADD COLUMN gravedad VARCHAR(20) NOT NULL DEFAULT 'Baja'
            """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisiones_directivas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                registro_id INT NULL,
                alumno VARCHAR(150) NOT NULL,
                accion VARCHAR(100) NOT NULL,
                justificacion TEXT,
                estado VARCHAR(40) DEFAULT 'Pendiente',
                director VARCHAR(100) NOT NULL,
                creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cartas_compromiso (
                id INT AUTO_INCREMENT PRIMARY KEY,
                alumno VARCHAR(150) NOT NULL,
                tutor VARCHAR(150),
                motivo TEXT,
                compromisos TEXT,
                fecha DATE,
                director VARCHAR(100) NOT NULL,
                creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS preferencias_usuario (
                usuario VARCHAR(100) PRIMARY KEY,
                colores JSON NOT NULL,
                actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP
            )
        """)

        for grupo in GRUPOS_BASE:
            cursor.execute("""
                INSERT IGNORE INTO grupos_escolares (nombre)
                VALUES (%s)
            """, (grupo,))

        conexion.commit()

    finally:
        conexion.close()


class SistemaNezahualcoyotl:

    def __init__(self, root):
        self.root = root
        self.root.title("Sistema Escolar Nezahualcóyotl")
        self.root.configure(bg=FONDO)
        self.root.minsize(320, 480)
        self._configurando_ventana = False
        self._modo_movil = None
        self._ventana_menu_movil = None
        self._programar_ajuste = None

        try:
            self.root.state("zoomed")
        except tk.TclError:
            ancho = self.root.winfo_screenwidth()
            alto = self.root.winfo_screenheight()
            self.root.geometry(f"{ancho}x{alto}+0+0")

        self.usuario = ""
        self.nombre = ""
        self.rol = ""

        self.color = AZUL_BOTON
        self.oscuro = AZUL
        self.claro = AZUL_CLARO

        self.contenido = None
        self.campos = {}
        self.vista_actual = "Inicio"
        self.grupo_seleccionado = None
        self.alumnos_lista = []
        self.variables_asistencia = {}
        self.variables_observaciones = {}
        self.canvas_grafica = None
        self.marco_graficas = None
        self._temporizador_campana = None
        self.colores_actuales = (FONDO, PANEL, GRAFITO, AMARILLO, CIAN, MAGENTA, TEXTO, SECUNDARIO, ENTRADA)

        self.configurar_estilos()
        self.mostrar_login()

   

    def configurar_estilos(self):
        """Aplica estilos ttk coherentes con el tema activo."""
        estilo = ttk.Style()

        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass

        estilo.configure(
            "Treeview",
            rowheight=34,
            font=("Segoe UI", 10),
            background=PANEL,
            fieldbackground=PANEL,
            foreground=TEXTO,
            borderwidth=0,
            relief="flat"
        )
        estilo.map(
            "Treeview",
            background=[("selected", AMARILLO)],
            foreground=[("selected", GRAFITO)]
        )
        estilo.configure(
            "Treeview.Heading",
            font=("Segoe UI", 10, "bold"),
            background=GRAFITO,
            foreground="#FFFFFF",
            padding=(9, 9),
            relief="flat"
        )
        estilo.map(
            "Treeview.Heading",
            background=[("active", AMARILLO)],
            foreground=[("active", GRAFITO)]
        )
        estilo.configure("TEntry", padding=(9, 8), fieldbackground=ENTRADA)
        estilo.configure("TCombobox", padding=(9, 7), fieldbackground=ENTRADA)
        estilo.configure("TScrollbar", arrowsize=14)

    def limpiar_root(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def limpiar_contenido(self):
        if self.contenido:
            for widget in self.contenido.winfo_children():
                widget.destroy()

    def boton(self, padre, texto, comando, color=None):
        """Crea botones planos con contraste automático para ambos temas."""
        fondo_boton = color or self.color
        texto_boton = GRAFITO if fondo_boton.upper() in (AMARILLO.upper(), CIAN.upper()) else PANEL
        boton = tk.Button(
            padre,
            text=texto,
            command=comando,
            bg=fondo_boton,
            fg=texto_boton,
            activebackground=CIAN if fondo_boton.upper() != CIAN.upper() else AMARILLO,
            activeforeground=GRAFITO,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=14,
            pady=9,
            highlightthickness=0
        )
        color_normal = fondo_boton
        texto_normal = texto_boton
        boton.bind(
            "<Enter>",
            lambda evento, w=boton: w.configure(bg=CIAN, fg=GRAFITO)
        )
        boton.bind(
            "<Leave>",
            lambda evento, w=boton, c=color_normal, t=texto_normal: w.configure(bg=c, fg=t)
        )
        return boton

    def titulo(self, texto, descripcion=""):
        encabezado = tk.Frame(self.contenido, bg=FONDO)
        encabezado.pack(fill="x", pady=(0, 14))
        tk.Frame(encabezado, bg=AMARILLO, width=5, height=38).pack(side="left", padx=(0, 11))
        textos = tk.Frame(encabezado, bg=FONDO)
        textos.pack(side="left", fill="x", expand=True)
        tk.Label(
            textos,
            text=texto,
            bg=FONDO,
            fg=TEXTO,
            font=("Segoe UI", 22, "bold"),
            anchor="w"
        ).pack(fill="x")

        if descripcion:
            tk.Label(
                textos,
                text=descripcion,
                bg=FONDO,
                fg=SECUNDARIO,
                font=("Segoe UI", 10),
                anchor="w",
                justify="left",
                wraplength=1000
            ).pack(fill="x", pady=(3, 0))

    def leer_campo(self, nombre):
        widget = self.campos.get(nombre)

        if widget is None:
            return ""

        if isinstance(widget, tk.Text):
            return widget.get("1.0", "end-1c").strip()

        return widget.get().strip()

    def crear_scroll(self, padre):
        """Area desplazable para pantallas con muchos elementos."""
        marco = tk.Frame(padre, bg=FONDO)
        marco.pack(fill="both", expand=True)

        canvas = tk.Canvas(
            marco, bg=FONDO, highlightthickness=0
        )
        scroll = ttk.Scrollbar(
            marco, orient="vertical", command=canvas.yview
        )

        interior = tk.Frame(canvas, bg=FONDO)
        ventana = canvas.create_window(
            (0, 0), window=interior, anchor="nw"
        )

        interior.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfigure(
                ventana, width=e.width
            )
        )

        canvas.configure(yscrollcommand=scroll.set)

        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        return interior

   

    def mostrar_login(self):
        self.limpiar_root()
        self.root.configure(bg=FONDO)

        marco = tk.Frame(
            self.root,
            bg=BLANCO,
            padx=22,
            pady=22,
            highlightbackground="#CBD5E1",
            highlightthickness=1
        )
        marco.place(
            relx=0.5, rely=0.5, anchor="center",
            relwidth=0.90, width=-24, height=380
        )
        marco.configure(width=390)
        marco.bind("<Configure>", self._ajustar_login)

        tk.Label(
            marco, text="NEZAHUALCÓYOTL",
            bg=BLANCO, fg=AZUL,
            font=("Segoe UI", 28, "bold")
        ).pack(pady=(5, 0))

        tk.Label(
            marco, text="Sistema Escolar Nezahualcóyotl",
            bg=BLANCO, fg=GRIS
        ).pack(pady=(0, 22))

        tk.Label(
            marco, text="Usuario",
            bg=BLANCO, fg=TEXTO, anchor="w"
        ).pack(fill="x")

        self.entrada_usuario = ttk.Entry(marco)
        self.entrada_usuario.pack(fill="x", pady=(5, 12))

        tk.Label(
            marco, text="Contraseña",
            bg=BLANCO, fg=TEXTO, anchor="w"
        ).pack(fill="x")

        self.entrada_password = ttk.Entry(marco, show="*")
        self.entrada_password.pack(fill="x", pady=(5, 18))
        self.entrada_password.bind(
            "<Return>", lambda e: self.validar_login()
        )

        self.boton(
            marco, "Iniciar sesión",
            self.validar_login, AZUL_BOTON
        ).pack(fill="x")

        tk.Label(
            marco,
            text="Acceso para docentes y dirección",
            bg=BLANCO, fg=GRIS,
            font=("Segoe UI", 9)
        ).pack(pady=17)

        self.entrada_usuario.focus_set()

    def _ajustar_login(self, evento=None):
        """Reduce tipografías y espacios cuando la ventana es estrecha."""
        if not hasattr(self, "entrada_usuario"):
            return
        ancho = self.root.winfo_width()
        compacto = ancho < 520
        tam_titulo = 19 if compacto else 25
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Frame):
                for hijo in widget.winfo_children():
                    if isinstance(hijo, tk.Label) and hijo.cget("text") == "NEZAHUALCÓYOTL":
                        hijo.configure(font=("Segoe UI", tam_titulo, "bold"))

    def _programar_ajuste_responsivo(self, evento=None):
        """Evita ejecutar el ajuste muchas veces durante un redimensionamiento."""
        if evento is not None and evento.widget is not self.root:
            return
        if self._programar_ajuste is not None:
            try:
                self.root.after_cancel(self._programar_ajuste)
            except tk.TclError:
                pass
        self._programar_ajuste = self.root.after(120, self._ajustar_distribucion)

    def _ajustar_distribucion(self):
        self._programar_ajuste = None
        if not hasattr(self, "menu_lateral") or not self.menu_lateral.winfo_exists():
            return
        ancho = self.root.winfo_width()
        modo_movil = ancho < 760
        if hasattr(self, "etiqueta_usuario_barra") and self.etiqueta_usuario_barra.winfo_exists():
            if ancho < 520:
                self.etiqueta_usuario_barra.pack_forget()
            elif not self.etiqueta_usuario_barra.winfo_manager():
                self.etiqueta_usuario_barra.pack(side="left", padx=10)
        if hasattr(self, "etiqueta_marca") and self.etiqueta_marca.winfo_exists():
            self.etiqueta_marca.configure(font=("Segoe UI", 12 if ancho < 520 else 17, "bold"))
        if modo_movil == self._modo_movil:
            return
        self._modo_movil = modo_movil
        if modo_movil:
            self.menu_lateral.pack_forget()
            if hasattr(self, "boton_menu_movil") and self.boton_menu_movil.winfo_exists():
                self.boton_menu_movil.pack(side="left", padx=4, pady=8)
            if hasattr(self, "contenido") and self.contenido.winfo_exists():
                self.contenido.configure(padx=8, pady=10)
        else:
            if hasattr(self, "boton_menu_movil") and self.boton_menu_movil.winfo_exists():
                self.boton_menu_movil.pack_forget()
            self.menu_lateral.pack(side="left", fill="y", before=self.area_principal)
            if hasattr(self, "contenido") and self.contenido.winfo_exists():
                self.contenido.configure(padx=16, pady=16)
            if self._ventana_menu_movil is not None:
                try:
                    self._ventana_menu_movil.destroy()
                except tk.TclError:
                    pass
                self._ventana_menu_movil = None

    def _abrir_menu_movil(self):
        """Muestra las secciones en una ventana compacta para pantallas pequeñas."""
        if self._ventana_menu_movil is not None:
            try:
                if self._ventana_menu_movil.winfo_exists():
                    self._ventana_menu_movil.lift()
                    return
            except tk.TclError:
                pass
        ventana = tk.Toplevel(self.root)
        self._ventana_menu_movil = ventana
        ventana.title("Menú principal")
        ventana.configure(bg=self.oscuro)
        ancho = max(250, min(320, self.root.winfo_width() - 30))
        alto = min(max(360, ventana.winfo_screenheight() - 140), 620)
        ventana.geometry(f"{ancho}x{alto}")
        ventana.transient(self.root)
        encabezado = tk.Label(
            ventana, text="MENÚ PRINCIPAL", bg=self.oscuro,
            fg=BLANCO, font=("Segoe UI", 12, "bold")
        )
        encabezado.pack(fill="x", padx=12, pady=12)
        lienzo = tk.Canvas(ventana, bg=self.oscuro, highlightthickness=0)
        barra = ttk.Scrollbar(ventana, orient="vertical", command=lienzo.yview)
        interior = tk.Frame(lienzo, bg=self.oscuro)
        interior.bind("<Configure>", lambda e: lienzo.configure(scrollregion=lienzo.bbox("all")))
        lienzo.create_window((0, 0), window=interior, anchor="nw", width=ancho - 25)
        lienzo.configure(yscrollcommand=barra.set)
        lienzo.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        for opcion in self.obtener_menu():
            tk.Button(
                interior, text=opcion, command=lambda n=opcion: self._seleccionar_menu_movil(n),
                bg=AMARILLO if opcion == self.vista_actual else self.oscuro,
                fg=GRAFITO if opcion == self.vista_actual else BLANCO,
                activebackground=AMARILLO, activeforeground=GRAFITO,
                font=("Segoe UI", 10), relief="flat", anchor="w",
                padx=14, pady=12, bd=0
            ).pack(fill="x", padx=5, pady=2)
        ventana.protocol("WM_DELETE_WINDOW", self._cerrar_menu_movil)

    def _seleccionar_menu_movil(self, opcion):
        self._cerrar_menu_movil()
        self.ir(opcion)

    def _cerrar_menu_movil(self):
        if self._ventana_menu_movil is not None:
            try:
                self._ventana_menu_movil.destroy()
            except tk.TclError:
                pass
            self._ventana_menu_movil = None

    def validar_login(self):
        usuario = self.entrada_usuario.get().strip()
        password = self.entrada_password.get()

        if not usuario or not password:
            messagebox.showwarning(
                "Datos incompletos",
                "Escribe tu usuario y contraseña."
            )
            return

        conexion = None

        try:
            conexion = conectar()
            cursor = conexion.cursor(dictionary=True)

            cursor.execute("""
                SELECT nombre, usuario, password_hash, rol
                FROM usuarios
                WHERE usuario = %s
                LIMIT 1
            """, (usuario,))

            fila = cursor.fetchone()

            if not fila or not verificar_password(
                password, fila.get("password_hash")
            ):
                messagebox.showerror(
                    "Acceso denegado",
                    "Usuario o contraseña incorrectos."
                )
                return

            rol = str(fila.get("rol") or "").strip().lower()

            if rol not in ("docente", "director"):
                messagebox.showerror(
                    "Rol inválido",
                    "La cuenta debe tener rol docente o director."
                )
                return

            self.usuario = str(fila["usuario"])
            self.nombre = str(fila.get("nombre") or usuario)
            self.rol = rol

            hash_actual = str(fila.get("password_hash") or "")
            if not hash_actual.startswith("pbkdf2_sha256$"):
                nuevo_hash = generar_hash_password(password)
                cursor.execute(
                    "UPDATE usuarios SET password_hash=%s WHERE usuario=%s",
                    (nuevo_hash, self.usuario)
                )
                conexion.commit()

            if rol == "docente":
                self.color, self.oscuro, self.claro = (
                    AZUL_BOTON, AZUL, AZUL_CLARO
                )
            else:
                self.color, self.oscuro, self.claro = (
                    AZUL_MEDIO, AZUL, AZUL_SUAVE
                )

        except mysql.connector.Error as error:
            messagebox.showerror(
                "Error de MySQL",
                f"No se pudo iniciar sesión:\n\n{error}\n\n"
                "Verifica DB_CONFIG y la estructura de usuarios."
            )
            return

        finally:
            if conexion is not None and conexion.is_connected():
                conexion.close()

        try:
            crear_tablas()
        except mysql.connector.Error as error:
            messagebox.showerror(
                "Error al preparar tablas", str(error)
            )
            return

        self.cargar_colores_usuario()
        self.mostrar_sistema()

    
    def guardar_colores_usuario(self, colores=None):
        """Guarda el tema de la cuenta activa para restaurarlo en el próximo acceso."""
        if not self.usuario:
            return
        colores = tuple(colores or self.colores_actuales)
        conexion = None
        try:
            conexion = conectar()
            cursor = conexion.cursor()
            cursor.execute("""
                INSERT INTO preferencias_usuario (usuario, colores)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE colores=VALUES(colores)
            """, (self.usuario, json.dumps(colores)))
            conexion.commit()
        except mysql.connector.Error as error:
            if conexion is not None:
                conexion.rollback()
            messagebox.showwarning(
                "No se guardó el tema",
                f"Los colores se aplicaron, pero no fue posible guardarlos en MySQL.\\n{error}"
            )
        finally:
            if conexion is not None and conexion.is_connected():
                conexion.close()

    def cargar_colores_usuario(self):
        """Recupera los nueve colores guardados para la cuenta activa."""
        if not self.usuario:
            return
        try:
            filas = self.consultar(
                "SELECT colores FROM preferencias_usuario WHERE usuario=%s",
                (self.usuario,)
            )
            if filas and filas[0].get("colores"):
                colores = json.loads(filas[0]["colores"])
                if isinstance(colores, list) and len(colores) == 6:
                    fondo, oscuro, acento, seleccionado, texto, panel = colores
                    colores = [
                        fondo, panel, oscuro, acento, "#00E5FF",
                        "#FF2BD6", texto, "#A8A8B8", panel
                    ]
                if isinstance(colores, list) and len(colores) == 9:
                    global FONDO, PANEL, GRAFITO, AMARILLO, CIAN, MAGENTA
                    global TEXTO, SECUNDARIO, ENTRADA, BLANCO, AZUL, AZUL_BOTON
                    global AZUL_CLARO, GRIS
                    (FONDO, PANEL, GRAFITO, AMARILLO, CIAN, MAGENTA,
                     TEXTO, SECUNDARIO, ENTRADA) = tuple(colores)
                    BLANCO = PANEL
                    AZUL = GRAFITO
                    AZUL_BOTON = AMARILLO
                    AZUL_CLARO = AMARILLO
                    GRIS = SECUNDARIO
                    self.colores_actuales = tuple(colores)
                    self.oscuro = GRAFITO
                    self.color = AMARILLO
                    self.claro = AMARILLO
        except (mysql.connector.Error, ValueError, TypeError, json.JSONDecodeError):
            pass

    def pantalla_personalizado(self):
        self.limpiar_contenido()
        self.titulo(
            "Temas y apariencia",
            "Elige una identidad visual para el sistema. Cada tema se guarda en la cuenta activa y no modifica los datos de MySQL."
        )

        paletas = {
            "Institucional": (
                "#F1F5F9", "#FFFFFF", "#0D3B66", "#1565C0", "#00A6C7",
                "#A855F7", "#1E293B", "#64748B", "#FFFFFF"
            ),
            "Cyberpunk 2077": (
                "#070B18", "#111A2E", "#050816", "#FFE600", "#00F0FF",
                "#FF3CAC", "#FFFFFF", "#D6E2F0", "#1D2942"
            ),
            "Océano": (
                "#EAF4F8", "#FFFFFF", "#123B52", "#087EAB", "#27C2D1",
                "#5265C8", "#183447", "#668394", "#F5FBFD"
            ),
            "Bosque": (
                "#EEF4EC", "#FFFFFF", "#203B2B", "#347A45", "#7CBF70",
                "#C18B45", "#203128", "#718174", "#F7FAF5"
            ),
            "Atardecer": (
                "#FFF3EA", "#FFFFFF", "#552C3B", "#D85B42", "#F29B62",
                "#A84E83", "#402B32", "#8B7077", "#FFFAF6"
            ),
            "Violeta": (
                "#F3EFFA", "#FFFFFF", "#34264F", "#7652B5", "#43BFC2",
                "#D66BAA", "#30283D", "#82758F", "#FBF8FF"
            )
        }

        tema_actual = None
        for nombre_tema, colores_tema in paletas.items():
            if tuple(self.colores_actuales) == tuple(colores_tema):
                tema_actual = nombre_tema
                break

        descripciones = {
            "Institucional": "Formal, claro y profesional",
            "Cyberpunk 2077": "Neón intenso · oscuro · futurista",
            "Océano": "Azules frescos y tonos acuáticos",
            "Bosque": "Verdes naturales y tranquilos",
            "Atardecer": "Tonos cálidos y modernos",
            "Violeta": "Morados elegantes con acentos brillantes"
        }

        panel_temas = tk.Frame(self.contenido, bg=FONDO)
        panel_temas.pack(fill="x", pady=(0, 12))
        for columna in range(3):
            panel_temas.columnconfigure(columna, weight=1, uniform="tema")

        for indice, (nombre_tema, colores_tema) in enumerate(paletas.items()):
            fondo, panel_color, grafito, acento, cian, magenta, texto, secundario, entrada = colores_tema
            seleccionado = nombre_tema == tema_actual
            cyberpunk = nombre_tema == "Cyberpunk 2077"
            borde_tarjeta = (
                "#00F0FF" if cyberpunk and seleccionado else
                "#FFE600" if cyberpunk else
                acento if seleccionado else secundario
            )
            tarjeta = tk.Frame(
                panel_temas, bg=panel_color, padx=14, pady=13,
                highlightbackground=borde_tarjeta,
                highlightthickness=3 if seleccionado else (2 if cyberpunk else 1)
            )
            tarjeta.grid(
                row=indice // 3, column=indice % 3,
                sticky="nsew", padx=6, pady=6
            )

            tk.Label(
                tarjeta, text=nombre_tema, bg=panel_color, fg=texto,
                font=("Segoe UI", 12, "bold")
            ).pack(anchor="w")
            tk.Label(
                tarjeta, text=descripciones[nombre_tema], bg=panel_color,
                fg=secundario, font=("Segoe UI", 9)
            ).pack(anchor="w", pady=(3, 10))

            
            color_marco = "#00F0FF" if cyberpunk else grafito
            muestra = tk.Frame(
                tarjeta, bg=fondo, padx=9, pady=9,
                highlightbackground=color_marco,
                highlightthickness=2 if cyberpunk else 1
            )
            muestra.pack(fill="x", pady=(0, 11))
            barra_muestra = tk.Frame(
                muestra, bg=acento if cyberpunk else grafito, height=25
            )
            barra_muestra.pack(fill="x")
            barra_muestra.pack_propagate(False)
            tk.Label(
                barra_muestra, text="CECyTEM  //  NIGHT CITY" if cyberpunk else "CECyTEM",
                bg=acento if cyberpunk else grafito,
                fg="#050816" if cyberpunk else "#FFFFFF",
                font=("Segoe UI", 8, "bold")
            ).pack(side="left", padx=8)

            contenido_muestra = tk.Frame(
                muestra, bg=panel_color, padx=8, pady=8,
                highlightbackground=cian if cyberpunk else panel_color,
                highlightthickness=1 if cyberpunk else 0
            )
            contenido_muestra.pack(fill="x", pady=(6, 0))
            tk.Label(
                contenido_muestra, text="Vista general", bg=panel_color,
                fg=texto, font=("Segoe UI", 9, "bold")
            ).pack(anchor="w")
            fila_muestras = tk.Frame(contenido_muestra, bg=panel_color)
            fila_muestras.pack(fill="x", pady=(7, 2))
            for color_muestra in (acento, cian, magenta):
                tk.Frame(
                    fila_muestras, bg=color_muestra, height=13
                ).pack(side="left", fill="x", expand=True, padx=2)

            color_texto_boton = "#050816" if cyberpunk else "#FFFFFF"
            tk.Button(
                tarjeta,
                text="✓ Tema activo" if seleccionado else "Aplicar tema",
                command=lambda c=colores_tema: self.aplicar_colores(c),
                bg=acento, fg=color_texto_boton,
                activebackground=cian, activeforeground=grafito,
                font=("Segoe UI", 9, "bold"), relief="flat", bd=0,
                cursor="hand2", padx=12, pady=8
            ).pack(anchor="e")

        panel_custom = tk.Frame(
            self.contenido, bg=PANEL, padx=18, pady=16,
            highlightbackground=SECUNDARIO, highlightthickness=1
        )
        panel_custom.pack(fill="x", pady=8)
        tk.Label(
            panel_custom, text="Personalización avanzada", bg=PANEL, fg=TEXTO,
            font=("Segoe UI", 13, "bold")
        ).pack(anchor="w", pady=(0, 4))
        tk.Label(
            panel_custom, text="También puedes ajustar los nueve colores manualmente.",
            bg=PANEL, fg=SECUNDARIO, font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(0, 10))

        definiciones = [
            ("Fondo general", "fondo"),
            ("Tarjetas y paneles", "panel"),
            ("Barra y menú", "grafito"),
            ("Color principal", "amarillo"),
            ("Cian", "cian"),
            ("Magenta", "magenta"),
            ("Texto principal", "texto"),
            ("Texto secundario", "secundario"),
            ("Campos de entrada", "entrada")
        ]
        valores_actuales = dict(zip(
            ("fondo", "panel", "grafito", "amarillo", "cian", "magenta",
             "texto", "secundario", "entrada"),
            self.colores_actuales
        ))
        self.colores_personalizados = {}

        for etiqueta, clave in definiciones:
            fila = tk.Frame(panel_custom, bg=PANEL)
            fila.pack(fill="x", pady=4)
            tk.Label(fila, text=etiqueta, bg=PANEL, fg=TEXTO,
                     font=("Segoe UI", 9)).pack(side="left")
            muestra = tk.Label(
                fila, text=valores_actuales[clave], bg=valores_actuales[clave],
                fg="#FFFFFF" if clave in ("grafito", "magenta") else "#111111",
                width=13, relief="flat", padx=5, pady=4
            )
            muestra.pack(side="right", padx=8)
            self.colores_personalizados[clave] = muestra

            def elegir(k=clave, widget=muestra):
                color = colorchooser.askcolor(
                    color=widget.cget("bg"), title="Selecciona un color"
                )
                if color and color[1]:
                    widget.configure(text=color[1], bg=color[1])

            self.boton(fila, "Elegir color", elegir).pack(side="right")

        def aplicar_custom():
            claves = ("fondo", "panel", "grafito", "amarillo", "cian",
                      "magenta", "texto", "secundario", "entrada")
            colores = tuple(self.colores_personalizados[k].cget("bg") for k in claves)
            self.aplicar_colores(colores)

        self.boton(panel_custom, "Aplicar colores personalizados", aplicar_custom).pack(anchor="e", pady=(12, 0))

        self.boton(
            self.contenido, "Restablecer tema institucional",
            lambda: self.aplicar_colores(paletas["Institucional"]),
            color=SECUNDARIO
        ).pack(anchor="w", pady=8)

    def aplicar_colores(self, colores, guardar=True, mostrar_mensaje=True):
        global FONDO, PANEL, GRAFITO, AMARILLO, CIAN, MAGENTA
        global TEXTO, SECUNDARIO, ENTRADA, BLANCO, AZUL, AZUL_BOTON
        global AZUL_CLARO, GRIS
        if len(colores) == 6:
            fondo, oscuro, acento, seleccionado, texto, panel = colores
            colores = (
                fondo, panel, oscuro, acento, "#00E5FF", "#FF2BD6",
                texto, "#A8A8B8", panel
            )
        if len(colores) != 9:
            messagebox.showerror("Colores inválidos", "El tema debe contener nueve colores.")
            return
        (FONDO, PANEL, GRAFITO, AMARILLO, CIAN, MAGENTA,
         TEXTO, SECUNDARIO, ENTRADA) = tuple(colores)
        BLANCO = PANEL
        AZUL = GRAFITO
        AZUL_BOTON = AMARILLO
        AZUL_CLARO = AMARILLO
        GRIS = SECUNDARIO
        self.colores_actuales = tuple(colores)
        self.oscuro = GRAFITO
        self.color = AMARILLO
        self.claro = AMARILLO
        try:
            self.configurar_estilos()
            self.root.configure(bg=FONDO)
            if self.usuario:
                self.mostrar_sistema()
                if guardar:
                    self.guardar_colores_usuario(colores)
                self.ir("Personalizado")
            if mostrar_mensaje:
                mensaje = "Los colores se aplicaron correctamente."
                if guardar and self.usuario:
                    mensaje += "\\nSe guardaron para esta cuenta."
                messagebox.showinfo("Personalización aplicada", mensaje)
        except tk.TclError as error:
            messagebox.showerror("Error de apariencia", str(error))

    def obtener_menu(self):
        comunes = ["Importar Excel", "Gráficas"]
        if self.rol == "docente":
            return ["Inicio", "Pase de lista", "Mis grupos", "Reportes",
                    "Alertas"] + comunes + ["Más opciones"]
        return ["Inicio", "Panel directivo", "Alumnos", "Reportes",
                "Alertas"] + comunes + ["Más opciones"]

    def mostrar_sistema(self):
        self.limpiar_root()

        principal = tk.Frame(self.root, bg=FONDO)
        principal.pack(fill="both", expand=True)

        barra = tk.Frame(
            principal, bg=self.oscuro, height=58
        )
        barra.pack(fill="x")
        barra.pack_propagate(False)

        self.boton_menu_movil = self.boton(
            barra, "Menú", self._abrir_menu_movil, color=self.oscuro
        )

        self.etiqueta_marca = tk.Label(
            barra, text="NEZAHUALCÓYOTL",
            bg=self.oscuro, fg=BLANCO,
            font=("Segoe UI", 17, "bold")
        )
        self.etiqueta_marca.pack(side="left", padx=18)

        self.etiqueta_usuario_barra = tk.Label(
            barra,
            text=f"{self.rol.capitalize()}: {self.nombre}",
            bg=self.oscuro, fg=BLANCO
        )
        self.etiqueta_usuario_barra.pack(side="left", padx=10)

        self.botones_campanas = {}
        for gravedad, estilo in COLORES_ALERTA.items():
            campana = tk.Button(
                barra, text=f"{estilo['icono']} 0",
                command=lambda g=gravedad: self.abrir_alertas_gravedad(g),
                bg=estilo["fuerte"], fg="#FFFFFF",
                activebackground=estilo["fuerte"], activeforeground="#FFFFFF",
                relief="flat", bd=0,
                font=("Segoe UI", 9, "bold"), cursor="hand2", padx=7
            )
            campana.pack(side="right", padx=2, pady=9)
            self.botones_campanas[gravedad] = campana
        if self._temporizador_campana is not None:
            try:
                self.root.after_cancel(self._temporizador_campana)
            except tk.TclError:
                pass
            self._temporizador_campana = None
        self.actualizar_campana()

        self.boton(
            barra, "Salir", self.cerrar_sesion
        ).pack(side="right", padx=5, pady=9)

        cuerpo = tk.Frame(principal, bg=FONDO)
        cuerpo.pack(fill="both", expand=True)

        menu = tk.Frame(
            cuerpo, bg=self.oscuro, width=210
        )
        menu.pack(side="left", fill="y")
        menu.pack_propagate(False)
        self.menu_lateral = menu

        tk.Label(
            menu, text="MENÚ PRINCIPAL",
            bg=self.oscuro, fg=BLANCO,
            font=("Segoe UI", 10, "bold")
        ).pack(fill="x", padx=12, pady=15)

        menu_canvas = tk.Canvas(
            menu, bg=self.oscuro, highlightthickness=0
        )
        menu_scroll = ttk.Scrollbar(
            menu, orient="vertical",
            command=menu_canvas.yview
        )
        menu_interior = tk.Frame(menu_canvas, bg=self.oscuro)

        menu_interior.bind(
            "<Configure>",
            lambda e: menu_canvas.configure(
                scrollregion=menu_canvas.bbox("all")
            )
        )

        menu_canvas.create_window(
            (0, 0), window=menu_interior, anchor="nw", width=190
        )
        menu_canvas.configure(yscrollcommand=menu_scroll.set)

        menu_canvas.pack(side="left", fill="both", expand=True)
        menu_scroll.pack(side="right", fill="y")

        self.botones_menu = {}
        for opcion in self.obtener_menu():
            boton_menu = tk.Button(
                menu_interior,
                text=opcion,
                command=lambda n=opcion: self.ir(n),
                bg=AMARILLO if opcion == self.vista_actual else self.oscuro,
                fg=GRAFITO if opcion == self.vista_actual else BLANCO,
                activebackground=CIAN,
                activeforeground=GRAFITO,
                font=("Segoe UI", 10, "bold" if opcion == self.vista_actual else "normal"),
                relief="flat", anchor="w",
                cursor="hand2", padx=12, pady=10, bd=0
            )
            boton_menu.pack(fill="x", padx=5, pady=2)
            self.botones_menu[opcion] = boton_menu

        area = tk.Frame(cuerpo, bg=FONDO)
        area.pack(side="left", fill="both", expand=True)
        self.area_principal = area

        self.area_canvas = tk.Canvas(
            area, bg=FONDO, highlightthickness=0
        )
        barra_scroll = ttk.Scrollbar(
            area, orient="vertical",
            command=self.area_canvas.yview
        )

        self.area_canvas.configure(
            yscrollcommand=barra_scroll.set
        )

        barra_scroll.pack(side="right", fill="y")
        self.area_canvas.pack(side="left", fill="both", expand=True)

        self.contenido = tk.Frame(
            self.area_canvas, bg=FONDO, padx=16, pady=16
        )

        self.ventana_contenido = self.area_canvas.create_window(
            (0, 0), window=self.contenido, anchor="nw"
        )

        self.contenido.bind(
            "<Configure>",
            lambda e: self.area_canvas.configure(
                scrollregion=self.area_canvas.bbox("all")
            )
        )

        self.area_canvas.bind(
            "<Configure>",
            lambda e: self.area_canvas.itemconfigure(
                self.ventana_contenido, width=e.width
            )
        )

        self.ir("Inicio")
        self._modo_movil = None
        self._programar_ajuste_responsivo()
        self.root.bind("<Configure>", self._programar_ajuste_responsivo)

    def obtener_alertas_clasificadas(self):
        """Clasifica pendientes y escala a Crítica por gravedad o acumulación."""
        if self.rol == "director":
            registros = self.consultar("""
                SELECT id, tipo, alumno, grupo, fecha, registrado_por, detalle, gravedad, estado
                FROM registros_escolares
                WHERE estado='Pendiente'
                  AND LOWER(tipo) IN ('conducta','reporte','incidencia','autocontrol')
                ORDER BY fecha DESC, id DESC
            """)
        else:
            registros = self.consultar("""
                SELECT id, tipo, alumno, grupo, fecha, registrado_por, detalle, gravedad, estado
                FROM registros_escolares
                WHERE estado='Pendiente' AND registrado_por=%s
                  AND LOWER(tipo) IN ('conducta','reporte','incidencia','autocontrol')
                ORDER BY fecha DESC, id DESC
            """, (self.usuario,))

        grupos = {}
        for registro in registros:
            clave = (str(registro.get("alumno", "")).strip().casefold(),
                     str(registro.get("grupo", "")).strip().casefold())
            grupos.setdefault(clave, []).append(registro)

        criticos = set()
        for clave, elementos in grupos.items():
            altas = sum(1 for x in elementos if str(x.get("gravedad", "")).casefold() == "alta")
            tiene_critica = any(str(x.get("gravedad", "")).casefold() == "crítica" for x in elementos)
            acumulacion_grave = altas >= 3 or (altas >= 2 and len(elementos) >= 4)
            if tiene_critica or acumulacion_grave:
                criticos.add(clave)

        for registro in registros:
            clave = (str(registro.get("alumno", "")).strip().casefold(),
                     str(registro.get("grupo", "")).strip().casefold())
            registro["gravedad_mostrada"] = "Crítica" if clave in criticos else registro.get("gravedad", "Baja")
        return registros, criticos

    def actualizar_campana(self):
        """Actualiza los cuatro contadores; Crítica cuenta alumnos escalados."""
        botones = getattr(self, "botones_campanas", {})
        if not botones:
            return
        temporizador = getattr(self, "_temporizador_campana", None)
        if temporizador is not None:
            try:
                self.root.after_cancel(temporizador)
            except tk.TclError:
                pass
            self._temporizador_campana = None
        try:
            registros, criticos = self.obtener_alertas_clasificadas()
            cantidades = {"Baja": 0, "Media": 0, "Alta": 0, "Crítica": len(criticos)}
            for registro in registros:
                nivel = registro.get("gravedad_mostrada", "Baja")
                if nivel != "Crítica" and nivel in cantidades:
                    cantidades[nivel] += 1
            for gravedad, boton in botones.items():
                if boton.winfo_exists():
                    estilo = COLORES_ALERTA[gravedad]
                    boton.configure(
                        text=f"{estilo['icono']} {cantidades.get(gravedad, 0)}",
                        bg=estilo["fuerte"], fg="#FFFFFF",
                        activebackground=estilo["fuerte"], activeforeground="#FFFFFF"
                    )
        except (mysql.connector.Error, tk.TclError, KeyError):
            pass
        try:
            if any(b.winfo_exists() for b in botones.values()):
                self._temporizador_campana = self.root.after(10000, self.actualizar_campana)
        except tk.TclError:
            pass


    def abrir_alertas_gravedad(self, gravedad):
        self.vista_actual = "Alertas"
        self.limpiar_contenido()
        self.pantalla_alertas(gravedad)

    def cerrar_sesion(self):
        if messagebox.askyesno(
            "Cerrar sesión", "¿Quieres salir de tu cuenta?"
        ):
            if self._temporizador_campana is not None:
                try:
                    self.root.after_cancel(self._temporizador_campana)
                except tk.TclError:
                    pass
                self._temporizador_campana = None
            self.usuario = ""
            self.nombre = ""
            self.rol = ""
            self.mostrar_login()

    def ir(self, nombre):
        solo_director = {
            "Justificantes", "Reportes generales", "Carta compromiso",
            "Creación de usuarios", "Alumnos", "Panel directivo",
            "Administrar usuarios", "Administrar grupos", "Administrar grupos y usuarios",
            "Asignar docentes", "Consultar alumnos", "Consultar reportes",
            "Monitoreo docente"
        }
        solo_docente = {
            "Mis grupos", "Pase de lista", "Registrar retardo/falta",
            "Conducta docente", "Autocontrol", "Registrar incidencia",
            "Justificantes docente", "Mis reportes"
        }

        if nombre in solo_director and self.rol != "director":
            messagebox.showwarning("Acceso restringido", "Esta pantalla es exclusiva de dirección.")
            return
        if nombre in solo_docente and self.rol != "docente":
            messagebox.showwarning("Acceso restringido", "Esta pantalla es exclusiva de docentes.")
            return

        self.vista_actual = nombre
        for opcion, boton_menu in getattr(self, "botones_menu", {}).items():
            seleccionado = opcion == nombre
            boton_menu.configure(
                bg=AMARILLO if seleccionado else self.oscuro,
                fg=GRAFITO if seleccionado else BLANCO,
                font=("Segoe UI", 10, "bold" if seleccionado else "normal")
            )

        self.limpiar_contenido()
        vistas = {
            "Inicio": self.pantalla_inicio,
            "Más opciones": self.pantalla_mas_opciones,
            "Alumnos": self.pantalla_alumnos_admin,
            "Reportes": self.pantalla_reportes if self.rol == "docente" else self.pantalla_reportes_generales,
            "Mis grupos": self.pantalla_grupos,
            "Pase de lista": self.pantalla_pase_lista,
            "Registrar retardo/falta": self.pantalla_retardos,
            "Conducta docente": self.pantalla_conducta,
            "Autocontrol": self.pantalla_autocontrol,
            "Registrar incidencia": self.pantalla_incidencia,
            "Justificantes docente": self.pantalla_justificantes,
            "Mis reportes": self.pantalla_reportes,
            "Retardos y faltas": self.pantalla_director_retardos_faltas,
            "Conducta": self.pantalla_director_conducta,
            "Justificantes": self.pantalla_director_justificantes,
            "Reportes generales": self.pantalla_reportes_generales,
            "Carta compromiso": self.pantalla_carta,
            "Creación de usuarios": self.pantalla_usuarios,
            "Consultar reportes": self.pantalla_reportes,
            "Panel directivo": self.pantalla_directivo,
            "Administrar usuarios": self.pantalla_usuarios,
            "Administrar grupos": self.pantalla_grupos_admin,
            "Administrar grupos y usuarios": self.pantalla_admin_grupos_usuarios,
            "Asignar docentes": self.pantalla_asignar,
            "Consultar alumnos": self.pantalla_alumnos_admin,
            "Monitoreo docente": self.pantalla_monitoreo,
            "Gráficos": self.pantalla_graficas,
            "Gráficas": self.pantalla_graficas,
            "Personalizado": self.pantalla_personalizado,
            "Buscar": self.pantalla_buscar,
            "Avisos": self.pantalla_avisos,
            "Alertas": self.pantalla_alertas,
            "Excel (Importar/Exportar)": self.pantalla_excel,
            "Importar Excel": self.pantalla_excel
        }
        vistas.get(nombre, self.pantalla_inicio)()

    def consultar(self, sql, parametros=(), diccionario=True):
        conexion = conectar()
        try:
            cursor = conexion.cursor(dictionary=diccionario)
            cursor.execute(sql, parametros)
            return cursor.fetchall()
        finally:
            conexion.close()

    def contar(self, tipo=None, estado=None):
        sql = "SELECT COUNT(*) AS total FROM registros_escolares"
        condiciones = []
        parametros = []

        if tipo:
            condiciones.append("tipo=%s")
            parametros.append(tipo)

        if estado:
            condiciones.append("estado=%s")
            parametros.append(estado)

        if self.rol == "docente":
            condiciones.append("registrado_por=%s")
            parametros.append(self.usuario)

        if condiciones:
            sql += " WHERE " + " AND ".join(condiciones)

        filas = self.consultar(sql, parametros)
        return filas[0]["total"]

    def tarjeta(self, padre, encabezado, valor, detalle=""):
        tarjeta = tk.Frame(
            padre, bg=PANEL, padx=16, pady=14,
            highlightbackground=SECUNDARIO,
            highlightthickness=1
        )
        tk.Frame(tarjeta, bg=AMARILLO, height=4).pack(fill="x", pady=(0, 9))
        tarjeta.pack(
            side="left", fill="both", expand=True, padx=5
        )

        tk.Label(
            tarjeta, text=encabezado,
            bg=PANEL, fg=SECUNDARIO,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")

        tk.Label(
            tarjeta, text=str(valor),
            bg=PANEL, fg=TEXTO,
            font=("Segoe UI", 25, "bold")
        ).pack(anchor="w", pady=5)

        if detalle:
            tk.Label(
                tarjeta, text=detalle,
                bg=PANEL, fg=SECUNDARIO,
                wraplength=220, justify="left",
                font=("Segoe UI", 9)
            ).pack(anchor="w")

    def pantalla_mas_opciones(self):
        self.limpiar_contenido()
        self.titulo("Más opciones", "Herramientas secundarias de CECyTEM.")
        if self.rol == "docente":
            opciones = [
                ("Registrar retardo o falta", "Registrar retardo/falta"),
                ("Registrar conducta", "Conducta docente"),
                ("Registrar autocontrol", "Autocontrol"),
                ("Registrar incidencia", "Registrar incidencia"),
                ("Justificantes", "Justificantes docente"),
                ("Buscar alumnos", "Buscar"),
                ("Temas y apariencia", "Personalizado")
            ]
        else:
            opciones = [
                ("Justificantes", "Justificantes"),
                ("Carta compromiso", "Carta compromiso"),
                ("Administrar grupos y usuarios", "Administrar grupos y usuarios"),
                ("Asignar docentes", "Asignar docentes"),
                ("Temas y apariencia", "Personalizado")
            ]
        panel = tk.Frame(self.contenido, bg=FONDO)
        panel.pack(fill="both", expand=True)
        for indice, (etiqueta, destino) in enumerate(opciones):
            fila, columna = divmod(indice, 2)
            tarjeta = tk.Frame(panel, bg=BLANCO, padx=12, pady=12,
                               highlightbackground=CIAN, highlightthickness=1)
            tarjeta.grid(row=fila, column=columna, sticky="nsew", padx=6, pady=6)
            tk.Label(tarjeta, text=etiqueta, bg=BLANCO, fg=self.oscuro,
                     font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 8))
            self.boton(tarjeta, "Abrir", lambda d=destino: self.ir(d)).pack(anchor="e")
        for columna in range(2):
            panel.columnconfigure(columna, weight=1)

    def pantalla_admin_grupos_usuarios(self):
        self.limpiar_contenido()
        self.titulo("Administrar grupos y usuarios",
                    "Selecciona qué apartado deseas administrar.")
        contenedor = tk.Frame(self.contenido, bg=FONDO)
        contenedor.pack(fill="x", pady=10)
        for titulo, descripcion, destino in [
            ("Administrar grupos", "Crear, editar y organizar los grupos escolares.", "Administrar grupos"),
            ("Administrar usuarios", "Crear y administrar cuentas de docentes y dirección.", "Administrar usuarios")
        ]:
            tarjeta = tk.Frame(contenedor, bg=BLANCO, padx=18, pady=16,
                               highlightbackground=CIAN, highlightthickness=1)
            tarjeta.pack(fill="x", pady=7)
            tk.Label(tarjeta, text=titulo, bg=BLANCO, fg=self.oscuro,
                     font=("Segoe UI", 12, "bold")).pack(anchor="w")
            tk.Label(tarjeta, text=descripcion, bg=BLANCO, fg=SECUNDARIO,
                     wraplength=700, justify="left").pack(anchor="w", pady=5)
            self.boton(tarjeta, "Abrir", lambda d=destino: self.ir(d)).pack(anchor="e")

    def pantalla_inicio(self):
        self.titulo(
            "Panel de inicio",
            f"Bienvenido/a, {self.nombre}. "
            "Selecciona una sección para continuar."
        )

        fila = tk.Frame(self.contenido, bg=FONDO)
        fila.pack(fill="x", pady=8)

        try:
            total = self.contar()
            incidencias = self.contar("Incidencia")
            pendientes = self.contar(estado="Pendiente")
        except mysql.connector.Error:
            total = incidencias = pendientes = "—"
#samadhi Cayetano Fonseca:tabla incidencaia
        for titulo, valor, detalle in [
            ("Registros", total, "Registros guardados"),
            ("Incidencias", incidencias, "Incidencias registradas"),
            ("Pendientes", pendientes, "Por revisar")
        ]:
            self.tarjeta(fila, titulo, valor, detalle)

        panel = tk.Frame(self.contenido, bg=BLANCO, padx=18, pady=18)
        panel.pack(fill="x", pady=15)

        tk.Label(
            panel, text="Accesos rápidos",
            bg=BLANCO, fg=self.oscuro,
            font=("Segoe UI", 15, "bold")
        ).pack(anchor="w", pady=(0, 10))

        accesos = (
            ["Pase de lista", "Registrar incidencia",
             "Mis reportes", "Gráficos"]
            if self.rol == "docente"
            else ["Retardos y faltas", "Conducta",
                  "Reportes generales", "Creación de usuarios"]
        )

       
        rejilla = tk.Frame(panel, bg=BLANCO)
        rejilla.pack(anchor="center", pady=4)

        for indice, acceso in enumerate(accesos):
            boton_acceso = self.boton(
                rejilla, acceso,
                lambda a=acceso: self.ir(a)
            )
            boton_acceso.configure(width=22, pady=12)
            boton_acceso.grid(
                row=indice // 2, column=indice % 2,
                padx=8, pady=7, sticky="ew"
            )

        for columna in range(2):
            rejilla.grid_columnconfigure(columna, weight=1, uniform="accesos")

        tk.Label(
            self.contenido,
            text=f"Fecha actual: {date.today().strftime('%d/%m/%Y')}  |  "
                 "Usa el menú lateral para acceder a todas las funciones.",
            bg=FONDO, fg=GRIS
        ).pack(anchor="w", pady=(4, 0))

    

    def pantalla_usuarios(self):
        self.limpiar_contenido()
        self.titulo(
            "Administrar usuarios",
            "Crea cuentas de docentes y directores."
        )

        panel = tk.Frame(self.contenido, bg=BLANCO, padx=20, pady=18)
        panel.pack(fill="x")
        panel.columnconfigure(1, weight=1)

        self.campos = {}

        for i, campo in enumerate(
            ["Nombre completo", "Usuario", "Contraseña", "Rol"]
        ):
            tk.Label(
                panel, text=campo,
                bg=BLANCO, fg=TEXTO,
                font=("Segoe UI", 10, "bold")
            ).grid(row=i, column=0, sticky="w", padx=8, pady=8)

            if campo == "Rol":
                widget = ttk.Combobox(
                    panel, values=["docente", "director"],
                    state="readonly"
                )
                widget.set("docente")
            elif campo == "Contraseña":
                widget = ttk.Entry(panel, show="*")
            else:
                widget = ttk.Entry(panel)

            widget.grid(row=i, column=1, sticky="ew", padx=8, pady=8)
            self.campos[campo] = widget

        self.boton(
            panel, "Crear cuenta", self.crear_usuario
        ).grid(row=4, column=1, sticky="e", padx=8, pady=12)

        self.boton(
            self.contenido, "Ver usuarios",
            lambda: self.mostrar_tabla(
                "Usuarios",
                """SELECT nombre, usuario, rol
                   FROM usuarios ORDER BY nombre"""
            )
        ).pack(anchor="w", pady=12)

    def crear_usuario(self):
        nombre = self.leer_campo("Nombre completo")
        usuario = self.leer_campo("Usuario")
        password = self.leer_campo("Contraseña")
        rol = self.leer_campo("Rol").lower()

        if not nombre or not usuario or not password or rol not in (
            "docente", "director"
        ):
            messagebox.showwarning(
                "Datos incompletos",
                "Completa todos los campos y selecciona un rol válido."
            )
            return


        hash_password = generar_hash_password(password)

        conexion = None

        try:
            conexion = conectar()
            cursor = conexion.cursor()

            cursor.execute(
                "SELECT usuario FROM usuarios WHERE usuario=%s",
                (usuario,)
            )

            if cursor.fetchone():
                messagebox.showwarning(
                    "Usuario existente",
                    "Ya existe una cuenta con ese nombre de usuario."
                )
                return

            cursor.execute("""
                INSERT INTO usuarios (nombre, usuario, password_hash, rol)
                VALUES (%s, %s, %s, %s)
            """, (nombre, usuario, hash_password, rol))

            conexion.commit()

            messagebox.showinfo(
                "Cuenta creada",
                f"Se creó la cuenta de {nombre} con rol {rol}."
            )

            for campo in ("Nombre completo", "Usuario", "Contraseña"):
                self.campos[campo].delete(0, "end")

        except mysql.connector.Error as error:
            messagebox.showerror(
                "Error al crear cuenta",
                f"{error}\n\n"
                "Comprueba las columnas de tu tabla usuarios."
            )

        finally:
            if conexion is not None and conexion.is_connected():
                conexion.close()

    
    def obtener_grupos(self):
        return self.consultar("""
            SELECT id, nombre
            FROM grupos_escolares
            ORDER BY nombre
        """)

    def obtener_mis_grupos(self):
        if self.rol == "director":
            return self.obtener_grupos()

        return self.consultar("""
            SELECT g.id, g.nombre
            FROM grupos_escolares g
            INNER JOIN docente_grupos dg ON dg.grupo_id=g.id
            WHERE dg.docente=%s
            ORDER BY g.nombre
        """, (self.usuario,))

    def pantalla_grupos_admin(self):
        self.limpiar_contenido()
        self.titulo(
            "Administrar grupos",
            "Crea grupos escolares y administra listas con tantos alumnos como necesites."
        )

        panel = tk.Frame(self.contenido, bg=BLANCO, padx=18, pady=18)
        panel.pack(fill="x")

        tk.Label(
            panel, text="Nombre del nuevo grupo",
            bg=BLANCO, fg=TEXTO
        ).pack(anchor="w")

        entrada = ttk.Entry(panel)
        entrada.pack(fill="x", pady=8)

        def crear_grupo():
            nombre = entrada.get().strip().upper()

            if not nombre:
                messagebox.showwarning(
                    "Grupo vacío", "Escribe un nombre de grupo."
                )
                return

            conexion = None
            try:
                conexion = conectar()
                cursor = conexion.cursor()
                cursor.execute("""
                    INSERT INTO grupos_escolares (nombre)
                    VALUES (%s)
                """, (nombre,))
                conexion.commit()
                messagebox.showinfo(
                    "Grupo creado",
                    f"El grupo {nombre} ya está disponible."
                )
                entrada.delete(0, "end")
            except mysql.connector.IntegrityError:
                messagebox.showwarning(
                    "Grupo existente",
                    "Ese grupo ya está registrado."
                )
            except mysql.connector.Error as error:
                messagebox.showerror("Error MySQL", str(error))
            finally:
                if conexion is not None and conexion.is_connected():
                    conexion.close()

        self.boton(panel, "Crear grupo", crear_grupo).pack(anchor="e")

        self.boton(
            self.contenido, "Asignar docentes",
            lambda: self.ir("Asignar docentes")
        ).pack(anchor="w", pady=10)

        self.mostrar_tabla(
            "Grupos disponibles",
            """SELECT g.nombre AS grupo,
                      COUNT(a.id) AS alumnos
               FROM grupos_escolares g
               LEFT JOIN alumnos_escolares a
                 ON a.grupo_id=g.id AND a.activo=TRUE
               GROUP BY g.id, g.nombre
               ORDER BY g.nombre"""
        )

    def pantalla_asignar(self):
        self.limpiar_contenido()
        self.titulo(
            "Asignar docentes",
            "Relaciona un docente con uno o varios grupos."
        )
#Leticia Alexa Silva Velasco
        try:
            docentes = self.consultar("""
                SELECT usuario, nombre
                FROM usuarios
                WHERE LOWER(rol)='docente'
                ORDER BY nombre
            """)

            grupos = self.obtener_grupos()

        except mysql.connector.Error as error:
            messagebox.showerror("Error MySQL", str(error))
            return

        if not docentes or not grupos:
            tk.Label(
                self.contenido,
                text="Primero crea al menos un docente y un grupo.",
                bg=FONDO, fg=GRIS
            ).pack(anchor="w")
            return

        panel = tk.Frame(self.contenido, bg=BLANCO, padx=18, pady=18)
        panel.pack(fill="x")

        tk.Label(
            panel, text="Docente",
            bg=BLANCO, fg=TEXTO
        ).pack(anchor="w")

        mapa_docentes = {
            f"{d['nombre']} ({d['usuario']})": d["usuario"]
            for d in docentes
        }

        docente = ttk.Combobox(
            panel, values=list(mapa_docentes), state="readonly"
        )
        docente.pack(fill="x", pady=6)

        tk.Label(
            panel, text="Grupo",
            bg=BLANCO, fg=TEXTO
        ).pack(anchor="w")

        mapa_grupos = {
            g["nombre"]: g["id"] for g in grupos
        }

        grupo = ttk.Combobox(
            panel, values=list(mapa_grupos), state="readonly"
        )
        grupo.pack(fill="x", pady=6)

        def asignar():
            if not docente.get() or not grupo.get():
                messagebox.showwarning(
                    "Datos incompletos",
                    "Selecciona un docente y un grupo."
                )
                return

            conexion = None
            try:
                conexion = conectar()
                cursor = conexion.cursor()
                cursor.execute("""
                    INSERT IGNORE INTO docente_grupos
                    (docente, grupo_id)
                    VALUES (%s, %s)
                """, (
                    mapa_docentes[docente.get()],
                    mapa_grupos[grupo.get()]
                ))
                conexion.commit()

                messagebox.showinfo(
                    "Asignación guardada",
                    "El docente ya puede consultar la lista del grupo."
                )

            except mysql.connector.Error as error:
                messagebox.showerror("Error MySQL", str(error))

            finally:
                if conexion is not None and conexion.is_connected():
                    conexion.close()

        self.boton(panel, "Asignar grupo", asignar).pack(anchor="e")

        self.mostrar_tabla(
            "Asignaciones actuales",
            """SELECT u.nombre AS docente, g.nombre AS grupo
               FROM docente_grupos dg
               INNER JOIN usuarios u ON u.usuario=dg.docente
               INNER JOIN grupos_escolares g ON g.id=dg.grupo_id
               ORDER BY u.nombre, g.nombre"""
        )

    def pantalla_grupos(self):
        self.limpiar_contenido()
        self.titulo(
            "Mis grupos",
            "Selecciona un grupo para consultar y administrar sus alumnos."
        )

        try:
            grupos = self.obtener_mis_grupos()
        except mysql.connector.Error as error:
            messagebox.showerror("Error MySQL", str(error))
            return

        if not grupos:
            tk.Label(
                self.contenido,
                text="Todavía no tienes grupos asignados. "
                     "Solicita a dirección que te asigne uno.",
                bg=FONDO, fg=GRIS, wraplength=750
            ).pack(anchor="w")
            return

        for grupo in grupos:
            panel = tk.Frame(
                self.contenido, bg=BLANCO, padx=18, pady=15
            )
            panel.pack(fill="x", pady=6)

            try:
                cantidad = self.consultar("""
                    SELECT COUNT(*) AS total
                    FROM alumnos_escolares
                    WHERE grupo_id=%s AND activo=TRUE
                """, (grupo["id"],))[0]["total"]
            except mysql.connector.Error:
                cantidad = 0

            tk.Label(
                panel,
                text=f"Grupo {grupo['nombre']}  ·  {cantidad} alumnos",
                bg=BLANCO, fg=self.oscuro,
                font=("Segoe UI", 13, "bold")
            ).pack(side="left")

            self.boton(
                panel, "Abrir lista",
                lambda g=grupo: self.abrir_alumnos(g)
            ).pack(side="right")

    def abrir_alumnos(self, grupo):
        """Editor de lista sin límite fijo de 30 lugares."""
        self.grupo_seleccionado = grupo
        self.limpiar_contenido()
        self.titulo(
            f"Lista del grupo {grupo['nombre']}",
            "Agrega nuevos apartados o elimina alumnos de la lista activa. El historial se conserva."
        )

        try:
            alumnos = self.consultar("""
                SELECT id, numero_lista, nombre
                FROM alumnos_escolares
                WHERE grupo_id=%s AND activo=TRUE
                ORDER BY numero_lista
            """, (grupo["id"],))
        except mysql.connector.Error as error:
            messagebox.showerror("Error MySQL", str(error))
            return

        panel = tk.Frame(self.contenido, bg=BLANCO, padx=14, pady=14)
        panel.pack(fill="x")
        self.alumnos_lista = []
        self.alumnos_eliminados = set()
        ultimo_numero = max([a["numero_lista"] for a in alumnos], default=0)
        cantidad_inicial = max(30, ultimo_numero)
        self.ultimo_numero_lista = cantidad_inicial

        def agregar_apartado(numero=None, nombre=""):
            if numero is None:
                self.ultimo_numero_lista += 1
                numero = self.ultimo_numero_lista
            fila = tk.Frame(panel, bg=BLANCO)
            fila.pack(fill="x", pady=3)
            tk.Label(
                fila, text=f"{numero:02d}.", bg=BLANCO, fg=GRIS,
                width=5, anchor="w"
            ).pack(side="left")
            entrada = ttk.Entry(fila)
            entrada.pack(side="left", fill="x", expand=True, padx=(0, 8))
            if nombre:
                entrada.insert(0, nombre)
            def eliminar_apartado():
                if not messagebox.askyesno(
                    "Eliminar alumno de la lista",
                    f"¿Deseas eliminar el apartado {numero} de la lista del grupo {grupo['nombre']}?\n\n"
                    "El alumno dejará de aparecer en la lista activa. Su historial se conservará."
                ):
                    return
                self.alumnos_eliminados.add(numero)
                self.alumnos_lista[:] = [item for item in self.alumnos_lista if item[0] != numero]
                fila.destroy()

            tk.Button(
                fila, text="Eliminar", command=eliminar_apartado,
                bg="#DC2626", fg="#FFFFFF", activebackground="#B91C1C",
                activeforeground="#FFFFFF", relief="flat", cursor="hand2",
                padx=10
            ).pack(side="right")
            self.alumnos_lista.append((numero, entrada))

        por_numero = {a["numero_lista"]: a for a in alumnos}
        for numero in range(1, cantidad_inicial + 1):
            existente = por_numero.get(numero)
            agregar_apartado(numero, existente["nombre"] if existente else "")

        controles = tk.Frame(self.contenido, bg=FONDO)
        controles.pack(fill="x", pady=8)
        self.boton(
            controles, "+ Agregar alumno", agregar_apartado
        ).pack(side="left")
        self.boton(
            controles, "Guardar lista de alumnos", self.guardar_lista_alumnos
        ).pack(side="right")
        self.boton(
            self.contenido, "Pasar lista",
            lambda: self.ir("Pase de lista")
        ).pack(anchor="e", pady=4)


    def guardar_lista_alumnos(self):
        grupo = self.grupo_seleccionado

        if not grupo:
            return

        nombres = [
            (numero, entrada.get().strip())
            for numero, entrada in self.alumnos_lista
        ]

        nombres_ocupados = [n for _, n in nombres if n]

        if len(nombres_ocupados) != len(set(
            n.casefold() for n in nombres_ocupados
        )):
            messagebox.showwarning(
                "Nombres repetidos",
                "Revisa los nombres duplicados de la lista."
            )
            return

        conexion = None

        try:
            conexion = conectar()
            cursor = conexion.cursor()

            for numero, nombre in nombres:
                cursor.execute("""
                    SELECT id
                    FROM alumnos_escolares
                    WHERE grupo_id=%s AND numero_lista=%s
                """, (grupo["id"], numero))

                existente = cursor.fetchone()

                if nombre and existente:
                    cursor.execute("""
                        UPDATE alumnos_escolares
                        SET nombre=%s, activo=TRUE
                        WHERE id=%s
                    """, (nombre, existente[0]))

                elif nombre:
                    cursor.execute("""
                        INSERT INTO alumnos_escolares
                        (grupo_id, numero_lista, nombre)
                        VALUES (%s, %s, %s)
                    """, (grupo["id"], numero, nombre))

                elif existente:
                    cursor.execute("""
                        UPDATE alumnos_escolares
                        SET activo=FALSE
                        WHERE id=%s
                    """, (existente[0],))

            for numero in getattr(self, "alumnos_eliminados", set()):
                cursor.execute("""
                    UPDATE alumnos_escolares
                    SET activo=FALSE
                    WHERE grupo_id=%s AND numero_lista=%s
                """, (grupo["id"], numero))

            conexion.commit()

            messagebox.showinfo(
                "Lista guardada",
                "Se guardaron los cambios. Los alumnos eliminados ya no aparecerán en la lista activa y su historial se conserva."
            )

        except mysql.connector.Error as error:
            if conexion is not None:
                conexion.rollback()
            messagebox.showerror("Error al guardar", str(error))

        finally:
            if conexion is not None and conexion.is_connected():
                conexion.close()

    def pantalla_alumnos_admin(self):
        self.mostrar_tabla(
            "Alumnos registrados",
            """SELECT g.nombre AS grupo, a.numero_lista,
                      a.nombre AS alumno
               FROM alumnos_escolares a
               INNER JOIN grupos_escolares g ON g.id=a.grupo_id
               WHERE a.activo=TRUE
               ORDER BY g.nombre, a.numero_lista"""
        )

    
    def pantalla_pase_lista(self):
        self.limpiar_contenido()
        self.titulo(
            "Pase de lista",
            "Edita los nombres, agrega o quita apartados y registra la asistencia. "
            "La lista puede crecer según las necesidades del grupo."
        )

        try:
            grupos = self.obtener_mis_grupos()
        except mysql.connector.Error as error:
            messagebox.showerror("Error MySQL", str(error))
            return
        if not grupos:
            tk.Label(
                self.contenido,
                text="No tienes grupos asignados. Solicita a dirección una asignación.",
                bg=FONDO, fg=GRIS
            ).pack(anchor="w")
            return

        panel = tk.Frame(self.contenido, bg=BLANCO, padx=14, pady=12)
        panel.pack(fill="x", pady=(0, 10))
        tk.Label(panel, text="Grupo", bg=BLANCO, fg=TEXTO).pack(side="left", padx=(0, 8))
        mapa = {g["nombre"]: g for g in grupos}
        seleccion = ttk.Combobox(panel, values=list(mapa), state="readonly", width=13)
        seleccion.pack(side="left")
        seleccion.set(grupos[0]["nombre"])
        tk.Label(panel, text="Fecha", bg=BLANCO, fg=TEXTO).pack(side="left", padx=(15, 5))
        fecha = ttk.Entry(panel, width=12)
        fecha.insert(0, date.today().isoformat())
        fecha.pack(side="left")

        contenedor = tk.Frame(self.contenido, bg=FONDO)
        contenedor.pack(fill="both", expand=True)
        encabezado = tk.Frame(contenedor, bg=self.oscuro, padx=8, pady=8)
        encabezado.pack(fill="x")
        for texto, ancho in [("N.º", 5), ("Alumno (editable)", 30), ("Acción / asistencia", 23), ("Detalle", 25), ("", 9)]:
            tk.Label(encabezado, text=texto, bg=self.oscuro, fg=BLANCO,
                     font=("Segoe UI", 9, "bold"), width=ancho, anchor="w").pack(side="left", padx=3)

        lista = tk.Frame(contenedor, bg=FONDO)
        lista.pack(fill="x")
        filas = {}
        eliminados = set()
        opciones = ["Asistencia", "Falta", "Retardo", "Justificante", "Conducta", "Reporte", "Incidencia", "Autocontrol"]

        def crear_fila(numero, alumno=None, anterior=None):
            fila = tk.Frame(lista, bg=BLANCO, padx=7, pady=4,
                            highlightbackground="#BFDBFE", highlightthickness=1)
            fila.pack(fill="x", pady=1)
            tk.Label(fila, text=f"{numero:02d}", bg=BLANCO, fg=self.oscuro,
                     width=5, anchor="w", font=("Segoe UI", 9, "bold")).pack(side="left", padx=3)
            entrada_nombre = ttk.Entry(fila)
            entrada_nombre.pack(side="left", fill="x", expand=True, padx=3)
            if alumno:
                entrada_nombre.insert(0, alumno["nombre"])
            estado_previo = anterior["estado"] if anterior else "Presente"
            estado_inicial = "Asistencia" if estado_previo == "Presente" else estado_previo
            accion = tk.StringVar(value=estado_inicial if estado_inicial in opciones else "Asistencia")
            combo = ttk.Combobox(fila, textvariable=accion, values=opciones,
                                 state="readonly", width=21)
            combo.pack(side="left", padx=3)
            detalle = ttk.Entry(fila)
            detalle.pack(side="left", fill="x", expand=True, padx=3)
            if anterior and anterior.get("observaciones"):
                detalle.insert(0, anterior["observaciones"])

            def quitar():
                if not messagebox.askyesno("Quitar apartado", f"¿Quitar el lugar {numero} de esta lista? El historial anterior se conservará."):
                    return
                if alumno:
                    eliminados.add(numero)
                filas.pop(numero, None)
                fila.destroy()

            tk.Button(fila, text="Quitar", command=quitar, bg="#FEE2E2", fg="#991B1B",
                      relief="flat", cursor="hand2", padx=7).pack(side="right", padx=3)
            filas[numero] = {"nombre": entrada_nombre, "accion": accion,
                             "detalle": detalle, "alumno": alumno}

        def agregar_fila():
            numero = max(list(filas.keys()) + list(eliminados), default=0) + 1
            crear_fila(numero)

        def cargar():
            for widget in lista.winfo_children():
                widget.destroy()
            filas.clear()
            eliminados.clear()
            try:
                datetime.strptime(fecha.get().strip(), "%Y-%m-%d")
            except ValueError:
                messagebox.showwarning("Fecha inválida", "Usa el formato AAAA-MM-DD.")
                return
            grupo = mapa[seleccion.get()]
            try:
                alumnos = self.consultar("""
                    SELECT id, numero_lista, nombre
                    FROM alumnos_escolares
                    WHERE grupo_id=%s AND activo=TRUE
                    ORDER BY numero_lista
                """, (grupo["id"],))
                anteriores = self.consultar("""
                    SELECT alumno_id, estado, observaciones
                    FROM asistencias_escolares
                    WHERE grupo_id=%s AND fecha=%s
                """, (grupo["id"], fecha.get().strip()))
            except mysql.connector.Error as error:
                messagebox.showerror("Error MySQL", str(error))
                return
            por_numero = {a["numero_lista"]: a for a in alumnos}
            previos = {a["alumno_id"]: a for a in anteriores}
            ultimo = max([a["numero_lista"] for a in alumnos], default=0)
            for numero in range(1, max(30, ultimo) + 1):
                alumno = por_numero.get(numero)
                anterior = previos.get(alumno["id"]) if alumno else None
                crear_fila(numero, alumno, anterior)
            tk.Label(lista,
                     text="Autocontrol inicia como Baja; Conducta e Incidencia como Media; Reporte como Alta. Puedes ajustar la gravedad en el siguiente paso.",
                     bg=FONDO, fg=GRIS, wraplength=900, justify="left").pack(anchor="w", pady=8)

        def guardar():
            if seleccion.get() not in mapa:
                messagebox.showwarning("Grupo inválido", "Selecciona un grupo válido.")
                return
            grupo = mapa[seleccion.get()]
            try:
                ids_permitidos = {g["id"] for g in self.obtener_mis_grupos()}
            except mysql.connector.Error as error:
                messagebox.showerror("Error MySQL", str(error))
                return
            if grupo["id"] not in ids_permitidos:
                messagebox.showerror("Acceso restringido", "El grupo ya no está asignado a tu cuenta.")
                return
            fecha_texto = fecha.get().strip()
            try:
                datetime.strptime(fecha_texto, "%Y-%m-%d")
            except ValueError:
                messagebox.showwarning("Fecha inválida", "Usa el formato AAAA-MM-DD.")
                return

            conexion = None
            incidencias_pendientes = []
            try:
                conexion = conectar()
                cursor = conexion.cursor()
                for numero in sorted(eliminados):
                    cursor.execute("UPDATE alumnos_escolares SET activo=FALSE WHERE grupo_id=%s AND numero_lista=%s", (grupo["id"], numero))
                for numero, datos in sorted(filas.items()):
                    nombre = datos["nombre"].get().strip()
                    if not nombre:
                        cursor.execute("UPDATE alumnos_escolares SET activo=FALSE WHERE grupo_id=%s AND numero_lista=%s", (grupo["id"], numero))
                        continue
                    cursor.execute("SELECT id FROM alumnos_escolares WHERE grupo_id=%s AND numero_lista=%s", (grupo["id"], numero))
                    existente = cursor.fetchone()
                    if existente:
                        alumno_id = existente[0]
                        cursor.execute("UPDATE alumnos_escolares SET nombre=%s, activo=TRUE WHERE id=%s", (nombre, alumno_id))
                    else:
                        cursor.execute("INSERT INTO alumnos_escolares (grupo_id, numero_lista, nombre) VALUES (%s,%s,%s)", (grupo["id"], numero, nombre))
                        alumno_id = cursor.lastrowid

                    accion = datos["accion"].get()
                    detalle = datos["detalle"].get().strip()
                    if accion in ("Asistencia", "Falta", "Retardo", "Justificante"):
                        estado = {"Asistencia": "Presente"}.get(accion, accion)
                        cursor.execute("""INSERT INTO asistencias_escolares
                            (alumno_id, grupo_id, fecha, estado, docente, observaciones)
                            VALUES (%s,%s,%s,%s,%s,%s)
                            ON DUPLICATE KEY UPDATE estado=VALUES(estado), docente=VALUES(docente), observaciones=VALUES(observaciones)""",
                            (alumno_id, grupo["id"], fecha_texto, estado, self.usuario, detalle or None))
                        if estado in ("Falta", "Retardo"):
                            cursor.execute("""INSERT INTO registros_escolares
                                (tipo, alumno, grupo, fecha, detalle, registrado_por)
                                VALUES (%s,%s,%s,%s,%s,%s)""",
                                (estado, nombre, grupo["nombre"], fecha_texto,
                                 detalle or f"Estado de asistencia: {estado}", self.usuario))
                    else:
                        gravedad_inicial = {
                            "Autocontrol": "Baja", "Conducta": "Media",
                            "Incidencia": "Media", "Reporte": "Alta"
                        }.get(accion, "Media")
                        cursor.execute("""INSERT INTO registros_escolares
                            (tipo, alumno, grupo, fecha, detalle, gravedad, registrado_por)
                            VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                            (accion, nombre, grupo["nombre"], fecha_texto,
                             detalle or None, gravedad_inicial, self.usuario))
                        if accion in ("Conducta", "Reporte", "Incidencia", "Autocontrol"):
                            incidencias_pendientes.append({
                                "id": cursor.lastrowid, "alumno": nombre,
                                "grupo": grupo["nombre"], "fecha": fecha_texto,
                                "tipo": accion, "detalle": detalle or ""
                            })
                conexion.commit()
                messagebox.showinfo("Lista guardada", f"Se guardó la lista de {grupo['nombre']} para el {fecha_texto}.")
                self.actualizar_campana()
                if incidencias_pendientes:
                    self.mostrar_detalles_incidencias_lista(incidencias_pendientes)
                else:
                    self.ir("Inicio")
            except (mysql.connector.Error, ValueError) as error:
                if conexion:
                    conexion.rollback()
                messagebox.showerror("Error al guardar", str(error))
            finally:
                if conexion is not None and conexion.is_connected():
                    conexion.close()

        controles = tk.Frame(self.contenido, bg=FONDO)
        controles.pack(fill="x", pady=8)
        self.boton(controles, "+ Agregar alumno", agregar_fila).pack(side="left")
        self.boton(controles, "Cargar lista", cargar).pack(side="left", padx=8)
        self.boton(self.contenido, "Guardar lista", guardar).pack(anchor="e", pady=12)
        self.boton(self.contenido, "Registrar incidencia detallada", lambda: self.ir("Registrar incidencia")).pack(anchor="e", pady=(0, 10))
        cargar()


    def mostrar_detalles_incidencias_lista(self, incidencias, indice=0):
        """Solicita detalles y gravedad uno por uno; los datos básicos ya vienen de la lista."""
        if indice >= len(incidencias):
            messagebox.showinfo("Incidencias completadas", "Se terminaron de capturar los detalles de todos los alumnos.")
            self.ir("Inicio")
            return

        registro = incidencias[indice]
        ventana = tk.Toplevel(self.root)
        ventana.title(f"Detalle de incidencia {indice + 1} de {len(incidencias)}")
        ventana.configure(bg=FONDO)
        ventana.transient(self.root)
        ventana.grab_set()
        ventana.geometry("560x470")
        ventana.resizable(True, True)

        tk.Label(ventana, text=f"Alumno {indice + 1} de {len(incidencias)}",
                 bg=FONDO, fg=self.oscuro, font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=20, pady=(18, 10))
        datos = tk.Frame(ventana, bg=BLANCO, padx=14, pady=12)
        datos.pack(fill="x", padx=20, pady=5)
        for etiqueta, valor in [
            ("Alumno", registro["alumno"]), ("Grupo", registro["grupo"]),
            ("Fecha", registro["fecha"]), ("Tipo", registro["tipo"]),
            ("Registró", self.nombre or self.usuario)
        ]:
            tk.Label(datos, text=f"{etiqueta}: {valor}", bg=BLANCO, fg=TEXTO,
                     font=("Segoe UI", 10, "bold" if etiqueta == "Alumno" else "normal")).pack(anchor="w", pady=2)

        tk.Label(ventana, text="Gravedad", bg=FONDO, fg=TEXTO,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=20, pady=(12, 3))
        gravedad = ttk.Combobox(ventana, values=["Baja", "Media", "Alta", "Crítica"], state="readonly")
        gravedad_inicial = {"Autocontrol": "Baja", "Conducta": "Media", "Incidencia": "Media", "Reporte": "Alta"}
        gravedad.set(gravedad_inicial.get(registro.get("tipo"), "Media"))
        gravedad.pack(fill="x", padx=20)
        tk.Label(ventana, text="Detalles de lo ocurrido", bg=FONDO, fg=TEXTO,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=20, pady=(12, 3))
        detalle = tk.Text(ventana, height=5, wrap="word", bg=BLANCO, fg=TEXTO, relief="solid", bd=1)
        detalle.pack(fill="both", expand=True, padx=20)
        if registro.get("detalle"):
            detalle.insert("1.0", registro["detalle"])

        botones = tk.Frame(ventana, bg=FONDO)
        botones.pack(fill="x", padx=20, pady=15)

        def avanzar(guardar=True):
            texto = detalle.get("1.0", "end").strip()
            if guardar and not texto:
                messagebox.showwarning("Falta el detalle", "Agrega una breve descripción para continuar.", parent=ventana)
                return
            conexion = None
            try:
                conexion = conectar()
                cursor = conexion.cursor()
                if guardar:
                    cursor.execute("""UPDATE registros_escolares
                        SET detalle=%s, gravedad=%s, estado='Pendiente'
                        WHERE id=%s""", (texto, gravedad.get(), registro["id"]))
                else:
                    cursor.execute("""UPDATE registros_escolares
                        SET gravedad=%s, estado='Pendiente' WHERE id=%s""",
                        (gravedad.get(), registro["id"]))
                conexion.commit()
            except mysql.connector.Error as error:
                if conexion:
                    conexion.rollback()
                messagebox.showerror("Error al guardar detalle", str(error), parent=ventana)
                return
            finally:
                if conexion is not None and conexion.is_connected():
                    conexion.close()
            ventana.destroy()
            self.actualizar_campana()
            self.mostrar_detalles_incidencias_lista(incidencias, indice + 1)

        tk.Button(botones, text="Omitir detalle", command=lambda: avanzar(False),
                  bg="#E2E8F0", fg=TEXTO, relief="flat", padx=12, pady=8).pack(side="left")
        tk.Button(botones, text="Guardar y siguiente", command=avanzar,
                  bg=self.color, fg=BLANCO, relief="flat", padx=14, pady=8).pack(side="right")

    def formulario(self, campos, tipo, boton_texto="Guardar"):
        self.limpiar_contenido()
        self.titulo(
            self.vista_actual,
            "Completa los datos y guarda el registro."
        )

        panel = tk.Frame(self.contenido, bg=BLANCO, padx=20, pady=18)
        panel.pack(fill="x")
        panel.columnconfigure(1, weight=1)

        self.campos = {}

        campos_texto = {
            "Motivo detallado", "Descripción",
            "Acción tomada", "Observaciones",
            "Decisión / justificación", "Compromisos del alumno",
            "Motivo"
        }

        opciones = {
            "Grupo": self.nombres_mis_grupos(),
            "Tipo de problema": [
                "Autocontrol", "Conducta", "Conflicto", "Otro"
            ],
            "Tipo de acción": [
                "Amonestación", "Citatorio Tutor",
                "Suspensión Temporal", "Seguimiento Psicológico"
            ],
            "Estado": [
                "Pendiente", "Revisado", "Resuelto", "Justificado"
            ],
            "Gravedad": ["Baja", "Media", "Alta", "Crítica"],
            "Tipo de justificante": [
                "Médico", "Familiar", "Académico", "Otro"
            ]
        }

        for i, campo in enumerate(campos):
            tk.Label(
                panel, text=campo,
                bg=BLANCO, fg=TEXTO,
                font=("Segoe UI", 10, "bold"),
                anchor="w"
            ).grid(
                row=i, column=0, sticky="nw",
                padx=(0, 15), pady=8
            )

            if campo in campos_texto:
                widget = tk.Text(
                    panel, height=4, wrap="word",
                    bg=self.claro, fg=TEXTO,
                    font=("Segoe UI", 10), relief="flat"
                )

            elif campo in opciones:
                valores = opciones[campo]

                widget = ttk.Combobox(
                    panel, values=valores,
                    state="readonly" if valores else "disabled"
                )

                if campo == "Grupo" and valores:
                    widget.set(valores[0])
                elif campo == "Gravedad" and valores:
                    widget.set("Media")

            else:
                widget = ttk.Entry(panel)

                if campo == "Fecha":
                    widget.insert(0, date.today().isoformat())

                if campo == "Hora":
                    widget.insert(
                        0, datetime.now().strftime("%H:%M")
                    )

            widget.grid(
                row=i, column=1, sticky="ew", pady=6
            )
            self.campos[campo] = widget

        self.boton(
            panel, boton_texto,
            lambda: self.guardar_registro(tipo)
        ).grid(
            row=len(campos), column=1,
            sticky="e", pady=(18, 0)
        )

    def nombres_mis_grupos(self):
        try:
            return [g["nombre"] for g in self.obtener_mis_grupos()]
        except mysql.connector.Error:
            return []

    def guardar_registro(self, tipo):
        alumno = self.leer_campo("Alumno")

        if not alumno:
            messagebox.showwarning(
                "Campo obligatorio", "Escribe el nombre del alumno."
            )
            return

        fecha = self.leer_campo("Fecha") or date.today().isoformat()
        hora = self.leer_campo("Hora") or None

        try:
            datetime.strptime(fecha, "%Y-%m-%d")

            if hora:
                formato = "%H:%M:%S" if len(hora) == 8 else "%H:%M"
                datetime.strptime(hora, formato)
                if len(hora) == 5:
                    hora += ":00"

        except ValueError:
            messagebox.showwarning(
                "Fecha u hora incorrecta",
                "Usa fecha AAAA-MM-DD y hora HH:MM."
            )
            return

        grupo = self.leer_campo("Grupo")

        if grupo and grupo not in self.nombres_mis_grupos():
            messagebox.showerror(
                "Grupo no autorizado",
                "No tienes permiso para registrar información en ese grupo."
            )
            return
        if "Grupo" in self.campos and not grupo:
            messagebox.showwarning(
                "Grupo obligatorio",
                "Selecciona un grupo asignado antes de guardar."
            )
            return

        detalle = next(
            (
                self.leer_campo(c) for c in (
                    "Motivo detallado", "Descripción",
                    "Observaciones", "Motivo",
                    "Decisión / justificación"
                ) if self.leer_campo(c)
            ),
            ""
        )
        accion = next(
            (
                self.leer_campo(c) for c in (
                    "Tipo de acción", "Acción tomada",
                    "Tipo de problema", "Tipo de justificante"
                ) if self.leer_campo(c)
            ),
            ""
        )

        evidencia = (
            self.leer_campo("Evidencia (ruta)")
            or self.leer_campo("Archivo de evidencia")
        )

        seguimiento = (
            self.leer_campo("Necesita seguimiento con tutor")
            .lower() in ("si", "sí", "1", "true")
        )
        gravedad_por_tipo = {
            "autocontrol": "Baja",
            "conducta": "Media",
            "incidencia": "Media",
            "reporte": "Alta"
        }
        gravedad = self.leer_campo("Gravedad") or gravedad_por_tipo.get(tipo.lower(), "Baja")
        if gravedad not in ("Baja", "Media", "Alta", "Crítica"):
            gravedad = gravedad_por_tipo.get(tipo.lower(), "Baja")

        conexion = None

        try:
            conexion = conectar()
            cursor = conexion.cursor()

            cursor.execute("""
                INSERT INTO registros_escolares
                (tipo, alumno, grupo, fecha, hora, detalle,
                 accion, evidencia, seguimiento, gravedad, registrado_por)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                tipo, alumno, grupo or None, fecha, hora,
                detalle or None, accion or None,
                evidencia or None, seguimiento, gravedad, self.usuario
            ))

            conexion.commit()

            messagebox.showinfo(
                "Registro guardado",
                f"Se guardó correctamente. Folio: {cursor.lastrowid}"
            )
            self.actualizar_campana()
            self.ir("Inicio")

        except mysql.connector.Error as error:
            messagebox.showerror("Error MySQL", str(error))

        finally:
            if conexion is not None and conexion.is_connected():
                conexion.close()

    def pantalla_retardos(self):
        self.formulario(
            ["Alumno", "Grupo", "Fecha", "Hora", "Observaciones"],
            "Retardo/Falta", "Guardar registro"
        )

    def pantalla_conducta(self):
        self.formulario(
            ["Alumno", "Grupo", "Fecha",
             "Tipo de problema", "Gravedad", "Motivo detallado",
             "Acción tomada"],
            "Conducta", "Guardar reporte"
        )

    def pantalla_autocontrol(self):
        self.formulario(
            ["Alumno", "Grupo", "Fecha", "Tipo de problema", "Gravedad",
             "Descripción", "Acción tomada"],
            "Autocontrol", "Guardar reporte"
        )

    def pantalla_incidencia(self):
        self.formulario(
            ["Alumno", "Grupo", "Fecha", "Hora", "Gravedad",
             "Motivo detallado", "Evidencia (ruta)",
             "Acción tomada"],
            "Incidencia", "Guardar incidencia"
        )

    def pantalla_justificantes(self):
        self.formulario(
            ["Alumno", "Grupo", "Fecha",
             "Tipo de justificante",
             "Archivo de evidencia", "Observaciones"],
            "Justificante", "Guardar justificante"
        )


    def mostrar_tabla(self, titulo, sql, parametros=()):
        self.limpiar_contenido()
        self.titulo(titulo, "Información consultada en MySQL.")

        marco = tk.Frame(self.contenido, bg=BLANCO)
        marco.pack(fill="both", expand=True)

        conexion = None

        try:
            conexion = conectar()
            cursor = conexion.cursor(dictionary=True)
            cursor.execute(sql, parametros)
            filas = cursor.fetchall()

            if not filas:
                tk.Label(
                    marco, text="No hay registros para mostrar.",
                    bg=BLANCO, fg=GRIS, padx=15, pady=20
                ).pack(anchor="w")
                return

            columnas = list(filas[0].keys())

            tabla_marco = tk.Frame(marco, bg=BLANCO)
            tabla_marco.pack(fill="both", expand=True)

            tabla = ttk.Treeview(
                tabla_marco, columns=columnas,
                show="headings"
            )

            sy = ttk.Scrollbar(
                tabla_marco, orient="vertical",
                command=tabla.yview
            )
            sx = ttk.Scrollbar(
                tabla_marco, orient="horizontal",
                command=tabla.xview
            )

            tabla.configure(
                yscrollcommand=sy.set,
                xscrollcommand=sx.set
            )

            sy.pack(side="right", fill="y")
            sx.pack(side="bottom", fill="x")
            tabla.pack(fill="both", expand=True)

            for columna in columnas:
                tabla.heading(
                    columna,
                    text=columna.replace("_", " ").title()
                )
                tabla.column(
                    columna, width=150,
                    minwidth=90, stretch=True
                )

            for fila in filas:
                tabla.insert(
                    "", "end",
                    values=[
                        "" if v is None else str(v)
                        for v in fila.values()
                    ]
                )

        except mysql.connector.Error as error:
            messagebox.showerror("Error de consulta", str(error))

        finally:
            if conexion is not None and conexion.is_connected():
                conexion.close()

    def pantalla_reportes(self):
        if self.rol == "docente":
            self.mostrar_tabla(
                "Mis reportes",
                """SELECT id, tipo, alumno, grupo, fecha,
                          estado, creado_en
                   FROM registros_escolares
                   WHERE registrado_por=%s
                   ORDER BY creado_en DESC""",
                (self.usuario,)
            )
        else:
            self.mostrar_tabla(
                "Consultar reportes",
                """SELECT id, tipo, alumno, grupo, fecha,
                          estado, registrado_por, creado_en
                   FROM registros_escolares
                   ORDER BY creado_en DESC"""
            )

    def pantalla_directivo(self):
        self.limpiar_contenido()
        self.titulo(
            "Panel directivo",
            "Resumen general de la actividad escolar."
        )

        distribucion = tk.Frame(self.contenido, bg=FONDO)
        distribucion.pack(fill="both", expand=True, pady=8)

        izquierda = tk.Frame(
            distribucion, bg=AZUL, width=220, padx=14, pady=16
        )
        izquierda.pack(side="left", fill="y", padx=(0, 12))
        izquierda.pack_propagate(False)

        tk.Label(
            izquierda, text="HERRAMIENTAS", bg=AZUL, fg=BLANCO,
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(0, 12))

        self.boton(
            izquierda, "Importar Excel", lambda: self.ir("Excel (Importar/Exportar)"),
            color=AZUL_BOTON
        ).pack(fill="x", pady=5)
        self.boton(
            izquierda, "Exportar Excel", self.exportar_excel,
            color=AZUL_BOTON
        ).pack(fill="x", pady=5)
        self.boton(
            izquierda, "Ver gráficas", lambda: self.ir("Gráficas"),
            color=AZUL_BOTON
        ).pack(fill="x", pady=5)
        self.boton(
            izquierda, "Temas y apariencia", lambda: self.ir("Personalizado"),
            color=AZUL_BOTON
        ).pack(fill="x", pady=5)

        derecha = tk.Frame(distribucion, bg=FONDO)
        derecha.pack(side="left", fill="both", expand=True)

        fila = tk.Frame(derecha, bg=FONDO)
        fila.pack(fill="x", pady=(0, 8))

        try:
            total = self.contar()
            incidencias = self.contar("Incidencia")
            pendientes = self.contar(estado="Pendiente")
        except mysql.connector.Error:
            total = incidencias = pendientes = "—"

        for encabezado, valor, detalle in [
            ("Registros", total, "Actividad acumulada"),
            ("Incidencias", incidencias, "Incidencias registradas"),
            ("Pendientes", pendientes, "Requieren revisión")
        ]:
            self.tarjeta(fila, encabezado, valor, detalle)

        self.boton(
            derecha, "Consultar reportes",
            lambda: self.ir("Consultar reportes")
        ).pack(anchor="w", pady=(0, 8))

        
        panel_grupos = tk.Frame(
            derecha, bg=BLANCO, padx=14, pady=14,
            highlightbackground=CIAN, highlightthickness=1
        )
        panel_grupos.pack(fill="x", pady=(8, 12))

        tk.Label(
            panel_grupos, text="INCIDENCIAS POR GRUPO",
            bg=BLANCO, fg=self.oscuro,
            font=("Segoe UI", 13, "bold")
        ).pack(anchor="w")
        tk.Label(
            panel_grupos,
            text="Selecciona un grupo para consultar solamente sus incidencias, o abre el listado completo.",
            bg=BLANCO, fg=GRIS, wraplength=760,
            justify="left", font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(3, 10))

        self.boton(
            panel_grupos, "Ver todas las incidencias",
            lambda: self.pantalla_incidencias_grupo(), color=AMARILLO
        ).pack(anchor="w", pady=(0, 9))

        rejilla_grupos = tk.Frame(panel_grupos, bg=BLANCO)
        rejilla_grupos.pack(fill="x")
        try:
            grupos_disponibles = self.obtener_grupos()
        except mysql.connector.Error as error:
            grupos_disponibles = []
            tk.Label(
                rejilla_grupos,
                text=f"No se pudieron cargar los grupos: {error}",
                bg=BLANCO, fg="#DC2626", wraplength=700,
                justify="left"
            ).pack(anchor="w")

        if grupos_disponibles:
            for indice, grupo in enumerate(grupos_disponibles):
                boton_grupo = self.boton(
                    rejilla_grupos,
                    str(grupo.get("nombre", "Grupo")),
                    lambda g=grupo: self.pantalla_incidencias_grupo(g),
                    color=AZUL_BOTON
                )
                boton_grupo.grid(
                    row=indice // 3, column=indice % 3,
                    padx=4, pady=4, sticky="ew"
                )
            for columna in range(3):
                rejilla_grupos.grid_columnconfigure(columna, weight=1)
        else:
            tk.Label(
                rejilla_grupos, text="Todavía no hay grupos registrados.",
                bg=BLANCO, fg=GRIS, font=("Segoe UI", 10)
            ).pack(anchor="w")

        self.marco_graficas = None
        self.grafica_tipo("Registros por tipo", padre=derecha)

    def pantalla_incidencias_grupo(self, grupo=None):
        """Abre incidencias filtradas por grupo o muestra todas las incidencias."""
        tipos = "LOWER(tipo) IN ('conducta', 'reporte', 'incidencia', 'autocontrol')"
        if grupo:
            nombre_grupo = str(grupo.get("nombre", "Grupo"))
            self.tabla_directiva_con_detalle(
                f"Incidencias del grupo {nombre_grupo}",
                f"""SELECT id, alumno, grupo, tipo, fecha, gravedad, detalle,
                          accion, seguimiento, estado, registrado_por
                   FROM registros_escolares
                   WHERE {tipos} AND grupo=%s
                   ORDER BY fecha DESC, creado_en DESC""",
                (nombre_grupo,)
            )
        else:
            self.tabla_directiva_con_detalle(
                "Todas las incidencias",
                f"""SELECT id, alumno, grupo, tipo, fecha, gravedad, detalle,
                          accion, seguimiento, estado, registrado_por
                   FROM registros_escolares
                   WHERE {tipos}
                   ORDER BY fecha DESC, creado_en DESC"""
            )

    def tabla_directiva_con_detalle(self, encabezado, sql, parametros=()):
        self.limpiar_contenido()
        self.titulo(encabezado, "Selecciona un registro para consultar el estatus y los detalles del alumno.")
        marco = tk.Frame(self.contenido, bg=BLANCO, padx=10, pady=10)
        marco.pack(fill="both", expand=True)

        try:
            filas = self.consultar(sql, parametros)
        except mysql.connector.Error as error:
            messagebox.showerror("Error MySQL", str(error))
            return

        if not filas:
            tk.Label(marco, text="No hay registros para mostrar.", bg=BLANCO,
                     fg=GRIS, font=("Segoe UI", 11)).pack(anchor="w", padx=8, pady=12)
            return

        columnas = list(filas[0].keys())
        tabla = ttk.Treeview(marco, columns=columnas, show="headings", height=12)
        sy = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
        sx = ttk.Scrollbar(marco, orient="horizontal", command=tabla.xview)
        tabla.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        sy.pack(side="right", fill="y")
        sx.pack(side="bottom", fill="x")
        tabla.pack(fill="both", expand=True)

        for columna in columnas:
            tabla.heading(columna, text=columna.replace("_", " ").title())
            tabla.column(columna, width=145, minwidth=90, stretch=True)

        por_id = {}
        for fila in filas:
            iid = str(fila["id"])
            tabla.insert("", "end", iid=iid,
                         values=["" if v is None else str(v) for v in fila.values()])
            por_id[iid] = fila

        detalle = tk.Frame(marco, bg=self.claro, padx=14, pady=12)
        detalle.pack(fill="x", pady=(10, 0))
        etiqueta = tk.Label(detalle, text="Selecciona un alumno de la tabla para ver su información.",
                            bg=self.claro, fg=self.oscuro, justify="left",
                            anchor="w", wraplength=900, font=("Segoe UI", 10))
        etiqueta.pack(fill="x")

        def mostrar_detalle(event=None):
            seleccion = tabla.selection()
            if not seleccion:
                return
            fila = por_id.get(seleccion[0])
            if fila:
                campos = [
                    f"{clave.replace('_', ' ').title()}: {valor if valor not in (None, '') else 'Sin información'}"
                    for clave, valor in fila.items() if clave != "id"
                ]
                etiqueta.configure(text="\n".join(campos))

        tabla.bind("<<TreeviewSelect>>", mostrar_detalle)

    def pantalla_director_retardos_faltas(self):
        self.tabla_directiva_con_detalle(
            "Retardos y faltas",
            """SELECT id, alumno, grupo, tipo, fecha, hora, estado, detalle,
                      registrado_por
               FROM registros_escolares
               WHERE LOWER(tipo) IN ('retardo', 'falta', 'retardo/falta')
               ORDER BY fecha DESC, creado_en DESC"""
        )

    def pantalla_director_conducta(self):
        self.tabla_directiva_con_detalle(
            "Conducta",
            """SELECT id, alumno, grupo, tipo, fecha, gravedad, detalle, accion,
                      seguimiento, estado, registrado_por
               FROM registros_escolares
               WHERE LOWER(tipo) IN ('conducta', 'incidencia', 'autocontrol')
               ORDER BY fecha DESC, creado_en DESC"""
        )

    def pantalla_director_justificantes(self):
        self.tabla_directiva_con_detalle(
            "Justificantes",
            """SELECT id, alumno, grupo, fecha, accion, detalle, evidencia,
                      estado, registrado_por
               FROM registros_escolares
               WHERE LOWER(tipo)='justificante'
               ORDER BY fecha DESC, creado_en DESC"""
        )

    def pantalla_reportes_generales(self):
        self.mostrar_tabla(
            "Reportes generales",
            """SELECT id, tipo, alumno, grupo, fecha, hora, gravedad, estado, detalle,
                      accion, registrado_por, creado_en
               FROM registros_escolares
               ORDER BY creado_en DESC"""
        )

    def pantalla_monitoreo(self):
        self.mostrar_tabla(
            "Monitoreo docente",
            """SELECT registrado_por AS docente,
                      COUNT(*) AS registros,
                      SUM(tipo='Incidencia') AS incidencias,
                      MAX(creado_en) AS ultimo_registro
               FROM registros_escolares
               GROUP BY registrado_por
               ORDER BY registros DESC"""
        )


    def pantalla_alertas(self, gravedad=None):
        """Muestra pendientes clasificados y seguimiento de alumnos acumulados."""
        self.limpiar_contenido()
        titulo = f"Alertas: {gravedad}" if gravedad else "Centro de alertas"
        self.titulo(titulo, "Las alertas críticas se activan por una gravedad crítica o por acumulación de alertas altas.")
        estilo_pantalla = COLORES_ALERTA.get(gravedad) if gravedad else None
        if estilo_pantalla:
            encabezado = tk.Frame(
                self.contenido, bg=estilo_pantalla["fuerte"],
                padx=16, pady=12, highlightthickness=2,
                highlightbackground=estilo_pantalla["fuerte"]
            )
            encabezado.pack(fill="x", pady=(4, 10))
            tk.Label(
                encabezado, text=f"{estilo_pantalla['icono']}  ALERTAS {gravedad.upper()}",
                bg=estilo_pantalla["fuerte"], fg="#FFFFFF",
                font=("Segoe UI", 16, "bold")
            ).pack(anchor="w")
            tk.Label(
                encabezado,
                text="Esta pantalla conserva el color de su campanita aunque cambies el tema del sistema.",
                bg=estilo_pantalla["fuerte"], fg="#FFFFFF",
                font=("Segoe UI", 9, "bold")
            ).pack(anchor="w", pady=(3, 0))
        try:
            registros, criticos = self.obtener_alertas_clasificadas()
            if gravedad:
                pendientes = [r for r in registros if r.get("gravedad_mostrada") == gravedad]
            else:
                pendientes = registros
            if gravedad == "Crítica":
                repetidos = [
                    {"alumno": r.get("alumno"), "grupo": r.get("grupo"), "total": sum(
                        1 for x in registros
                        if str(x.get("alumno", "")).strip().casefold() == str(r.get("alumno", "")).strip().casefold()
                        and str(x.get("grupo", "")).strip().casefold() == str(r.get("grupo", "")).strip().casefold()
                    )}
                    for r in pendientes
                ]
                vistos = set()
                repetidos = [x for x in repetidos if not ((x["alumno"], x["grupo"]) in vistos or vistos.add((x["alumno"], x["grupo"]))) ]
            else:
                repetidos = []
                for r in registros:
                    clave = (str(r.get("alumno", "")).strip().casefold(), str(r.get("grupo", "")).strip().casefold())
                    if clave in criticos:
                        repetidos.append({"alumno": r.get("alumno"), "grupo": r.get("grupo"), "total": sum(1 for x in registros if (str(x.get("alumno", "")).strip().casefold(), str(x.get("grupo", "")).strip().casefold()) == clave)})
                vistos = set()
                repetidos = [x for x in repetidos if not ((x["alumno"], x["grupo"]) in vistos or vistos.add((x["alumno"], x["grupo"]))) ]
        except mysql.connector.Error as error:
            messagebox.showerror("Error al consultar alertas", str(error))
            return

        resumen = tk.Frame(self.contenido, bg=FONDO)
        resumen.pack(fill="x", pady=5)
        self.tarjeta(resumen, "Pendientes", len(pendientes), "Registros por revisar")
        self.tarjeta(resumen, "Alumnos críticos", len(criticos), "Acumulación o gravedad crítica")

        if repetidos:
            tk.Label(self.contenido, text="Alumnos en seguimiento crítico", bg=FONDO,
                     fg=self.oscuro, font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(16, 6))
            for fila in repetidos:
                estilo_critico = COLORES_ALERTA["Crítica"]
                tarjeta = tk.Frame(self.contenido, bg=estilo_critico["suave"], padx=12, pady=10,
                                   highlightbackground=estilo_critico["fuerte"], highlightthickness=2)
                tarjeta.pack(fill="x", pady=4)
                tk.Label(tarjeta, text=f"{fila['alumno']} · Grupo {fila.get('grupo') or 'Sin grupo'}",
                         bg=estilo_critico["suave"], fg=estilo_critico["texto"],
                         font=("Segoe UI", 11, "bold")).pack(anchor="w")
                tk.Label(tarjeta, text=f"{fila['total']} alertas pendientes asociadas",
                         bg=estilo_critico["suave"], fg=estilo_critico["texto"],
                         font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(3, 0))

        tk.Label(self.contenido, text="Registros pendientes", bg=FONDO, fg=self.oscuro,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(16, 6))
        if pendientes:
            for aviso in pendientes:
                nivel = aviso.get("gravedad_mostrada", aviso.get("gravedad", "Baja"))
                estilo_nivel = COLORES_ALERTA.get(nivel, COLORES_ALERTA["Baja"])
                fondo_tarjeta = estilo_nivel["suave"] if gravedad else BLANCO
                tarjeta = tk.Frame(self.contenido, bg=fondo_tarjeta, padx=12, pady=9,
                                   highlightbackground=estilo_nivel["fuerte"], highlightthickness=2)
                tarjeta.pack(fill="x", pady=4)
                tk.Label(tarjeta, text=f"#{aviso['id']} · {aviso['tipo']} · {aviso['alumno']} · {nivel}",
                         bg=fondo_tarjeta, fg=estilo_nivel["texto"],
                         font=("Segoe UI", 10, "bold")).pack(anchor="w")
                tk.Label(tarjeta, text=f"Grupo: {aviso.get('grupo') or '—'} | Fecha: {aviso['fecha']} | Registró: {aviso.get('registrado_por') or '—'}",
                         bg=fondo_tarjeta, fg=estilo_nivel["texto"] if gravedad else GRIS).pack(anchor="w")
                if aviso.get("detalle"):
                    tk.Label(tarjeta, text=str(aviso["detalle"]), bg=fondo_tarjeta,
                             fg=estilo_nivel["texto"] if gravedad else TEXTO,
                             wraplength=900, justify="left").pack(anchor="w", pady=(3, 0))
                if nivel == "Crítica":
                    tk.Label(tarjeta, text="SEGUIMIENTO PRIORITARIO: alumno con acumulación de alertas graves.",
                             bg=fondo_tarjeta, fg=estilo_nivel["texto"],
                             font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(4, 0))
                acciones = tk.Frame(tarjeta, bg=fondo_tarjeta)
                acciones.pack(fill="x", pady=(7, 0))
                tk.Button(acciones, text="Marcar como resuelta",
                          command=lambda registro_id=aviso["id"]: self.resolver_incidencia(registro_id, gravedad),
                          bg=estilo_nivel["fuerte"], fg="#FFFFFF",
                          activebackground=estilo_nivel["fuerte"], activeforeground="#FFFFFF",
                          relief="flat", bd=0, padx=12, pady=6, cursor="hand2",
                          font=("Segoe UI", 9, "bold")).pack(side="right")
        else:
            tk.Label(self.contenido, text="No hay registros pendientes en esta categoría.",
                     bg=FONDO, fg=GRIS).pack(anchor="w")

        
        
        
        if estilo_pantalla:
            color_fuerte = estilo_pantalla["fuerte"]
            color_suave = estilo_pantalla["suave"]
            color_tarjeta = "#FFFFFF"

            if getattr(self, "area_canvas", None):
                self.area_canvas.configure(bg=color_fuerte)
            self.contenido.configure(bg=color_suave)

            def colorear_superficie(widget):
                try:
                    fondo_widget = widget.cget("bg")
                    if fondo_widget == FONDO:
                        widget.configure(bg=color_suave)
                    elif fondo_widget in (PANEL, BLANCO):
                        widget.configure(bg=color_tarjeta)
                except (tk.TclError, TypeError):
                    pass
                for hijo in widget.winfo_children():
                    colorear_superficie(hijo)

            colorear_superficie(self.contenido)
            self.contenido.configure(bg=color_suave)


    def resolver_incidencia(self, registro_id, gravedad=None):
        """Marca el aviso como resuelto sin eliminar el registro del historial."""
        if not messagebox.askyesno("Resolver incidencia",
                                   "¿Confirmas que esta incidencia ya fue atendida?"):
            return
        conexion = None
        try:
            conexion = conectar()
            cursor = conexion.cursor()
            if self.rol == "director":
                cursor.execute(
                    "UPDATE registros_escolares SET estado='Resuelto' WHERE id=%s AND estado='Pendiente'",
                    (registro_id,)
                )
            else:
                cursor.execute(
                    "UPDATE registros_escolares SET estado='Resuelto' WHERE id=%s AND registrado_por=%s AND estado='Pendiente'",
                    (registro_id, self.usuario)
                )
            conexion.commit()
            if cursor.rowcount == 0:
                messagebox.showinfo("Sin cambios", "La incidencia ya no está pendiente o no tienes permiso para resolverla.")
        except mysql.connector.Error as error:
            if conexion:
                conexion.rollback()
            messagebox.showerror("No se pudo resolver", str(error))
            return
        finally:
            if conexion is not None and conexion.is_connected():
                conexion.close()
        self.actualizar_campana()
        self.pantalla_alertas(gravedad)

    def pantalla_excel(self):
        self.limpiar_contenido()
        self.titulo(
            "Importación y exportación de Excel",
            "Carga listas de alumnos desde .xlsx y exporta reportes del sistema."
        )
        if not EXCEL_DISPONIBLE:
            tk.Label(
                self.contenido,
                text="Instala la dependencia con: pip install openpyxl",
                bg=FONDO, fg=ROJO, font=("Segoe UI", 11, "bold")
            ).pack(anchor="w", pady=10)
            return

        panel = tk.Frame(self.contenido, bg=BLANCO, padx=16, pady=16)
        panel.pack(fill="x", pady=8)
        tk.Label(panel, text="Carga masiva de alumnos", bg=BLANCO,
                 fg=self.oscuro, font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(
            panel,
            text="La hoja debe llamarse Alumnos y contener las columnas Grupo, Numero_lista y Alumno.",
            bg=BLANCO, fg=GRIS, wraplength=900, justify="left"
        ).pack(anchor="w", pady=6)
        self.boton(panel, "Descargar plantilla Excel", self.descargar_plantilla_excel).pack(anchor="w", pady=4)
        self.boton(panel, "Importar alumnos desde Excel", self.importar_alumnos_excel).pack(anchor="w", pady=4)

        panel_exportar = tk.Frame(self.contenido, bg=BLANCO, padx=16, pady=16)
        panel_exportar.pack(fill="x", pady=8)
        tk.Label(panel_exportar, text="Exportar información", bg=BLANCO,
                 fg=self.oscuro, font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(
            panel_exportar,
            text="Crea un libro con alumnos, asistencias y registros. Los docentes solo exportan los datos de sus grupos.",
            bg=BLANCO, fg=GRIS, wraplength=900, justify="left"
        ).pack(anchor="w", pady=6)
        self.boton(panel_exportar, "Exportar información a Excel", self.exportar_excel).pack(anchor="w", pady=4)

    def descargar_plantilla_excel(self):
        if not EXCEL_DISPONIBLE:
            messagebox.showerror("Falta openpyxl", "Ejecuta: pip install openpyxl")
            return
        ruta = filedialog.asksaveasfilename(
            title="Guardar plantilla de alumnos", defaultextension=".xlsx",
            filetypes=[("Libro de Excel", "*.xlsx")]
        )
        if not ruta:
            return
        libro = Workbook()
        hoja = libro.active
        hoja.title = "Alumnos"
        hoja.append(["Grupo", "Numero_lista", "Alumno"])
        hoja.append(["1A", 1, "Nombre completo del alumno"])
        for celda in hoja[1]:
            celda.font = Font(bold=True, color="FFFFFF")
            celda.fill = PatternFill("solid", fgColor="0D3B66")
        hoja.column_dimensions["A"].width = 18
        hoja.column_dimensions["B"].width = 18
        hoja.column_dimensions["C"].width = 38
        try:
            libro.save(ruta)
            messagebox.showinfo("Plantilla creada", "La plantilla se guardó correctamente.")
        except (OSError, PermissionError) as error:
            messagebox.showerror("Error al guardar", str(error))

    def importar_alumnos_excel(self):
        if not EXCEL_DISPONIBLE:
            messagebox.showerror("Falta openpyxl", "Ejecuta: pip install openpyxl")
            return
        ruta = filedialog.askopenfilename(
            title="Selecciona el archivo Excel", filetypes=[("Libro de Excel", "*.xlsx")]
        )
        if not ruta:
            return
        try:
            libro = load_workbook(ruta, read_only=True, data_only=True)
            if "Alumnos" not in libro.sheetnames:
                libro.close()
                raise ValueError("El archivo debe incluir una hoja llamada Alumnos.")
            hoja = libro["Alumnos"]
            primera = next(hoja.iter_rows(min_row=1, max_row=1, values_only=True), None)
            encabezados = [str(x or "").strip().casefold() for x in (primera or ())]
            requeridos = ("grupo", "numero_lista", "alumno")
            if not all(x in encabezados for x in requeridos):
                libro.close()
                raise ValueError("Las columnas requeridas son Grupo, Numero_lista y Alumno.")
            indices = {x: encabezados.index(x) for x in requeridos}
            filas = []
            for n_fila, valores in enumerate(hoja.iter_rows(min_row=2, values_only=True), start=2):
                grupo = str(valores[indices["grupo"]] or "").strip().upper()
                nombre = str(valores[indices["alumno"]] or "").strip()
                numero_original = valores[indices["numero_lista"]]
                if not grupo and not nombre and numero_original is None:
                    continue
                if not grupo or not nombre or numero_original is None:
                    raise ValueError(f"Faltan datos en la fila {n_fila}.")
                try:
                    numero = int(numero_original)
                except (ValueError, TypeError):
                    raise ValueError(f"Numero_lista inválido en la fila {n_fila}.")
                if numero < 1 or numero > 30:
                    raise ValueError(f"El número de lista de la fila {n_fila} debe estar entre 1 y 30.")
                filas.append((grupo, numero, nombre))
            libro.close()
            if not filas:
                raise ValueError("No hay alumnos para importar.")
            llaves = [(g, n) for g, n, _ in filas]
            if len(llaves) != len(set(llaves)):
                raise ValueError("Hay números de lista repetidos dentro de un mismo grupo.")
        except (OSError, ValueError, TypeError, KeyError, IndexError, StopIteration) as error:
            messagebox.showerror("Archivo no válido", str(error))
            return

        conexion = None
        nuevos = 0
        actualizados = 0
        try:
            conexion = conectar()
            cursor = conexion.cursor(dictionary=True)
            grupos_docente = None
            if self.rol == "docente":
                cursor.execute("""
                    SELECT g.nombre
                    FROM grupos_escolares g
                    INNER JOIN docente_grupos dg ON dg.grupo_id=g.id
                    WHERE dg.docente=%s
                """, (self.usuario,))
                grupos_docente = {x["nombre"] for x in cursor.fetchall()}

            for grupo, numero, nombre in filas:
                if grupos_docente is not None and grupo not in grupos_docente:
                    raise ValueError(f"No tienes asignado el grupo {grupo}; se canceló toda la importación.")
                cursor.execute("SELECT id FROM grupos_escolares WHERE nombre=%s", (grupo,))
                encontrado = cursor.fetchone()
                if not encontrado:
                    if self.rol != "director":
                        raise ValueError(f"El grupo {grupo} no existe. Solicita a dirección que lo registre.")
                    cursor.execute("INSERT INTO grupos_escolares (nombre) VALUES (%s)", (grupo,))
                    grupo_id = cursor.lastrowid
                else:
                    grupo_id = encontrado["id"]
                cursor.execute("""
                    SELECT id FROM alumnos_escolares
                    WHERE grupo_id=%s AND numero_lista=%s
                """, (grupo_id, numero))
                alumno = cursor.fetchone()
                if alumno:
                    cursor.execute(
                        "UPDATE alumnos_escolares SET nombre=%s, activo=TRUE WHERE id=%s",
                        (nombre, alumno["id"])
                    )
                    actualizados += 1
                else:
                    cursor.execute("""
                        INSERT INTO alumnos_escolares
                        (grupo_id, numero_lista, nombre, activo)
                        VALUES (%s, %s, %s, TRUE)
                    """, (grupo_id, numero, nombre))
                    nuevos += 1
            conexion.commit()
            messagebox.showinfo(
                "Importación completada",
                f"Alumnos nuevos: {nuevos}\\\\nAlumnos actualizados: {actualizados}\\\\nTotal procesado: {len(filas)}"
            )
        except (mysql.connector.Error, ValueError) as error:
            if conexion is not None:
                conexion.rollback()
            messagebox.showerror("Importación cancelada", str(error))
        finally:
            if conexion is not None and conexion.is_connected():
                conexion.close()

    def exportar_excel(self):
        if not EXCEL_DISPONIBLE:
            messagebox.showerror("Falta openpyxl", "Ejecuta: pip install openpyxl")
            return
        ruta = filedialog.asksaveasfilename(
            title="Exportar información escolar", defaultextension=".xlsx",
            filetypes=[("Libro de Excel", "*.xlsx")]
        )
        if not ruta:
            return
        conexion = None
        try:
            conexion = conectar()
            cursor = conexion.cursor()
            libro = Workbook()
            alumnos = libro.active
            alumnos.title = "Alumnos"
            alumnos.append(["Grupo", "Numero_lista", "Alumno", "Activo"])
            sql = """
                SELECT g.nombre, a.numero_lista, a.nombre, a.activo
                FROM alumnos_escolares a
                INNER JOIN grupos_escolares g ON g.id=a.grupo_id
            """
            params = ()
            if self.rol == "docente":
                sql += """
                    INNER JOIN docente_grupos dg ON dg.grupo_id=g.id
                    WHERE dg.docente=%s
                """
                params = (self.usuario,)
            sql += " ORDER BY g.nombre, a.numero_lista"
            cursor.execute(sql, params)
            for fila in cursor.fetchall():
                alumnos.append(list(fila))

            asistencias = libro.create_sheet("Asistencias")
            asistencias.append(["Alumno", "Grupo", "Fecha", "Estado", "Docente", "Observaciones"])
            sql = """
                SELECT a.nombre, g.nombre, x.fecha, x.estado, x.docente, x.observaciones
                FROM asistencias_escolares x
                INNER JOIN alumnos_escolares a ON a.id=x.alumno_id
                INNER JOIN grupos_escolares g ON g.id=x.grupo_id
            """
            params = ()
            if self.rol == "docente":
                sql += " WHERE x.docente=%s"
                params = (self.usuario,)
            sql += " ORDER BY x.fecha DESC"
            cursor.execute(sql, params)
            for fila in cursor.fetchall():
                asistencias.append(list(fila))

            registros = libro.create_sheet("Registros")
            registros.append(["ID", "Tipo", "Alumno", "Grupo", "Fecha", "Hora",
                              "Detalle", "Accion", "Estado", "Registrado_por"])
            sql = """
                SELECT id, tipo, alumno, grupo, fecha, hora, detalle,
                       accion, estado, registrado_por
                FROM registros_escolares
            """
            params = ()
            if self.rol == "docente":
                sql += " WHERE registrado_por=%s"
                params = (self.usuario,)
            sql += " ORDER BY fecha DESC, id DESC"
            cursor.execute(sql, params)
            for fila in cursor.fetchall():
                registros.append(list(fila))

            for hoja in libro.worksheets:
                hoja.freeze_panes = "A2"
                hoja.auto_filter.ref = hoja.dimensions
                for celda in hoja[1]:
                    celda.font = Font(bold=True, color="FFFFFF")
                    celda.fill = PatternFill("solid", fgColor="0D3B66")
                for columna in hoja.columns:
                    letra = columna[0].column_letter
                    ancho = min(max(max(len(str(c.value or "")) for c in columna) + 2, 12), 42)
                    hoja.column_dimensions[letra].width = ancho
            libro.save(ruta)
            messagebox.showinfo(
                "Exportación completada",
                "Se exportaron alumnos, asistencias y registros a un libro Excel."
            )
        except (mysql.connector.Error, OSError, PermissionError) as error:
            messagebox.showerror("Error de exportación", str(error))
        finally:
            if conexion is not None and conexion.is_connected():
                conexion.close()

    def pantalla_avisos(self):
        self.limpiar_contenido()
        self.titulo(
            "Notificaciones",
            "Novedades escolares recientes y asuntos pendientes. "
            "Se muestran registros de asistencia, retardos, faltas, conducta, reportes e incidencias."
        )
        try:
            if self.rol == "director":
                sql = """SELECT id, tipo, alumno, grupo, fecha, estado,
                                registrado_por, creado_en, detalle
                         FROM registros_escolares
                         WHERE estado='Pendiente'
                            OR creado_en >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                         ORDER BY creado_en DESC LIMIT 250"""
                filas = self.consultar(sql)
            else:
                sql = """SELECT id, tipo, alumno, grupo, fecha, estado,
                                registrado_por, creado_en, detalle
                         FROM registros_escolares
                         WHERE (registrado_por=%s)
                           AND (estado='Pendiente'
                            OR creado_en >= DATE_SUB(NOW(), INTERVAL 7 DAY))
                         ORDER BY creado_en DESC LIMIT 250"""
                filas = self.consultar(sql, (self.usuario,))
        except mysql.connector.Error as error:
            messagebox.showerror("Error MySQL", str(error))
            return

        if not filas:
            tk.Label(self.contenido, text="No hay novedades recientes ni notificaciones pendientes.",
                     bg=FONDO, fg=GRIS, font=("Segoe UI", 11)).pack(anchor="w", pady=12)
            return

        for aviso in filas:
            tarjeta = tk.Frame(self.contenido, bg=BLANCO, padx=14, pady=11,
                               highlightbackground="#BFDBFE", highlightthickness=1)
            tarjeta.pack(fill="x", pady=5)
            titulo = f"{aviso['tipo']} · {aviso['alumno']}"
            tk.Label(tarjeta, text=titulo, bg=BLANCO, fg=self.oscuro,
                     font=("Segoe UI", 11, "bold"), anchor="w").pack(fill="x")
            meta = f"Grupo: {aviso.get('grupo') or 'Sin grupo'}   |   Fecha: {aviso['fecha']}   |   Estado: {aviso.get('estado') or 'Registrado'}"
            tk.Label(tarjeta, text=meta, bg=BLANCO, fg=AZUL_MEDIO,
                     font=("Segoe UI", 9), anchor="w").pack(fill="x", pady=(3, 0))
            detalle = aviso.get("detalle") or "Sin detalle adicional."
            tk.Label(tarjeta, text=detalle, bg=BLANCO, fg=TEXTO,
                     justify="left", anchor="w", wraplength=850).pack(fill="x", pady=(4, 0))
            tk.Label(tarjeta, text=f"Registrado por: {aviso.get('registrado_por') or 'Sistema'}",
                     bg=BLANCO, fg=GRIS, font=("Segoe UI", 8), anchor="w").pack(fill="x", pady=(4, 0))


    def pantalla_decisiones(self):
        self.limpiar_contenido()
        self.titulo(
            "Toma de decisiones",
            "Registra una acción directiva para un alumno."
        )

        panel = tk.Frame(self.contenido, bg=BLANCO, padx=18, pady=18)
        panel.pack(fill="x")
        panel.columnconfigure(1, weight=1)

        self.campos = {}

        campos = [
            "Folio del registro (opcional)",
            "Alumno",
            "Tipo de acción",
            "Decisión / justificación"
        ]

        for i, campo in enumerate(campos):
            tk.Label(
                panel, text=campo,
                bg=BLANCO, fg=TEXTO
            ).grid(row=i, column=0, sticky="nw", padx=8, pady=8)

            if campo == "Tipo de acción":
                widget = ttk.Combobox(
                    panel,
                    values=[
                        "Amonestación", "Citatorio Tutor",
                        "Suspensión Temporal",
                        "Seguimiento Psicológico"
                    ],
                    state="readonly"
                )
            elif campo == "Decisión / justificación":
                widget = tk.Text(panel, height=5, wrap="word")
            else:
                widget = ttk.Entry(panel)

            widget.grid(row=i, column=1, sticky="ew", padx=8, pady=8)
            self.campos[campo] = widget

        self.boton(
            panel, "Guardar decisión",
            self.guardar_decision
        ).grid(row=len(campos), column=1, sticky="e", pady=12)

    def guardar_decision(self):
        alumno = self.leer_campo("Alumno")
        accion = self.leer_campo("Tipo de acción")
        justificacion = self.leer_campo("Decisión / justificación")
        folio = self.leer_campo("Folio del registro (opcional)")

        if not alumno or not accion:
            messagebox.showwarning(
                "Datos incompletos",
                "Escribe el alumno y selecciona una acción."
            )
            return

        try:
            registro_id = int(folio) if folio else None
        except ValueError:
            messagebox.showwarning(
                "Folio inválido", "El folio debe ser numérico."
            )
            return

        conexion = None

        try:
            conexion = conectar()
            cursor = conexion.cursor()

            cursor.execute("""
                INSERT INTO decisiones_directivas
                (registro_id, alumno, accion, justificacion, director)
                VALUES (%s,%s,%s,%s,%s)
            """, (
                registro_id, alumno, accion,
                justificacion or None, self.usuario
            ))

            if registro_id:
                cursor.execute("""
                    UPDATE registros_escolares
                    SET estado='Revisado'
                    WHERE id=%s
                """, (registro_id,))

            conexion.commit()

            messagebox.showinfo(
                "Decisión guardada",
                "La decisión se guardó correctamente."
            )
            self.ir("Inicio")

        except mysql.connector.Error as error:
            if conexion is not None:
                conexion.rollback()
            messagebox.showerror("Error MySQL", str(error))

        finally:
            if conexion is not None and conexion.is_connected():
                conexion.close()

    def pantalla_carta(self):
        self.limpiar_contenido()
        self.titulo(
            "Carta compromiso",
            "Registra los compromisos acordados con el alumno."
        )

        panel = tk.Frame(self.contenido, bg=BLANCO, padx=18, pady=18)
        panel.pack(fill="x")
        panel.columnconfigure(1, weight=1)

        self.campos = {}

        for i, campo in enumerate([
            "Alumno", "Tutor", "Motivo",
            "Fecha", "Compromisos del alumno"
        ]):
            tk.Label(
                panel, text=campo,
                bg=BLANCO, fg=TEXTO
            ).grid(row=i, column=0, sticky="nw", padx=8, pady=8)

            if campo == "Compromisos del alumno" or campo == "Motivo":
                widget = tk.Text(panel, height=4, wrap="word")
            else:
                widget = ttk.Entry(panel)
                if campo == "Fecha":
                    widget.insert(0, date.today().isoformat())

            widget.grid(row=i, column=1, sticky="ew", padx=8, pady=8)
            self.campos[campo] = widget

        self.boton(
            panel, "Guardar carta", self.guardar_carta
        ).grid(row=5, column=1, sticky="e", pady=10)

    def guardar_carta(self):
        alumno = self.leer_campo("Alumno")
        fecha = self.leer_campo("Fecha")
        tutor = self.leer_campo("Tutor")
        motivo = self.leer_campo("Motivo")
        compromisos = self.leer_campo("Compromisos del alumno")

        if not alumno:
            messagebox.showwarning(
                "Dato obligatorio", "Escribe el nombre del alumno."
            )
            return

        try:
            datetime.strptime(fecha, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning(
                "Fecha incorrecta", "Usa el formato AAAA-MM-DD."
            )
            return

        conexion = None

        try:
            conexion = conectar()
            cursor = conexion.cursor()
            cursor.execute("""
                INSERT INTO cartas_compromiso
                (alumno, tutor, motivo, compromisos, fecha, director)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (
                alumno, tutor or None, motivo or None,
                compromisos or None, fecha, self.usuario
            ))
            conexion.commit()

            messagebox.showinfo(
                "Carta guardada",
                "La carta compromiso se guardó en MySQL."
            )
            self.ir("Inicio")

        except mysql.connector.Error as error:
            messagebox.showerror("Error MySQL", str(error))

        finally:
            if conexion is not None and conexion.is_connected():
                conexion.close()

   
    def pantalla_graficas(self):
        self.limpiar_contenido()
        if self.rol == "docente":
            descripcion = "Estadísticas de los alumnos y grupos que tienes asignados."
            opciones = ["Alumnos por grupo", "Asistencia por estado", "Asistencia del día", "Registros por tipo"]
        else:
            descripcion = "Estadísticas generales de alumnos, grupos y actividad de toda la escuela."
            opciones = ["Alumnos por grupo", "Alumnos por grado", "Alumnos activos e inactivos", "Cantidad de grupos", "Resumen de la escuela", "Asistencia por estado", "Registros por tipo"]

        self.titulo("Gráficos", descripcion)
        controles = tk.Frame(self.contenido, bg=FONDO)
        controles.pack(fill="x", pady=8)
        tipo = ttk.Combobox(controles, values=opciones, state="readonly", width=32)
        tipo.set(opciones[0])
        tipo.pack(side="left", padx=(0, 8))

        def dibujar():
            self.limpiar_grafica()
            self.grafica_tipo(tipo.get())

        self.boton(controles, "Mostrar estadísticas", dibujar).pack(side="left")
        self.grafica_tipo(opciones[0])

    def limpiar_grafica(self):
        if self.canvas_grafica is not None:
            try:
                self.canvas_grafica.get_tk_widget().destroy()
            except tk.TclError:
                pass
            self.canvas_grafica = None

    def grafica_tipo(self, tipo, padre=None):
        if not hasattr(self, "marco_graficas"):
            self.marco_graficas = None
        if not GRAFICAS_DISPONIBLES:
            tk.Label(
                self.contenido,
                text="Instala matplotlib con: "
                     "pip install matplotlib",
                bg=FONDO, fg=GRIS
            ).pack(anchor="w", pady=12)
            return

       
        destino = padre or self.contenido
        if (self.marco_graficas is None or
                not self.marco_graficas.winfo_exists() or
                self.marco_graficas.master is not destino):
            self.marco_graficas = tk.Frame(destino, bg=FONDO)
            self.marco_graficas.pack(fill="both", expand=True)
        else:
            for widget in self.marco_graficas.winfo_children():
                widget.destroy()

        try:
            if tipo == "Alumnos por grupo":
                if self.rol == "docente":
                    filas = self.consultar("""
                        SELECT g.nombre AS etiqueta, COUNT(a.id) AS cantidad
                        FROM docente_grupos dg
                        INNER JOIN grupos_escolares g ON g.id=dg.grupo_id
                        LEFT JOIN alumnos_escolares a ON a.grupo_id=g.id AND a.activo=TRUE
                        WHERE dg.docente=%s
                        GROUP BY g.id, g.nombre ORDER BY g.nombre
                    """, (self.usuario,))
                else:
                    filas = self.consultar("""
                        SELECT g.nombre AS etiqueta, COUNT(a.id) AS cantidad
                        FROM grupos_escolares g
                        LEFT JOIN alumnos_escolares a ON a.grupo_id=g.id AND a.activo=TRUE
                        GROUP BY g.id, g.nombre ORDER BY g.nombre
                    """)

            elif tipo == "Alumnos por grado":
                filas = self.consultar("""
                    SELECT CONCAT(LEFT(g.nombre, 1), '° grado') AS etiqueta,
                           COUNT(a.id) AS cantidad
                    FROM grupos_escolares g
                    LEFT JOIN alumnos_escolares a ON a.grupo_id=g.id AND a.activo=TRUE
                    GROUP BY LEFT(g.nombre, 1) ORDER BY etiqueta
                """)

            elif tipo == "Alumnos activos e inactivos":
                filas = self.consultar("""
                    SELECT IF(a.activo=TRUE, 'Activos', 'Inactivos') AS etiqueta,
                           COUNT(*) AS cantidad
                    FROM alumnos_escolares a
                    GROUP BY a.activo ORDER BY a.activo DESC
                """)

            elif tipo == "Cantidad de grupos":
                filas = self.consultar("""
                    SELECT 'Grupos registrados' AS etiqueta, COUNT(*) AS cantidad
                    FROM grupos_escolares
                """)

            elif tipo == "Resumen de la escuela":
                filas = self.consultar("""
                    SELECT 'Alumnos activos' AS etiqueta, COUNT(*) AS cantidad
                    FROM alumnos_escolares WHERE activo=TRUE
                    UNION ALL
                    SELECT 'Grupos' AS etiqueta, COUNT(*) AS cantidad
                    FROM grupos_escolares
                    UNION ALL
                    SELECT 'Docentes' AS etiqueta, COUNT(*) AS cantidad
                    FROM usuarios WHERE LOWER(rol)='docente'
                    UNION ALL
                    SELECT 'Registros escolares' AS etiqueta, COUNT(*) AS cantidad
                    FROM registros_escolares
                """)

            elif tipo == "Registros por tipo":
                if self.rol == "docente":
                    filas = self.consultar("""
                        SELECT tipo AS etiqueta, COUNT(*) AS cantidad
                        FROM registros_escolares WHERE registrado_por=%s
                        GROUP BY tipo ORDER BY cantidad DESC
                    """, (self.usuario,))
                else:
                    filas = self.consultar("""
                        SELECT tipo AS etiqueta, COUNT(*) AS cantidad
                        FROM registros_escolares
                        GROUP BY tipo ORDER BY cantidad DESC
                    """)

            elif tipo == "Asistencia del día":
                if self.rol == "docente":
                    filas = self.consultar("""
                        SELECT ae.estado AS etiqueta, COUNT(*) AS cantidad
                        FROM asistencias_escolares ae
                        INNER JOIN docente_grupos dg ON dg.grupo_id=ae.grupo_id
                        WHERE ae.fecha=%s AND dg.docente=%s
                        GROUP BY ae.estado ORDER BY cantidad DESC
                    """, (date.today().isoformat(), self.usuario))
                else:
                    filas = self.consultar("""
                        SELECT estado AS etiqueta, COUNT(*) AS cantidad
                        FROM asistencias_escolares WHERE fecha=%s
                        GROUP BY estado ORDER BY cantidad DESC
                    """, (date.today().isoformat(),))

            elif tipo == "Asistencia por estado":
                if self.rol == "docente":
                    filas = self.consultar("""
                        SELECT ae.estado AS etiqueta, COUNT(*) AS cantidad
                        FROM asistencias_escolares ae
                        INNER JOIN docente_grupos dg ON dg.grupo_id=ae.grupo_id
                        WHERE dg.docente=%s
                        GROUP BY ae.estado ORDER BY cantidad DESC
                    """, (self.usuario,))
                else:
                    filas = self.consultar("""
                        SELECT estado AS etiqueta, COUNT(*) AS cantidad
                        FROM asistencias_escolares
                        GROUP BY estado ORDER BY cantidad DESC
                    """)

            else:
                filas = self.consultar("""
                    SELECT registrado_por AS etiqueta,
                           COUNT(*) AS cantidad
                    FROM registros_escolares
                    GROUP BY registrado_por
                    ORDER BY cantidad DESC LIMIT 12
                """)

        except mysql.connector.Error as error:
            tk.Label(
                self.marco_graficas,
                text=f"Error al consultar datos: {error}",
                bg=FONDO, fg=ROJO
            ).pack(anchor="w")
            return

        if not filas:
            tk.Label(
                self.marco_graficas,
                text="Todavía no hay datos suficientes para esta gráfica.",
                bg=FONDO, fg=GRIS
            ).pack(anchor="w", pady=15)
            return

        etiquetas = [str(f["etiqueta"]) for f in filas]
        valores = [max(0, int(f["cantidad"] or 0)) for f in filas]

        
        
        datos_positivos = [
            (etiqueta, valor)
            for etiqueta, valor in zip(etiquetas, valores)
            if valor > 0
        ]
        if not datos_positivos:
            tk.Label(
                self.marco_graficas,
                text="Todavía no hay datos registrados para esta gráfica.",
                bg=FONDO, fg=GRIS,
                font=("Segoe UI", 11),
                padx=12, pady=18
            ).pack(anchor="center", pady=20)
            self.canvas_grafica = None
            return

        etiquetas, valores = zip(*datos_positivos)
        etiquetas = list(etiquetas)
        valores = list(valores)

        figura = Figure(figsize=(8, 4.5), dpi=100)
        eje = figura.add_subplot(111)

        colores = [
            self.color, "#00E5FF", "#FF2A6D", "#9D4EDD",
            "#00F5A0", "#FF8C42", "#FCEE0A", "#64748B"
        ]
        wedges, _, _ = eje.pie(
            valores,
            labels=etiquetas,
            autopct="%1.1f%%",
            startangle=90,
            colors=[colores[i % len(colores)] for i in range(len(valores))],
            wedgeprops={"edgecolor": FONDO, "linewidth": 1.5}
        )
        eje.set_title(tipo, color=TEXTO)
        eje.axis("equal")
        figura.tight_layout()

        aviso = tk.Label(
            self.marco_graficas,
            text="Haz clic en una sección del pastel para consultar su cantidad.",
            bg=FONDO, fg=GRIS
        )
        aviso.pack(anchor="w")

        def seleccionar_seccion(evento):
            if evento.artist in wedges:
                i = list(wedges).index(evento.artist)
                aviso.config(text=f"{etiquetas[i]}: {valores[i]} registros")

        canvas = FigureCanvasTkAgg(figura, master=self.marco_graficas)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, pady=8)
        canvas.mpl_connect("pick_event", seleccionar_seccion)
        for wedge in wedges:
            wedge.set_picker(True)
        self.canvas_grafica = canvas

    
    def pantalla_buscar(self):
        self.limpiar_contenido()
        self.titulo(
            "Buscar registros",
            "Busca reportes por nombre de alumno."
        )

        fila = tk.Frame(self.contenido, bg=FONDO)
        fila.pack(fill="x", pady=8)

        entrada = ttk.Entry(fila)
        entrada.pack(
            side="left", fill="x", expand=True, padx=(0, 8)
        )

        def buscar():
            texto = entrada.get().strip()

            if not texto:
                messagebox.showwarning(
                    "Búsqueda vacía",
                    "Escribe el nombre de un alumno."
                )
                return

            if self.rol == "docente":
                sql = """
                    SELECT id, tipo, alumno, grupo, fecha, estado
                    FROM registros_escolares
                    WHERE alumno LIKE %s AND registrado_por=%s
                    ORDER BY creado_en DESC
                """
                params = (f"%{texto}%", self.usuario)
            else:
                sql = """
                    SELECT id, tipo, alumno, grupo, fecha,
                           estado, registrado_por
                    FROM registros_escolares
                    WHERE alumno LIKE %s
                    ORDER BY creado_en DESC
                """
                params = (f"%{texto}%",)

            self.mostrar_tabla(
                "Resultados de búsqueda", sql, params
            )

        self.boton(fila, "Buscar", buscar).pack(side="left")


if __name__ == "__main__":
    root = tk.Tk()
    app = SistemaNezahualcoyotl(root)
    root.mainloop()