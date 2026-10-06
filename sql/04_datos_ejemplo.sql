USE soporte_ti;
INSERT IGNORE INTO especialidades (nombre) VALUES ('Hardware'), ('Software'), ('Redes');

INSERT IGNORE INTO usuarios (nombre, correo) VALUES
('Ana Muñoz', 'ana@example.com'), ('Luis Peña', 'luis@example.com');
INSERT IGNORE INTO perfiles_usuario (usuario_id, departamento, telefono)
SELECT id, 'Administración', '111111111' FROM usuarios WHERE correo = 'ana@example.com';
INSERT IGNORE INTO perfiles_usuario (usuario_id, departamento, telefono)
SELECT id, 'Bodega', '222222222' FROM usuarios WHERE correo = 'luis@example.com';

INSERT IGNORE INTO tecnicos (nombre, correo) VALUES
('Carla Rojas', 'carla@example.com'), ('Diego Soto', 'diego@example.com');
INSERT IGNORE INTO tecnico_especialidad (tecnico_id, especialidad_id)
SELECT t.id, e.id FROM tecnicos t CROSS JOIN especialidades e
WHERE (t.correo = 'carla@example.com' AND e.nombre IN ('Software','Hardware'))
   OR (t.correo = 'diego@example.com' AND e.nombre = 'Redes');

-- Crea este ticket solo si todavía no existe uno con este título de ejemplo.
INSERT INTO tickets (titulo, descripcion, usuario_id, especialidad_id, prioridad)
SELECT 'Impresora sin conexión', 'La impresora de la oficina no responde.', u.id, e.id, 'Media'
FROM usuarios u CROSS JOIN especialidades e
WHERE u.correo = 'ana@example.com' AND e.nombre = 'Hardware'
  AND NOT EXISTS (SELECT 1 FROM tickets WHERE titulo = 'Impresora sin conexión');

