-- =============================================
-- Notification Service Database Setup
-- Run this on your Railway MySQL instance
-- =============================================

CREATE DATABASE IF NOT EXISTS notification;
USE notification;

DROP TABLE IF EXISTS Notification;

CREATE TABLE IF NOT EXISTS Notification (
    notificationID INT AUTO_INCREMENT PRIMARY KEY,
    driverID INT NULL,
    message VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    sentAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(10) NOT NULL DEFAULT 'sent'
        CHECK (status IN ('sent', 'failed'))
);

-- Dummy data for testing
INSERT INTO Notification (notificationID, driverID, message, type, sentAt, status) VALUES
(1, 1, 'Your booking #1 is confirmed.', 'booking', '2026-03-20 08:00:00', 'sent'),
(2, 2, 'You have been charged a late fee.', 'late-fee', '2026-03-20 12:20:00', 'sent'),
(3, 3, 'No-show detected. Deposit forfeited.', 'no-show', '2026-03-21 09:05:00', 'sent'),
(4, NULL, 'Fault reported at slot 3.', 'fault', '2026-03-21 14:00:00', 'sent');
