USE soporte_ti;
DROP TRIGGER IF EXISTS tr_historial_estado;
DELIMITER $$
CREATE TRIGGER tr_historial_estado
AFTER UPDATE ON tickets
FOR EACH ROW
BEGIN
  IF OLD.estado <> NEW.estado THEN
    INSERT INTO historial_tickets(ticket_id, estado_anterior, estado_nuevo)
    VALUES (NEW.id, OLD.estado, NEW.estado);
  END IF;
END$$
DELIMITER ;

