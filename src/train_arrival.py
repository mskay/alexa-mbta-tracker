from botocore.vendored import requests
import os
import time
from datetime import datetime, timedelta
from src.stations import stations
API_KEY = os.environ.get('API_KEY', '587ee13438e34b7bbb1ce10d225638a5')
BASE_URL = 'https://api-v3.mbta.com/'


class TrainCalculator:

    @staticmethod
    def get_station_id(intent: dict):
        """
        Gets Id for a station based on intent
        :param intent:
        :return: Id of station
        """
        line = intent['slots']['Line']['value'].lower()
        direction = intent['slots']['Direction']['value'].lower()
        stop = intent['slots']['Stop']['value'].lower()
        station_id = stations[line][stop][direction]
        return station_id, line, direction, stop

    @staticmethod
    def calculate_arrival(response_json: dict):
        """
        Calculates the time difference between current time and estimated train arrival time
        :param response_json:
        :return: float of time difference between current time and expected arrival time
        """
        next_train = str(response_json['data'][0]['attributes']['arrival_time']).split('-05:00')[0]

        train_arrival = datetime.strptime(next_train, '%Y-%m-%dT%H:%M:%S') + timedelta(hours=5)

        current_time = int(time.time() * 1000)
        arrival_time = int(train_arrival.timestamp() * 1000)
        time_difference = (arrival_time - current_time)/1000

        # When time difference is negative, means train is at the station and need to look for next train
        if time_difference <= 0:
            next_train = str(response_json['data'][1]['attributes']['arrival_time']).split('-05:00')[0]
            train_arrival = datetime.strptime(next_train, '%Y-%m-%dT%H:%M:%S') + timedelta(hours=5)
            arrival_time = int(train_arrival.timestamp() * 1000)
            time_difference = (arrival_time - current_time)/1000

        return time_difference

    @staticmethod
    def get_train_arrival(intent):
        """
        Gets the expected arrival time for a train at a particular stop/direction provided an intent
        :param intent:
        :return: string of expected arrival time
        """
        # Retrieve the station_id, line, direction, and stop for the provided intent
        station_id, line, direction, stop = TrainCalculator.get_station_id(intent)

        # Call API to get train predictions for station_id
        url = '{}predictions/?api_key={}&filter[stop]={}'.format(BASE_URL, API_KEY, station_id)
        response = requests.get(url)
        response_json = response.json()

        # Get the time difference between current time and estimated train arrival time
        time_difference = TrainCalculator.calculate_arrival(response_json)
        time_difference = time_difference/60
        minutes = str(time_difference).split('.')[0]
        seconds = '.' + str(time_difference).split('.')[1]
        seconds = round(float(seconds), 4)
        seconds = str(int(round((seconds * 60), 0)))

        response_speech = 'The next {} line train {} will arrive at {}  in {} minutes, and {} seconds'.format(line, direction, stop, minutes, seconds)

        return response_speech
