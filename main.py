import numpy as np
import pandas as pd
import sqlite3
import math
from datetime import datetime
import sys
import matplotlib.pyplot as plt
import seaborn as sns


# load data (make sure you have downloaded database.sqlite) - credit: Yoni Lev
with sqlite3.connect('database.sqlite') as con:
    countries = pd.read_sql("SELECT * from Country", con)
    matches = pd.read_sql("SELECT * from Match", con)
    leagues = pd.read_sql("SELECT * from League", con)
    teams = pd.read_sql("SELECT * from Team", con)
    players = pd.read_sql("SELECT * from Player", con)
    player_stats = pd.read_sql("SELECT * from Player_Stats", con)

#select country and 2 teams
selected_country = "England"
selected_team1 = "Manchester United"
selected_team2 = "Arsenal"

# select relevant countries and merge with leagues
countries = countries[countries.name.isin([selected_country])]
leagues = countries.merge(leagues, on='id', suffixes=('', '_y'))
teams = teams[teams.team_long_name.isin([selected_team1, selected_team2])]

# select all games between team1 and team2
matches = matches[matches.home_team_api_id.isin(teams.team_api_id)]
matches = matches[matches.away_team_api_id.isin(teams.team_api_id)]
print list(matches.columns.values)
matches = matches[
    ['id',
     'country_id',
     'league_id',
     'season',
     'stage',
     'date',
     'match_api_id',
     'home_team_api_id',
     'away_team_api_id',
     'home_team_goal',
     'away_team_goal',
     'home_player_1', 'home_player_2', 'home_player_3', 'home_player_4', 'home_player_5', 'home_player_6', 'home_player_7', 'home_player_8', 'home_player_9', 'home_player_10', 'home_player_11',
     'away_player_1', 'away_player_2', 'away_player_3', 'away_player_4', 'away_player_5', 'away_player_6', 'away_player_7', 'away_player_8', 'away_player_9', 'away_player_10', 'away_player_11',
     'home_player_X1', 'home_player_X2', 'home_player_X3', 'home_player_X4', 'home_player_X5', 'home_player_X6', 'home_player_X7', 'home_player_X8', 'home_player_X9', 'home_player_X10', 'home_player_X11',
     'away_player_X1', 'away_player_X2', 'away_player_X3', 'away_player_X4', 'away_player_X5', 'away_player_X6', 'away_player_X7', 'away_player_X8', 'away_player_X9', 'away_player_X10', 'away_player_X11',
     'home_player_Y1', 'home_player_Y2', 'home_player_Y3', 'home_player_Y4', 'home_player_Y5', 'home_player_Y6', 'home_player_Y7', 'home_player_Y8', 'home_player_Y9', 'home_player_Y10', 'home_player_Y11',
     'away_player_Y1', 'away_player_Y2', 'away_player_Y3', 'away_player_Y4', 'away_player_Y5', 'away_player_Y6', 'away_player_Y7', 'away_player_Y8', 'away_player_Y9', 'away_player_Y10', 'away_player_Y11',
     'goal',
     'shoton',
     'shotoff',
     'foulcommit',
     'card',
     'cross',
     'corner',
     'possession',
     'B365H',
     'B365D',
     'B365A']]

matches.dropna(inplace=True)
matches.sort_values(['date'], inplace=True)
# print matches['date'].tolist()

# select the players that appeared in starting line-ups for the matches above
player_id_set = set()
for index, row in matches.iterrows():
    for i in range(1, 12):
        player_id_set.add(row['home_player_%d' % i])
        player_id_set.add(row['away_player_%d' % i])


player_id_list = list(player_id_set)

# select the players and their stats from the list
players = players[players.player_api_id.isin(player_id_list)]
players = players[ ['id', 'player_api_id', 'player_name', 'height', 'weight'] ]
player_stats = player_stats[player_stats.player_api_id.isin(player_id_list)]

#merge the 2 lists to player_stats and clean up
player_stats = pd.merge(players, player_stats, on="player_api_id")
player_stats.drop("id_x", axis=1, inplace=True)
player_stats.rename(columns={'player_name_x': 'player_name', 'height_x': 'height', 'weight_x': 'weight', 'id_y': 'id'}, inplace=True)

# print list(player_stats.columns.values)

#given two dates, what is the absolute difference between them in days
def num_diff_days(prev, curr):
    diff = curr - prev
    days = diff.days
    return int( math.fabs(days) )

# given a player_api_id and a date, find me his stat closest to that time
def get_player_stat(player_id, date):
    required_datetime = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    that_player_stats = player_stats[player_stats.player_api_id.isin([player_id])]
    # that_player_stats.sort(['date_stat'], inplace=True)
    # print that_player_stats.head()

    #enumerate his stats looking at the date and return stat closest to date
    min_diff = sys.maxint
    stat = None
    for index, row in that_player_stats.iterrows():
        curr_date = row['date_stat']
        curr_datetime = datetime.strptime(curr_date, '%Y-%m-%d %H:%M:%S')
        curr_diff = num_diff_days(required_datetime, curr_datetime)
        if( curr_diff < min_diff ):
            min_diff = curr_diff
            stat = row

    return stat

# get_player_stat(23686, '2008-11-08 00:00:00')


#given a list of player_ids, return a list with their names
def get_player_names(player_ids):
    names = []
    for id in player_ids:
        # pl = players.query('player_api_id == %d' % id)
        pl = players.loc[ players['player_api_id'] == id ]
        s = pl['player_name'] #pandas series object
        n = s.values[0]
        names.append(n)

    return names


#given a list of player_ids, give me the overall ratings of the top 'k' players close to that date in each team
def top_k_players(player_ids, date, k):
    stats = []
    #get players stats using the id
    for p in player_ids:
        stats.append( get_player_stat(p, date) )

    stats.sort(key=lambda s: s['overall_rating'], reverse=True) #sort in place
    top_players = []
    for i in range(k):
        s = stats[i]
        t = (  s['player_api_id'], s['player_name'], s['overall_rating'] ) #tuple
        top_players.append(t)

    return top_players

def plot_squad_formation(home_players_ids, away_players_ids):
    home_players_x = []
    home_players_y = []
    away_players_x = []
    away_players_y = []
    for i in range(1, 12):
        home_players_x.append( row['home_player_X%d' % i] )
        home_players_y.append(row['home_player_Y%d' % i])
        away_players_x.append(row['away_player_X%d' % i])
        away_players_y.append(row['away_player_Y%d' % i])

    # rework the x coordinate a little bit, replacing 1 (the goal keeper) with 5 - the middle of the screen
    home_players_x = [5 if x == 1 else x for x in home_players_x]
    away_players_x = [5 if x == 1 else x for x in away_players_x]

    home_players_names = get_player_names(home_players_ids)
    away_players_names = get_player_names(away_players_ids)

    # COPY - START - credit: Squad Visualization (XY Coordinate) - Hugo Mathien
    #Home team (in blue)
    fig = plt.figure(index)
    title_string = "Date: " + date_string + "\nHome Team: " + home_team_name + " (shown in blue)\nScore (Home - Away): "\
                   + str(row['home_team_goal']) + " - " +  str(row['away_team_goal'])
    fig.suptitle(title_string, fontsize=20)
    ax1 = plt.subplot(2, 1, 1)
    # plt.rc('grid', linestyle="-", color='black')
    plt.rc('figure', figsize=(12, 20))
    plt.gca().invert_yaxis()  # Invert y axis to start with the goalkeeper at the top
    for label, x, y in zip(home_players_names, home_players_x, home_players_y):
        plt.annotate(
            label,
            xy=(x, y), xytext=(-20, 20),
            textcoords='offset points', va='bottom')
    plt.scatter(home_players_x, home_players_y, s=480, c='blue')
    ax1.set_xticklabels([])
    ax1.set_yticklabels([])

    # Away team (in red)
    ax2 = plt.subplot(2, 1, 2)
    # plt.rc('grid', linestyle="-", color='black')
    plt.rc('figure', figsize=(12, 16))
    plt.gca().invert_xaxis()  # Invert x axis to have right wingers on the right
    for label, x, y in zip(away_players_names, away_players_x, away_players_y):
        plt.annotate(
            label,
            xy=(x, y), xytext=(-20, 20),
            textcoords='offset points', va='bottom')
    plt.scatter(away_players_x, away_players_y, s=480, c='red')
    # plt.grid(True)

    ax2.set_xticklabels([])
    ax2.set_yticklabels([])

    plt.subplots_adjust(wspace=0, hspace=0)

    plt.show()
    # COPY -END

# analyse each match between team1 & team2
team1_id = teams.loc[ teams['team_long_name'] == selected_team1 ]['team_api_id'].values[0]
team2_id = teams.loc[ teams['team_long_name'] == selected_team2 ]['team_api_id'].values[0]
# mun_id = 10260
# ars_id = 9825
matches = matches[0:3] #make it smaller for now, easier to check
for index, row in matches.iterrows():
    date_string = row['date'].split(" ")[0]
    print "Match Date: ", date_string
    home_team_name = selected_team1 if row['home_team_api_id'] == team1_id else selected_team2
    away_team_name =  selected_team2 if row['home_team_api_id'] == team1_id else selected_team1
    print "Home Team: ", home_team_name
    print("Score (Home - Away): %d - %d" % (row['home_team_goal'], row['away_team_goal']) )

    home_players_ids = []
    away_players_ids = []
    for i in range(1, 12):
        home_players_ids.append(row['home_player_%d' % i])
        away_players_ids.append(row['away_player_%d' % i])

    # plot the formation and the players in the starting 11
    plot_squad_formation(home_players_ids, away_players_ids)

    top_home_players = top_k_players(home_players_ids, row['date'], k=7)
    top_away_players = top_k_players(away_players_ids, row['date'], k=7)

    print "Top Home Players: ", top_home_players
    print "Top Away Players: ", top_away_players
    print


