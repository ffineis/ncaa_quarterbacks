/* create table for expressing (inherently temporal) relationships between players,
college football teams, and a players position on a team over time */

CREATE TABLE team_player_position(
    player_id MEDIUMINT NOT NULL,
    team_id MEDIUMINT NOT NULL,
    position_id MEDIUMINT NOT NULL,
    year Year NOT NULL,
    year_in_school VARCHAR(4) NOT NULL,
    height VARCHAR(8),
    weight SMALLINT,
    CONSTRAINT fk_tpp_player_id FOREIGN KEY (player_id) REFERENCES player(player_id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_tpp_team_id FOREIGN KEY (team_id) REFERENCES team(team_id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_tpp_position_id FOREIGN KEY (position_id) REFERENCES positions(position_id) ON UPDATE CASCADE ON DELETE CASCADE,
    INDEX idx_tpp_player_team_position_year (player_id, team_id, position_id, year)
)