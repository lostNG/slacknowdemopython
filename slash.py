from flask import Flask, request, make_response, Response, jsonify
import os
import json
from slackclient import SlackClient
import boto3
import datetime
import gzip
import csv
from slack_api_class import SlackApi, verify_slack_token, write_csv
from bs4 import BeautifulSoup


SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_VERIFICATION_TOKEN = os.environ["SLACK_VERIFICATION_TOKEN"]



slack_client = SlackClient(SLACK_BOT_TOKEN)

# Flask webserver for incoming traffic from Slack
app = Flask(__name__)

sa = SlackApi()





@app.route("/slack/message_options", methods=["POST"])
def message_options():
    form_json = json.loads(request.form["payload"])

    verify_slack_token(form_json["token"])
    menu_options = {
        "options": [
            {
                "text": "Get a sample from s3 bucket files",
                "value": "sample"
            }, {
                "text": "Find a string in s3 bucket files",
                "value": "string"
            }
        ]
    }
    return Response(json.dumps(menu_options), mimetype='application/json')


sel = ["don't know"]
wn = ["don't know"]
sa.selections['hours'] = None
sa.selections['onefile'] = None
check = ''


def what_now(form_json):
    if 'other_files' in sa.selections:
        if form_json['actions'][0]['name'] == 'what_now':
            sa.selections['what_now'] = form_json['actions'][0]['value']



def download_file(file_name):
    message = "I'm downloading the file. Please wait..."
    sa.prompt_message(message, "downloading_file")
    message = "I'll let you know once I'm done..."
    sa.prompt_message(message, "still_donwloading")
    s3_client = boto3.client('s3')
    s3_client.download_file(Bucket=sa.selections['bucket'], Key=sa.selections['prefix'] + file_name,
                            Filename=os.getcwd() + '/' + file_name)
    message = file_name + ' has been downloaded in ' + os.getcwd()
    sa.prompt_message(message, "downloaded_file")


def checking_message(file_name, i):
    if 'string' in sa.selections:
        message = "checking if `" + file_name + "` (file number " + str(i + 1) + " out of " + \
                  str(len(sa.selections['files'])) + ") contains `" + sa.selections['string'] + '`'
        sa.prompt_message(message, 'contains_check')
    elif sa.selections['menu'] == 'sample':
        if 'what_now' in sa.selections and sa.selections['what_now'] == '2':
            exit()
        message = "taking a sample in `" + file_name + "` (file number " + str(i + 1) + ')'
        sa.selections['test_sample'] = file_name + " (file number " + str(i + 1)
        sa.prompt_message(message, 'what_to_sample')




def if_what_now(file_name, ln):
    if 'what_now' in sa.selections:
        if sa.selections['what_now'] == '1':
            if sa.selections['onefile'] == '1':
                write_csv("ddds3_parser_" + sa.selections['string'] + ".csv", 'a', file_name, ln)
            message = 'string found in file `' + file_name + '`\n'
            sa.prompt_message(message, 'string_found')
            message = "\naaaaThis is the full line found:\n```" + ln + '```'
            sa.prompt_message(message, 'full_line')
            return 'ok'
        if sa.selections['what_now'] == '3':
            message = "Gotcha. Thanks. Bye!"
            sa.prompt_message(message, "sample_done")
            exit()
    if 'gz' in file_name:
        if sa.selections['download'] != '3' and sa.selections['onefile'] == '1':
            write_csv("aaaaas3_parser_" + sa.selections['string'] + ".csv", 'a', file_name, ln)
    else:
        with open("filtered_sample_of_%s" % file_name, 'a') as writexml:
            writexml.write(str(ln.parent))
        message = "string `%s` found in file `%s` node: ```%s```" % (
            sa.selections['string'], file_name, ln.parent)
        sa.prompt_message(message, 'channel_found')


def ask_what_now():
    if "what_now" not in sa.selections:
        if (sa.selections['download'] != '1' and 'other_files' not in sa.selections) or (sa.selections['download'] != '1' and 'what_now' in sa.selections):
            message = sa.selections['string'] + " might be in other files... Do you want me to continue?"
            texts = ["check other files",
                     "stay in this file, then others",
                     "I'm fine. Stop the script"]
            attachments = sa.set_attachments(texts, sa.selections['callback_id'], "what_now")
            sa.prompt_message_attachments(message, 'other_files', attachments)



def parse_file(file_name, i, gf, form_json):
    checking_message(file_name, i)
    for ln in gf:
        if sa.selections['menu'] == 'string':
            filter_data = sa.selections['string'] in ln  ##### usually for zipped files
            if filter_data is False:
                try:
                    filter_data = 'class' in str(type(ln)) and sa.selections['string'] in ln[
                        'channel']  ##### usually for unzipped files basic rules
                except:
                    pass

            if filter_data is False:
                try:
                    filter_data = 'class' in str(type(ln)) and sa.selections['string'] in ln[
                        'param']  ##### usually for unzipped files basic rules
                except:
                    try:
                        filter_data = 'class' in str(type(ln)) and sa.selections['string'] in ln[
                            'rule-value']  ##### usually for unzipped files basic rules
                    except:
                        try:
                            filter_data = 'class' in str(type(ln)) and sa.selections['string'] in ln['beacon-version-code']
                        except:
                            print('cacca')
                            try:
                                filter_data = 'class' in str(type(ln)) and sa.selections['string'] in ln['op-value']
                            except:
                                try:
                                    filter_data = 'class' in str(type(ln)) and sa.selections['string'] in ln['segment']
                                except:
                                    pass
            if filter_data:
                ask_what_now()
                check_csv()
                check_txt(file_name)
                add_what_now(form_json)
                if_what_now(file_name, ln)
                if 'download' in sa.selections and sa.selections['download'] == '2' and sa.selections['onefile'] == '1' and 'what_now' in sa.selections and  sa.selections['what_now'] != '1':
                    if 'gz' in file_name:
                        write_csv("s3_parser_" + sa.selections['string'] + ".csv", 'a', file_name, ln)

                elif 'download' in sa.selections and sa.selections['download'] == '2' and sa.selections['onefile'] == '2':
                    with open(sa.selections['string'] + '_' + file_name.split('.')[0] + '.txt', 'a') as write_file:
                        if 'gz' in file_name:
                            write_file.write(ln)
                        if sa.selections['what_now'] == '1':
                            break
                    # message = sa.selections['string'] + '_' + file_name.split('.')[
                    #     0] + '.txt' + ' has been created and populated in ' + os.getcwd()
                    # sa.prompt_message(message, "all_txt_created")
                elif sa.selections['download'] == '4' and sa.selections['onefile'] == '1':
                    if 'gz' in file_name:
                        write_csv("s3_parser_" + sa.selections['string'] + ".csv", 'a', file_name, ln)
                    break
                elif sa.selections['download'] == '3' and 'what_now' in sa.selections and sa.selections['what_now'] == '1':
                    break
                elif sa.selections['download'] == '3' and 'what_now' in sa.selections and sa.selections['what_now'] == '2':
                    pass
                elif sa.selections['download'] == '1':
                    download_file(file_name)

        elif (sa.selections['menu'] == 'sample' and 'what_now' not in sa.selections) or \
                ('what_now' in sa.selections and sa.selections['menu'] == 'sample' and sa.selections['what_now'] != '3'):
            # print('AAAAAAAAAAAAAAAAAAAAA\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n')

            # if 'what_now' not in sa.selections:
            s3_client = boto3.client('s3')
            obj = s3_client.get_object(Bucket=sa.selections['bucket'], Key=sa.selections['prefix'] + file_name)
            body = obj['Body']
            lns = []

            with gzip.open(body, 'rt') as gf:
                for ln in gf:
                    # print(ln.rstrip())
                    i += 1
                    lns.append(ln.rstrip())
                    if i == 10:
                        break
            what_to_sample(file_name, lns, i)
            add_what_now(form_json)
            if 'what_now' in sa.selections and sa.selections['what_now'] == '1':
                break
            elif 'what_now' in sa.selections and sa.selections['what_now'] == '2':
                exit()
        else:
            sa.prompt_message("Terminated as requested.", 'kill')


def parse_zipped_files(body, file_name, i, form_json):
    if 'gz' in file_name:
        with gzip.open(body, 'rt') as gf:
            parse_file(file_name, i, gf, form_json)


def parse_unzipped_files(body, file_name, i, form_json):
    if '.xml' in file_name:
        soup = BeautifulSoup(body, 'lxml')
        parse_file(file_name, i, soup.find_all(), form_json)
        # parse_file(file_name, i, soup.find_all('rule-argument'), form_json)





def what_to_string_found(i, file_name, form_json):
    add_what_now(form_json)
    if 'what_now' in sa.selections:
        if sa.selections['what_now'] == '3':
            message = "Gotcha. Thanks. Bye!"
            sa.prompt_message(message, "sample_done")
            exit()
        ##### try to fix It restarts from scratch when asked check other files
        if sa.selections['what_now'] == '1':
            i += 1
    obj = boto3.client('s3').get_object(Bucket=sa.selections['bucket'], Key=sa.selections['prefix'] + file_name)
    body = obj['Body']
    parse_zipped_files(body, file_name, i, form_json)
    parse_unzipped_files(body, file_name, i, form_json)



def write_csv_sample(lns, file_name):
    if 'download' in sa.selections and sa.selections['download'] != '3':
        with open('sample_' + file_name.split('.')[0] + '.csv', 'a') as write_file:
            for line in lns:
                write_csv = csv.writer(write_file, delimiter='\t')
                write_csv.writerow([line])

            message = 'sample_' + file_name.split('.')[
                0] + '.csv' + ' has been created and populated in ' + os.getcwd()
            sa.prompt_message(message, 'sample_csv_done')



def what_to_sample(file_name, lns, i):
    if 'what_now' in sa.selections:
        if sa.selections['what_now'] == '2':
            message = "Gotcha. Thanks. Bye!"
            sa.prompt_message(message, "sample_done")
            exit()

    if 'other_files' not in sa.selections:
        pass

    if ('sample_displayed%s' % i not in sa.selections and 'what_now' not in sa.selections) or \
            ('sample_displayed%s' % i not in sa.selections and 'what_now' in sa.selections):
        message = "This is part of the sample of %s: ```%s```" % (file_name, lns[:10][0])
        sa.prompt_message(message, 'sample_displayed%s' % i)

    if (sa.selections['download'] == '2' and 'what_now' not in sa.selections) or (sa.selections['download'] == '2' and 'what_now' in sa.selections  and sa.selections['what_now'] != '3'):
        write_csv_sample(lns, file_name)

    elif sa.selections['download'] == '1':
        if 'sample_download_full' not in sa.selections:
            message = "I'm downloading the file. Please wait...\nI'll let you know once I'm done..."
            sa.prompt_message(message, "sample_download_full")
        s3_client = boto3.client('s3')
        s3_client.download_file(Bucket=sa.selections['bucket'], Key=sa.selections['prefix'] + file_name, Filename=os.getcwd() + '/' + file_name)
        message = file_name + ' has been downloaded in ' + os.getcwd()
        sa.prompt_message(message, "sample_download_full_done")
    if ('what_now' not in sa.selections and 'what_to_sample' in sa.selections and 'other_files' not in sa.selections) or \
        ('what_now' in sa.selections and sa.selections['what_now'] == '1'):
        message = "Do you want me to continue with other files?"
        texts = ["check other files",
                 "stay in this file, then others",
                 "I'm fine. Stop the script"]

        attachments = sa.set_attachments(texts, sa.selections['callback_id'], "what_now")
        sa.prompt_message_attachments(message, 'other_files', attachments)



def check_txt(file_name):
    if 'string' in sa.selections and 'txt_created' not in sa.selections and sa.selections['onefile'] == '2':
        for file_or_folder in os.listdir(os.getcwd()):
            if file_or_folder == sa.selections['string'] + '_' + file_name.split('.')[
                    0] + '.txt':
                message = sa.selections['string'] + '_' + file_name.split('.')[
                    0] + '.txt' + ' has been created and populated in ' + os.getcwd()
                sa.prompt_message(message, "txt_created")


def check_csv():
    if 'string' in sa.selections and "csv_created" not in sa.selections and 'download' in sa.selections \
            and sa.selections['download'] != '3' and sa.selections['onefile'] == '1':
        for file_or_folder in os.listdir(os.getcwd()):
            if file_or_folder == "s3_parser_" + sa.selections['string'] + ".csv":
                with open("s3_parser_" + sa.selections['string'] + ".csv", 'r') as checkcsv:
                    reader = csv.reader(checkcsv)
                    if len([line for line in reader]) == 0:
                        # print("No results")
                        os.remove("s3_parser_" + sa.selections['string'] + ".csv")
                    else:
                        message = "File `%s` has been created and populated in `%s`" % ("s3_parser_" + sa.selections['string'] + ".csv", os.getcwd())

                        sa.prompt_message(message, "csv_created")


def set_bucket(form_json):
    if 'submission' in form_json and 'path' not in sa.selections:
        path = form_json['submission']['path']
        sa.selections['path'] = path
        if path[0] == '/': path = path.replace('/', '', 1)
        sa.selections['bucket'] = path.split('/')[0]
        try:
            px = path.split('/', 1)[1]
        except IndexError:
            message = "Please make sure you type a right path."
            sa.prompt_message(message, "wrong_path")
            # exit()
        if px[-1] != '/': px += '/'
        if px[0] == '/': px = px.replace('/', '', 1)
        sa.selections['prefix'] = px
        return make_response("", 200)




def set_menu(form_json):
    try:
        if 'path' not in sa.selections:
            sa.selections['trigger_id'] = form_json['trigger_id']
            selection = form_json["actions"][0]["selected_options"][0]["value"]
            if selection == 'string':
                sa.selections['menu'] = 'string'
            elif selection == 'sample':
                sa.selections['menu'] = 'sample'
            return make_response("", 200)
    except:
        message_options()


def set_string(form_json):
    if 'menu' in sa.selections and sa.selections['menu'] == 'string' and 'download' in sa.selections and 'initiate_string' not in sa.selections:
        # print("aAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        trigger_id = form_json['trigger_id']
        callback_id = form_json['callback_id']
        label = "Additional information"  ### this is a smaller display message
        title = "Type the string"  #### this is the title message
        name = "string"  ##### this is how is stored in the response payload
        dialog = sa.set_dialog(label, title, name, callback_id)
        sa.prompt_dialog('initiate_string', trigger_id, dialog)


def set_hours_trigger(form_json):
    if ('trigger_id' in form_json and sa.selections['menu'] == 'string' and "set_hours" not in sa.selections and 'looking_for_string' in sa.selections and
        'string' in sa.selections and sa.selections['hours'] == None) or ('trigger_id' in form_json and sa.selections['menu'] == 'sample' and "set_hours" not in sa.selections and
                                       'bucket_check' in sa.selections  and sa.selections['hours'] == None):

        sa.selections['trigger_id'] = form_json['trigger_id']
        sa.selections['callback_id'] = form_json['callback_id']



def set_hours():
    if 'hours_feedback' in sa.selections and sa.selections['hours_feedback'] == '2':
        label = "Please type how many hours"  ### this is a smaller display message
        title = "Hours"  #### this is the title message
        name = "hours"  ##### this is how is stored in the response payload
        dialog = sa.set_dialog(label, title, name, sa.selections['callback_id'])
        sa.prompt_dialog('set_hours', sa.selections['trigger_id'], dialog)


def filtering_hours():
    if sa.selections['hours'] != None  and 'filtering_hours' not in sa.selections:
        message = "I'll be looking for filtering files ingested in the last %s hours" % sa.selections['hours']
        sa.prompt_message(message, "filtering_hours")


def looking_in_path():
    if 'path' in sa.selections and 'looking_in_path' not in sa.selections:
        message = "I'll be looking in path ```%s```" % sa.selections['path']
        sa.prompt_message(message, "looking_in_path")


def set_path(form_json):
    if 'path' not in sa.selections:
        callback_id = form_json['callback_id']
        sa.selections['callback_id'] = callback_id
        label = "Additional information"  ### this is a smaller display message
        title = "Type the bucket and path"  #### this is the title message
        name = "path"  ##### this is how is stored in the response payload
        hint = "For example: clientfolders-ap/xl8startapp/HK/" #### this is optional
        dialog = sa.set_dialog(label, title, name, callback_id, hint)
        sa.prompt_dialog('set_path', sa.selections['trigger_id'], dialog)


def download_selection(form_json):
    if 'download_selection' not in sa.selections and 'path' in sa.selections:
    # if sa.selections['menu'] == 'string' and 'download_selection' not in sa.selections and 'path' in sa.selections:
        callback_id = form_json['callback_id']
        message = "What would you like to do if I find what you are looking for?"
        if 'string' in sa.selections:
            x = 'found string'
        else: x = 'sample'
        texts = [
            "Download entire file(s) locally",
            "Save file with %s locally" % x,
            "Don't download anything"]
        attachments = sa.set_attachments(texts, callback_id, "download")
        sa.prompt_message_attachments(message, 'download_selection', attachments)


def looking_for_string():
    if 'string' in sa.selections and 'looking_for_string' not in sa.selections:
        message = "I'll be looking for string ```%s```" % sa.selections['string']
        sa.prompt_message(message, "looking_for_string")


def add_download_selection(form_json):
    if 'actions' in form_json and form_json['actions'][0]['name'] == 'download':
        sa.selections['download'] =  form_json['actions'][0]['value']


def add_string_selection(form_json):
    if 'submission' in form_json and 'string' not in sa.selections and 'initiate_string'  in sa.selections:
        sa.selections['string'] = form_json['submission']['string']

# def sample():
#     if sa.selections['menu'] == 'sample' and 'bucket' in sa.selections and 'bucket_check' not in sa.selections and 'sample' not in sa.selections:
#         message = "I will be getting a sample in ```%s```" % sa.selections['path']
#         sa.prompt_message(message, "sample")

##### you need to add buttons before triggering set_hours as you need a fresh trigger id
def bucket_check():

    if (sa.selections['menu'] == 'string' and 'looking_for_string' in sa.selections
        and bucket_check not in sa.selections and 'download' in sa.selections and sa.selections['download'] == '3') or\
            (sa.selections['menu'] == 'string' and 'bucket' in sa.selections and bucket_check not in sa.selections and
        'download' in sa.selections and 'files_to_check' not in sa.selections and 'looking_for_string' in sa.selections
    and 'hours_feedback' not in sa.selections and sa.selections['onefile'] != None) or (sa.selections['menu'] == 'sample'
        and 'bucket' in sa.selections and bucket_check not in sa.selections and 'files_to_check' not in sa.selections
                                                                                        and 'download' in sa.selections ):
        s3_client = boto3.client('s3')
        response = s3_client.list_objects(
            Bucket=sa.selections['bucket'],
            Prefix=sa.selections['prefix']
        )
        if ('what_now' not in sa.selections) or ('what_now' in sa.selections and sa.selections['what_now'] != '3'):
            message = """There are """ + str(
                len(response['Contents'])) + """ files to check. Some might be filtered out as archived\n"""
            sa.prompt_message(message, "files_to_check")

            if '1000' in message and 'bucket_check' not in sa.selections:
                timemachine = """As there are many files here, I'll be looking for files added in the last 24 hours."""
                texts = ['Yes', "No, I'll tell you how many hours"]
                attachments = sa.set_attachments(texts, sa.selections['callback_id'], "hours_feedback")
                # time.sleep(5)
                sa.prompt_message_attachments(timemachine, "bucket_check", attachments)
            else:
                sa.selections['response'] = response
                sa.selections['hours_feedback'] = 'more_than_1000'



def get_file_check():
    if sa.selections['menu'] == 'string' and sa.selections['onefile'] == None and 'string' in sa.selections \
            and 'get_file_check' not in sa.selections and sa.selections['download'] != '3'\
            and 'hours_feedback' not in sa.selections:


        message = "As there might be many files containing the string, do you want me to store all details in one file (having file name + string)?"
        texts = ["Yes",
                 "No"]
        attachments = sa.set_attachments(texts, sa.selections['callback_id'], "onefile")
        sa.prompt_message_attachments(message, "get_file_check", attachments)


def add_file_check(form_json):
    if 'actions' in form_json and form_json['actions'][0]['name'] == 'onefile':
        sa.selections['onefile'] = form_json['actions'][0]['value']


def remember_file():
    if sa.selections['onefile'] != None and 'remember_file' not in sa.selections:
        if sa.selections['onefile'] == '1': x = 'one file'
        elif sa.selections['onefile'] == '2': x = 'more file'
        message = "I'll be storing results in ```%s```" % x
        sa.prompt_message(message, "remember_file")


def add_hours_selection(form_json):
    if 'actions' in form_json and form_json['actions'][0]['name'] == 'hours_feedback':
        if form_json['actions'][0]['value'] == '1':
            sa.selections['hours'] = '24'
        elif form_json['actions'][0]['value'] == '2':
            sa.selections['hours_feedback'] = '2'

def input_hours(form_json):
    try:
        if 'submission' in form_json:
            sa.selections['hours'] = form_json['submission']['hours']
    except KeyError:
        pass



def get_files():
    if ('get_files' not in sa.selections and sa.selections['hours'] != None and 'hours_feedback' in sa.selections) \
            or ('get_files' not in sa.selections and 'response' in sa.selections) or \
            ('get_files' not in sa.selections and sa.selections['hours'] == '24') or (sa.selections['menu'] == 'sample'
                                                                                      and 'get_files' not in sa.selections and 'response' in sa.selections):
        message = "Please wait..."
        sa.prompt_message(message, "please_wait")
        if sa.selections['hours'] != None:
            td = datetime.timedelta(hours=int(sa.selections['hours']))
            s3 = boto3.resource('s3')
            s3_bucket = s3.Bucket(sa.selections['bucket'])
            items = [item for item in s3_bucket.objects.filter(Prefix=sa.selections['prefix'])]  # get them all
            now = datetime.datetime.now(datetime.timezone.utc)
            last_24_hours_keys = [item.key for item in items if now - item.last_modified < td]  # filter
            if last_24_hours_keys == []:
                message = "No files were ingested in the past %s hours" % sa.selections['hours']
                sa.prompt_message(message, "no_files")
            else:
                sa.selections['files'] = last_24_hours_keys
                sa.selections['hs'] = 'y'
        else:
            sa.selections['files'] = sa.selections['response']['Contents']
            sa.selections['hs'] = 'n'
        sa.prompt_message("Please wait...", 'get_files')




def parse_s3(form_json):
    if ('get_files' in sa.selections and 'what_now' not in sa.selections) or ('get_files' in sa.selections and 'what_now' in sa.selections and sa.selections['what_now'] != '3'):
        for i, f in enumerate(sa.selections['files']):
            if sa.selections['hs'] == 'y' or f['StorageClass'] == 'STANDARD':
                try:
                    name = f['Key'].rsplit('/', 1)
                    if name[1] != '':
                        file_name = name[1]
            #### f.split('/')[-1] = file name as without has path
                except:
                    file_name = f.split('/')[-1]
                print('9')
                try: print(file_name) ##### meaning file first key in response['contents'] is not glacier and it's a folder. example: 'Key': 'basic-rules/api/'
                except UnboundLocalError: file_name = ''
                print('11111')
                if file_name != '':
                    what_to_string_found(i, file_name, form_json)
                    # check_txt(file_name)




def add_what_now(form_json):
    if 'actions' in form_json and form_json['actions'][0]['name'] == 'what_now':
        sa.selections['what_now'] = form_json['actions'][0]['value']


        # The endpoint Slack will send the user's menu selection to
@app.route("/slack/message_actions", methods=['POST'])
def message_actions():
    form_json = json.loads(request.form["payload"])
    print("ciao")
    print(form_json)
    print("ciao")
    add_what_now(form_json)  ##### verify user changed his mind about sa.selections['what_now']
    print("selection")
    print(sa.selections)
    print("selection")
    ##### check if use changed his mind. if yes, delete the selection dictionary and basically kill the script
    if 'what_now' in sa.selections and sa.selections['what_now'] == '3':
        sa.selections = {}
        return make_response("Stopping as requested!", 200)
    set_menu(form_json) #####       set sa.selections['menu'] = 'string' and sa.selections['menu'] = 'sample'
    set_path(form_json) ##### "Type the bucket and path"
    set_bucket(form_json) ####   define sa.selections['bucket']  and sa.selections['prefix'] "Please make sure you type a right path."
    looking_in_path() #### print "I'll be looking in path ```%s```" % sa.selections['path']
    # sample()
    add_download_selection(form_json) #### set sa.selections['download']
    download_selection(form_json) #### "What would you like to do if I find what you are looking for?"
    set_string(form_json) ##### "Type the string"
    add_string_selection(form_json) #### set sa.selections['string']
    looking_for_string() #### print "I'll be looking for string ```%s```" % sa.selections['string']
    add_file_check(form_json) #### set sa.selections['onefile']

    add_hours_selection(form_json) #### sa.selections['hours'] = '24'
    remember_file() #### "I'll be storing results in ```%s```" % x
    get_file_check() ##### As there might be many files containing the string, do you want me to store all details in one file (having file name + string)  ['onefile']

    input_hours(form_json) #### add sa.selections['hours']
    bucket_check() ##### """There are """ + str(len(response['Contents'])) + """ files to check. Some might be filtered out as archived\n""" \\\ if '1000' in message...

    # time.sleep(10)
    set_hours_trigger(form_json) #### set third trigger id (after the one for menu, string, now hours) and store it in sa.selections['trigger_id']
    set_hours() #### "Please type how many hours" / you need trigger ID
    filtering_hours() #### print "I'll be looking for filtering files ingested in the last %s hours" % sa.selections['hours']

    get_files()
    # if 'job_done' not in sa.selections:
    parse_s3(form_json) #### call what_to_string_found(i, file_name, form_json) and check_txt(file_name)

    check_csv() ### message = "File %s has been created and populated in %s" % ("s3_parser_" + sa.selections['string'] + ".csv", os.getcwd())

    return make_response("", 200)





attachments_json = [
    {
        "fallback": "Upgrade your Slack client to use messages like these.",
        "color": "#3AA3E3",
        "attachment_type": "default",
        "callback_id": "menu_options_2319",
        "actions": [
            {
                "name": "bev_list",
                "text": "Pick from list...",
                "type": "select",
                "data_source": "external"
            }
        ]
    }
]


# @app.route("/slash", methods=['POST'])
slack_client.api_call(
    "chat.postMessage",
    channel="#test-api",
    text="What can I do for you? :aws-s3:",
    attachments=attachments_json)


@app.route("/kill", methods=['POST'])
def kill():
    sa.selections = {}
    return make_response("", 200)
# Start the Flask server
if __name__ == "__main__":
    # count = 0
    # while count < 10:
    app.run(debug=True)
    # send_message()

    # count += 1


