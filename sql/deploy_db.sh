#! /bin/bash

USER="$1"
PASSWORD="$2"
HOST="$3"

if [ -z $HOST ]
then
    echo "HOST argument was not supplied. Defaulting to localhost.\n"
    HOST="localhost"
fi
echo "Deploying college_football MySQL database to $HOST...\n"

mysql -u root -h $HOST -e "DROP DATABASE IF EXISTS college_football; CREATE DATABASE college_football; SET GLOBAL time_zone = '+00:00'; SET GLOBAL max_allowed_packet=1600000000;"
echo "New college_football database created on $HOST.\n"

mysql -u root -h $HOST college_football < conference.sql
mysql -u root -h $HOST college_football < team.sql
mysql -u root -h $HOST college_football < player.sql
mysql -u root -h $HOST college_football < positions.sql
mysql -u root -h $HOST college_football < player_stats.sql
mysql -u root -h $HOST college_football < conference_team.sql
mysql -u root -h $HOST college_football < team_player_position.sql
mysql -u root -h $HOST -e "GRANT ALL PRIVILEGES ON college_football.* TO '$USER'@'$HOST' IDENTIFIED BY '$PASSWORD'"

echo "The following tables were successfully created:\n conference\n team\n player\n positions\n player_stats\n conference_team\n team_player_position\n"
echo "college_football database successfully deployed to $HOST."