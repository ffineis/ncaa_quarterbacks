/* relationship table expressing temporal (conference, team) relationships) */

CREATE TABLE conference_team (
    team_id MEDIUMINT NOT NULL,
    conference_id MEDIUMINT NOT NULL,
    year YEAR,
    games_won MEDIUMINT,
    games_lost MEDIUMINT,
    CONSTRAINT fk_ctt_team_id FOREIGN KEY (team_id) REFERENCES team(team_id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_ctt_conference_id FOREIGN KEY (conference_id) REFERENCES conference(conference_id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT u_ct_conference_team_year UNIQUE (conference_id, team_id, year),
    INDEX idx_ct_team_conference_year (team_id, conference_id, year)
);
