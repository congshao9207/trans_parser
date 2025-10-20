# @Time : 2024-11-18
# @Author : lixiaobo
# @File : task_receiver.py
# @Software: PyCharm

from component.task_scheduler import TaskScheduler
from logger.logger_util import LoggerUtil
from component.mtr.mtr_01_file_load_executor import MtrFileLoadExecutor
from component.mtr.mtr_02_data_standardization import MtrDataStandardization
from component.mtr.mtr_03_rectify_executor import MtrRectifyExecutor
from component.mtr.mtr_04_title_match_executor import MtrTitleMatchExecutor
from component.mtr.mtr_05_time_standardization import MtrTimeStandardization
from component.mtr.mtr_06_amount_standardization import MtrAmountStandardization
from component.mtr.mtr_07_other_info_standardization import MtrOtherInfoStandardization
from component.mtr.mtr_08_raw_data_persistence import MtrRawData

logger = LoggerUtil().logger(__name__)


class MtrTaskScheduler(TaskScheduler):
    def __init__(self, task, session):
        super().__init__(task, session)

    def _init_task_executor(self):
        try:
            # 收单流水处理
            self.executors.append(MtrFileLoadExecutor())
            self.executors.append(MtrDataStandardization())
            self.executors.append(MtrRectifyExecutor())
            self.executors.append(MtrTitleMatchExecutor())
            self.executors.append(MtrTimeStandardization())
            self.executors.append(MtrAmountStandardization())
            self.executors.append(MtrOtherInfoStandardization())
            self.executors.append(MtrRawData())
            return True
        except Exception as e:
            logger.fatal("Init task executor exception %s", str(e))
            return False
