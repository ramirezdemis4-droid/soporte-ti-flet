-- Ejecuta este script conectado a la base indicada en DB_NAME de .env.
-- JOIN: información de cuatro tablas en una sola vista.
SELECT t.id, t.titulo, u.nombre AS solicitante,
       COALESCE(te.nombre, 'Sin asignar') AS tecnico,
       e.nombre AS especialidad, t.estado, t.prioridad
FROM tickets t
JOIN usuarios u ON u.id = t.usuario_id
LEFT JOIN tecnicos te ON te.id = t.tecnico_id
JOIN especialidades e ON e.id = t.especialidad_id
ORDER BY t.id DESC;

-- Agrupación: resumen operativo por estado.
SELECT estado, COUNT(*) AS cantidad FROM tickets GROUP BY estado ORDER BY estado;

-- Demostración manual: primero mira el estado, luego ejecuta y mira el historial.
-- CALL asignar_tecnico(1, 1);
-- SELECT * FROM historial_tickets WHERE ticket_id = 1 ORDER BY id;
