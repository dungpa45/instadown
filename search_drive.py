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

def list_file_in_folder(folder_id,servi):
    result = servi.files().list(q="'" + folder_id + "' in parents",
                            fields="nextPageToken, files(id, name, mimeType)").execute()
    files = result.get('files',[])
    return files

def return_data(l_files):
    l_name = []
    l_mess = []
    for data in l_files:
        file_id = data["id"]
        file_name = data["name"]
        l_name.append(file_name)

        messages = "file name: " + file_name + "\nlink: https://docs.google.com/document/d/"+file_id
        l_mess.append(messages)
    return l_mess

def find_text_wildcard(l_object,text_find):
    l_result = []
    for obj in l_object:
        name = obj["name"]
        if text_find.lower() in name.lower():
            l_result.append(obj)
    return l_result

def get_data_drive(text_input):
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token_drive.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'drive-cre-osamdung.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('drive', 'v3', credentials=creds)

    # Call the Drive v3 API
    re = service.files().list(q="'1PvkmZIFXKGibpjqyjvT9NKfgiWR9dqNu' in parents",fields="nextPageToken, files(id, name, mimeType)").execute()
    items = re.get('files', [])

    l_folder = []
    for item in items:
        if item["mimeType"] == "application/vnd.google-apps.folder":
            l_folder.append(item)
    # print(l_folder)

    for folder in l_folder:
        folderID = folder["id"]
        folder_name = folder["name"]
        print(folder_name)
        l_files = list_file_in_folder(folderID,service)
        # print("list file in folder", l_files)
        l_result = find_text_wildcard(l_files,text_input)
        data = return_data(l_result)
    messages = "\n".join(str(i) for i in data)
    if messages == "":
        return "Not found :("
    return messages

def start(bot , update):
    user = update.message.from_user
    update.message.reply_text('''Hello {} \nYou can type something you want find more information.
    \nPlease type keyword with English'''.format(user.full_name))

def reply_user(bot, update):
    user_text = update.message.text
    # input_text = user_text.split(" ")
    # print(input_text, type(input_text),input_text[0])
    print(user_text)
    info_data = get_data_drive(user_text)
    print(info_data)
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