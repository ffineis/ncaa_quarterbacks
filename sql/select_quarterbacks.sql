SELECT pl.player_id,
  pl.player_name,
  pl.hometown,
  t.team_name,
  pos.position_name,
  pl.is_caucasian
FROM player pl,
  team t,
  positions pos,
  team_player_position tpp,
  player_stats ps
WHERE pl.player_id = tpp.player_id
AND t.team_id = tpp.team_id
AND pos.position_id = tpp.position_id
AND ps.player_id = tpp.player_id
AND pos.position_name = 'QB'
AND pl.is_caucasian IS NULL
GROUP BY pl.player_id
ORDER BY player_name ASC;
