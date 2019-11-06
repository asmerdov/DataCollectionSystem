import json
import joblib
import os
import pandas as pd
from datetime import datetime
from config import *
from collections import defaultdict

summoner_names = ['TUK Trannas', 'AE Iromator']

replays_json_path = data_folder + 'replays_json/'
replays_jsons_filenames = os.listdir(replays_json_path)

replays_jsons = {}

def get_match_id_from_filename(filename):
    match_id_index_start = filename.find('_')
    match_id_index_end = filename.find('.json')
    if (match_id_index_start != -1) and (match_id_index_end != -1):
        return filename[match_id_index_start+1:match_id_index_end]
    else:
        return None
        # raise ValueError(f'can\'t extract match_id from filename {filename}')

for replays_jsons_filename in replays_jsons_filenames:
    match_id = get_match_id_from_filename(replays_jsons_filename)
    if match_id is None:
        continue
    replay_json = json.load(open(replays_json_path + replays_jsons_filename))
    replays_jsons[match_id] = replay_json

replays_processed = {}

# replays_json = replays_jsons['4232819529']  # DEBUG

for match_id, replay_json in replays_jsons.items():
    # players_dict4replay = {}
    participant_id2summoner_name_dict = {}

    for participant in replay_json['participantIdentities']:
        if participant['player']['summonerName'] in summoner_names:
            participant_id = participant['participantId']
            participant_id2summoner_name_dict[participant_id] = participant['player']['summonerName']

    def get_player_id_from_participant_id(participant_id):
        summoner_name = participant_id2summoner_name_dict[participant_id]
        player_id = summoner_name2player_id_dict[summoner_name]

        return player_id


    replay_processed = {}
    loading_screen_correction = 90
    replay_processed['start_time'] = pd.to_datetime(replay_json['gameCreation'] / 1000 + 3600 * 2 + loading_screen_correction, unit='s')
    replay_processed['game_duration'] = replay_json['gameDuration']
    replay_processed['end_time'] = replay_processed['start_time'] + pd.Timedelta(replay_processed['game_duration'], unit='s')

    # for participant_id, summoner_name in participant_id2summoner_name_dict.items():
    for summoner_name, player_id in summoner_name2player_id_dict.items():
        replay_processed[f'events_player_{player_id}'] = {
            'death_times': [],
            'kill_times': [],
            'assist_times': [],
        }

    for frames in replay_json['frames']:
        for event in frames['events']:
        # for event in replay_json['frames'][10]['events']:
            if event['type'] == 'CHAMPION_KILL':
                if event['killerId'] in participant_id2summoner_name_dict:
                    timestamp = event['timestamp'] / 1000
                    # summoner_name = participant_id2summoner_name_dict[event['killerId']]
                    player_id = get_player_id_from_participant_id(event['killerId'])
                    replay_processed[f'events_player_{player_id}']['kill_times'].append(timestamp)
                if event['victimId'] in participant_id2summoner_name_dict:
                    timestamp = event['timestamp'] / 1000
                    # summoner_name = participant_id2summoner_name_dict[event['victimId']]
                    player_id = get_player_id_from_participant_id(event['victimId'])
                    replay_processed[f'events_player_{player_id}']['death_times'].append(timestamp)

                for assistant_participant_id in event['assistingParticipantIds']:
                    if assistant_participant_id in participant_id2summoner_name_dict:
                        timestamp = event['timestamp'] / 1000
                        # summoner_name = participant_id2summoner_name_dict[assistant_participant_id]
                        player_id = get_player_id_from_participant_id(assistant_participant_id)
                        replay_processed[f'events_player_{player_id}']['assist_times'].append(timestamp)

    replays_processed[match_id] = replay_processed


joblib.dump(replays_processed, data_folder + 'replays_dict')



# datetime.fromtimestamp(replays_json['gameCreation']/1000)
# replays_json['gameDuration']
# replays_json.keys()





























