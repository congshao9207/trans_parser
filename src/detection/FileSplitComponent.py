import os
import shutil
import uuid
import zipfile

from get_filename import get_filename

from config.trans_config import WORK_SPACE
from detection.split import pdf_image
from logger.logger_util import LoggerUtil


logger = LoggerUtil().logger(__name__)


class FileSplitComponent(object):
    def __init__(self, zoom_x, zoom_y, rotation_angle, file):
        self.zoom_x = zoom_x
        self.zoom_y = zoom_y
        self.rotation_angle = rotation_angle
        self.file = file
        self.stand_file_path = ''
        self.result_dir = ''
        self.result_zip_file = ''
        self.result_zip_name = ''

    def __enter__(self):
        if type(self.file) == str:
            self.stand_file_path = self.file
        else:
            ext = get_filename(self.file.filename, "extension", -1)
            stand_file_name = "split_" + str(uuid.uuid1()) + "." + ext
            self.stand_file_path = WORK_SPACE + os.path.sep + stand_file_name
            self.file.save(self.stand_file_path)

        self.result_dir = WORK_SPACE + os.path.sep + "fresult_" + str(uuid.uuid1())
        os.mkdir(self.result_dir)
        self.result_zip_name = "split_" + str(uuid.uuid1()) + ".zip"
        self.result_zip_file = WORK_SPACE + os.path.sep + self.result_zip_name

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.stand_file_path and os.path.exists(self.stand_file_path):
            os.remove(self.stand_file_path)
        if self.result_dir and os.path.exists(self.result_dir):
            shutil.rmtree(self.result_dir)
        if self.result_zip_file and os.path.exists(self.result_zip_file):
            os.remove(self.result_zip_file)

    def _compress_result_dir(self):
        with zipfile.ZipFile(self.result_zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.result_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arch_name = os.path.relpath(file_path, self.result_dir)
                    zipf.write(file_path, arch_name)

    def split(self):
        res = pdf_image(self.stand_file_path, self.result_dir, self.zoom_x, self.zoom_y, self.rotation_angle)
        logger.info(f"split result:{res}")
        if res != "true":
            return "split fail", ''
        self._compress_result_dir()
        return WORK_SPACE, self.result_zip_name




