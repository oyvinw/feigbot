import boto3

session = boto3.Session(profile_name="default")
polly = session.client("polly")
boto3.set_stream_logger('')


def get_polly_voice(text):
    response = polly.synthesize_speech(VoiceId='Joanna',
                                       OutputFormat='mp3',
                                       Text=text,
                                       Engine='neural')

    return response['AudioStream'].read()
