/* create table for possible football player positions */

CREATE TABLE positions(
    position_id MEDIUMINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    position_name VARCHAR(4) NOT NULL,
    CONSTRAINT u_position_name UNIQUE (position_name),
    INDEX idx_position_name (position_name)
);