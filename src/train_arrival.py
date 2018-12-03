import os
import time
from datetime import datetime, timedelta

from botocore.vendored import requests

from src.stations import stations

API_KEY = os.environ.get('API_KEY')
BASE_URL = 'https://api-v3.mbta.com/'


class TrainCalculator:
    """
    Class for calculating train arrivals
    """

    @staticmethod
    def get_station_id(intent: dict):
        """
        Gets Id for a station based on intent
        :param intent: Intent provided by alexa invocation
        :return: tuple of station_id, line, direction, stop, and message
        """
        line = intent['slots']['Line']['value'].lower()
        Stop = intent['slots']['Stop']
        # If the stop maps to the Stop Intent, we use that mapping instead of the literal string
        if 'resolutions' in Stop and 'resolutionsPerAuthority' in Stop['resolutions'] and 'values' in \
                Stop['resolutions']['resolutionsPerAuthority'][0]:
            stop = Stop['resolutions']['resolutionsPerAuthority'][0]['values'][0]['value']['name']
        else:
            stop = intent['slots']['Stop']['value']

        if line not in stations:
            message = '{} train line not found, please specify a valid route. For example green, red, blue, orange'.format(
                line)
            return None, None, None, None, message
        if stop not in stations[line]:
            message = 'No stations on {} line with name {} were found, please specify a valid train station'.format(
                line, stop)
            return None, None, None, None, message

        # If the direction is not specified we provide all possible destination for that route
        if not intent['slots'].get('Direction') or not intent['slots']['Direction'].get('value'):
            station_id = {}
            for direction in stations[line][stop]:
                station_id[direction] = stations[line][stop][direction]
            # Returning None for direction tells us that we want to provide all possible destinations
            return station_id, line, None, stop, ''
        else:
            Direction = intent['slots']['Direction']
            # If the direction maps to the Direction Intent, we use that mapping instead of the literal string
            if 'resolutions' in Direction and 'resolutionsPerAuthority' in Direction['resolutions'] and 'values' in \
                    Direction['resolutions']['resolutionsPerAuthority'][0]:
                direction = Direction['resolutions']['resolutionsPerAuthority'][0]['values'][0]['value']['name']
            else:
                direction = intent['slots']['Direction']['value']

            if direction not in stations[line][stop]:
                message = 'No routes for {} line trains to {} from {} found. '.format(line, direction, stop)
                station_id = {}
                for direction in stations[line][stop]:
                    station_id[direction] = stations[line][stop][direction]
                return station_id, line, None, stop, message

            station_id = stations[line][stop][direction]

        return station_id, line, direction, stop, ''

    @staticmethod
    def calculate_arrival(response_json: dict):
        """
        Calculates the time difference between current time and estimated train arrival time
        :param response_json:
        :return: float of time difference between current time and expected arrival time
        """
        if response_json['data'][0]['attributes']['arrival_time']:
            next_train = str(response_json['data'][0]['attributes']['arrival_time']).split('-05:00')[0]
            arrive_depart = 'arrive at'
        else:
            next_train = str(response_json['data'][0]['attributes']['departure_time']).split('-05:00')[0]
            arrive_depart = 'depart from'

        train_arrival = datetime.strptime(next_train, '%Y-%m-%dT%H:%M:%S') + timedelta(hours=5)

        current_time = int(time.time() * 1000)
        arrival_time = int(train_arrival.timestamp() * 1000)
        time_difference = (arrival_time - current_time) / 1000

        # When time difference is negative, means train is at the station and need to look for next train
        if time_difference <= 0:
            next_train = str(response_json['data'][1]['attributes']['arrival_time']).split('-05:00')[0]
            train_arrival = datetime.strptime(next_train, '%Y-%m-%dT%H:%M:%S') + timedelta(hours=5)
            arrival_time = int(train_arrival.timestamp() * 1000)
            time_difference = (arrival_time - current_time) / 1000

        return time_difference, arrive_depart

    @staticmethod
    def get_train_arrival(intent):
        """
        Gets the expected arrival time for a train at a particular stop/direction provided an intent
        :param intent:
        :return: string of expected arrival time
        """
        if not API_KEY:
            return 'No API key specified'

        # Retrieve the station_id, line, direction, and stop for the provided intent
        station_id, line, direction, stop, message = TrainCalculator.get_station_id(intent)
        if not station_id:
            return message

        if direction is None:
            directions = {}
            for station in station_id:
                if station_id[station] not in directions.values():
                    directions[station] = station_id[station]
            response_speech = message
            for direction in directions:
                # Call API to get train predictions for station_id
                url = '{}predictions/?api_key={}&filter[stop]={}'.format(BASE_URL, API_KEY, directions[direction])
                response = requests.get(url)
                response_json = response.json()

                # Get the time difference between current time and estimated train arrival time
                time_difference, arrive_depart = TrainCalculator.calculate_arrival(response_json)
                time_difference = time_difference / 60
                minutes = str(time_difference).split('.')[0]
                seconds = '.' + str(time_difference).split('.')[1]
                seconds = round(float(seconds), 4)
                seconds = str(int(round((seconds * 60), 0)))

                if int(minutes) == 0:
                    arrival_time = '{} seconds.'.format(seconds)
                elif int(minutes) == 1:
                    arrival_time = '{} minute, and {} seconds.'.format(minutes, seconds)
                else:
                    arrival_time = '{} minutes, and {} seconds '.format(minutes, seconds)
                response_speech += 'The next {} line train to {} will {} {} in {}. '.format(line, direction,
                                                                                            arrive_depart,
                                                                                            stop, arrival_time)
        else:
            # Call API to get train predictions for station_id
            url = '{}predictions/?api_key={}&filter[stop]={}'.format(BASE_URL, API_KEY, station_id)
            response = requests.get(url)
            response_json = response.json()

            # Get the time difference between current time and estimated train arrival time
            time_difference, arrive_depart = TrainCalculator.calculate_arrival(response_json)
            time_difference = time_difference / 60
            minutes = str(time_difference).split('.')[0]
            seconds = '.' + str(time_difference).split('.')[1]
            seconds = round(float(seconds), 4)
            seconds = str(int(round((seconds * 60), 0)))

            if int(minutes) == 0:
                arrival_time = '{} seconds.'.format(seconds)
            elif int(minutes) == 1:
                arrival_time = '{} minute, and {} seconds.'.format(minutes, seconds)
            else:
                arrival_time = '{} minutes, and {} seconds '.format(minutes, seconds)
            response_speech = 'The next {} line train to {} will {} {} in {}. '.format(line, direction, arrive_depart,
                                                                                       stop, arrival_time)

        return response_speech
