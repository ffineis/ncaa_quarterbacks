/* create table for college football team entities */

CREATE TABLE team (
    team_id MEDIUMINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    team_name VARCHAR(128) NOT NULL,
    CONSTRAINT u_team_name UNIQUE (team_name),
    INDEX idx_team_name (team_name)
);