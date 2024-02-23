#!/usr/bin/env python3

"""Send an email message from the user's account.
PIP packages needed:
    google-api-python-client
    google-auth-oauthlib
Must have valid Oauth 2.0 credential saved in credentials.json. Follow steps here:
    https://developers.google.com/workspace/guides/create-credentials
"""

import base64
import os
import pickle
import argparse
import sys
import os.path
import json

try:
    from email.mime.audio import MIMEAudio
    from email.mime.base import MIMEBase
    from email.mime.image import MIMEImage
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    import mimetypes
    from googleapiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from apiclient import errors
except ImportError:
    print("ERROR: Some required libraries not found")
    print("Do something like this to install them using pip:")
    print("  python3 -m pip install google-api-python-client google-auth-oauthlib")
    exit(1)

SCOPES=['https://www.googleapis.com/auth/gmail.send']

scriptdir = os.path.dirname(os.path.realpath(__file__))

def send_message(service, user_id, message):
  """Send an email message.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    message: Message to be sent.

  Returns:
    Sent Message.
  """
  try:
    message = (service.users().messages().send(userId=user_id, body=message)
               .execute())
    #print 'Message Id: %s' % message['id']
    return message
  except: # errors.HttpError, error:
    print('An error occurred: %s' % error)

def create_message(sender, tos, subject, message_text, ccs=(), alist=()):
    """Create a message for an email.

    Args:
      sender: Email address of the sender.
      tos: List of recipient emails
      subject: The subject of the email message.
      message_text: The text of the email message.
      alist: List of strings with attachment file pathnames.
      ccs: List of email addresses for CC field

    Returns:
      An object containing a base64url encoded email object.
    """
    message = MIMEText(message_text)
    if alist:
        inner = message
        message = MIMEMultipart()
        message.attach(inner)

    message['to'] = ', '.join(tos)
    message['from'] = sender
    message['subject'] = subject
    if ccs:
        message['cc'] = ', '.join(ccs)

    for fname in alist:
        content_type, encoding = mimetypes.guess_type(fname)

        if content_type is None or encoding is not None:
            content_type = 'application/octet-stream'
        main_type, sub_type = content_type.split('/', 1)
        if main_type == 'text':
            fp = open(fname, 'r')
            msg = MIMEText(fp.read(), _subtype=sub_type)
            fp.close()
        elif main_type == 'image':
            fp = open(fname, 'rb')
            msg = MIMEImage(fp.read(), _subtype=sub_type)
            fp.close()
        elif main_type == 'audio':
            fp = open(fname, 'rb')
            msg = MIMEAudio(fp.read(), _subtype=sub_type)
            fp.close()
        else:
            fp = open(fname, 'rb')
            msg = MIMEBase(main_type, sub_type)
            msg.set_payload(fp.read())
            fp.close()
        filename = os.path.basename(fname)
        msg.add_header('Content-Disposition', 'attachment', filename=filename)
        message.attach(msg)

    return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

def build_service(credfile, pickfile):
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(pickfile):
        with open(pickfile, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credfile, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(pickfile, 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)
    return service

def get_config():
    global configpath, conffile
    # https://stackoverflow.com/a/53222876/1008966
    configpath = os.path.join(
        os.environ.get('APPDATA') or
        os.environ.get('XDG_CONFIG_HOME') or
        os.path.join(os.environ['HOME'], '.config'),
        "send-gmail")
    os.makedirs(configpath, exist_ok=True)
    conffile = os.path.join(configpath, 'config.json')
    if os.path.exists(conffile):
        with open(conffile, 'r') as confin:
            return json.load(confin)
    else:
        defcredfile = os.path.join(configpath, 'credentials.json')
        print(f"""No config file found. Let's create it now!

First, you need to create an OAuth2 credential from Google
and download the JSON.

As of January 2024, here is what you do:
(1) Go to the GMail API page https://console.cloud.google.com/apis/library/gmail.googleapis.com
    Log in and enable this API.
    (Note, for USNA, you might need to put in an ITSD help ticket to enable Google cloud access.)
(2) Set up OAuth consent screen - set to INTERNAL
    https://console.cloud.google.com/apis/credentials/consent
(3) Go to APIs/Credentials https://console.cloud.google.com/apis/credentials
    Click Create Credentials -> OAuth -> Desktop App. Pick any name you like.
    Once created, click "download JSON" and save the file to a safe place
    I recommend saving to {defcredfile}
""")
        credfile = input(f"Filename of OAuth json (blank for {defcredfile}): ")
        if not credfile:
            credfile = defcredfile
        if not os.path.exists(credfile):
            print("ERROR: could not find credentials file; aborting", file=sys.stderr)
            raise FileNotFoundError(credfile)
        fromEmail = input("Email address sending from (should match your credential): ")
        fromName = input("Name to display as sending from: ")
        fromAdd = f"{fromName} <{fromEmail}>"
        info = {
            'credfile': credfile,
            'pickfile': os.path.join(configpath, 'token.pickle'),
            'fromAdd': fromAdd,
        }
        with open(conffile, 'w') as confout:
            json.dump(info, confout)
        return info


def main(tos, subject, attach=(), bodyfile=None, cc=(), loud=True):
    txtsrc = open(bodyfile, 'r') if (bodyfile is not None) else sys.stdin

    try:
        info = get_config()
        credfile = info['credfile']
        pickfile = info['pickfile']
        fromAdd = info['fromAdd']
    except FileNotFoundError:
        exit(1)
    except (json.decoder.JSONDecodeError, KeyError):
        print("ERROR loading config info", file=sys.stderr)
        print(f"Try deleting '{conffile}' if it exists", file=sys.stderr)
        exit(1)

    if loud: print("Trying to read credentials and connect to gmail...")
    service = build_service(credfile, pickfile)
    if loud: print("Connected successfully.")

    if loud:
        if bodyfile is not None:
            print(f"Reading message body from '{bodyfile}'...")
        elif os.isatty(sys.stdin.fileno()):
            print("Type the body of your message below, followed by EOF (Ctrl-D)")
        else:
            print("Reading message body from standard in...")
    txt = txtsrc.read()

    if loud: print("Creating MIME message...")
    msg = create_message(
        sender=fromAdd,
        tos=tos,
        subject=subject,
        message_text=txt,
        ccs=cc,
        alist=attach,
    )

    if loud: print("Sending message to gmail...")
    send_message(service, 'me', msg)

    if loud:
        mlen = len(msg['raw'])
        print(f"Success! Sent {mlen} bytes to {tos}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--cc', action='append',
            help="CC recipient (may be specified multiple times)")
    parser.add_argument('-t', '--to', action='append',
            help="Additional TO recipient (may be specified multiple times)")
    parser.add_argument('-a', '--attach', action='append', default=[],
            help="attachment (may be specified multiple times)")
    parser.add_argument('-b', '--body', default=None,
            help="filename containing the body of the message (by default, read from standard in)")
    parser.add_argument('-q', '--quiet', action='store_true',
            help="don't print any info to say what is happening")
    parser.add_argument('recipient', help='the email address of the recipient')
    parser.add_argument('subject', nargs='+', help="subject line")
    args = parser.parse_args()
    tos = [args.recipient]
    if args.to:
        tos.extend(args.to)
    main(
        tos = tos,
        subject = ' '.join(args.subject),
        attach = args.attach,
        bodyfile = args.body,
        cc = args.cc,
        loud = not args.quiet,
    )
