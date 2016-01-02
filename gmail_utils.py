from __future__ import print_function

import os
from email.mime.text import MIMEText
import base64
import httplib2
import email
from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools
from apiclient import errors
import ip_utils
import time

try:
    import argparse

    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

SCOPES = 'https://mail.google.com/'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Amazon bot'

SENDER = "tars.raspi@gmail.com"
TO = "marimuthu125@gmail.com"


def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, 'gmail-python-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)

    return credentials


def main():
    """Shows basic usage of the Gmail API.

    Creates a Gmail API service object and outputs a list of label names
    of the user's Gmail account.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)

    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    if not labels:
        print('No labels found.')
    else:
        print('Labels:')
        for label in labels:
            print(label['name'])


def get_service():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    return service


def create_message(subject, message_text):
    message = MIMEText(message_text)
    message['to'] = TO
    message['from'] = SENDER
    message['subject'] = subject
    return {'raw': base64.urlsafe_b64encode(message.as_string())}


def send_message(subject, message_text):
    print("Sending mail...")
    message = create_message(subject, message_text)
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    message = (service.users().messages().send(userId=SENDER, body=message).execute())
    return message


def read(label):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    return list_messages_matching_query(service, SENDER, TO, label)


def list_messages_matching_query(service, user_id, query='', label_ids=[]):
    response = service.users().messages().list(userId=user_id, q=query, labelIds=label_ids).execute()
    messages = []
    if 'messages' in response:
        messages.extend(response['messages'])

    while 'nextPageToken' in response:
        page_token = response['nextPageToken']
        response = service.users().messages().list(userId=user_id, q=query,
                                                   pageToken=page_token).execute()
        messages.extend(response['messages'])

    return messages


def ListMessagesWithLabels(service, user_id, label_ids=[]):
    response = service.users().messages().list(userId=user_id,
                                               labelIds=label_ids).execute()
    messages = []
    if 'messages' in response:
        messages.extend(response['messages'])

    while 'nextPageToken' in response:
        page_token = response['nextPageToken']
        response = service.users().messages().list(userId=user_id,
                                                   labelIds=label_ids,
                                                   pageToken=page_token).execute()
        messages.extend(response['messages'])

    return messages


def GetMessage(msg_id):
    try:
        service = get_service()
        message = service.users().messages().get(userId='me', id=msg_id).execute()

        print('Message snippet: %s' % message['snippet'])

        return message['snippet']
    except errors.HttpError, error:
        print('An error occurred: %s' % error)


def GetMimeMessage(service, user_id, msg_id):
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id,
                                                 format='raw').execute()

        print('Message snippet: %s' % message['snippet'])

        msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))

        mime_msg = email.message_from_string(msg_str)

        return mime_msg
    except errors.HttpError, error:
        print('An error occurred: %s' % error)


def set_as_read_message(msg_id):
    try:
        service = get_service()
        message = service.users().messages().modify(userId='me', id=msg_id, resource={"addLabelIds": [],
                                                                                      "removeLabelIds": [
                                                                                          'UNREAD']}).execute()
        label_ids = message['labelIds']

        print('Message ID: %s - With Label IDs %s' % (msg_id, label_ids))
        return message
    except errors.HttpError, error:
        print('An error occurred: %s' % error)


def delete_message(msg_id):
    try:
        service = get_service()
        service.users().messages().delete(userId='me', id=msg_id).execute()
        print('Message with id: %s deleted successfully.' % msg_id)
    except errors.HttpError, error:
        print('An error occurred: %s' % error)


def create_msg_labels():
    return {'removeLabelIds': [], 'addLabelIds': ['UNREAD', 'INBOX', 'Label_2']}


def serve_your_master():
    messages = read("UNREAD")
    print (len(messages))
    for ids in messages:
        order = GetMessage(ids['id'])
        print(order)
        if order == 'Your ip?':
            send_message('My IP', ip_utils.get_public_ip())
            delete_message(ids['id'])


def serve_pi():
    print('Gmail Utils')
    while (True):
        try:
            serve_your_master()
            time.sleep(60)
        except:
            time.sleep(60)


if __name__ == '__main__':
    serve_pi()
