from __future__ import print_function
import pickle
import json
import os.path
#google
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
#telegram
from telegram.ext import Updater ,CommandHandler, InlineQueryHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, InputTextMessageContent, ReplyKeyboardMarkup
import glob, os
# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/documents.readonly']

# The ID of a sample document.
DOCUMENT_ID = '1hd-wEVwYwqIZ8fVCyeSrhiR5TNMVk7S_zUavm6TPZjM'
# DOCUMENT_ID = "1MUWmY74s_bAji9zAjW5ftbm5wjmbKMVVS8I8NmD4dXo"


def find_text_wildcard(l_text,text_find):
    l_result = []
    for string in l_text:
        print("string",string)
        if text_find in string:
            l_result.append(string)
    return l_result

def get_data_docs(text_user):
    """Shows basic usage of the Docs API.
    Prints the title of a sample document.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'docs_cre_osamdungpham.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('docs', 'v1', credentials=creds)

    # Retrieve the documents contents from the Docs service.
    document = service.documents().get(documentId=DOCUMENT_ID).execute()
    print('The title of the document is: {}'.format(document.get('title')))
    body = document.get('body')
    content = body["content"]
    # print(content)
    list_content=[]
    for i in content:
        try:
            para = i["paragraph"]
            if i["paragraph"]:
                list_line_content = para["elements"]
                if list_content is not None:
                    list_content = list_line_content+list_content
            else:
                continue
        except Exception as e:
            print(e)
    print(list_content)
    list_text = []
    for line in list_content:
        textline = line["textRun"]["content"]
        list_text.append(textline)
    print(list_text)
    result = find_text_wildcard(list_text,text_user)
    return result

def start(bot , update):
    user = update.message.from_user
    update.message.reply_text('''Hello {} \nYou can type something you want find more information.
    \nPlease type keyword with English'''.format(user.full_name))

def reply_user(bot, update):
    user_text = update.message.text
    input_text = user_text.split(" ")
    print(input_text, type(input_text),input_text[0])
    info_data = get_data_docs(input_text[0])
    update.message.reply_text(info_data,ParseMode.MARKDOWN)

def main():
    TOKEN = "1074719682:AAGB0S76v5lwAIxbkEIZJkXz-COgh23gPG8"
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    start_handler = CommandHandler('start', start)
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(MessageHandler(Filters.text,reply_user))
    dp.add_handler(start_handler)
    # start the bot
    updater.start_polling()
    # Run the bot until press ctrl +C
    updater.idle()

if __name__ == '__main__':
    main()