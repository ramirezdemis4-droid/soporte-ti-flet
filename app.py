"""Interfaz de escritorio Flet para registrar y administrar tickets."""

import flet as ft
import mysql.connector

import database as db


ESTADOS = ["Pendiente", "En proceso", "Resuelto", "Cerrado"]
PRIORIDADES = ["Baja", "Media", "Alta"]


def main(page: ft.Page):
    page.title = "Mesa de ayuda | Soporte TI"
    page.window_width = 1180
    page.window_height = 780
    page.padding = 22
    page.scroll = ft.ScrollMode.AUTO
    page.theme_mode = ft.ThemeMode.LIGHT

    titulo = ft.Text("Mesa de ayuda TI", size=28, weight=ft.FontWeight.BOLD)
    subtitulo = ft.Text("Registra solicitudes y sigue el trabajo de los técnicos.")
    contenido = ft.Column(spacing=15)
    busqueda = ft.TextField(label="Buscar título o solicitante", width=300,
                            on_change=lambda e: mostrar_tickets())
    filtro = ft.Dropdown(label="Estado", width=170, value="Todos",
                         options=[ft.dropdown.Option(x) for x in ["Todos", *ESTADOS]],
                         on_change=lambda e: mostrar_tickets())

    def aviso(mensaje, error=False):
        page.snack_bar = ft.SnackBar(ft.Text(str(mensaje)),
                                     bgcolor="#B42318" if error else "#16794A")
        page.snack_bar.open = True
        page.update()

    def accion(funcion, exito):
        try:
            funcion()
            aviso(exito)
            return True
        except (mysql.connector.Error, ValueError) as exc:
            aviso(f"No se pudo completar la operación: {exc}", True)
            return False

    def cambiar_vista(nombre):
        try:
            if nombre == "tickets":
                mostrar_tickets()
            elif nombre == "datos":
                mostrar_datos()
            else:
                mostrar_resumen()
        except (mysql.connector.Error, ValueError) as exc:
            contenido.controls = [ft.Text("No se pudo conectar a MySQL. Revisa .env y ejecuta los SQL."),
                                  ft.Text(str(exc), color="#B42318")]
            page.update()

    def abrir_formulario(ticket=None):
        try:
            lista_usuarios = db.usuarios()
            lista_especialidades = db.especialidades()
        except mysql.connector.Error as exc:
            aviso(exc, True)
            return
        if not lista_usuarios or not lista_especialidades:
            aviso("Primero crea un usuario y una especialidad.", True)
            return

        campo_titulo = ft.TextField(label="Título", value=ticket["titulo"] if ticket else "", width=430)
        descripcion = ft.TextField(label="Descripción", multiline=True, min_lines=2,
                                   max_lines=3, value=ticket["descripcion"] if ticket else "")
        usuario = ft.Dropdown(label="Solicitante", width=260,
                              value=str(ticket["usuario_id"]) if ticket else None,
                              options=[ft.dropdown.Option(str(u["id"]), u["nombre"]) for u in lista_usuarios])
        especialidad = ft.Dropdown(label="Especialidad", width=220,
                                  value=str(ticket["especialidad_id"]) if ticket else None,
                                  options=[ft.dropdown.Option(str(e["id"]), e["nombre"]) for e in lista_especialidades])
        prioridad = ft.Dropdown(label="Prioridad", width=150,
                                value=ticket["prioridad"] if ticket else "Media",
                                options=[ft.dropdown.Option(p) for p in PRIORIDADES])
        estado = ft.Dropdown(label="Estado", width=180,
                             value=ticket["estado"] if ticket else "Pendiente",
                             options=[ft.dropdown.Option(s) for s in ESTADOS],
                             visible=ticket is not None)

        def guardar(e):
            if not campo_titulo.value.strip() or not descripcion.value.strip():
                aviso("Escribe un título y una descripción.", True)
                return
            if not usuario.value or not especialidad.value:
                aviso("Selecciona un solicitante y una especialidad.", True)
                return
            if ticket and ticket["estado"] == "Cerrado" and estado.value != "Cerrado":
                aviso("No se puede reabrir un ticket cerrado.", True)
                return
            if ticket and ticket["especialidad_id"] != int(especialidad.value):
                aviso("La especialidad cambió: se quitará el técnico y el ticket quedará Pendiente.")
            if accion(lambda: db.guardar_ticket(
                ticket["id"] if ticket else None, campo_titulo.value.strip(),
                descripcion.value.strip(), int(usuario.value), int(especialidad.value),
                prioridad.value, estado.value), "Ticket guardado correctamente"):
                dialogo.open = False
                page.update()
                mostrar_tickets()

        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("Editar ticket" if ticket else "Nuevo ticket"),
            content=ft.Column([campo_titulo, descripcion,
                               ft.Row([usuario, especialidad], wrap=True),
                               ft.Row([prioridad, estado])], tight=True, scroll=ft.ScrollMode.AUTO,
                              width=520, height=390),
            actions=[ft.TextButton("Cancelar", on_click=lambda e: cerrar_dialogo(dialogo)),
                     ft.ElevatedButton("Guardar", on_click=guardar)])
        page.dialog = dialogo
        dialogo.open = True
        page.update()

    def cerrar_dialogo(dialogo):
        dialogo.open = False
        page.update()

    def confirmar_eliminacion(ticket):
        def borrar(e):
            if accion(lambda: db.eliminar_ticket(ticket["id"]), "Ticket eliminado"):
                cerrar_dialogo(dialogo)
                mostrar_tickets()
        dialogo = ft.AlertDialog(
            title=ft.Text("Confirmar eliminación"),
            content=ft.Text(f"¿Eliminar el ticket #{ticket['id']} y su historial?"),
            actions=[ft.TextButton("Cancelar", on_click=lambda e: cerrar_dialogo(dialogo)),
                     ft.ElevatedButton("Eliminar", on_click=borrar)])
        page.dialog = dialogo
        dialogo.open = True
        page.update()

    def abrir_asignacion(ticket):
        try:
            tecnicos = db.tecnicos()
        except mysql.connector.Error as exc:
            aviso(exc, True)
            return
        tecnico = ft.Dropdown(label="Técnico", width=300,
                              options=[ft.dropdown.Option(str(t["id"]),
                                       f"{t['nombre']} · {t['especialidades'] or 'Sin especialidad'}")
                                       for t in tecnicos])

        def asignar(e):
            if not tecnico.value:
                aviso("Selecciona un técnico.", True)
                return
            if accion(lambda: db.asignar_tecnico(ticket["id"], int(tecnico.value)),
                      "Técnico asignado; el ticket pasó a En proceso"):
                cerrar_dialogo(dialogo)
                mostrar_tickets()

        dialogo = ft.AlertDialog(title=ft.Text(f"Asignar ticket #{ticket['id']}"),
                                 content=ft.Column([tecnico,
                                    ft.Text("Solo se aceptan técnicos con la especialidad del ticket.")],
                                    tight=True),
                                 actions=[ft.TextButton("Cancelar", on_click=lambda e: cerrar_dialogo(dialogo)),
                                          ft.ElevatedButton("Asignar", on_click=asignar)])
        page.dialog = dialogo
        dialogo.open = True
        page.update()

    def ver_historial(ticket):
        try:
            cambios = db.historial(ticket["id"])
        except mysql.connector.Error as exc:
            aviso(exc, True)
            return
        lineas = [ft.Text(f"{c['cambiado_en']}: {c['estado_anterior']} → {c['estado_nuevo']}")
                  for c in cambios] or [ft.Text("Todavía no hay cambios de estado.")]
        dialogo = ft.AlertDialog(title=ft.Text(f"Historial del ticket #{ticket['id']}"),
                                 content=ft.Column(lineas, tight=True, scroll=ft.ScrollMode.AUTO,
                                                   height=min(300, max(80, len(lineas) * 50))),
                                 actions=[ft.TextButton("Cerrar", on_click=lambda e: cerrar_dialogo(dialogo))])
        page.dialog = dialogo
        dialogo.open = True
        page.update()

    def mostrar_tickets():
        try:
            filas = db.tickets(busqueda.value or "", filtro.value or "Todos")
        except mysql.connector.Error as exc:
            contenido.controls = [ft.Text(f"Error al consultar tickets: {exc}", color="#B42318")]
            page.update()
            return
        tabla = ft.DataTable(
            columns=[ft.DataColumn(ft.Text(t)) for t in
                     ["ID", "Título", "Solicitante", "Especialidad", "Técnico", "Prioridad", "Estado", "Acciones"]],
            rows=[ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(t["id"]))), ft.DataCell(ft.Text(t["titulo"])),
                ft.DataCell(ft.Text(t["solicitante"])), ft.DataCell(ft.Text(t["especialidad"])),
                ft.DataCell(ft.Text(t["tecnico"])), ft.DataCell(ft.Text(t["prioridad"])),
                ft.DataCell(ft.Text(t["estado"])),
                ft.DataCell(ft.Row([
                    ft.TextButton("Editar", on_click=lambda e, item=t: abrir_formulario(item)),
                    ft.TextButton("Asignar", on_click=lambda e, item=t: abrir_asignacion(item)),
                    ft.TextButton("Historial", on_click=lambda e, item=t: ver_historial(item)),
                    ft.TextButton("Eliminar", on_click=lambda e, item=t: confirmar_eliminacion(item)),
                ], spacing=0)),
            ]) for t in filas])
        contenido.controls = [ft.Row([ft.Text("Tickets", size=22, weight=ft.FontWeight.BOLD),
                                      ft.ElevatedButton("+ Nuevo ticket", on_click=lambda e: abrir_formulario())]),
                              ft.Row([busqueda, filtro], wrap=True),
                              ft.Row([tabla], scroll=ft.ScrollMode.AUTO)
                              if filas else ft.Text("No hay tickets para mostrar.")]
        page.update()

    def mostrar_datos():
        nombre_u = ft.TextField(label="Nombre del usuario", width=250)
        correo_u = ft.TextField(label="Correo", width=270)
        departamento = ft.TextField(label="Departamento", width=230)
        telefono = ft.TextField(label="Teléfono (opcional)", width=190)
        nombre_t = ft.TextField(label="Nombre del técnico", width=250)
        correo_t = ft.TextField(label="Correo del técnico", width=270)
        try:
            opciones = db.especialidades()
            lista_usuarios = db.usuarios()
            lista_tecnicos = db.tecnicos()
        except mysql.connector.Error as exc:
            contenido.controls = [ft.Text(f"Error de base de datos: {exc}", color="#B42318")]
            page.update()
            return
        especialidad_t = ft.Dropdown(label="Especialidad inicial", width=220,
                                    options=[ft.dropdown.Option(str(x["id"]), x["nombre"]) for x in opciones])

        def crear_usuario(e):
            if not all([nombre_u.value.strip(), correo_u.value.strip(), departamento.value.strip()]):
                aviso("Completa nombre, correo y departamento.", True)
                return
            if accion(lambda: db.agregar_usuario(nombre_u.value.strip(), correo_u.value.strip(),
                                                 departamento.value.strip(), telefono.value.strip()),
                      "Usuario y perfil registrados"):
                mostrar_datos()

        def crear_tecnico(e):
            if not nombre_t.value.strip() or not correo_t.value.strip() or not especialidad_t.value:
                aviso("Completa nombre, correo y especialidad.", True)
                return
            if accion(lambda: db.agregar_tecnico(nombre_t.value.strip(), correo_t.value.strip(),
                                                 int(especialidad_t.value)),
                      "Técnico y especialidad registrados"):
                mostrar_datos()

        contenido.controls = [
            ft.Text("Usuarios y técnicos", size=22, weight=ft.FontWeight.BOLD),
            ft.Text("Nuevo solicitante (se crea también su perfil 1:1)", weight=ft.FontWeight.BOLD),
            ft.Row([nombre_u, correo_u, departamento, telefono], wrap=True),
            ft.ElevatedButton("Guardar usuario", on_click=crear_usuario),
            ft.Text("Nuevo técnico", weight=ft.FontWeight.BOLD),
            ft.Row([nombre_t, correo_t, especialidad_t], wrap=True),
            ft.ElevatedButton("Guardar técnico", on_click=crear_tecnico),
            ft.Text("Solicitantes: " + ", ".join(x["nombre"] for x in lista_usuarios)),
            ft.Text("Técnicos: " + ", ".join(f"{x['nombre']} ({x['especialidades'] or 'sin especialidad'})"
                                            for x in lista_tecnicos)),
        ]
        page.update()

    def mostrar_resumen():
        try:
            conteos = db.resumen()
        except mysql.connector.Error as exc:
            contenido.controls = [ft.Text(f"Error de base de datos: {exc}", color="#B42318")]
            page.update()
            return
        cantidades = {x["estado"]: x["cantidad"] for x in conteos}
        contenido.controls = [ft.Text("Resumen de tickets", size=22, weight=ft.FontWeight.BOLD),
                              ft.Text("Consulta SQL con GROUP BY"),
                              ft.Row([ft.Container(content=ft.Column([
                                  ft.Text(estado, size=17),
                                  ft.Text(str(cantidades.get(estado, 0)), size=30,
                                          weight=ft.FontWeight.BOLD)]),
                                  padding=16, border=ft.border.all(1, "#CCCCCC"),
                                  border_radius=8, width=180)
                                  for estado in ESTADOS], wrap=True)]
        page.update()

    page.add(titulo, subtitulo,
             ft.Row([ft.ElevatedButton("Tickets", on_click=lambda e: cambiar_vista("tickets")),
                     ft.ElevatedButton("Usuarios y técnicos", on_click=lambda e: cambiar_vista("datos")),
                     ft.ElevatedButton("Resumen", on_click=lambda e: cambiar_vista("resumen"))], wrap=True),
             ft.Divider(), contenido)
    cambiar_vista("tickets")


if __name__ == "__main__":
    ft.app(target=main)
