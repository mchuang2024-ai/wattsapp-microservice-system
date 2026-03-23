CREATE DATABASE IF NOT EXISTS maintenance;
USE maintenance;

DROP TABLE IF EXISTS MaintenanceTicket;

CREATE TABLE MaintenanceTicket (
    ticketID INT AUTO_INCREMENT PRIMARY KEY,
    slotID VARCHAR(50) NOT NULL,
    reportedBy INT NOT NULL,
    description VARCHAR(255),
    chargerType VARCHAR(50),
    status VARCHAR(20) DEFAULT 'OPEN'
);

-- Dummy data
INSERT INTO MaintenanceTicket (slotID, reportedBy, description, chargerType, status)
VALUES
('S1', 1, 'Charger not working', 'fast', 'OPEN'),
('S2', 2, 'Cable damaged', 'slow', 'OPEN');