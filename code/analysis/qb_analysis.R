require(usmap)
require(data.table)
require(ggplot2)
require(RMySQL)
require(extrafont)


# -------------------------------------------------- #
# Helper functions                                   #
# -------------------------------------------------- #
GetFipsCodes <- function(fipsFile = './etc/fips_codes.txt'){ # edit relative path as needed
  fipsDT <- fread(fipsFile
                  , sep = '\t'
                  , col.names = c('state', 'fips'))
  return(fipsDT)
}
  

# -------------------------------------------------- #
# Connect to college_football database and get data  #
# -------------------------------------------------- #
conn <- DBI::dbConnect(RMySQL::MySQL()
                       , dbname = 'college_football'
                       , host = 'localhost'
                       , user = 'ffineis'
                       , password = 'password') # make a better password than this
on.exit({dbDisconnect(conn)})

# Query for team- and conference-level QB race data.
teamQbQuery <- 'SELECT
  team_name,
  team_city,
  team_state,
  conference_name,
  SUM(is_caucasian) / COUNT(*) as qb_whiteness,
  COUNT(*) as qb_count
  FROM (
  SELECT
  pl.player_id,
  pl.is_caucasian,
  pos.position_name,
  t.team_name,
  t.team_city,
  t.team_state,
  t.team_id,
  c.conference_name
  FROM player pl,
  team t,
  positions pos,
  team_player_position tpp,
  player_stats ps,
  conference_team ct,
  conference c
  WHERE pl.player_id = tpp.player_id
  AND t.team_id = tpp.team_id
  AND pos.position_id = tpp.position_id
  AND ps.player_id = tpp.player_id
  AND ct.team_id = t.team_id
  AND ct.conference_id = c.conference_id
  AND pos.position_name = \'QB\'
  GROUP BY pl.player_id
  ORDER BY player_name ASC
  ) AS race_query
  GROUP BY team_id
  ORDER BY qb_whiteness DESC;'

# Query data.
qbDT <- as.data.table(suppressWarnings(DBI::dbGetQuery(conn
                                                       , statement = teamQbQuery)))


# -------------------------------------------------- #
# Map qb whiteness by state                          #
# -------------------------------------------------- #

# Compute qb whiteness proportions by state.
stateQbDT <- merge(qbDT[, .(stateWhiteQb = mean(qb_whiteness)), by = 'team_state']
                   , y = GetFipsCodes()
                   , by.x = 'team_state'
                   , by.y = 'state'
                   , all.y = TRUE)

# Identify avg/most/least qb whiteness.
avgWhiteLabel <- sprintf('Overall whiteness: %s'
                         , round(weighted.mean(qbDT$qb_whiteness
                                               , w = qbDT$qb_count
                                               , na.rm = TRUE), 3))
leastWhiteLabel <- sprintf('Least white: %s (%s)'
                           , stateQbDT[which.min(stateWhiteQb), team_state]
                           , round(stateQbDT[which.min(stateWhiteQb), stateWhiteQb], 3))
mostWhiteLabel <- sprintf('Most white: %s (%s)'
                          , stateQbDT[which.max(stateWhiteQb), team_state]
                          , round(stateQbDT[which.max(stateWhiteQb), stateWhiteQb], 3))

# Plot qb whiteness by state.
qbStateMap <- usmap::plot_usmap(data = stateQbDT
                  , values = 'stateWhiteQb'
                  , lines = 'grey68'
                  , include = stateQbDT[!is.na(stateWhiteQb), team_state]) + 
  scale_fill_continuous(low = 'blue2'
                        , high = 'orangered'
                        , name = 'Portion/all QBs'
                        , label = scales::comma) +
  theme(legend.position = 'right'
        , plot.title = element_text(family = 'Tahoma'
                                    , color = 'grey30'
                                    , face = 'bold'
                                    , size = 20)
        , legend.text = element_text(family = 'Tahoma'
                                     , color = 'grey30'
                                     , size = 10)) +
  ggtitle('College QB Whiteness by State') +
  annotate('text'
           , x = -1360000
           , y = -2300000
           , label = avgWhiteLabel
           , family = 'Tahoma') +
  annotate('text'
           , x = -1360000
           , y = -2500000
           , label = leastWhiteLabel
           , family = 'Tahoma') +
  annotate('text'
           , x = -1390000
           , y = -2700000
           , label = mostWhiteLabel
           , family = 'Tahoma')

# Save plot.
ggsave('./etc/qb_whiteness.png'
       , plot = qbStateMap)


# -------------------------------------------------- #
# Compute qb whiteness by conference                 #
# -------------------------------------------------- #
confQbDT <- qbDT[, .(confWhiteQb = mean(qb_whiteness)), by = 'conference_name']
confQbDT <- confQbDT[order(confWhiteQb)]