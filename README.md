# send-gmail
Send email on the command line via gmail

## Features

*   OAuth 2.0 authentication (no password needed after initial setup)
*   Supports subject, body, attachments, and CC's
*   Easily scripted or imported into other command-line or Python apps

## Python Requirements

You need a recent version of Python and two pip packages.

Running
    ./setup.sh

will install a virtual environment (venv) with the necessary packages,
and create a launcher script `send-gmail` which can be moved
and run from anywhere on this machine.

## Gmail requirements

The first time you run `send-gmail`, you will need to log in to
the Google Cloud Console to create an API token, which will be saved
to the local account for future invocations.

The program itself tells you want you need to do if you try to send a
simple test message like:

    ./send-gmail.py -b <(echo message body) 'YOUREMAIL@DOMAIN.COM' 'Test Subject'

## Usage

Run `./send-gmail.py -h`
