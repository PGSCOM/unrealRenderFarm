"""
Unreal render job request class for data representation and database operation
"""

import logging
import socket
import uuid
from datetime import datetime
import requests
import json
import os

with open(os.path.join(os.path.dirname(__file__), '..', 'config.json'), 'r') as f:
    config = json.load(f)

# Coger la contraseña de cloudflarepassword.json desde el valor "password", si no exsiste dejar la variable vacía
try:
    with open(os.path.join(os.path.dirname(__file__), '..', 'cloudflarepassword.json'), 'r') as f:
        password = json.load(f)['password']
except FileNotFoundError:
    password = ''

DATABASE_url = config.get('serverUrl', 'http://localhost:5000') + '/api/'


LOGGER = logging.getLogger(__name__)

'''
MODULE_PATH = os.path.dirname(os.path.abspath(__file__))
ROOT_PATH = os.path.dirname(MODULE_PATH)
DATABASE = os.path.join(ROOT_PATH, 'database')
'''


class RenderStatus(object):
    """
    Enum class to represent render job status
    """

    unassigned = 'un-assigned'
    ready_to_start = 'ready to start'
    in_progress = 'in progress'
    finished = 'finished'
    errored = 'errored'
    cancelled = 'cancelled'
    paused = 'paused'


class RenderRequest(object):
    """
    An object representing request for an Unreal render job sent from a
    machine to the request manager (renderManager.py)
    """

    def __init__(
            self,
            uid='',
            name='',
            owner='',
            worker='',
            time_created='',
            priority=0,
            category='',
            tags=[],
            status='',
            umap_path='',
            useq_path='',
            uconfig_path='',
            output_path='',
            width=0,
            height=0,
            frame_rate=0,
            format='',
            start_frame=0,
            end_frame=0,
            time_estimate='',
            progress=0,
            datapswd=None
    ):
        """
        Initialization

        :param uid: str. unique identifier, server as primary key for database
        :param name: str. job name
        :param owner: str. the name of the submitter
        :param worker: str. the name of the worker to render the job
        :param time_created: str. datetime in .strftime("%m/%d/%Y, %H:%M:%S") format
        :param priority: int. job priority [0 lowest to 100 highest]
        :param category: str.
        :param tags: [str].
        :param status: RenderStatus. job render status
        :param umap_path: str. Unreal path to the map/level asset
        :param useq_path: str. Unreal path to the sequence asset
        :param uconfig_path: str. Unreal path to the preset/config asset
        :param output_path: str. system path to the output directory
        :param width: int. output width
        :param height: int. output height
        :param frame_rate: int. output frame rate
        :param format: int. output format
        :param start_frame: int. custom render start frame
        :param end_frame: int. custom render end frame
        :param time_estimate: str. render time remaining estimate
        :param progress: int. render progress [0 to 100]
        :param description: str. job description
        :param datapswd: str. password for the job
        """
        self.uid = uid or str(uuid.uuid4())[:4]
        self.name = name
        self.owner = owner or socket.gethostname()
        self.worker = worker
        self.time_created = time_created or datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        self.priority = priority or 0
        self.category = category
        self.tags = tags
        self.status = status or RenderStatus.unassigned
        self.umap_path = umap_path
        self.useq_path = useq_path
        self.uconfig_path = uconfig_path
        self.output_path = output_path
        self.width = width or 1280
        self.height = height or 720
        self.frame_rate = frame_rate or 30
        self.format = format or 'JPG'
        self.start_frame = start_frame or 0
        self.end_frame = end_frame or 0
        self.length = self.end_frame - self.start_frame
        self.time_estimate = time_estimate
        self.progress = progress
        self.datapswd = datapswd

    @classmethod
    def from_db(cls, uid):
        """
        re-create a request object from database using uid

        This is a fake database using json

        :param uid: int. unique id from database
        :return: RenderRequest. request object
        """
        #request_file = os.path.join(DATABASE, '{}.json'.format(uid))
        request_fileurl = DATABASE_url + '/get/' + uid
    
        try:
            response = requests.get(request_fileurl, params={'password': password})
            response.raise_for_status()
            request_dict = response.json()
        except Exception as e:
            LOGGER.error('Failed to load request object from db: %s', e)
            return None
        return cls.from_dict(request_dict)

    @classmethod
    def from_dict(cls, d):
        """
        Create a new request object from partial dictionary/json or.
        re-create a request object from function 'to_dict'

        :param d: dict. input dictionary
        :return: RenderRequest. request object
        """
        # has to assign a default value of '' or 0 for initialization
        # value to kick-in
        uid = d.get('uid') or ''
        name = d.get('name') or ''
        owner = d.get('owner') or ''
        worker = d.get('worker') or ''
        time_created = d.get('time_created') or ''
        priority = d.get('priority') or 0
        category = d.get('category') or ''
        tags = d.get('tags') or []
        status = d.get('status') or ''
        umap_path = d.get('umap_path') or ''
        useq_path = d.get('useq_path') or ''
        uconfig_path = d.get('uconfig_path') or ''
        output_path = d.get('output_path') or ''
        width = d.get('width') or 0
        height = d.get('height') or 0
        frame_rate = d.get('frame_rate') or 0
        format = d.get('format') or ''
        start_frame = d.get('start_frame') or 0
        end_frame = d.get('end_frame') or 0
        time_estimate = d.get('time_estimate') or ''
        progress = d.get('progress') or 0
        datapswd = d.get('datapswd') or None

        return cls(
            uid=uid,
            name=name,
            owner=owner,
            worker=worker,
            time_created=time_created,
            priority=priority,
            category=category,
            tags=tags,
            status=status,
            umap_path=umap_path,
            useq_path=useq_path,
            uconfig_path=uconfig_path,
            output_path=output_path,
            width=width,
            height=height,
            frame_rate=frame_rate,
            format=format,
            start_frame=start_frame,
            end_frame=end_frame,
            time_estimate=time_estimate,
            progress=progress,
            datapswd=datapswd
        )

    def to_dict(self):
        """
        Convert current request to a dictionary
        """
        return self.__dict__

    def write_json(self):
        """
        Write current request to the fake database (as a .json)
        """
        write_db(self.__dict__)

    def remove(self):
        """
        Remove current request from the fake database
        """
        remove_db(self.uid)

    def update(self, progress=0, status='', time_estimate=''):
        """
        Update current request progress in the fake database
        """
        if progress:
            self.progress = progress
        if status:
            self.status = status
        if time_estimate:
            self.time_estimate = time_estimate

        LOGGER.debug('Updating RenderRequest UID: %s with progress=%d, status=%s, time_estimate=%s',
                     self.uid, self.progress, self.status, self.time_estimate)
        
        update_db(self.uid, self.__dict__)


# region database utility

def read_all():
    """
    Read and convert everything in the database to RenderRequest objects
    via API
    """
    get_url = DATABASE_url + 'get'
    response = requests.get(get_url, params={'password': password})
    if response.status_code != 200:
        raise Exception(f"Failed to read from DB: {response.text}")

    data = response.json()
    rrequests = []
    for rdict in data.get("results", []):
        rr = RenderRequest.from_dict(rdict)
        rrequests.append(rr)

    return rrequests


def remove_db(uid):
    """
    Remove a RenderRequest object from the database

    :param uid: str. request uid
    """
    delete_url = f"{DATABASE_url}delete/{uid}"
    response = requests.delete(delete_url, params={'password': password})
    if response.status_code != 200:
        raise Exception(f"Delete failed for UID {uid}: {response.text}")


def remove_all():
    """
    Clear database via API request
    """
    delete_url = f"{DATABASE_url}delete/all"
    response = requests.delete(delete_url, params={'password': password})
    if response.status_code != 200:
        raise Exception(f"Delete all failed: {response.text}")


def write_db(d):
    """
    Write/overwrite a database entry via HTTP request
    """
    uid = d['uid']
    LOGGER.info('writing to %s', uid)
    post_url = DATABASE_url + 'post'
    response = requests.post(post_url, json=d, params={'password': password})
    if response.status_code != 200:
        raise Exception(f"Write failed for UID {uid}: {response.text}")


def update_db(uid, d):
    """
    Update a database entry via HTTP PUT request
    """
    LOGGER.info('Updating RenderRequest %s', uid)
    put_url = f"{DATABASE_url}put/{uid}"
    payload = f"{d['progress']};{d['time_estimate']};{d['status']}"
    headers = {'Content-Type': 'text/plain'}
    response = requests.put(put_url, data=payload, headers=headers, params={'password': password})
    if response.status_code != 200:
        raise Exception(f"Update failed for UID {uid}: {response.text}")

# endregion
