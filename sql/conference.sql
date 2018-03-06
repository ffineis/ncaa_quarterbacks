/* create table for college football team conferences */

CREATE TABLE conference(
    conference_id MEDIUMINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    conference_name VARCHAR(64) NOT NULL,
    CONSTRAINT u_conference_name UNIQUE (conference_name),
    INDEX idx_conference_name (conference_name)
);

