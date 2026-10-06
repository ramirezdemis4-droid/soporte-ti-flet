"""Consultas MySQL del sistema de soporte TI."""

import os
from contextlib import contextmanager

import mysql.connector
from dotenv import load_dotenv

load_dotenv()


@contextmanager
def conexion():
    """Abre una conexión por operación y la cierra incluso si ocurre un error."""
    con = mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "soporte_ti"),
        connection_timeout=5,
    )
    try:
        yield con
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def consultar(sql, valores=()):
    with conexion() as con:
        with con.cursor(dictionary=True) as cur:
            cur.execute(sql, valores)
            return cur.fetchall()


def ejecutar(sql, valores=()):
    with conexion() as con:
        with con.cursor() as cur:
            cur.execute(sql, valores)
            con.commit()
            return cur.rowcount


def usuarios():
    return consultar("SELECT id, nombre, correo FROM usuarios WHERE activo = TRUE ORDER BY nombre")


def tecnicos():
    return consultar("""SELECT t.id, t.nombre, t.correo,
        GROUP_CONCAT(e.nombre ORDER BY e.nombre SEPARATOR ', ') AS especialidades
        FROM tecnicos t LEFT JOIN tecnico_especialidad x ON x.tecnico_id = t.id
        LEFT JOIN especialidades e ON e.id = x.especialidad_id
        WHERE t.activo = TRUE GROUP BY t.id, t.nombre, t.correo ORDER BY t.nombre""")


def especialidades():
    return consultar("SELECT id, nombre FROM especialidades ORDER BY nombre")


def tickets(texto="", estado="Todos"):
    patron = f"%{texto.strip()}%"
    return consultar("""SELECT t.id, t.titulo, t.descripcion, t.usuario_id,
        t.tecnico_id, t.especialidad_id, t.prioridad, t.estado, t.creado_en,
        u.nombre AS solicitante, COALESCE(te.nombre, 'Sin asignar') AS tecnico,
        e.nombre AS especialidad
        FROM tickets t JOIN usuarios u ON u.id = t.usuario_id
        LEFT JOIN tecnicos te ON te.id = t.tecnico_id
        JOIN especialidades e ON e.id = t.especialidad_id
        WHERE (t.titulo LIKE %s OR u.nombre LIKE %s)
          AND (%s = 'Todos' OR t.estado = %s)
        ORDER BY t.id DESC""", (patron, patron, estado, estado))


def resumen():
    return consultar("SELECT estado, COUNT(*) AS cantidad FROM tickets GROUP BY estado ORDER BY estado")


def historial(ticket_id):
    return consultar("""SELECT estado_anterior, estado_nuevo, cambiado_en
        FROM historial_tickets WHERE ticket_id = %s ORDER BY id DESC""", (ticket_id,))


def guardar_ticket(ticket_id, titulo, descripcion, usuario_id, especialidad_id, prioridad, estado):
    if ticket_id is None:
        ejecutar("""INSERT INTO tickets
            (titulo, descripcion, usuario_id, especialidad_id, prioridad)
            VALUES (%s, %s, %s, %s, %s)""",
            (titulo, descripcion, usuario_id, especialidad_id, prioridad))
    else:
        # Si cambia la especialidad, la asignación anterior deja de ser válida.
        ejecutar("""UPDATE tickets SET titulo = %s, descripcion = %s,
            usuario_id = %s,
            estado = IF(especialidad_id <> %s, 'Pendiente', %s),
            tecnico_id = IF(especialidad_id <> %s, NULL, tecnico_id),
            especialidad_id = %s, prioridad = %s WHERE id = %s""",
            (titulo, descripcion, usuario_id, especialidad_id, estado,
             especialidad_id, especialidad_id, prioridad, ticket_id))


def eliminar_ticket(ticket_id):
    return ejecutar("DELETE FROM tickets WHERE id = %s", (ticket_id,))


def asignar_tecnico(ticket_id, tecnico_id):
    with conexion() as con:
        with con.cursor() as cur:
            cur.callproc("asignar_tecnico", (ticket_id, tecnico_id))
            con.commit()


def agregar_usuario(nombre, correo, departamento, telefono):
    with conexion() as con:
        with con.cursor() as cur:
            cur.execute("INSERT INTO usuarios(nombre, correo) VALUES (%s, %s)", (nombre, correo))
            cur.execute("""INSERT INTO perfiles_usuario(usuario_id, departamento, telefono)
                VALUES (%s, %s, %s)""", (cur.lastrowid, departamento, telefono or None))
            con.commit()


def agregar_tecnico(nombre, correo, especialidad_id):
    with conexion() as con:
        with con.cursor() as cur:
            cur.execute("INSERT INTO tecnicos(nombre, correo) VALUES (%s, %s)", (nombre, correo))
            cur.execute("""INSERT INTO tecnico_especialidad(tecnico_id, especialidad_id)
                VALUES (%s, %s)""", (cur.lastrowid, especialidad_id))
            con.commit()
