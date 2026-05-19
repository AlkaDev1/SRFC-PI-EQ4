import sqlite3
import sys
import tkinter as tk
import importlib
import json
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

try:
    DateEntry = importlib.import_module("tkcalendar").DateEntry
except ModuleNotFoundError:
    DateEntry = None

try:
    from PIL import Image as PILImage
    from PIL import ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ui.styles import PALETA, PALETA_VERDE_UDEC, PALETA_OSCURO, configurar_estilos


# __________________________1__________________________#
# Paleta activa y catalogo de temas
PALETAS_DISPONIBLES = {
    "Gris neutro": PALETA,
    "Verde UdeC": PALETA_VERDE_UDEC,
    "Modo oscuro": PALETA_OSCURO,
}
PALETA_ACTIVA = dict(PALETA)
# ________________________FIN_1_______________________#


# __________________________1_A__________________________#
# Parametros del logo (tamanio y espacio - usados en carga inicial y cambios de tema)
LOGO_SUBSAMPLE_X = 8
LOGO_SUBSAMPLE_Y = 8
LOGO_PADX = (12, 20)
LOGO_TARGET_SIZE = (230, 100)  # Tamanio objetivo en pixeles para redimensionamiento
# ________________________FIN_1_A_______________________#


# __________________________1_B__________________________#
# Funcion auxiliar para cargar y redimensionar logos
def cargar_logo(ruta_logo: Path) -> tk.PhotoImage | None:
    """Carga un logo y lo redimensiona a LOGO_TARGET_SIZE usando PIL si esta disponible."""
    if not ruta_logo.exists():
        return None
    
    try:
        if HAS_PIL:
            # BLOQUE 1: Usar PIL para redimensionamiento preciso
            imagen_pil = PILImage.open(str(ruta_logo))
            imagen_pil = imagen_pil.resize(LOGO_TARGET_SIZE, PILImage.Resampling.LANCZOS)
            # Usar ImageTk para convertir PIL Image a PhotoImage
            return ImageTk.PhotoImage(imagen_pil)
            # FIN BLOQUE 1
        else:
            # Caer de vuelta a subsample si PIL no esta disponible
            return tk.PhotoImage(file=str(ruta_logo)).subsample(LOGO_SUBSAMPLE_X, LOGO_SUBSAMPLE_Y)
    except Exception:
        return None
# ________________________FIN_1_B_______________________#


# __________________________1_C__________________________#
# Helpers de traduccion dinamica
I18N_DIR = BASE_DIR / "data" / "i18n"


def cargar_packs_idioma_locales() -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    """Carga packs de idioma desde data/i18n en formato JSON local."""
    idiomas: dict[str, str] = {}
    packs: dict[str, dict[str, str]] = {}

    if I18N_DIR.exists():
        for ruta in sorted(I18N_DIR.glob("*.json")):
            try:
                data = json.loads(ruta.read_text(encoding="utf-8"))
            except Exception:
                continue

            codigo = ruta.stem.lower()
            nombre = str(data.get("language_name", codigo)).strip() or codigo
            traducciones = data.get("translations", {})
            if isinstance(traducciones, dict):
                idiomas[codigo] = nombre
                packs[codigo] = {str(k): str(v) for k, v in traducciones.items()}

    # Fallback minimo para que siempre exista espanol.
    if "es" not in idiomas:
        idiomas["es"] = "Espanol"
        packs["es"] = {}

    return idiomas, packs


LANGUAGES, TRADUCCIONES_UI_RAPIDAS = cargar_packs_idioma_locales()


def traducir_texto_local(
    texto: str,
    idioma_destino: str,
    cache: dict[tuple[str, str], str],
) -> str:
    if not texto.strip() or idioma_destino == "es":
        return texto

    key = (idioma_destino, texto)
    if key in cache:
        return cache[key]

    # Traduccion local instantanea desde pack.
    traducciones_locales = TRADUCCIONES_UI_RAPIDAS.get(idioma_destino, {})
    if texto in traducciones_locales:
        cache[key] = traducciones_locales[texto]
        return cache[key]

    # Si no existe clave en el pack, mantener original para no bloquear la UI.
    cache[key] = texto
    return texto


def traducir_interfaz(widget: tk.Misc, traducir_fn) -> None:
    for child in widget.winfo_children():
        if isinstance(child, (ttk.Label, ttk.Button, ttk.Checkbutton, tk.Label, tk.Button, tk.Checkbutton)):
            try:
                texto_actual = child.cget("text")
            except tk.TclError:
                texto_actual = ""

            if texto_actual:
                if not hasattr(child, "_texto_base"):
                    setattr(child, "_texto_base", texto_actual)
                texto_base = getattr(child, "_texto_base")
                child.configure(text=traducir_fn(texto_base))

        if isinstance(child, ttk.Treeview):
            if not hasattr(child, "_headings_base"):
                setattr(child, "_headings_base", {})
            headings_base = getattr(child, "_headings_base")

            for columna in child["columns"]:
                texto_heading = child.heading(columna).get("text", "")
                if texto_heading and columna not in headings_base:
                    headings_base[columna] = texto_heading
                if columna in headings_base:
                    child.heading(columna, text=traducir_fn(headings_base[columna]))

        traducir_interfaz(child, traducir_fn)
# ________________________FIN_1_C_______________________#

def obtener_ruta_db() -> Path:
    return BASE_DIR / "data" / "SRFC.db"


def obtener_ruta_script() -> Path:
    return BASE_DIR / "script.sqlite"


def obtener_conexion() -> sqlite3.Connection:
    conn = sqlite3.connect(obtener_ruta_db())
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def sanitizar_script_sqlite(sql_text: str) -> str:
    lineas_limpias = []
    for linea in sql_text.splitlines():
        linea_upper = linea.strip().upper()
        if linea_upper.startswith("CREATE DATABASE"):
            continue
        if linea_upper.startswith("USE "):
            continue
        lineas_limpias.append(linea)
    return "\n".join(lineas_limpias)


def inicializar_db_si_falta() -> None:
    ruta_db = obtener_ruta_db()
    ruta_db.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(ruta_db) as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Usuarios'")
        ya_existe = cur.fetchone() is not None

    if ya_existe:
        return

    ruta_script = obtener_ruta_script()
    if not ruta_script.exists():
        raise FileNotFoundError("No se encontro script.sqlite para inicializar la base de datos.")

    sql_text = sanitizar_script_sqlite(ruta_script.read_text(encoding="utf-8"))
    with sqlite3.connect(ruta_db) as conn:
        conn.executescript(sql_text)
        conn.commit()


def obtener_roles_disponibles() -> list[str]:
    with obtener_conexion() as conn:
        cur = conn.cursor()
        cur.execute("SELECT nombre FROM Roles ORDER BY id_rol")
        return [fila[0] for fila in cur.fetchall()]


def obtener_usuarios(filtro_texto: str = "", filtro_rol: str = "Todos los roles", filtro_dia: str = "") -> list[tuple[str, str, str, str, str]]:
    like = f"%{filtro_texto.strip()}%"

    query = """
        SELECT
            u.cod_institucional,
            TRIM(
                u.primer_nombre || ' ' ||
                COALESCE(u.segundo_nombre || ' ', '') ||
                u.apellido_paterno || ' ' ||
                COALESCE(u.apellido_materno, '')
            ) AS nombre_completo,
            COALESCE(strftime('%d/%m/%Y', ua.ultimo_acceso), '--/--/----') AS fecha,
            COALESCE(strftime('%H:%M', ua.ultimo_acceso), '--:--') AS hora,
            COALESCE(r.nombre, 'Sin rol') AS rol
        FROM Usuarios u
        LEFT JOIN Roles r ON r.id_rol = u.id_rol
        LEFT JOIN (
            SELECT
                cod_institucional,
                MAX(datetime(fecha || ' ' || hora)) AS ultimo_acceso
            FROM Acceso
            GROUP BY cod_institucional
        ) ua ON ua.cod_institucional = u.cod_institucional
        WHERE (
            ? = '' OR
            u.cod_institucional LIKE ? OR
            u.primer_nombre LIKE ? OR
            COALESCE(u.segundo_nombre, '') LIKE ? OR
            u.apellido_paterno LIKE ? OR
            COALESCE(u.apellido_materno, '') LIKE ?
        )
        AND (? = 'Todos los roles' OR r.nombre = ?)
        AND (? = '' OR date(ua.ultimo_acceso) = date(?))
        ORDER BY u.cod_institucional
    """

    params = (
        filtro_texto.strip(),
        like,
        like,
        like,
        like,
        like,
        filtro_rol,
        filtro_rol,
        filtro_dia,
        filtro_dia,
    )

    with obtener_conexion() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        return cur.fetchall()


def obtener_usuario_por_codigo(codigo: str) -> tuple | None:
    query = """
        SELECT
            u.cod_institucional,
            u.primer_nombre,
            COALESCE(u.segundo_nombre, ''),
            u.apellido_paterno,
            COALESCE(u.apellido_materno, ''),
            COALESCE(r.nombre, 'Sin rol')
        FROM Usuarios u
        LEFT JOIN Roles r ON r.id_rol = u.id_rol
        WHERE u.cod_institucional = ?
    """

    with obtener_conexion() as conn:
        cur = conn.cursor()
        cur.execute(query, (codigo,))
        return cur.fetchone()


def actualizar_usuario(codigo: str, primer_nombre: str, segundo_nombre: str, apellido_paterno: str, apellido_materno: str, rol_nombre: str) -> None:
    with obtener_conexion() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id_rol FROM Roles WHERE nombre = ?", (rol_nombre,))
        rol = cur.fetchone()
        if rol is None:
            raise ValueError("El rol seleccionado no existe.")

        cur.execute(
            """
            UPDATE Usuarios
            SET
                primer_nombre = ?,
                segundo_nombre = ?,
                apellido_paterno = ?,
                apellido_materno = ?,
                id_rol = ?,
                fecha_actualizacion = CURRENT_TIMESTAMP,
                usuario_actualizacion = 'UI'
            WHERE cod_institucional = ?
            """,
            (primer_nombre, segundo_nombre or None, apellido_paterno, apellido_materno or None, rol[0], codigo),
        )
        conn.commit()


def eliminar_usuario(codigo: str) -> None:
    with obtener_conexion() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM Acceso WHERE cod_institucional = ?", (codigo,))
        cur.execute("DELETE FROM Usuarios WHERE cod_institucional = ?", (codigo,))
        conn.commit()


def obtener_historial_accesos(filtro_fecha: str = "") -> list[tuple[str, str, str]]:
    """Obtiene el historial completo de accesos desde la tabla Acceso."""
    query = """
        SELECT
            a.cod_institucional,
            TRIM(
                u.primer_nombre || ' ' ||
                COALESCE(u.segundo_nombre || ' ', '') ||
                u.apellido_paterno || ' ' ||
                COALESCE(u.apellido_materno, '')
            ) AS nombre_completo,
            a.fecha,
            a.hora
        FROM Acceso a
        LEFT JOIN Usuarios u ON a.cod_institucional = u.cod_institucional
        WHERE ? = '' OR a.fecha = ?
        ORDER BY a.fecha DESC, a.hora DESC
        LIMIT 500
    """
    params = (filtro_fecha, filtro_fecha)

    with obtener_conexion() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        return cur.fetchall()
# ________________________FIN_2_______________________#


# __________________________3__________________________#
# Componentes de interfaz

def actualizar_fecha_hora(label: ttk.Label, root: tk.Tk) -> None:
    fecha = datetime.now().strftime("Fecha: %d/%m/%Y")
    hora = datetime.now().strftime("Hora: %I:%M:%S %p")
    label.config(text=f"{fecha}\n{hora}")
    root.after(1000, lambda: actualizar_fecha_hora(label, root))


def actualizar_fecha_hora_traducida(label: ttk.Label, root: tk.Tk, traducir_fn) -> None:
    """Actualiza fecha/hora usando traduccion activa sin tocar datos de BD."""
    txt_fecha = traducir_fn("Fecha")
    txt_hora = traducir_fn("Hora")
    fecha = datetime.now().strftime(f"{txt_fecha}: %d/%m/%Y")
    hora = datetime.now().strftime(f"{txt_hora}: %I:%M:%S %p")
    label.config(text=f"{fecha}\n{hora}")
    root.after(1000, lambda: actualizar_fecha_hora_traducida(label, root, traducir_fn))


def configurar_estilo_tabla(style: ttk.Style) -> None:
    style.configure(
        "Users.Treeview",
        background=PALETA_ACTIVA["row_a"],
        fieldbackground=PALETA_ACTIVA["row_a"],
        foreground=PALETA_ACTIVA["title_fg"],
        rowheight=30,
        font=("Segoe UI", 10),
    )
    style.map("Users.Treeview", background=[("selected", PALETA_ACTIVA["header_bg"])])

    style.configure(
        "Users.Treeview.Heading",
        background=PALETA_ACTIVA["header_bg"],
        foreground="#ffffff",
        font=("Segoe UI", 10, "bold"),
    )


def crear_encabezado(
    parent: ttk.Frame,
    root: tk.Tk,
    tema_actual: tk.StringVar,
    on_theme_change,
    idioma_display_actual: tk.StringVar,
    opciones_idioma: list[str],
    on_language_change,
    on_language_search,
    traducir_fn,
) -> dict:
    top_bar = ttk.Frame(parent, style="TopDark.TFrame")
    top_bar.pack(fill="x")

    brand = ttk.Frame(top_bar, style="Brand.TFrame")
    brand.pack(side="left", fill="y", ipadx=16, ipady=10)

    logo_label = None
    logo_path = BASE_DIR / "src" / "img" / "logoUDEC.png"
    logo_img = cargar_logo(logo_path)
    if logo_img is not None:
        logo_label = ttk.Label(brand, image=logo_img, style="BrandTitle.TLabel")
        logo_label.image = logo_img
        logo_label.pack(side="left", padx=LOGO_PADX)
    else:
        ttk.Label(brand, text="UNIVERSIDAD\nDE COLIMA", style="BrandTitle.TLabel").pack(side="left", padx=LOGO_PADX)

    separador = tk.Frame(brand, bg="#666666", width=5, height=60)
    separador.pack(side="left", padx=10)
    ttk.Label(brand, text="SISTEMA DE\nCONTROL\nBIOMETRICO", style="BrandSub.TLabel").pack(side="left", padx=10)

    right = ttk.Frame(top_bar, style="TopDark.TFrame")
    right.pack(side="left", fill="y", padx=(20, 0), pady=10)

    caja_fecha_hora = tk.Frame(
        right,
        bg=PALETA_ACTIVA["topbar_bg"],
        highlightbackground="red",
        highlightthickness=2,
        bd=0,
        padx=8,
        pady=6,
    )
    caja_fecha_hora.pack(side="left", padx=(0, 14))

    date_label = ttk.Label(caja_fecha_hora, style="Date.TLabel", justify="center")
    date_label.pack()
    actualizar_fecha_hora_traducida(date_label, root, traducir_fn)

    cmb_idioma = ttk.Combobox(right, values=opciones_idioma, state="normal", width=24)
    cmb_idioma.set(idioma_display_actual.get())
    cmb_idioma.pack(side="left", padx=5)
    cmb_idioma.bind("<<ComboboxSelected>>", lambda _event: on_language_change(cmb_idioma.get()))
    cmb_idioma.bind("<KeyRelease>", lambda _event: on_language_search(cmb_idioma.get()))

    cambio_tema = ttk.Combobox(right, values=list(PALETAS_DISPONIBLES.keys()), state="readonly", width=14)
    cambio_tema.set(tema_actual.get())
    cambio_tema.pack(side="left", padx=5)
    cambio_tema.bind("<<ComboboxSelected>>", lambda _event: on_theme_change(cambio_tema.get()))

    return {
        "caja_fecha_hora": caja_fecha_hora,
        "separador": separador,
        "cambio_tema": cambio_tema,
        "logo_label": logo_label,
        "cmb_idioma": cmb_idioma,
        "date_label": date_label,
    }


def crear_tabla(parent: ttk.Frame) -> tuple[ttk.Treeview, ttk.Scrollbar]:
    columnas = ("cod", "nombre", "fecha", "hora", "rol")
    tree = ttk.Treeview(parent, columns=columnas, show="headings", style="Users.Treeview")

    tree.heading("cod", text="No. Institucional")
    tree.heading("nombre", text="Nombre")
    tree.heading("fecha", text="Fecha de acceso")
    tree.heading("hora", text="Hora de acceso")
    tree.heading("rol", text="Rol")

    tree.column("cod", width=160, anchor="center")
    tree.column("nombre", width=280, anchor="w")
    tree.column("fecha", width=140, anchor="center")
    tree.column("hora", width=120, anchor="center")
    tree.column("rol", width=140, anchor="center")

    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    return tree, scrollbar


def aplicar_estilo_calendario(widget_calendario) -> None:
    """Sincroniza colores del selector de fecha con el tema activo."""
    widget_calendario.configure(
        background=PALETA_ACTIVA["header_bg"],
        foreground="#ffffff",
        bordercolor=PALETA_ACTIVA["outer_frame"],
        headersbackground=PALETA_ACTIVA["topbar_bg"],
        headersforeground=PALETA_ACTIVA["date_fg"],
        normalbackground=PALETA_ACTIVA["page_bg"],
        normalforeground=PALETA_ACTIVA["title_fg"],
        weekendbackground=PALETA_ACTIVA["row_b"],
        weekendforeground=PALETA_ACTIVA["title_fg"],
        selectbackground=PALETA_ACTIVA["header_bg"],
        selectforeground="#ffffff",
    )


def abrir_historial_accesos(root: tk.Tk, traducir_fn=lambda x: x) -> None:
    """Abre una ventana modal con el historial de accesos."""
    t = traducir_fn
    modal = tk.Toplevel(root)
    modal.title(t("Historial de Accesos"))
    modal.geometry("800x500")
    modal.resizable(True, True)
    modal.transient(root)
    modal.configure(bg=PALETA_ACTIVA["page_bg"])

    frame = ttk.Frame(modal, style="Page.TFrame", padding=20)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text=t("Historial de Accesos"), style="SectionTitle.TLabel").pack(anchor="w", pady=(0, 12))

    # Filtro de fecha
    barra_filtro = ttk.Frame(frame, style="Page.TFrame")
    barra_filtro.pack(fill="x", pady=(0, 10))

    ttk.Label(barra_filtro, text=t("Filtrar por fecha"), style="PageSub.TLabel").pack(side="left", padx=(0, 6))
    date_entrada = DateEntry(barra_filtro, width=12, date_pattern="yyyy-mm-dd")
    date_entrada.pack(side="left", padx=(0, 8))
    aplicar_estilo_calendario(date_entrada)

    chk_filtro_fecha = tk.BooleanVar(value=False)
    ttk.Checkbutton(barra_filtro, text=t("Aplicar filtro"), variable=chk_filtro_fecha).pack(side="left", padx=(0, 8))

    # Tabla de historial
    contenedor_tabla = ttk.Frame(frame, style="Page.TFrame")
    contenedor_tabla.pack(fill="both", expand=True, pady=(0, 10))

    columnas = ("cod", "nombre", "fecha", "hora")
    tree_historial = ttk.Treeview(
        contenedor_tabla,
        columns=columnas,
        show="headings",
        style="Users.Treeview",
        height=15,
    )

    tree_historial.heading("cod", text=t("No. Institucional"))
    tree_historial.heading("nombre", text=t("Nombre Completo"))
    tree_historial.heading("fecha", text=t("Fecha"))
    tree_historial.heading("hora", text=t("Hora"))

    tree_historial.column("cod", width=150, anchor="center")
    tree_historial.column("nombre", width=300, anchor="w")
    tree_historial.column("fecha", width=120, anchor="center")
    tree_historial.column("hora", width=100, anchor="center")

    scrollbar_historial = ttk.Scrollbar(contenedor_tabla, orient="vertical", command=tree_historial.yview)
    tree_historial.configure(yscrollcommand=scrollbar_historial.set)

    tree_historial.pack(side="left", fill="both", expand=True)
    scrollbar_historial.pack(side="right", fill="y")

    def recargar_historial() -> None:
        for item in tree_historial.get_children():
            tree_historial.delete(item)
        fecha_filtro = date_entrada.get_date().strftime("%Y-%m-%d") if chk_filtro_fecha.get() else ""
        filas = obtener_historial_accesos(filtro_fecha=fecha_filtro)
        for fila in filas:
            tree_historial.insert("", "end", values=fila)

    # Botones inferiores
    barra_inferior = ttk.Frame(frame, style="Page.TFrame")
    barra_inferior.pack(fill="x")

    ttk.Button(barra_inferior, text=t("Recargar"), style="Ghost.TButton", command=recargar_historial).pack(side="left", padx=(0, 8))
    ttk.Button(barra_inferior, text=t("Cerrar"), style="Ghost.TButton", command=modal.destroy).pack(side="right")

    recargar_historial()
# ________________________FIN_3_______________________#


# __________________________4__________________________#
# Formulario de edicion

def abrir_formulario_edicion(root: tk.Tk, codigo: str, roles_disponibles: list[str], on_guardado, traducir_fn=lambda x: x) -> None:
    t = traducir_fn
    fila = obtener_usuario_por_codigo(codigo)
    if fila is None:
        messagebox.showerror(t("Error"), t("No se encontro el usuario seleccionado."))
        return

    modal = tk.Toplevel(root)
    modal.title(f"{t('Editar usuario')}: {codigo}")
    modal.geometry("520x380")
    modal.resizable(False, False)
    modal.transient(root)
    modal.grab_set()
    modal.configure(bg=PALETA_ACTIVA["page_bg"])

    frame = ttk.Frame(modal, style="Page.TFrame", padding=20)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text=t("Editar usuario"), style="SectionTitle.TLabel").pack(anchor="w", pady=(0, 12))

    campos = ttk.Frame(frame, style="Page.TFrame")
    campos.pack(fill="both", expand=True)

    ttk.Label(campos, text=t("Codigo"), style="PageSub.TLabel").grid(row=0, column=0, sticky="w", pady=6)
    ttk.Label(campos, text=codigo, style="PageSub.TLabel").grid(row=0, column=1, sticky="w", pady=6)

    ttk.Label(campos, text=t("Primer nombre"), style="PageSub.TLabel").grid(row=1, column=0, sticky="w", pady=6)
    ent_primer = ttk.Entry(campos, width=32)
    ent_primer.insert(0, fila[1])
    ent_primer.grid(row=1, column=1, sticky="w", pady=6)

    ttk.Label(campos, text=t("Segundo nombre"), style="PageSub.TLabel").grid(row=2, column=0, sticky="w", pady=6)
    ent_segundo = ttk.Entry(campos, width=32)
    ent_segundo.insert(0, fila[2])
    ent_segundo.grid(row=2, column=1, sticky="w", pady=6)

    ttk.Label(campos, text=t("Apellido paterno"), style="PageSub.TLabel").grid(row=3, column=0, sticky="w", pady=6)
    ent_paterno = ttk.Entry(campos, width=32)
    ent_paterno.insert(0, fila[3])
    ent_paterno.grid(row=3, column=1, sticky="w", pady=6)

    ttk.Label(campos, text=t("Apellido materno"), style="PageSub.TLabel").grid(row=4, column=0, sticky="w", pady=6)
    ent_materno = ttk.Entry(campos, width=32)
    ent_materno.insert(0, fila[4])
    ent_materno.grid(row=4, column=1, sticky="w", pady=6)

    ttk.Label(campos, text=t("Rol"), style="PageSub.TLabel").grid(row=5, column=0, sticky="w", pady=6)
    cmb_rol = ttk.Combobox(campos, values=roles_disponibles, state="readonly", width=29)
    cmb_rol.set(fila[5] if fila[5] in roles_disponibles else roles_disponibles[0])
    cmb_rol.grid(row=5, column=1, sticky="w", pady=6)

    def guardar_edicion() -> None:
        primer = ent_primer.get().strip()
        paterno = ent_paterno.get().strip()
        if not primer or not paterno:
            messagebox.showwarning(t("Campos incompletos"), t("Primer nombre y apellido paterno son obligatorios."))
            return

        try:
            actualizar_usuario(
                codigo=codigo,
                primer_nombre=primer,
                segundo_nombre=ent_segundo.get().strip(),
                apellido_paterno=paterno,
                apellido_materno=ent_materno.get().strip(),
                rol_nombre=cmb_rol.get(),
            )
            modal.destroy()
            on_guardado()
            messagebox.showinfo(t("Actualizado"), t("El registro se actualizo correctamente."))
        except Exception as error:
            messagebox.showerror(t("Error"), f"{t('No se pudo actualizar')}: {error}")

    barra = ttk.Frame(frame, style="Page.TFrame")
    barra.pack(fill="x", pady=(16, 0))
    ttk.Button(barra, text=t("Guardar"), style="Add.TButton", command=guardar_edicion).pack(side="right")
    ttk.Button(barra, text=t("Cancelar"), style="Ghost.TButton", command=modal.destroy).pack(side="right", padx=(0, 8))
# ________________________FIN_4_______________________#


# __________________________5__________________________#
# Aplicacion principal

def app() -> None:
    if DateEntry is None:
        raise ImportError("Falta instalar tkcalendar. Ejecuta: pip install tkcalendar")

    inicializar_db_si_falta()

    # __________________________5_1__________________________#
    # Ventana base sin marco visual adicional
    root = tk.Tk()
    root.title("Sistema de Control Biometrico")
    root.geometry("1200x760")
    root.minsize(1000, 650)
    root.configure(bg=PALETA_ACTIVA["window_bg"])
    # ________________________FIN_5_1_______________________#

    # __________________________5_2__________________________#
    # Estilos globales
    style = ttk.Style()
    configurar_estilos(style, PALETA_ACTIVA)
    configurar_estilo_tabla(style)
    # ________________________FIN_5_2_______________________#

    tema_actual = tk.StringVar(value="Gris neutro")
    idioma_actual = tk.StringVar(value="es")
    cache_traducciones: dict[tuple[str, str], str] = {}

    IDIOMA_PLACEHOLDER = "Buscar idioma..."
    idiomas_ordenados = sorted(LANGUAGES.items(), key=lambda item: item[1]) if LANGUAGES else [("es", "Espanol")]
    opciones_idioma = [f"{nombre.title()} ({codigo})" for codigo, nombre in idiomas_ordenados]
    display_a_codigo = {f"{nombre.title()} ({codigo})": codigo for codigo, nombre in idiomas_ordenados}
    codigo_a_display = {codigo: f"{nombre.title()} ({codigo})" for codigo, nombre in idiomas_ordenados}
    idioma_display_actual = tk.StringVar(value=codigo_a_display.get("es", "Espanol (es)"))

    pantalla = ttk.Frame(root, style="Page.TFrame")
    pantalla.pack(fill="both", expand=True)

    contenido = ttk.Frame(pantalla, style="Page.TFrame", padding=30)

    tabla_refs = {"tree": None, "scroll": None}
    encabezado_refs = {}

    def traducir_texto(texto: str) -> str:
        return traducir_texto_local(
            texto=texto,
            idioma_destino=idioma_actual.get(),
            cache=cache_traducciones,
        )

    def aplicar_traduccion_general() -> None:
        traducir_interfaz(pantalla, traducir_texto)
        root.title(traducir_texto("Sistema de Control Biometrico"))
        if "cmb_idioma" in encabezado_refs and encabezado_refs["cmb_idioma"] is not None:
            encabezado_refs["cmb_idioma"]["values"] = opciones_idioma
        if "ent_busqueda" in tabla_refs and tabla_refs["ent_busqueda"] is not None:
            ent = tabla_refs["ent_busqueda"]
            if getattr(ent, "_es_placeholder", False):
                ent.delete(0, tk.END)
                ent.insert(0, traducir_texto("Buscar..."))

    def cambiar_idioma_desde_combobox(seleccion_display: str) -> None:
        codigo = display_a_codigo.get(seleccion_display, "es")
        idioma_actual.set(codigo)
        idioma_display_actual.set(codigo_a_display.get(codigo, seleccion_display))

        if "cmb_idioma" in encabezado_refs and encabezado_refs["cmb_idioma"] is not None:
            encabezado_refs["cmb_idioma"].set(idioma_display_actual.get())

        root.configure(cursor="watch")
        root.update_idletasks()
        aplicar_traduccion_general()
        root.configure(cursor="")

    def filtrar_idiomas(texto_busqueda: str) -> None:
        if "cmb_idioma" not in encabezado_refs:
            return

        combo = encabezado_refs["cmb_idioma"]
        texto = texto_busqueda.strip().lower()

        if not texto or texto == IDIOMA_PLACEHOLDER.lower():
            combo["values"] = opciones_idioma
            return

        filtrados = [op for op in opciones_idioma if texto in op.lower()]
        combo["values"] = filtrados if filtrados else opciones_idioma

    def on_focus_in_idioma() -> None:
        if "cmb_idioma" not in encabezado_refs:
            return
        combo = encabezado_refs["cmb_idioma"]
        actual = combo.get().strip()
        if actual == idioma_display_actual.get() or actual == IDIOMA_PLACEHOLDER:
            combo.delete(0, tk.END)
            combo.insert(0, IDIOMA_PLACEHOLDER)
            combo.selection_range(0, tk.END)

    def on_focus_out_idioma() -> None:
        if "cmb_idioma" not in encabezado_refs:
            return
        combo = encabezado_refs["cmb_idioma"]
        actual = combo.get().strip()
        if not actual or actual == IDIOMA_PLACEHOLDER:
            combo.set(idioma_display_actual.get())

    def on_keyrelease_idioma() -> None:
        if "cmb_idioma" not in encabezado_refs:
            return
        combo = encabezado_refs["cmb_idioma"]
        if combo.get().strip() == IDIOMA_PLACEHOLDER:
            combo.delete(0, tk.END)
        filtrar_idiomas(combo.get())

    # __________________________5_3__________________________#
    # Funciones internas de refresco y tema
    def recargar_tabla() -> None:
        tree = tabla_refs["tree"]
        if tree is None:
            return

        for item in tree.get_children():
            tree.delete(item)

        texto = ent_busqueda.get().strip()
        if getattr(ent_busqueda, "_es_placeholder", False):
            texto = ""
        rol = cmb_roles.get().strip() or "Todos los roles"
        dia = date_filtro.get_date().strftime("%Y-%m-%d") if chk_filtrar_dia.get() else ""

        filas = obtener_usuarios(filtro_texto=texto, filtro_rol=rol, filtro_dia=dia)
        for fila in filas:
            tree.insert("", "end", values=fila)

    def aplicar_tema(nombre_tema: str) -> None:
        paleta_nueva = PALETAS_DISPONIBLES.get(nombre_tema, PALETA)
        PALETA_ACTIVA.clear()
        PALETA_ACTIVA.update(paleta_nueva)

        tema_actual.set(nombre_tema)
        configurar_estilos(style, PALETA_ACTIVA)
        configurar_estilo_tabla(style)

        # Cambiar imagen del logo según el tema
        if "logo_label" in encabezado_refs and encabezado_refs["logo_label"] is not None:
            logo_label_widget = encabezado_refs["logo_label"]
            if nombre_tema == "Modo oscuro":
                logo_file = BASE_DIR / "src" / "img" / "logoUDECblanco.png"
            else:
                logo_file = BASE_DIR / "src" / "img" / "logoUDEC.png"
            
            nueva_img = cargar_logo(logo_file)
            if nueva_img is not None:
                logo_label_widget.config(image=nueva_img)
                logo_label_widget.image = nueva_img

        root.configure(bg=PALETA_ACTIVA["window_bg"])
        if "caja_fecha_hora" in encabezado_refs:
            encabezado_refs["caja_fecha_hora"].configure(bg=PALETA_ACTIVA["topbar_bg"])

        aplicar_estilo_calendario(date_filtro)

        recargar_tabla()
        aplicar_traduccion_general()

    def on_editar() -> None:
        tree = tabla_refs["tree"]
        if tree is None:
            return
        seleccion = tree.selection()
        if not seleccion:
            messagebox.showwarning(traducir_texto("Sin seleccion"), traducir_texto("Selecciona una fila para editar."))
            return

        valores = tree.item(seleccion[0], "values")
        codigo = valores[0]
        roles = obtener_roles_disponibles()
        abrir_formulario_edicion(root, codigo, roles, recargar_tabla, traducir_texto)

    def on_eliminar() -> None:
        tree = tabla_refs["tree"]
        if tree is None:
            return
        seleccion = tree.selection()
        if not seleccion:
            messagebox.showwarning(traducir_texto("Sin seleccion"), traducir_texto("Selecciona una fila para eliminar."))
            return

        valores = tree.item(seleccion[0], "values")
        codigo = valores[0]

        confirmar = messagebox.askyesno(
            traducir_texto("Confirmar eliminacion"),
            f"{traducir_texto('Se eliminara el usuario')} {codigo}. "
            f"{traducir_texto('Esta accion no se puede deshacer.')}\n\n"
            f"{traducir_texto('Deseas continuar?')}",
        )
        if not confirmar:
            return

        try:
            eliminar_usuario(codigo)
            recargar_tabla()
            messagebox.showinfo(traducir_texto("Eliminado"), traducir_texto("Registro eliminado correctamente."))
        except Exception as error:
            messagebox.showerror(traducir_texto("Error"), traducir_texto(f"No se pudo eliminar: {error}"))
    # ________________________FIN_5_3_______________________#

    # __________________________5_4__________________________#
    # Encabezado
    encabezado_refs.update(
        crear_encabezado(
            pantalla,
            root,
            tema_actual,
            aplicar_tema,
            idioma_display_actual,
            opciones_idioma,
            cambiar_idioma_desde_combobox,
            filtrar_idiomas,
            traducir_texto,
        )
    )

    if "cmb_idioma" in encabezado_refs and encabezado_refs["cmb_idioma"] is not None:
        cmb_idioma = encabezado_refs["cmb_idioma"]
        cmb_idioma.bind("<FocusIn>", lambda _event: on_focus_in_idioma(), add="+")
        cmb_idioma.bind("<FocusOut>", lambda _event: on_focus_out_idioma(), add="+")
        cmb_idioma.bind("<KeyRelease>", lambda _event: on_keyrelease_idioma(), add="+")
    # ________________________FIN_5_4_______________________#

    # __________________________5_5__________________________#
    # Contenido principal y filtros
    contenido.pack(fill="both", expand=True)
    ttk.Label(contenido, text="GESTION DE USUARIOS", style="MainTitle.TLabel").pack(anchor="w", pady=(0, 20))

    barra = ttk.Frame(contenido, style="Page.TFrame")
    barra.pack(fill="x", pady=(0, 12))

    ent_busqueda = ttk.Entry(barra, width=26)
    ent_busqueda.insert(0, "Buscar...")
    ent_busqueda._es_placeholder = True
    tabla_refs["ent_busqueda"] = ent_busqueda
    ent_busqueda.pack(side="left", padx=(0, 10), ipady=4)

    valores_roles = ["Todos los roles", *obtener_roles_disponibles()]
    cmb_roles = ttk.Combobox(barra, values=valores_roles, state="readonly", width=18)
    cmb_roles.current(0)
    cmb_roles.pack(side="left", padx=6)

    ttk.Label(barra, text="Dia", style="PageSub.TLabel").pack(side="left", padx=(10, 4))
    date_filtro = DateEntry(barra, width=12, date_pattern="yyyy-mm-dd")
    date_filtro.pack(side="left", padx=(0, 6))
    aplicar_estilo_calendario(date_filtro)

    chk_filtrar_dia = tk.BooleanVar(value=False)
    ttk.Checkbutton(barra, text="Filtrar por dia", variable=chk_filtrar_dia).pack(side="left", padx=(0, 8))

    ttk.Button(barra, text="Aplicar filtros", style="Ghost.TButton", command=recargar_tabla).pack(side="left", padx=6)
    ttk.Button(barra, text="Limpiar dia", style="Ghost.TButton", command=lambda: (chk_filtrar_dia.set(False), recargar_tabla())).pack(side="left", padx=6)
    # ________________________FIN_5_5_______________________#

    # __________________________5_6__________________________#
    # Tabla con scroll
    tabla_container = ttk.Frame(contenido, style="Page.TFrame")
    tabla_container.pack(fill="both", expand=True)

    tree, _scroll = crear_tabla(tabla_container)
    tabla_refs["tree"] = tree

    tree.bind("<Double-1>", lambda _event: on_editar())
    # ________________________FIN_5_6_______________________#

    # __________________________5_7__________________________#
    # Acciones CRUD
    barra_acciones = ttk.Frame(contenido, style="Page.TFrame")
    barra_acciones.pack(fill="x", pady=(10, 0))

    ttk.Button(barra_acciones, text="Editar seleccionado", style="Add.TButton", command=on_editar).pack(side="right")
    ttk.Button(barra_acciones, text="Eliminar seleccionado", style="Ghost.TButton", command=on_eliminar).pack(side="right", padx=(0, 8))
    ttk.Button(
        barra_acciones,
        text="Historial de accesos",
        style="Ghost.TButton",
        command=lambda: abrir_historial_accesos(root, traducir_texto),
    ).pack(side="right", padx=(0, 8))
    ttk.Button(barra_acciones, text="< Regresar", style="Ghost.TButton", command=root.destroy).pack(side="left")
    # ________________________FIN_5_7_______________________#

    # __________________________5_8__________________________#
    # Eventos y primer render
    def limpiar_placeholder(_: tk.Event) -> None:
        if getattr(ent_busqueda, "_es_placeholder", False):
            ent_busqueda.delete(0, tk.END)
            ent_busqueda._es_placeholder = False

    def restaurar_placeholder(_: tk.Event) -> None:
        if not ent_busqueda.get().strip():
            ent_busqueda.delete(0, tk.END)
            ent_busqueda.insert(0, traducir_texto("Buscar..."))
            ent_busqueda._es_placeholder = True

    ent_busqueda.bind("<FocusIn>", limpiar_placeholder)
    ent_busqueda.bind("<FocusOut>", restaurar_placeholder)
    ent_busqueda.bind("<Return>", lambda _event: recargar_tabla())

    aplicar_traduccion_general()
    recargar_tabla()
    root.mainloop()
    # ________________________FIN_5_8_______________________#
# ________________________FIN_5_______________________#


if __name__ == "__main__":
    app()
