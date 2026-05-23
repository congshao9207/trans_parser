import os
import uuid

from get_filename import get_filename

from config.res_code import ResCodeEnum
from config.trans_config import WORK_SPACE
from detection.checkBOC import checkBC
from detection.checkBOR import checkBOR
from detection.checkBank import checkBank
from detection.checkCIB import checkCIB
from detection.checkNullValue import checkNullValue
from detection.checkPHB import checkPHB
from logger.logger_util import LoggerUtil

logger = LoggerUtil().logger(__name__)


DETECTION_FUNS = {
        "BANK": checkBank,
        "BOC": checkBC,
        "CIB": checkCIB,
        "PHB": checkPHB,
        "NULLVALUE": checkNullValue,
        "BOR": checkBOR,
    }


class FileDetection(object):

    def __init__(self, file, engine_type):
        self.stand_file_path = ''
        self.file = file
        self.engine_type = engine_type

    def __enter__(self):
        is_local_file = type(self.file) == str
        if is_local_file:
            self.stand_file_path = self.file
        else:
            ext = get_filename(self.file.filename, "extension", -1)
            stand_file_name = 'detect_' + str(uuid.uuid1()) + "." + ext
            self.stand_file_path = WORK_SPACE + os.path.sep + stand_file_name
            self.file.save(self.stand_file_path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.stand_file_path:
            os.remove(self.stand_file_path)

    def detection(self):
        fun = DETECTION_FUNS.get(self.engine_type)
        if not fun:
            logger.error(f"detection function is not exists:{self.engine_type}")
            return ResCodeEnum.FAILED.value[0], f"detection function is not exists:{self.engine_type}", ''

        return ResCodeEnum.SUCCESS.value[0], "success", fun(self.stand_file_path)
