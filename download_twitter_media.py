import os
import tweepy
import credentials
import csv
from functions import get_entities, item_retrieve, if_no_dir_make
import glob
import sys
import datetime as dt

def main():
    print('**** Welcome to the Gephi/Twitter Media Downloader ****')

    if credentials.CONSUMER_KEY == '' or credentials.CONSUMER_SECRET == '':

        print('We will need your Twitter API Consumer Key and Consumer Secret to continue...')
        print('To avoid this prompt in the future please edit the "credentials.py" file.')
        CONSUMER_KEY = input('Please paste your Consumer Key here and press enter: ')
        CONSUMER_SECRET = input('Please paste your Consumer Secret here and press enter: ')
    else:
        CONSUMER_KEY = credentials.CONSUMER_KEY
        CONSUMER_SECRET = credentials.CONSUMER_SECRET

    print('Establishing folders...')
    if_no_dir_make(os.path.join('media', 'video'))
    if_no_dir_make(os.path.join('media', 'photo'))
    if_no_dir_make(os.path.join('media', 'animated_gif'))
    if_no_dir_make('reports')

    print ('[*] Please ensure your Gephi export .csv file is in the same folder as this script')
    if input('[*] When ready enter "y"...').lower() == 'y':
        # Read in data from Gephi export and build list of tweet_ids with a parallel list of indexes.
        indexes = []
        tweet_ids = []

        print('[*] Loading your Gephi Export...')
        file_list = glob.glob('*.csv')

        if len(file_list) == 0:
            sys.exit('[!] No file found...Quitting')


        print('.csv file found')
        print(f'The script will now load {file_list[0]}')
        if input('Continue?...y/n').lower() != 'y':
            sys.exit('Quitting')

        with open(file_list[0], mode='r') as f:
            csv_reader = csv.DictReader(f)
            for i, row in enumerate(csv_reader):
                if row['twitter_type'] == 'Tweet':
                    indexes.append(i)
                    tweet_ids.append(row['Id'])
        print(f'Located {len(indexes)} tweet ids in {file_list[0]}')

        # Establish Twitter API connection
        print('Establishing API Link...')
        try:
            auth = tweepy.AppAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
            api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
        except tweepy.TweepError:
            print('Error establishing API...')
            print(f'Is your CONSUMER_KEY correct?: {CONSUMER_KEY}')
            print(f'Is your CONSUMER_SECRET correct?: {CONSUMER_SECRET}')
            sys.exit('Quitting')

        # Iterate over the Ids check for the presence of media and generate a data dictionary of urls and meta_data
            # for reporting and media retrieval.

        print('Checking for media...')
        report_data = []
        for i, _id in enumerate(tweet_ids):
            if i % 10 == 0:
                print(f'Checked {i} of {len(tweet_ids)} tweets...')
            try:
                data = api.get_status(_id, include_entities=True)._json
                data_dict = get_entities(data, _id)
                data_dict['original_index'] = indexes[i]
                data_dict['tweet_url'] = f'https://twitter.com/statuses/{str(_id)}'
                report_data.append(data_dict)

            except tweepy.TweepError as e:
                report_data.append({'message': e, 'original_index': indexes[i], 'tweet_id': _id})
                continue

        num_media = len([x for x in report_data if 'medium' in x])
        print(f'Retrieved meta-data for {num_media} media items...')

        print('Retrieving Media items...')
        # Retrieve media items
        for row in report_data:
            if 'medium' in row:
                item_retrieve(row)
        now_str = dt.datetime.today().strftime('%Y-%m-%d_%H:%M:%S')
        report_name = f'{file_list[0][:-4]}_{now_str}_report.csv'
        print(f'Writing Report: {report_name} to the "reports" folder')
        # Write report
        with open(os.path.join('reports',report_name), mode='w') as csv_file:
            fieldnames = ['original_index','tweet_id','tweet_url','bitrate','type',
                          'medium','media_url','url','media_file','message']
            writer = csv.DictWriter(csv_file,fieldnames=fieldnames)
            writer.writeheader()
            for report in report_data:
                writer.writerow(report)
        print(f'Job Complete. Check the "media" folder for your files. Have a nice day!')
    else:
        sys.exit('Quitting...')

if __name__ == '__main__':
    main()
