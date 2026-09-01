/*
SQLyog Community v13.3.1
Database: scamshield_db
Compatible collation: utf8mb4_unicode_ci
*/

SET NAMES utf8mb4;
SET SQL_MODE = '';

SET @OLD_UNIQUE_CHECKS = @@UNIQUE_CHECKS;
SET UNIQUE_CHECKS = 0;

SET @OLD_FOREIGN_KEY_CHECKS = @@FOREIGN_KEY_CHECKS;
SET FOREIGN_KEY_CHECKS = 0;

SET @OLD_SQL_MODE = @@SQL_MODE;
SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO';

SET @OLD_SQL_NOTES = @@SQL_NOTES;
SET SQL_NOTES = 0;


/* =========================================================
   DATABASE
   ========================================================= */

DROP DATABASE IF EXISTS `scamshield_db`;

CREATE DATABASE `scamshield_db`
DEFAULT CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE `scamshield_db`;


/* =========================================================
   TABLE: demo_cases
   ========================================================= */

DROP TABLE IF EXISTS `demo_cases`;

CREATE TABLE `demo_cases` (
    `case_id` INT NOT NULL AUTO_INCREMENT,
    `title` VARCHAR(100) NOT NULL,
    `sample_message` VARCHAR(2000) DEFAULT NULL,
    `sample_number` VARCHAR(20) DEFAULT NULL,
    `sample_link` VARCHAR(500) DEFAULT NULL,
    `expected_level` VARCHAR(20) DEFAULT NULL,

    PRIMARY KEY (`case_id`)
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;


/* =========================================================
   DATA: demo_cases
   ========================================================= */

INSERT INTO `demo_cases`
(
    `case_id`,
    `title`,
    `sample_message`,
    `sample_number`,
    `sample_link`,
    `expected_level`
)
VALUES
(
    1,
    'SBI KYC Phishing Alert',
    'Dear customer, your SBI account is suspended today. Update KYC immediately at http://secure-sbi-update-kyc.com',
    '+919876543210',
    'http://secure-sbi-update-kyc.com',
    'CRITICAL'
),
(
    2,
    'Telegram Crypto Scam',
    'You won 0.5 BTC! Claim your reward now at http://free-crypto-airdrop.xyz',
    '+919123456789',
    'http://free-crypto-airdrop.xyz',
    'HIGH'
),
(
    3,
    'Electricity Disconnection Scam',
    'Dear consumer your electricity line will be disconnected tonight at 9:30 PM. Call officer at +918888877777',
    '+918888877777',
    NULL,
    'CRITICAL'
),
(
    4,
    'YouTube Like Job Scam',
    'Earn Rs 5000/day by liking YouTube videos. Join our Telegram group now!',
    '+919999900000',
    'http://amazon-parttime-job.vip',
    'HIGH'
),
(
    5,
    'Fake Traffic E-Challan',
    'Traffic Challan pending against your vehicle. Clear fine before court notice: http://paytm-cashback-claim.org',
    '+917000011111',
    'http://paytm-cashback-claim.org',
    'MEDIUM'
);


/* =========================================================
   TABLE: messages_log
   ========================================================= */

DROP TABLE IF EXISTS `messages_log`;

CREATE TABLE `messages_log` (
    `scan_id` INT NOT NULL AUTO_INCREMENT,
    `message` VARCHAR(2000) DEFAULT NULL,
    `phone_number` VARCHAR(20) DEFAULT NULL,
    `link` VARCHAR(500) DEFAULT NULL,
    `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`scan_id`)
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;


/* =========================================================
   DATA: messages_log
   ========================================================= */

INSERT INTO `messages_log`
(
    `scan_id`,
    `message`,
    `phone_number`,
    `link`,
    `created_at`
)
VALUES
(
    1,
    'Dear customer, your SBI account is suspended today. Update KYC immediately at http://secure-sbi-update-kyc.com',
    '+919876543210',
    'http://secure-sbi-update-kyc.com',
    '2026-08-20 13:01:17'
),
(
    2,
    'You won 0.5 BTC! Claim your reward now at http://free-crypto-airdrop.xyz',
    '+919123456789',
    'http://free-crypto-airdrop.xyz',
    '2026-08-20 13:01:17'
),
(
    3,
    'Dear consumer your electricity line will be disconnected tonight at 9:30 PM. Call officer at +918888877777',
    '+918888877777',
    NULL,
    '2026-08-20 13:01:17'
),
(
    4,
    'Earn Rs 5000/day by liking YouTube videos. Join our Telegram group now!',
    '+919999900000',
    'http://amazon-parttime-job.vip',
    '2026-08-20 13:01:17'
),
(
    5,
    'Traffic Challan pending against your vehicle. Clear fine before court notice: http://paytm-cashback-claim.org',
    '+917000011111',
    'http://paytm-cashback-claim.org',
    '2026-08-20 13:01:17'
);


/* =========================================================
   TABLE: scam_patterns
   ========================================================= */

DROP TABLE IF EXISTS `scam_patterns`;

CREATE TABLE `scam_patterns` (
    `pattern_id` INT NOT NULL AUTO_INCREMENT,
    `pattern_name` VARCHAR(100) NOT NULL,
    `description` VARCHAR(500) DEFAULT NULL,
    `keywords` VARCHAR(500) DEFAULT NULL,
    `risk_score` INT DEFAULT NULL,

    PRIMARY KEY (`pattern_id`)
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;


/* =========================================================
   DATA: scam_patterns
   ========================================================= */

INSERT INTO `scam_patterns`
(
    `pattern_id`,
    `pattern_name`,
    `description`,
    `keywords`,
    `risk_score`
)
VALUES
(
    1,
    'Banking Urgency Scam',
    'Urgent request to verify bank account or KYC to avoid suspension.',
    'KYC, block, expired, urgent, verify',
    90
),
(
    2,
    'Lottery Fraud',
    'Fake claims of winning cash prize requiring processing fee.',
    'congratulations, won, claim, cash, transfer',
    85
),
(
    3,
    'Part-Time Job Scam',
    'Promises easy daily income via YouTube likes or Telegram tasks.',
    'part-time, earn daily, telegram, task, pre-pay',
    88
),
(
    4,
    'Electricity Bill Threat',
    'Threatens to disconnect power supply tonight if bill is not paid via link.',
    'electricity, power cut, bill due, tonight, light officer',
    95
),
(
    5,
    'E-Challan Fake Alert',
    'Fake traffic violation notice forcing payment on scam URL.',
    'challan, traffic police, pending fine, pay immediately',
    82
);


/* =========================================================
   TABLE: spam_numbers
   ========================================================= */

DROP TABLE IF EXISTS `spam_numbers`;

CREATE TABLE `spam_numbers` (
    `number_id` INT NOT NULL AUTO_INCREMENT,
    `phone_number` VARCHAR(20) NOT NULL,
    `reputation` VARCHAR(50) DEFAULT NULL,
    `report_count` INT DEFAULT 0,

    PRIMARY KEY (`number_id`),
    UNIQUE KEY `unique_phone_number` (`phone_number`)
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;


/* =========================================================
   DATA: spam_numbers
   ========================================================= */

INSERT INTO `spam_numbers`
(
    `number_id`,
    `phone_number`,
    `reputation`,
    `report_count`
)
VALUES
(
    1,
    '+919876543210',
    'HIGH_RISK',
    142
),
(
    2,
    '+919123456789',
    'SUSPICIOUS',
    28
),
(
    3,
    '+918888877777',
    'HIGH_RISK',
    210
),
(
    4,
    '+917000011111',
    'SAFE',
    0
),
(
    5,
    '+919999900000',
    'HIGH_RISK',
    89
);


/* =========================================================
   TABLE: spam_domains
   ========================================================= */

DROP TABLE IF EXISTS `spam_domains`;

CREATE TABLE `spam_domains` (
    `domain_id` INT NOT NULL AUTO_INCREMENT,
    `domain` VARCHAR(255) NOT NULL,
    `brand_misuse` VARCHAR(100) DEFAULT NULL,
    `reputation` VARCHAR(50) DEFAULT NULL,

    PRIMARY KEY (`domain_id`),
    UNIQUE KEY `unique_domain` (`domain`)
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;


/* =========================================================
   DATA: spam_domains
   ========================================================= */

INSERT INTO `spam_domains`
(
    `domain_id`,
    `domain`,
    `brand_misuse`,
    `reputation`
)
VALUES
(
    1,
    'secure-sbi-update-kyc.com',
    'SBI Bank',
    'MALICIOUS'
),
(
    2,
    'free-crypto-airdrop.xyz',
    'Binance',
    'PHISHING'
),
(
    3,
    'hdfc-rewards-login.net',
    'HDFC Bank',
    'MALICIOUS'
),
(
    4,
    'paytm-cashback-claim.org',
    'Paytm',
    'SUSPICIOUS'
),
(
    5,
    'amazon-parttime-job.vip',
    'Amazon',
    'MALICIOUS'
);


/* =========================================================
   TABLE: scan_results
   ========================================================= */

DROP TABLE IF EXISTS `scan_results`;

CREATE TABLE `scan_results` (
    `result_id` INT NOT NULL AUTO_INCREMENT,
    `scan_id` INT NOT NULL,

    `final_score` INT DEFAULT NULL,
    `risk_level` VARCHAR(20) DEFAULT NULL,
    `recommendation` VARCHAR(500) DEFAULT NULL,

    `message_score` INT DEFAULT NULL,
    `number_score` INT DEFAULT NULL,
    `link_score` INT DEFAULT NULL,

    PRIMARY KEY (`result_id`),
    KEY `idx_scan_results_scan_id` (`scan_id`),

    CONSTRAINT `scan_results_ibfk_1`
        FOREIGN KEY (`scan_id`)
        REFERENCES `messages_log` (`scan_id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;


/* =========================================================
   DATA: scan_results
   ========================================================= */

INSERT INTO `scan_results`
(
    `result_id`,
    `scan_id`,
    `final_score`,
    `risk_level`,
    `recommendation`,
    `message_score`,
    `number_score`,
    `link_score`
)
VALUES
(
    1,
    1,
    92,
    'CRITICAL',
    'Do not click the link. Block sender immediately and report on cybercrime portal.',
    88,
    95,
    93
),
(
    2,
    2,
    84,
    'HIGH',
    'Potentially fraudulent giveaway. Do not connect your crypto wallet.',
    80,
    80,
    92
),
(
    3,
    3,
    96,
    'CRITICAL',
    'Impersonation scam. Do not call the provided contact number.',
    95,
    98,
    0
),
(
    4,
    4,
    88,
    'HIGH',
    'Task-based financial fraud scheme detected.',
    85,
    89,
    90
),
(
    5,
    5,
    75,
    'MEDIUM',
    'Suspicious URL posing as official payment gateway.',
    70,
    20,
    85
);


/* =========================================================
   TABLE: scan_explanations
   ========================================================= */

DROP TABLE IF EXISTS `scan_explanations`;

CREATE TABLE `scan_explanations` (
    `explanation_id` INT NOT NULL AUTO_INCREMENT,
    `scan_id` INT NOT NULL,

    `fingerprint_json` JSON DEFAULT NULL,
    `attack_chain_json` JSON DEFAULT NULL,
    `confidence` VARCHAR(20) DEFAULT NULL,
    `what_if_json` JSON DEFAULT NULL,

    PRIMARY KEY (`explanation_id`),
    KEY `idx_scan_explanations_scan_id` (`scan_id`),

    CONSTRAINT `scan_explanations_ibfk_1`
        FOREIGN KEY (`scan_id`)
        REFERENCES `messages_log` (`scan_id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;


/* =========================================================
   DATA: scan_explanations
   ========================================================= */

INSERT INTO `scan_explanations`
(
    `explanation_id`,
    `scan_id`,
    `fingerprint_json`,
    `attack_chain_json`,
    `confidence`,
    `what_if_json`
)
VALUES
(
    1,
    1,
    '{"type":"Phishing","brand":"SBI"}',
    '{"step1":"SMS received","step2":"Link redirects to fake login"}',
    '98%',
    '{"if_clicked":"Bank credentials compromised"}'
),
(
    2,
    2,
    '{"type":"Crypto Fraud","brand":"Binance"}',
    '{"step1":"Unsolicited reward","step2":"Malicious smart contract call"}',
    '91%',
    '{"if_clicked":"Wallet drained"}'
),
(
    3,
    3,
    '{"type":"Impersonation","brand":"State Electricity Board"}',
    '{"step1":"Threat SMS","step2":"Coerced direct call/transfer"}',
    '99%',
    '{"if_called":"Social engineering pressure for quick payment"}'
),
(
    4,
    4,
    '{"type":"Employment Scam","brand":"Amazon/YouTube"}',
    '{"step1":"Task lure","step2":"Telegram onboarding","step3":"Prepayment demand"}',
    '94%',
    '{"if_joined":"Advanced fee scam loss"}'
),
(
    5,
    5,
    '{"type":"Smishing","brand":"Traffic Police"}',
    '{"step1":"Fake fine SMS","step2":"Phishing gateway"}',
    '89%',
    '{"if_clicked":"Payment gateway credential harvesting"}'
);


/* =========================================================
   TABLE: feedback_events
   ========================================================= */

DROP TABLE IF EXISTS `feedback_events`;

CREATE TABLE `feedback_events` (
    `feedback_id` INT NOT NULL AUTO_INCREMENT,
    `scan_id` INT NOT NULL,
    `verdict` VARCHAR(50) DEFAULT NULL,
    `note` VARCHAR(500) DEFAULT NULL,
    `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (`feedback_id`),
    KEY `idx_feedback_scan_id` (`scan_id`),

    CONSTRAINT `feedback_events_ibfk_1`
        FOREIGN KEY (`scan_id`)
        REFERENCES `messages_log` (`scan_id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;


/* =========================================================
   DATA: feedback_events
   ========================================================= */

INSERT INTO `feedback_events`
(
    `feedback_id`,
    `scan_id`,
    `verdict`,
    `note`,
    `created_at`
)
VALUES
(
    1,
    1,
    'CONFIRMED_SCAM',
    'Verified phishing URL mimicking official SBI domain',
    '2026-08-20 13:01:17'
),
(
    2,
    2,
    'CONFIRMED_SCAM',
    'Reported by community users as wallet drainer',
    '2026-08-20 13:01:17'
),
(
    3,
    3,
    'CONFIRMED_SCAM',
    'Known electricity bill scam pattern active nationwide',
    '2026-08-20 13:01:17'
),
(
    4,
    4,
    'CONFIRMED_SCAM',
    'Telegram task scam reported multiple times',
    '2026-08-20 13:01:17'
),
(
    5,
    5,
    'SUSPICIOUS',
    'Pending manual verification by domain scanner',
    '2026-08-20 13:01:17'
);


/* =========================================================
   RESET AUTO_INCREMENT
   ========================================================= */

ALTER TABLE `demo_cases`
    AUTO_INCREMENT = 6;

ALTER TABLE `messages_log`
    AUTO_INCREMENT = 6;

ALTER TABLE `scam_patterns`
    AUTO_INCREMENT = 6;

ALTER TABLE `spam_numbers`
    AUTO_INCREMENT = 6;

ALTER TABLE `spam_domains`
    AUTO_INCREMENT = 6;

ALTER TABLE `scan_results`
    AUTO_INCREMENT = 6;

ALTER TABLE `scan_explanations`
    AUTO_INCREMENT = 6;

ALTER TABLE `feedback_events`
    AUTO_INCREMENT = 6;


/* =========================================================
   RESTORE SETTINGS
   ========================================================= */

SET SQL_MODE = @OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS = @OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS = @OLD_UNIQUE_CHECKS;
SET SQL_NOTES = @OLD_SQL_NOTES;


/* =========================================================
   TEST
   ========================================================= */

USE `scamshield_db`;

SELECT 'ScamShield Database Created Successfully' AS status;

SELECT
    TABLE_NAME
FROM
    INFORMATION_SCHEMA.TABLES
WHERE
    TABLE_SCHEMA = 'scamshield_db'
ORDER BY
    TABLE_NAME;