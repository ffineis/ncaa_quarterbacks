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

ggsave('./etc/qb_whiteness.png'
       , plot = qbStateMap)


# -------------------------------------------------- #
# Compute qb whiteness by conference                 #
# -------------------------------------------------- #
confQbDT <- qbDT[, .(confWhiteQb = weighted.mean(qb_whiteness
                                                 , w = qb_count)), by = 'conference_name']
confQbDT <- confQbDT[order(confWhiteQb)]


# -------------------------------------------------- #
# Compute qb whiteness by conference over time       #
# -------------------------------------------------- #

# Query fraction and count of white qb's per conference per year
confTimeQbQuery <- 'SELECT
  year,
  conference_name,
  SUM(is_caucasian) / COUNT(*) as qb_whiteness,
  COUNT(*) as qb_count
  FROM (
  SELECT
  tpp.year,
  pl.is_caucasian,
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
  GROUP BY pl.player_id, tpp.year
  ORDER BY player_name ASC
  ) as qb_time_whiteness
  GROUP BY conference_name, year
  ORDER BY conference_name ASC, year ASC;'

# Query qb whiteness by conference timeseries data.
qbTsDT <- as.data.table(suppressWarnings(DBI::dbGetQuery(conn
                                                         , statement = confTimeQbQuery)))

# Compute grand total qb whiteness by year, append to qbTsDT
avgQbTsDT <- qbTsDT[, .(qb_whiteness = weighted.mean(qb_whiteness
                                                     , w = qb_count)), by = 'year']
avgQbTsDT[, conference_name := 'mean']
avgQbTsDT[, qb_count := NA_integer_]
qbTsDT <- rbindlist(list(qbTsDT
                         , avgQbTsDT)
                    , use.names = TRUE)

# Plot qb whiteness trends for max/min/avg conference
qbTrends <- ggplot(qbTsDT[conference_name %in% c('Atlantic Coast Conference'
                                     , 'Big Ten Conference'
                                     , 'mean')]
       , mapping = aes(x = year
                       , y = qb_whiteness
                       , group = conference_name
                       , colour = conference_name
                       , linetype = conference_name)) +
  geom_line(show.legend = F) +
  scale_color_manual('conference'
                     , labels = c('Atlantic Coast', 'Big 10', 'Avg')
                     , values = c('#2737E3', '#EF2914', '#EF14E7')) +
  scale_linetype_manual(values = c(rep('solid', 2), 'longdash')) +
  theme(legend.position = 'right'
        , plot.title = element_text(family = 'Tahoma'
                                    , color = 'grey30'
                                    , face = 'bold'
                                    , size = 16)
        , legend.text = element_text(family = 'Tahoma'
                                     , color = 'grey30'
                                     , size = 8)
        , axis.title.x = element_text(size = 10
                                     , family = 'Tahoma'
                                     , color = 'grey30')
        , axis.title.y = element_text(size = 10
                                     , family = 'Tahoma'
                                     , color = 'grey30')) +
  ggtitle('College QB Whiteness Trends by Conference') +
  xlab('Year') + 
  ylab('White QBs/Total') +
  annotate('text'
           , x = 3
           , y = 0.8
           , label = 'Big 10'
           , family = 'Tahoma') +
  annotate('text'
           , x = 7
           , y = 0.74
           , label = 'Mean'
           , family = 'Tahoma') +
  annotate('text'
           , x = 4
           , y = 0.63
           , label = 'Atlantic Athletic Conf'
           , family = 'Tahoma') 
  
ggsave('./etc/qb_whiteness_trends.png'
       , plot = qbTrends)
