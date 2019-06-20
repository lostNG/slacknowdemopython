# This scripts implements a simple endpoint for responding to Slack slash commands
# After receiving a slash command request from Slack
# it will try to read the name for the current channel and then respond directly

import os
import slack
import json
from flask import Flask, request  # import main Flask class and request object

app = Flask(__name__)  # create the Flask app


@app.route('/', methods=['POST'])
def slash_response():
    # init web client
    client = slack.WebClient(token=os.environ['SLACK_TOKEN'])

    # get full info for current channel
    response = client.conversations_info(
        channel=request.form.get('channel_id')
    )
    assert response['ok']
    channel = response['channel']

    ## compose response message
    user_id = request.form.get('user_id')
    text = 'Hi there, <@' + user_id + '>. Your are talking in channel *' + channel['name'] + '*'
    response = {
        "text": text
    }

    ## send response message
    return json.dumps(response), 200, {'content-type': 'application/json'}


if __name__ == '__main__':
    app.run(debug=True, port=5000)  # run app in debug mode on port 5000