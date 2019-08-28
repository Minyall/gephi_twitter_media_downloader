import os
import requests
from urllib.error import HTTPError
from shutil import copyfileobj
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


def get_video_url(entity, _id, medium):
    data_dict = {'tweet_id': _id, 'media_url': '', 'bitrate': -1, 'type': '', 'medium': medium}

    for variant in entity['video_info']['variants']:
        if 'bitrate' in variant:
            if variant['bitrate'] > data_dict['bitrate']:
                data_dict['media_url'] = variant['url']
                data_dict['bitrate'] = variant['bitrate']
                data_dict['type'] = variant['content_type'][-3:]
    return data_dict


def get_photo_url(entity, _id, medium):
    data_dict = {'tweet_id': _id, 'media_url': '', 'type': '', 'medium': medium}
    data_dict['media_url'] = entity['media_url']
    data_dict['type'] = entity['media_url'][-3:]
    return data_dict


def get_entities(data, _id):
    if 'extended_entities' in data:
        target = data['extended_entities']
    elif 'entities' in data:
        target = data['entities']
    else:
        return {'message': 'No Media Found', 'tweet_id': _id}

    entities = []
    if 'media' in target:
        for ent in target['media']:
            if ent['type'] == 'video':
                data_dict = get_video_url(ent, _id, medium='video')
            elif ent['type'] == 'photo':
                data_dict = get_photo_url(ent, _id, medium='photo')
            elif ent['type'] == 'animated_gif':
                data_dict = get_video_url(ent, _id, medium='animated_gif')
            entities.append(data_dict)

    else:
        entities.append({'message': 'No Media Found', 'tweet_id': _id})

    return entities

def item_retrieve(data_dict):
    try:
        media_dir = os.path.join('media',data_dict['medium'])
        name = os.path.join(media_dir,'{}_{}.{}'.format(data_dict['original_row'],data_dict['tweet_id'], data_dict['type'][-3:]))
        r = requests_retry_session().get(data_dict['media_url'], stream=True)
        with open(name, 'wb') as f:
            copyfileobj(r.raw, f)
        data_dict['media_file'] = name
    except HTTPError:
        data_dict['media_file'] = 'Error - Could Not Retrieve'
        return
    return

def if_no_dir_make(path):
    import os
    try:
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise
    finally:
    	return path

def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

if __name__ == '__main__':
    pass
