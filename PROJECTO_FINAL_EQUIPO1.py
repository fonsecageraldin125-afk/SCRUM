    # ==================== PARTE 3 DE 5 - ESPINO CHAVEZ LEONARDO FRANCO (DESARROLLADOR): USUARIOS, GRUPOS, ALUMNOS Y ASISTENCIA ====================
    
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

        tk.Label(self.contenido, text="Cuentas registradas", bg=FONDO, fg=TEXTO,
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(12, 5))
        marco_usuarios = tk.Frame(self.contenido, bg=PANEL, padx=8, pady=8)
        marco_usuarios.pack(fill="both", expand=True)
        tabla_usuarios = ttk.Treeview(marco_usuarios, columns=("usuario", "nombre", "rol"), show="headings", height=8)
        for col, etiqueta, ancho in [("usuario", "Usuario", 150), ("nombre", "Nombre completo", 260), ("rol", "Rol", 110)]:
            tabla_usuarios.heading(col, text=etiqueta)
            tabla_usuarios.column(col, width=ancho, stretch=(col == "nombre"))
        tabla_usuarios.pack(fill="both", expand=True)

        def cargar_usuarios():
            tabla_usuarios.delete(*tabla_usuarios.get_children())
            try:
                for fila in self.consultar("SELECT usuario, nombre, rol FROM usuarios ORDER BY nombre"):
                    tabla_usuarios.insert("", "end", values=(fila["usuario"], fila["nombre"], fila["rol"]))
            except mysql.connector.Error as error:
                messagebox.showerror("Error MySQL", str(error))

        def seleccionar_usuario(event=None):
            seleccion = tabla_usuarios.selection()
            if not seleccion: return
            usuario, nombre_usuario, rol_usuario = tabla_usuarios.item(seleccion[0], "values")
            self.campos["Nombre completo"].delete(0, "end")
            self.campos["Nombre completo"].insert(0, nombre_usuario)
            self.campos["Usuario"].delete(0, "end")
            self.campos["Usuario"].insert(0, usuario)
            self.campos["Usuario"].configure(state="disabled")
            self.campos["Rol"].set(rol_usuario)
            self.campos["Contraseña"].delete(0, "end")

        tabla_usuarios.bind("<<TreeviewSelect>>", seleccionar_usuario)

        def actualizar_usuario():
            seleccion = tabla_usuarios.selection()
            if not seleccion:
                messagebox.showwarning("Selecciona una cuenta", "Elige una cuenta de la tabla para editar.")
                return
            usuario = tabla_usuarios.item(seleccion[0], "values")[0]
            nombre_usuario = self.campos["Nombre completo"].get().strip()
            rol_usuario = self.campos["Rol"].get().strip().lower()
            password_nueva = self.campos["Contraseña"].get()
            if not nombre_usuario or rol_usuario not in ("docente", "director"):
                messagebox.showwarning("Datos inválidos", "Revisa el nombre y el rol.")
                return
            conexion_editar = None
            try:
                conexion_editar = conectar(); cursor_editar = conexion_editar.cursor()
                if password_nueva:
                    cursor_editar.execute("UPDATE usuarios SET nombre=%s, rol=%s, password_hash=%s WHERE usuario=%s", (nombre_usuario, rol_usuario, generar_hash_password(password_nueva), usuario))
                else:
                    cursor_editar.execute("UPDATE usuarios SET nombre=%s, rol=%s WHERE usuario=%s", (nombre_usuario, rol_usuario, usuario))
                conexion_editar.commit()
                self.campos["Usuario"].configure(state="normal")
                cargar_usuarios()
                messagebox.showinfo("Cuenta actualizada", "Los datos de la cuenta se actualizaron.")
            except mysql.connector.Error as error:
                if conexion_editar: conexion_editar.rollback()
                messagebox.showerror("No se pudo editar", str(error))
            finally:
                if conexion_editar and conexion_editar.is_connected(): conexion_editar.close()

        def eliminar_usuario():
            seleccion = tabla_usuarios.selection()
            if not seleccion:
                messagebox.showwarning("Selecciona una cuenta", "Elige una cuenta para eliminar.")
                return
            usuario = tabla_usuarios.item(seleccion[0], "values")[0]
            if usuario == self.usuario:
                messagebox.showwarning("Acción no permitida", "No puedes eliminar la cuenta con la que iniciaste sesión.")
                return
            if not messagebox.askyesno("Eliminar cuenta", f"¿Eliminar la cuenta {usuario}?"): return
            conexion_borrar = None
            try:
                conexion_borrar = conectar(); cursor_borrar = conexion_borrar.cursor()
                cursor_borrar.execute("DELETE FROM usuarios WHERE usuario=%s", (usuario,))
                conexion_borrar.commit(); cargar_usuarios()
                self.campos["Usuario"].configure(state="normal")
                messagebox.showinfo("Cuenta eliminada", "La cuenta se eliminó.")
            except mysql.connector.Error as error:
                if conexion_borrar: conexion_borrar.rollback()
                messagebox.showerror("No se pudo eliminar", str(error))
            finally:
                if conexion_borrar and conexion_borrar.is_connected(): conexion_borrar.close()

        botones_usuarios = tk.Frame(self.contenido, bg=FONDO)
        botones_usuarios.pack(fill="x", pady=6)
        self.boton(botones_usuarios, "✏️ Editar cuenta", actualizar_usuario, "#1D4ED8").pack(side="left", padx=4)
        self.boton(botones_usuarios, "🗑 Eliminar cuenta", eliminar_usuario, "#B91C1C").pack(side="left", padx=4)
        self.boton(botones_usuarios, "Limpiar", lambda: (self.campos["Usuario"].configure(state="normal"), [w.delete(0, "end") for w in (self.campos["Nombre completo"], self.campos["Usuario"], self.campos["Contraseña"])]), "#475569").pack(side="left", padx=4)
        cargar_usuarios()

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
                cargar_grupos_admin()
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

        tk.Label(self.contenido, text="Grupos disponibles", bg=FONDO, fg=TEXTO,
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(12, 5))
        marco_grupos = tk.Frame(self.contenido, bg=PANEL, padx=8, pady=8)
        marco_grupos.pack(fill="both", expand=True)
        tabla_grupos = ttk.Treeview(marco_grupos, columns=("id", "grupo", "alumnos"), show="headings", height=8)
        for col, etiqueta, ancho in [("id", "ID", 55), ("grupo", "Grupo", 160), ("alumnos", "Alumnos", 100)]:
            tabla_grupos.heading(col, text=etiqueta); tabla_grupos.column(col, width=ancho)
        tabla_grupos.pack(fill="both", expand=True)

        def cargar_grupos_admin():
            tabla_grupos.delete(*tabla_grupos.get_children())
            try:
                filas = self.consultar("""SELECT g.id, g.nombre AS grupo, COUNT(a.id) AS alumnos
                    FROM grupos_escolares g LEFT JOIN alumnos_escolares a
                    ON a.grupo_id=g.id
                    GROUP BY g.id, g.nombre ORDER BY g.nombre""")
                for fila in filas:
                    tabla_grupos.insert("", "end", values=(fila["id"], fila["grupo"], fila["alumnos"]))
            except mysql.connector.Error as error:
                messagebox.showerror("Error MySQL", str(error))

        def elegir_grupo(event=None):
            sel = tabla_grupos.selection()
            if sel:
                entrada.delete(0, "end")
                entrada.insert(0, tabla_grupos.item(sel[0], "values")[1])

        tabla_grupos.bind("<<TreeviewSelect>>", elegir_grupo)

        def editar_grupo():
            sel = tabla_grupos.selection()
            if not sel:
                messagebox.showwarning("Selecciona un grupo", "Selecciona un grupo para editar."); return
            nuevo = entrada.get().strip().upper()
            if not nuevo:
                messagebox.showwarning("Nombre vacío", "Escribe el nuevo nombre del grupo."); return
            grupo_id = tabla_grupos.item(sel[0], "values")[0]
            conexion_editar = None
            try:
                conexion_editar = conectar(); cursor_editar = conexion_editar.cursor()
                cursor_editar.execute("UPDATE grupos_escolares SET nombre=%s WHERE id=%s", (nuevo, grupo_id))
                conexion_editar.commit(); cargar_grupos_admin(); entrada.delete(0, "end")
            except mysql.connector.Error as error:
                if conexion_editar: conexion_editar.rollback()
                messagebox.showerror("No se pudo editar", str(error))
            finally:
                if conexion_editar and conexion_editar.is_connected(): conexion_editar.close()

        def eliminar_grupo():
            sel = tabla_grupos.selection()
            if not sel:
                messagebox.showwarning("Selecciona un grupo", "Selecciona un grupo para eliminar."); return
            grupo_id, nombre_grupo, alumnos_total = tabla_grupos.item(sel[0], "values")
            if int(alumnos_total) > 0:
                messagebox.showwarning("Grupo con alumnos", "No se puede eliminar un grupo que todavía tiene alumnos activos. Da de baja o mueve primero a sus alumnos."); return
            if not messagebox.askyesno("Eliminar grupo", f"¿Eliminar el grupo {nombre_grupo}?"): return
            conexion_borrar = None
            try:
                conexion_borrar = conectar(); cursor_borrar = conexion_borrar.cursor()
                cursor_borrar.execute("DELETE FROM grupos_escolares WHERE id=%s", (grupo_id,))
                conexion_borrar.commit(); cargar_grupos_admin(); entrada.delete(0, "end")
            except mysql.connector.Error as error:
                if conexion_borrar: conexion_borrar.rollback()
                messagebox.showerror("No se pudo eliminar", str(error))
            finally:
                if conexion_borrar and conexion_borrar.is_connected(): conexion_borrar.close()

        acciones_grupos = tk.Frame(self.contenido, bg=FONDO)
        acciones_grupos.pack(fill="x", pady=6)
        self.boton(acciones_grupos, "✏️ Editar grupo", editar_grupo, "#1D4ED8").pack(side="left", padx=4)
        self.boton(acciones_grupos, "🗑 Eliminar grupo", eliminar_grupo, "#B91C1C").pack(side="left", padx=4)
        cargar_grupos_admin()

    def pantalla_asignar(self):
        self.limpiar_contenido()
        self.titulo(
            "Asignar docentes",
            "Asigna docentes a grupos y administra las asignaciones existentes."
        )

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

        mapa_docentes = {
            f"{d['nombre']} ({d['usuario']})": d["usuario"]
            for d in docentes
        }
        mapa_grupos = {g["nombre"]: g["id"] for g in grupos}
        panel = tk.Frame(self.contenido, bg=BLANCO, padx=18, pady=18)
        panel.pack(fill="x")

        tk.Label(panel, text="Docente", bg=BLANCO, fg=TEXTO).pack(anchor="w")
        docente = ttk.Combobox(panel, values=list(mapa_docentes), state="readonly")
        docente.pack(fill="x", pady=6)

        tk.Label(panel, text="Grupo", bg=BLANCO, fg=TEXTO).pack(anchor="w")
        grupo = ttk.Combobox(panel, values=list(mapa_grupos), state="readonly")
        grupo.pack(fill="x", pady=6)

        marco_tabla = tk.Frame(self.contenido, bg=PANEL, padx=8, pady=8)
        marco_tabla.pack(fill="both", expand=True, pady=(12, 6))
        tk.Label(
            self.contenido, text="Asignaciones actuales", bg=FONDO, fg=TEXTO,
            font=("Segoe UI", 13, "bold")
        ).pack(anchor="w", pady=(8, 5), before=marco_tabla)

        tabla = ttk.Treeview(
            marco_tabla, columns=("id", "docente", "grupo"),
            show="headings", height=9
        )
        tabla.heading("id", text="ID")
        tabla.heading("docente", text="Docente")
        tabla.heading("grupo", text="Grupo")
        tabla.column("id", width=55, anchor="center")
        tabla.column("docente", width=300)
        tabla.column("grupo", width=140, anchor="center")
        tabla.pack(fill="both", expand=True)

        def cargar_asignaciones():
            tabla.delete(*tabla.get_children())
            try:
                filas = self.consultar("""
                    SELECT dg.id, u.nombre AS docente, g.nombre AS grupo
                    FROM docente_grupos dg
                    INNER JOIN usuarios u ON u.usuario=dg.docente
                    INNER JOIN grupos_escolares g ON g.id=dg.grupo_id
                    ORDER BY u.nombre, g.nombre
                """)
                for fila in filas:
                    tabla.insert("", "end", values=(
                        fila["id"], fila["docente"], fila["grupo"]
                    ))
            except mysql.connector.Error as error:
                messagebox.showerror("Error al consultar asignaciones", str(error))

        def asignar():
            if not docente.get() or not grupo.get():
                messagebox.showwarning(
                    "Datos incompletos", "Selecciona un docente y un grupo."
                )
                return
            conexion = None
            try:
                conexion = conectar()
                cursor = conexion.cursor()
                cursor.execute("""
                    INSERT IGNORE INTO docente_grupos (docente, grupo_id)
                    VALUES (%s, %s)
                """, (mapa_docentes[docente.get()], mapa_grupos[grupo.get()]))
                if cursor.rowcount == 0:
                    messagebox.showinfo("Asignación existente", "Ese docente ya está asignado a ese grupo.")
                else:
                    conexion.commit()
                    messagebox.showinfo("Asignación guardada", "El docente ya puede consultar la lista del grupo.")
                cargar_asignaciones()
            except mysql.connector.Error as error:
                if conexion:
                    conexion.rollback()
                messagebox.showerror("Error MySQL", str(error))
            finally:
                if conexion is not None and conexion.is_connected():
                    conexion.close()

        def editar_asignacion():
            seleccion = tabla.selection()
            if not seleccion:
                messagebox.showwarning("Selecciona una asignación", "Elige una fila para editar.")
                return
            valores = tabla.item(seleccion[0], "values")
            ventana = tk.Toplevel(self.root)
            ventana.title("Editar asignación")
            ventana.transient(self.root)
            ventana.grab_set()
            ventana.configure(bg=BLANCO)
            ventana.geometry("420x230")
            formulario = tk.Frame(ventana, bg=BLANCO, padx=20, pady=20)
            formulario.pack(fill="both", expand=True)
            tk.Label(formulario, text="Docente", bg=BLANCO, fg=TEXTO).pack(anchor="w")
            combo_docente = ttk.Combobox(formulario, values=list(mapa_docentes), state="readonly")
            combo_docente.pack(fill="x", pady=5)
            tk.Label(formulario, text="Grupo", bg=BLANCO, fg=TEXTO).pack(anchor="w")
            combo_grupo = ttk.Combobox(formulario, values=list(mapa_grupos), state="readonly")
            combo_grupo.pack(fill="x", pady=5)
            for etiqueta, usuario in mapa_docentes.items():
                if usuario and etiqueta.startswith(valores[1] + " ("):
                    combo_docente.set(etiqueta)
                    break
            combo_grupo.set(valores[2])

            def guardar_edicion():
                if not combo_docente.get() or not combo_grupo.get():
                    messagebox.showwarning("Datos incompletos", "Selecciona docente y grupo.")
                    return
                conexion_edicion = None
                try:
                    conexion_edicion = conectar()
                    cursor_edicion = conexion_edicion.cursor()
                    cursor_edicion.execute("""
                        UPDATE docente_grupos
                        SET docente=%s, grupo_id=%s WHERE id=%s
                    """, (mapa_docentes[combo_docente.get()], mapa_grupos[combo_grupo.get()], valores[0]))
                    conexion_edicion.commit()
                    ventana.destroy()
                    cargar_asignaciones()
                except mysql.connector.Error as error:
                    if conexion_edicion:
                        conexion_edicion.rollback()
                    messagebox.showerror("No se pudo editar", str(error))
                finally:
                    if conexion_edicion and conexion_edicion.is_connected():
                        conexion_edicion.close()

            self.boton(formulario, "Guardar cambios", guardar_edicion, "#15803D").pack(anchor="e", pady=8)

        def eliminar_asignacion():
            seleccion = tabla.selection()
            if not seleccion:
                messagebox.showwarning("Selecciona una asignación", "Elige una fila para eliminar.")
                return
            valores = tabla.item(seleccion[0], "values")
            if not messagebox.askyesno(
                "Eliminar asignación",
                f"¿Eliminar la asignación de {valores[1]} al grupo {valores[2]}?"
            ):
                return
            conexion_borrar = None
            try:
                conexion_borrar = conectar()
                cursor_borrar = conexion_borrar.cursor()
                cursor_borrar.execute("DELETE FROM docente_grupos WHERE id=%s", (valores[0],))
                conexion_borrar.commit()
                cargar_asignaciones()
            except mysql.connector.Error as error:
                if conexion_borrar:
                    conexion_borrar.rollback()
                messagebox.showerror("No se pudo eliminar", str(error))
            finally:
                if conexion_borrar and conexion_borrar.is_connected():
                    conexion_borrar.close()

        acciones = tk.Frame(self.contenido, bg=FONDO)
        acciones.pack(fill="x", pady=8)
        self.boton(panel, "➕ Asignar grupo", asignar, "#15803D").pack(anchor="e", pady=(8, 0))
        self.boton(acciones, "✏️ Editar asignación", editar_asignacion, "#1D4ED8").pack(side="left", padx=4)
        self.boton(acciones, "🗑 Eliminar asignación", eliminar_asignacion, "#B91C1C").pack(side="left", padx=4)
        self.boton(acciones, "↻ Actualizar", cargar_asignaciones).pack(side="left", padx=4)
        cargar_asignaciones()

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
        self.limpiar_contenido()
        self.titulo("Administrar alumnos", "Ambos perfiles pueden agregar, editar y dar de baja alumnos. Los registros históricos se conservan.")
        grupos = self.obtener_mis_grupos()
        if not grupos:
            tk.Label(self.contenido, text="No hay grupos disponibles para tu cuenta.", bg=FONDO, fg=TEXTO).pack(anchor="w")
            return
        mapa_grupos = {g["nombre"]: g for g in grupos}
        panel = tk.Frame(self.contenido, bg=PANEL, padx=14, pady=12)
        panel.pack(fill="x", pady=(0, 10))
        tk.Label(panel, text="Grupo", bg=PANEL, fg=TEXTO, font=("Segoe UI", 11, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        grupo_var = tk.StringVar(value=grupos[0]["nombre"])
        combo = ttk.Combobox(panel, textvariable=grupo_var, values=list(mapa_grupos), state="readonly", width=16)
        combo.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(panel, text="N.º de lista", bg=PANEL, fg=TEXTO).grid(row=0, column=2, padx=5)
        numero = ttk.Entry(panel, width=9)
        numero.grid(row=0, column=3, padx=5)
        tk.Label(panel, text="Nombre del alumno", bg=PANEL, fg=TEXTO).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        nombre = ttk.Entry(panel, width=36)
        nombre.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
        panel.columnconfigure(1, weight=1)

        tabla_marco = tk.Frame(self.contenido, bg=PANEL, padx=8, pady=8)
        tabla_marco.pack(fill="both", expand=True)
        tabla = ttk.Treeview(tabla_marco, columns=("id", "grupo", "numero", "nombre"), show="headings", height=12)
        for col, texto, ancho in [("id", "ID", 55), ("grupo", "Grupo", 100), ("numero", "N.º lista", 90), ("nombre", "Alumno", 300)]:
            tabla.heading(col, text=texto)
            tabla.column(col, width=ancho, minwidth=60, stretch=(col == "nombre"))
        tabla.pack(fill="both", expand=True)

        def cargar():
            tabla.delete(*tabla.get_children())
            try:
                filas = self.consultar("""SELECT a.id, g.nombre AS grupo, a.numero_lista, a.nombre
                    FROM alumnos_escolares a INNER JOIN grupos_escolares g ON g.id=a.grupo_id
                    WHERE a.activo=TRUE AND a.grupo_id IN (""" + ",".join(["%s"] * len(grupos)) + ") ORDER BY g.nombre, a.numero_lista", tuple(g["id"] for g in grupos))
                for f in filas:
                    tabla.insert("", "end", values=(f["id"], f["grupo"], f["numero_lista"], f["nombre"]))
            except mysql.connector.Error as error:
                messagebox.showerror("Error MySQL", str(error))

        def limpiar_campos():
            numero.delete(0, "end")
            nombre.delete(0, "end")
            seleccion_actual = tabla.selection()
            if seleccion_actual:
                tabla.selection_remove(*seleccion_actual)

        def seleccionar(event=None):
            sel = tabla.selection()
            if not sel: return
            valores = tabla.item(sel[0], "values")
            grupo_var.set(valores[1])
            numero.delete(0, "end")
            nombre.delete(0, "end")
            numero.insert(0, valores[2])
            nombre.insert(0, valores[3])

        tabla.bind("<<TreeviewSelect>>", seleccionar)

        def guardar():
            try:
                n = int(numero.get().strip())
                nom = nombre.get().strip()
                if n < 1 or not nom: raise ValueError
            except ValueError:
                messagebox.showwarning("Datos inválidos", "Escribe un número de lista válido y el nombre del alumno.")
                return
            grupo = mapa_grupos.get(grupo_var.get())
            if not grupo: return
            seleccionado = tabla.selection()
            conexion = None
            try:
                conexion = conectar(); cursor = conexion.cursor()
                if seleccionado:
                    alumno_id = int(tabla.item(seleccionado[0], "values")[0])
                    cursor.execute("UPDATE alumnos_escolares SET grupo_id=%s, numero_lista=%s, nombre=%s, activo=TRUE WHERE id=%s", (grupo["id"], n, nom, alumno_id))
                else:
                    cursor.execute("INSERT INTO alumnos_escolares (grupo_id, numero_lista, nombre, activo) VALUES (%s,%s,%s,TRUE)", (grupo["id"], n, nom))
                conexion.commit(); limpiar_campos(); cargar()
                messagebox.showinfo("Alumnos", "Los datos del alumno se guardaron correctamente.")
            except mysql.connector.Error as error:
                if conexion: conexion.rollback()
                messagebox.showerror("No se pudo guardar", str(error))
            finally:
                if conexion and conexion.is_connected(): conexion.close()

        def eliminar():
            seleccionado = tabla.selection()
            if not seleccionado:
                messagebox.showwarning("Selecciona un alumno", "Selecciona primero un registro de la tabla.")
                return
            if not messagebox.askyesno("Dar de baja", "¿Deseas dar de baja al alumno? Su historial se conservará."): return
            alumno_id = int(tabla.item(seleccionado[0], "values")[0])
            conexion = None
            try:
                conexion = conectar(); cursor = conexion.cursor()
                cursor.execute("UPDATE alumnos_escolares SET activo=FALSE WHERE id=%s", (alumno_id,))
                conexion.commit(); limpiar_campos(); cargar()
            except mysql.connector.Error as error:
                messagebox.showerror("No se pudo eliminar", str(error))
            finally:
                if conexion and conexion.is_connected(): conexion.close()

        controles = tk.Frame(panel, bg=PANEL)
        controles.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(8, 0))
        self.boton(controles, "➕ Agregar / guardar", guardar, "#15803D").pack(side="left", padx=4)
        self.boton(controles, "✏️ Editar seleccionado", seleccionar, "#1D4ED8").pack(side="left", padx=4)
        self.boton(controles, "🗑 Eliminar", eliminar, "#B91C1C").pack(side="left", padx=4)
        self.boton(controles, "Limpiar", limpiar_campos, "#475569").pack(side="left", padx=4)
        cargar()

    
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

            if "id" in columnas and "tipo" in columnas and "alumno" in columnas:
                acciones = tk.Frame(marco, bg=BLANCO, padx=8, pady=8)
                acciones.pack(fill="x")

                def nuevo_registro():
                    self.vista_actual = "Registrar incidencia"
                    self.pantalla_incidencia()

                def editar_registro():
                    seleccion = tabla.selection()
                    if not seleccion:
                        messagebox.showwarning("Selecciona un registro", "Elige una fila para editar.")
                        return
                    valores = tabla.item(seleccion[0], "values")
                    indice_id = columnas.index("id")
                    registro_id = valores[indice_id]
                    datos = next((f for f in filas if str(f.get("id")) == str(registro_id)), None)
                    if not datos:
                        return
                    ventana = tk.Toplevel(self.root)
                    ventana.title("Editar registro")
                    ventana.configure(bg=FONDO)
                    ventana.transient(self.root)
                    ventana.grab_set()
                    formulario = tk.Frame(ventana, bg=PANEL, padx=16, pady=14)
                    formulario.pack(fill="both", expand=True)
                    entradas = {}
                    editables = [c for c in columnas if c not in ("id", "creado_en", "registrado_por")]
                    for i, campo in enumerate(editables):
                        tk.Label(formulario, text=campo.replace("_", " ").title(), bg=PANEL, fg=TEXTO, font=("Segoe UI", 10, "bold")).grid(row=i, column=0, sticky="w", padx=5, pady=5)
                        entrada = ttk.Entry(formulario, width=42)
                        entrada.grid(row=i, column=1, sticky="ew", padx=5, pady=5)
                        entrada.insert(0, "" if datos.get(campo) is None else str(datos.get(campo)))
                        entradas[campo] = entrada
                    formulario.columnconfigure(1, weight=1)

                    def guardar_edicion():
                        conexion_edicion = None
                        try:
                            conexion_edicion = conectar()
                            cursor_edicion = conexion_edicion.cursor()
                            asignaciones = ", ".join(f"`{c}`=%s" for c in editables)
                            valores_nuevos = [entradas[c].get().strip() or None for c in editables]
                            if self.rol == "docente":
                                cursor_edicion.execute(f"UPDATE registros_escolares SET {asignaciones} WHERE id=%s AND registrado_por=%s", tuple(valores_nuevos) + (registro_id, self.usuario))
                            else:
                                cursor_edicion.execute(f"UPDATE registros_escolares SET {asignaciones} WHERE id=%s", tuple(valores_nuevos) + (registro_id,))
                            conexion_edicion.commit()
                            ventana.destroy()
                            self.ir(self.vista_actual)
                        except (mysql.connector.Error, ValueError) as error:
                            if conexion_edicion:
                                conexion_edicion.rollback()
                            messagebox.showerror("No se pudo editar", str(error))
                        finally:
                            if conexion_edicion and conexion_edicion.is_connected():
                                conexion_edicion.close()

                    self.boton(formulario, "💾 Guardar cambios", guardar_edicion, "#15803D").grid(row=len(editables), column=1, sticky="e", pady=10)

                def eliminar_registro():
                    seleccion = tabla.selection()
                    if not seleccion:
                        messagebox.showwarning("Selecciona un registro", "Elige una fila para eliminar.")
                        return
                    registro_id = tabla.item(seleccion[0], "values")[columnas.index("id")]
                    if not messagebox.askyesno("Confirmar eliminación", "¿Eliminar definitivamente este registro? Esta acción no se puede deshacer."):
                        return
                    conexion_borrar = None
                    try:
                        conexion_borrar = conectar()
                        cursor_borrar = conexion_borrar.cursor()
                        if self.rol == "docente":
                            cursor_borrar.execute("DELETE FROM registros_escolares WHERE id=%s AND registrado_por=%s", (registro_id, self.usuario))
                        else:
                            cursor_borrar.execute("DELETE FROM registros_escolares WHERE id=%s", (registro_id,))
                        conexion_borrar.commit()
                        self.ir(self.vista_actual)
                    except mysql.connector.Error as error:
                        if conexion_borrar:
                            conexion_borrar.rollback()
                        messagebox.showerror("No se pudo eliminar", str(error))
                    finally:
                        if conexion_borrar and conexion_borrar.is_connected():
                            conexion_borrar.close()

                self.boton(acciones, "➕ Agregar", nuevo_registro, "#15803D").pack(side="left", padx=4)
                self.boton(acciones, "✏️ Editar", editar_registro, "#1D4ED8").pack(side="left", padx=4)
                self.boton(acciones, "🗑 Eliminar", eliminar_registro, "#B91C1C").pack(side="left", padx=4)

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

