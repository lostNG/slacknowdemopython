import os
from slackclient import SlackClient
from flask import Flask, request, make_response, Response, jsonify
import json
import csv

# Your app's Slack bot user token
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_VERIFICATION_TOKEN = os.environ["SLACK_VERIFICATION_TOKEN"]



slack_client = SlackClient(SLACK_BOT_TOKEN)

# Flask webserver for incoming traffic from Slack
app = Flask(__name__)

# # Helper for verifying that requests came from Slack
# def verify_slack_token(request_token):
#     if SLACK_VERIFICATION_TOKEN != request_token:
#         print("Error: invalid verification token!")
#         print("Received {} but was expecting {}".format(request_token, SLACK_VERIFICATION_TOKEN))
#         return make_response("Request contains invalid Slack verification token", 403)
#
#
# @app.route("/index")
# def index():
#     return 'ok'
#
#
# @app.route("/slack/message_options", methods=["POST"])
# def message_options(menu_options):
#     form_json = json.loads(request.form["payload"])
#     verify_slack_token(form_json["token"])
#     return Response(json.dumps(menu_options), mimetype='application/json')




headers = {'content-type': 'x-www-form-urlencoded'}




# Helper for verifying that requests came from Slack
def verify_slack_token(request_token):
    if SLACK_VERIFICATION_TOKEN != request_token:
        print("Error: invalid verification token!")
        print("Received {} but was expecting {}".format(request_token, SLACK_VERIFICATION_TOKEN))
        return make_response("Request contains invalid Slack verification token", 403)


@app.route("/index")
def index():
    return 'ok'


def write_csv(output, first_column, *more_column):
    with open(output, 'a') as singlefile:
        write_csv = csv.writer(singlefile)
        write_csv.writerows([[first_column, *more_column]])





class SlackApi:
    def __init__(self):
        # self.selections = selections
        self.selections = {} #### https://stackoverflow.com/questions/13411668/global-dictionary-within-a-class-python


    def prompt_message(self, message, name):
        response = slack_client.api_call("chat.postMessage",
                              channel='#test-api',

                              text=message,
                              as_user="true")
        self.selections[str(name)] = 'done'
        return make_response("", 200)




    def set_attachments(self, texts, callback_id, name):
        self.attachments = [
            {"callback_id": callback_id,
                "text": "",
                "attachment_type": "default",
                "actions": [
                    {
                        "name": name,
                        "type": "button",
                        'text': text,
                        'value': str(i + 1),

                    }
                ]
            }
            for i, text
            in enumerate(texts)
        ]
        return self.attachments

    def set_dialog(self, label, title, name, callback_id, hint=''):
        self.dialog = {
                    "callback_id": callback_id,
                    "title": title,
                    "submit_label": "Request",
                    "state": "Limo",
                    "elements": [{
                        "type": "textarea",
                        "label": label,
                        "hint": hint,
                        "name": name}]}

        return self.dialog

    def prompt_dialog(self, name, trigger_id, dialog, channel='#test-api', headers=headers):
        response = slack_client.api_call(
            "dialog.open",
            channel=channel,
            headers=headers,
            trigger_id=trigger_id,
            dialog=dialog)
        self.selections[str(name)] = 'done'
        return make_response("", 200)

    def prompt_message_attachments(self, message, name, attachments, channel='#test-api', headers=headers):
        response = slack_client.api_call("chat.postMessage",
                              channel=channel,
                              text=message,
                              as_user="true",
                              attachments=attachments)
        self.selections[str(name)] = 'done'
        return make_response("", 200)


def main():
    pass

if __name__ == '__main__':
    main()
    # app.run(debug=True)

