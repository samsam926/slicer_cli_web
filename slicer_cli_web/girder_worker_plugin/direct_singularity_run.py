from os import R_OK, access, getenv, F_OK,chdir,system
from os.path import abspath, basename, isfile, join

from girder_worker.app import app, Task
from girder_worker.docker.io import FDReadStreamConnector
from girder_worker.docker.tasks import SingularityTask,singularity_run, DockerTask
from girder_worker.docker.transforms import BindMountVolume, ContainerStdOut
from girder_worker.docker.transforms.girder import GirderFileIdToVolume
from girder_worker_utils import _walk_obj
from girder_worker_utils.transforms.girder_io import GirderClientTransform
from girder import logger
from utils.singularity_helper import SINGULARITY_COMMANDS, singularity_cmd_list

from .cli_progress import CLIProgressCLIWriter


def _get_basename(filename, direct_path):
    if filename:
        return filename
    if not direct_path:
        return None
    return basename(direct_path)


TEMP_VOLUME_DIRECT_MOUNT_PREFIX = '/mnt/girder_direct_worker'


class DirectGirderFileIdToVolume(GirderFileIdToVolume):
    def __init__(self, _id, filename=None, direct_file_path=None, **kwargs):
        superc = super()
        superc.__init__(_id, filename=_get_basename(filename, direct_file_path),
                        **kwargs)
        self._direct_file_path = direct_file_path
        self._direct_container_path = None

    def resolve_direct_file_path(self):
        if not self._direct_file_path:
            return None

        path = abspath(self._direct_file_path)
        if isfile(path) and access(path, R_OK):
            self._direct_container_path = join(TEMP_VOLUME_DIRECT_MOUNT_PREFIX, self._filename)
            return BindMountVolume(path, self._direct_container_path, mode='ro')
        return None

    def transform(self, **kwargs):
        if self._direct_container_path:
            return self._direct_container_path
        return super().transform(**kwargs)


class GirderApiUrl(GirderClientTransform):
    def transform(self, **kwargs):
        return self.gc.urlBase


class GirderToken(GirderClientTransform):
    def transform(self, **kwargs):
        return self.gc.token


def _resolve_direct_file_paths(args, kwargs):
    extra_volumes = []

    def resolve(arg, **kwargs):
        if isinstance(arg, DirectGirderFileIdToVolume):
            path = arg.resolve_direct_file_path()
            if path:
                extra_volumes.append(path)
        return arg
    _walk_obj(args, resolve)
    _walk_obj(kwargs, resolve)

    return extra_volumes


class DirectDockerTask(DockerTask):
    def __call__(self, *args, **kwargs):
        extra_volumes = _resolve_direct_file_paths(args, kwargs)
        if extra_volumes:
            volumes = kwargs.setdefault('volumes', [])
            if isinstance(volumes, list):
                # list mode use
                volumes.extend(extra_volumes)
            else:
                for extra_volume in extra_volumes:
                    volumes.update(extra_volume._repr_json_())

        super().__call__(*args, **kwargs)

class DirectSingularityTask(Task):
    def __call__(*args,**kwargs):
        super().__call__(*args,**kwargs)

def check_local_sif_image(image):
    """
    Pulls the specified Plugin image (Ususally a docker image) onto the singularity container if the image is not present
    """
    #Image path - Image path has to be present in tmp/images folder
    if not image:
        logger.exception('Image name cannot be empty')
        return False
    #Just for testing. Change it later...
    return False




@app.task(base=DirectSingularityTask, bind=True)
def run(task, *args, **kwargs):
    """Wraps singularity_run to support running singularity containers"""

    pull_image = kwargs.get('pull_image')
    if pull_image == 'if-not-present':
        kwargs['pull_image'] = not check_local_sif_image(kwargs['image'])
    image = kwargs.get('image','')
    logger.info('LOG!! Sending job to girder_worker!!')
    return singularity_run(task,image,*args **kwargs)
