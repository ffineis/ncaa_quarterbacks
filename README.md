# NCAA football quarterback racial equity analysis

Caveat: I'm not a football afficionado. In fact, I'm a football n00b, even more n00by when it comes to matters of college football. But during one fall afternoon in the height of the [Colin Kaepernick kneel for the anthem movement](https://www.washingtonpost.com/graphics/2017/sports/colin-kaepernick-national-anthem-protests-and-NFL-activism-in-quotes/?utm_term=.b9e537c5d3d6), I was out running errands and somewhere ESPN was blaring on a TV; they were playing college football highlight reels from the morning's games. They featured three games, and all six of the quarterbacks featured were white. The recent NFL activism had put a prominent statistic out there - the fact that 70% of NFL players are black. What were the odds that all six of the quarterbacks would be white?

According to [The Institute for Diversity and Ethics in Sport](https://theundefeated.com/features/the-nfls-racial-divide/), white guys consistently comprised about 80% of the quarterbacks in the NFL over the last 15 years. Was the same true in college football? What are the patterns? Are there some conferences more biased than others? 

This repository contains everything needed to 

1. Set up a MySQL database to hold college football rosters and statistics.
2. Run a web scrape to obtain said data.
3. Load the scraped data into the database.
4. Run some queries and analysis to describe the racial inequities in this position.

## The database
A normal tendency when working on some type of data scraping project is to write one-off functions that will gather specific data every time we run the function. This isn't always a bad idea, but this has three really obvious drawbacks - (1) if the data is dependent on some other data being scraped, we have to run other scrapers first, (2) if the data is large, the scrape could take a while, and (3) if the website changes, the scraper could break.

Instead, it might just be easier to just set up a relational database (e.g. a SQL database), scrape the data once (or at regular periodic intervals), and then write SQL queries to get whatever we need from our own database, whenever we want. 

Even a football insider like me can get the gist of how a football league works. Here's my stab at the relationships between conferences, teams, and players:

![ncaa](./etc/college_football_db.png)


## The data
The data comes from [cfbstats.com](http://www.cfbstats.com/). Each quarterback was hand labelled `is_caucasian`, a "1" meaning "player is caucasian," and "0" indicates otherwise. Those labels are not perfect, but they're what I could ascertain from Google/Google Image searches for all of the 1600 college quarterbacks between 2008 and 2017.
