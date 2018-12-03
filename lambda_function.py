from src.train_arrival import TrainCalculator
from src.blue import blue

def lambda_handler(event, context):
    if event['session']['application']['applicationId'] != 'amzn1.ask.skill.bc3a2097-1952-4ef0-a6d6-9161c2f88eea':
        raise ValueError('Invalid Application ID')
    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']}, event['session'])

    if event['request']['type'] == 'LaunchRequest':
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == 'IntentRequest':
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == 'SessionEndedRequest':
        return on_session_ended(event['request'], event['session'])


def on_session_started(session_started_request, session):
    print('Starting new session.')


def on_launch(launch_request, session):
    return get_welcome_response()


def on_intent(intent_request, session):
    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    if intent_name == 'TrainTrackerIntent':
        return get_train_time(intent)
    elif intent_name == 'AMAZON.HelpIntent':
        return get_welcome_response()
    elif intent_name == 'AMAZON.CancelIntent' or intent_name == 'AMAZON.StopIntent':
        return handle_session_end_request()
    else:
        raise ValueError('Invalid intent')


def on_session_ended(session_ended_request, session):
    print('Ending session.')
    # Cleanup goes here...


def get_train_time(intent):
    session_attributes = {}
    speech_output = TrainCalculator.get_train_arrival(intent)
    card_title = 'MBTA'
    should_end_session = False

    return build_response(session_attributes, build_speechlet_response(card_title, speech_output, None, should_end_session))


def handle_session_end_request():
    card_title = 'BART - Thanks'
    speech_output = 'Thank you for using the BART skill.  See you next time!'
    should_end_session = True

    return build_response({}, build_speechlet_response(card_title, speech_output, None, should_end_session))


def get_welcome_response():
    session_attributes = {}
    card_title = 'MBTA'
    speech_output = 'Welcome to the Alexa MBTA Charlie Tracker. You can ask me for train times from any station.'
    reprompt_text = 'Please ask me for train times to a station, for example when does the next Red line train ' \
                    'to Inbound arrive at Andrew.'
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }