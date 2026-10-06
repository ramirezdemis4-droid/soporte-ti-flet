-- Ejecuta este script conectado a la base indicada en DB_NAME de .env.
DROP PROCEDURE IF EXISTS asignar_tecnico;
DELIMITER $$
CREATE PROCEDURE asignar_tecnico(IN p_ticket_id INT, IN p_tecnico_id INT)
BEGIN
  DECLARE v_especialidad INT DEFAULT NULL;
  DECLARE v_estado VARCHAR(20) DEFAULT NULL;
  DECLARE v_activo INT DEFAULT NULL;
  DECLARE v_compatible INT DEFAULT 0;

  SELECT especialidad_id, estado INTO v_especialidad, v_estado
  FROM tickets WHERE id = p_ticket_id;

  IF v_especialidad IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El ticket no existe';
  END IF;
  IF v_estado IN ('Resuelto', 'Cerrado') THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No se asignan tickets resueltos o cerrados';
  END IF;

  SELECT activo INTO v_activo FROM tecnicos WHERE id = p_tecnico_id;
  IF v_activo IS NULL OR v_activo = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El técnico no existe o está inactivo';
  END IF;

  SELECT COUNT(*) INTO v_compatible FROM tecnico_especialidad
  WHERE tecnico_id = p_tecnico_id AND especialidad_id = v_especialidad;
  IF v_compatible = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El técnico no tiene la especialidad del ticket';
  END IF;

  UPDATE tickets SET tecnico_id = p_tecnico_id, estado = 'En proceso'
  WHERE id = p_ticket_id AND estado IN ('Pendiente', 'En proceso');
  IF ROW_COUNT() = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No se pudo asignar el ticket';
  END IF;
END$$
DELIMITER ;
