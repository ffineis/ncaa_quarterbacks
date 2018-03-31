/* create table for individual college football players */

CREATE TABLE player(
    player_id MEDIUMINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    player_name VARCHAR(256) NOT NULL,
    player_hometown VARCHAR(256),
    is_caucasian BOOLEAN,
    INDEX idx_player_name (player_name)
);