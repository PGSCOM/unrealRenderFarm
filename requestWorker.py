"""
Client to work/process render request, which launches executor locally and
updates status to the server
"""

import logging
import os
import subprocess
import time

from util import client
from util import renderRequest
import requests

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

MODULE_PATH = os.path.dirname(os.path.abspath(__file__))

# render worker specific configuration
WORKER_NAME = 'RENDER_MACHINE_01'
UNREAL_EXE = r'C:\Program Files\Epic Games\UE_5.5\Engine\Binaries\Win64\UnrealEditor.exe'
UNREAL_PROJECT = r"D:\Documentos publicos\Unreal Projects\MeerkatDemo\MeerkatDemo.uproject"


def render(uid, umap_path, useq_path, uconfig_path):
    """
    Render a job locally using the custom executor (myExecutor.py)

    Note:
    I only listed the necessary arguments here,
    we can easily add custom commandline flags like '-StartFrame', '-FrameRate' etc.
    but we also need to implement in the MyExecutor class as well

    :param uid: str. render request uid
    :param umap_path: str. Unreal path to the map/level asset
    :param useq_path: str. Unreal path to the sequence asset
    :param uconfig_path: str. Unreal path to the preset/config asset
    :return: (str. str). output and error messages
    """
    command = [
        UNREAL_EXE,
        UNREAL_PROJECT,

        umap_path,
        "-JobId={}".format(uid),
        "-LevelSequence={}".format(useq_path),
        "-MoviePipelineConfig={}".format(uconfig_path),

        # required
        "-game",
        "-MoviePipelineLocalExecutorClass=/Script/MovieRenderPipelineCore.MoviePipelinePythonHostExecutor",
        "-ExecutorPythonClass=/Engine/PythonTypes.MoviePipelineExampleRuntimeExecutor",

        # render preview
        "-windowed",
        "-resX=1280",
        "-resY=720",

        # logging
        "-StdOut",
        "-FullStdOutLogOutput"
    ]
    env = os.environ.copy()
    env["UE_PYTHONPATH"] = MODULE_PATH
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env
    )
    return proc.communicate()


def update_render_status(uid, progress=0, status='', time_estimate=''):
    """
    Update the render status on the server

    :param uid: str. render request uid
    :param progress: int. updated progress
    :param status: str. updated status
    :param time_estimate: str. updated estimate remaining time
    """
    try:
        client.update_request(uid, progress, status, time_estimate)
    except requests.exceptions.JSONDecodeError as e:
        LOGGER.error('Failed to decode JSON response: %s', e)


if __name__ == '__main__':
    LOGGER.info('Starting render worker %s', WORKER_NAME)
    while True:
        rrequests = client.get_all_requests()
        uids = [rrequest.uid for rrequest in rrequests
                if rrequest.worker == WORKER_NAME and
                rrequest.status == renderRequest.RenderStatus.ready_to_start]

        # render blocks main loop
        for uid in uids:
            LOGGER.info('rendering job %s', uid)

            rrequest = renderRequest.RenderRequest.from_db(uid)
            update_render_status(uid, progress=0, status=renderRequest.RenderStatus.in_progress)

            output = render(
                uid,
                rrequest.umap_path,
                rrequest.useq_path,
                rrequest.uconfig_path
            )

            # for debugging
            # for line in str(output).split(r'\r\n'):
            #     if 'LogPython' in line:
            #         print(line)

            LOGGER.info("finished rendering job %s", uid)
            update_render_status(uid, progress=100, status=renderRequest.RenderStatus.finished)

        # check assigned job every 10 sec after previous job has finished
        time.sleep(10)
        LOGGER.info('current job(s) finished, searching for new job(s)')
