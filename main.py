from flask import Flask, render_template, request
import requests
import datetime
import json

app = Flask(__name__)

##########################################################################################################################
def flatten_json(json_object):
    """
        desc:     Flatten json object using recursive method
        args:     nested json object (super helpful with extremely nested object)
        returns:  flatten json object (single level like a dictionary)
    """
    flatten_json_object = {}

    def flatten_recursive(obj, name=''):
        if type(obj) is dict:
            for ele in obj:
                flatten_recursive(obj[ele], name + ele + '_')
        elif type(obj) is list:
            i = 0
            for ele in obj:
                flatten_recursive(ele, name + str(i) + '_')
                i += 1
        else:
            flatten_json_object[name[:-1]] = obj

    flatten_recursive(json_object)
    return flatten_json_object


########################################################################################################################
def checkrankandscore(dict, id):

    """
        desc:     return rank and points based on given team_id from team rankings data
        args:     flatten dictionary containg team rankings and team_id
        returns:  team rank and team adjusted points
    """

    rank = 0
    score = 0
    index = 0

    for key in dict.keys():
        list_of_keys = key.split('_', 3)
        if (len(list_of_keys) >= 4 and str(list_of_keys[2]).isdecimal() == True):
            team_index = str(list_of_keys[2])
            team_column = list_of_keys[3]
        if (team_column == 'team_id' and int(dict[key]) == int(id)):
            index = team_index
        if(team_index == index and team_column == 'rank'):
            rank = dict[key]
        elif(team_index == index and team_column == 'adjusted_points'):
            score = round(float(dict[key]),2)

    return rank, score;


#######################################################################################################################
@app.route('/events',methods=['POST'])
def display_list_of_events():

    """
        desc:     API Call, Display required data from API response (each steps explained below)
        args:
        returns:
    """

    #Source Labels
    labels = ["event_id","event_date","event_time","away_team_id", "away_nick_name", "away_city", "rank", "away_rank_points", "home_team_id", "home_nick_name", "Chiefs","home_city","adjusted_points"]
    #Response Labels
    response_labels = ["event_id", "event_date", "event_time", "away_team_id", "away_nick_name", "away_city", "away_rank", "away_rank_points", "home_team_id", "home_nick_name", "home_city", "home_rank", "home_rank_points"]


    #get start and end date from form(index.html)
    dateFrom = request.form['dateFrom']
    dateTo = request.form['dateTo']


    # Call an API
    scoreboard_API_response = requests.get('https://delivery.chalk247.com/scoreboard/NFL/' + dateFrom + '/' + dateTo + '.json?api_key=74db8efa2a6db279393b433d97c2bc843f8e32b0')
    team_rankings_API_response = requests.get('https://delivery.chalk247.com/team_rankings/NFL.json?api_key=74db8efa2a6db279393b433d97c2bc843f8e32b0')


    # convert response from an API to JSON object
    json_object_scoreboard = scoreboard_API_response.json()
    json_object_team_rankings = team_rankings_API_response.json()


    # flatten json object from nested json
    flatten_json_scoreboard = flatten_json(json_object_scoreboard)
    flatten_json_team_rankings = flatten_json(json_object_team_rankings)


    # Find Unique event_ids from scoreboard API response
    list_of_unique_ids = []
    for key in flatten_json_scoreboard.keys():
        list_of_keys = key.split('_', 4)
        if (len(list_of_keys) >= 5 and str(list_of_keys[3]).isdecimal() == True):
            if(list_of_keys[3] not in list_of_unique_ids):
                list_of_unique_ids.append(list_of_keys[3])


    # Fetch required values from from API response
    nfl_event_list = []
    for ele in list_of_unique_ids:
        sub_nfl_event_dict = {}
        for key in flatten_json_scoreboard.keys():
            scoreboard_id = 0
            scoreboard_column = ''
            list_of_keys = key.split('_', 4)                                            # split key of flatten object to get column names
            if (len(list_of_keys) >= 5 and str(list_of_keys[3]).isdecimal() == True):
                scoreboard_id = list_of_keys[3]                                         #event id
                scoreboard_column = list_of_keys[4]                                     # event column name
            if(scoreboard_id == ele and scoreboard_column in labels):
                sub_nfl_event_dict[scoreboard_column] = flatten_json_scoreboard[key]    # add each value to sub dictionary
        nfl_event_list.append(sub_nfl_event_dict)                                 # add subdictionary to the main list


    # Get rank and points from team scoring dictionary and split date and time record
    NFL_events = []
    for ele in nfl_event_list:
        temp_dict  = ele
        temp_dict_arrange_labels = {}
        # get rank and points from team scorings
        temp_dict['away_rank'], temp_dict['away_rank_points'] = checkrankandscore(flatten_json_team_rankings, int(ele['away_team_id']))
        temp_dict['home_rank'], temp_dict['home_rank_points'] = checkrankandscore(flatten_json_team_rankings, int(ele['home_team_id']))

        # split date-time
        date = datetime.datetime.strptime(temp_dict['event_date'], "%Y-%m-%d %H:%M")
        temp_dict['event_date'] = str(date.year) + '-' + str(date.month) + '-' + str(date.day)
        temp_dict['event_time'] = str(date.hour) + ':' + str(date.minute)
        NFL_events.append(temp_dict)

    return render_template('events.html', responseFROMAPI=NFL_events)


########################################################################################################################
@app.route('/')
def index():
    """
        desc:     render index.html as home page
        args:
        returns:
    """

    return render_template('index.html')

########################################################################################################################
if __name__== '__main__':
    app.run(debug=True)
