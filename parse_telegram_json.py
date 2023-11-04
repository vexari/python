
import json
import pandas as pd
from datetime import datetime
import argparse
import csv
import logging
import os

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_text_entities(message):
    """Extracts and concatenates text content from a message object."""
    full_text = ''
    if isinstance(message.get('text'), str):
        full_text += message['text']
    elif isinstance(message.get('text'), list):
        full_text += ''.join(filter(lambda x: isinstance(x, str), message['text']))

    for entity in message.get('text_entities', []):
        if isinstance(entity, dict) and 'text' in entity:
            full_text += entity['text']
        elif isinstance(entity, str):
            full_text += entity

    return full_text

def parse_telegram_chat(file_path, output_csv_path):
    """Parses a Telegram chat backup JSON file and exports non-empty messages to a CSV file."""
    # Check if output file exists and ask for confirmation to overwrite
    if os.path.exists(output_csv_path):
        proceed = input(f'The file "{output_csv_path}" already exists. Do you want to overwrite it? (y/n): ')
        if proceed.lower() != 'y':
            logging.info('Operation cancelled by user.')
            return

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            logging.info(f'Reading data from "{file_path}"...')
            telegram_data = json.load(file)
    except FileNotFoundError:
        logging.error(f'Error: The file "{file_path}" was not found.')
        return
    except json.JSONDecodeError:
        logging.error(f'Error: The file "{file_path}" is not a valid JSON file.')
        return

    logging.info('Processing messages...')
    channel_name = telegram_data.get('messages', [{}])[0].get('title', 'Unknown Channel')

    messages_data = [
        {
            'Channel Name': channel_name,
            'Timestamp': datetime.strptime(message['date'], '%Y-%m-%dT%H:%M:%S').strftime('%d/%m/%Y %H:%M'),
            'Sender Name': message.get('from', ''),
            'Message Content': extract_text_entities(message)
        }
        for message in telegram_data.get('messages', [])
        if message.get('type') == 'message' and extract_text_entities(message)
    ]

    df_messages = pd.DataFrame(messages_data)
    df_messages.sort_values(by='Timestamp', inplace=True)
    df_messages.to_csv(output_csv_path, index=False, quoting=csv.QUOTE_ALL, encoding='utf-8-sig')
    logging.info(f'Exported {len(df_messages)} messages to "{output_csv_path}"')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Parse a Telegram chat backup JSON file into a CSV.")
    parser.add_argument('file_path', help="The path to the Telegram JSON file.")
    parser.add_argument('output_csv_path', help="The path where the output CSV file will be saved.")

    args = parser.parse_args()
    parse_telegram_chat(args.file_path, args.output_csv_path)
