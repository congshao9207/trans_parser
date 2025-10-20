# @Time : 3/3/22 5:17 PM 
# @Author : lixiaobo
# @File : trans_01_file_load_executor_test.py.py 
# @Software: PyCharm
from executors.builder import execute_common
from src.parser.impl.trans_01_file_load_executor import TransFileLoadExecutor
from src.parser.impl.trans_02_data_standardization import TransDataStandardization
from src.parser.impl.trans_03_rectify_executor import RectifyExecutor
from src.parser.impl.trans_04_title_match_executor import TitleMatchExecutor
from src.parser.impl.trans_05_time_standardization import TransTimeStandardization
from src.parser.impl.trans_06_amount_standardization import TransAmountStandardization
from src.parser.impl.trans_07_opponent_info_standardization import TransOpponentInfoStandardization
from src.parser.impl.trans_08_other_info_standardization import TransOtherInfoStandardization
from src.parser.impl.trans_09_verify_authenticity_executor import VerifyAuthenticityExecutor
from src.parser.impl.trans_10_raw_data_persistence import TransFlowRawData
from component.mtr.mtr_01_file_load_executor import MtrFileLoadExecutor
from component.mtr.mtr_02_data_standardization import MtrDataStandardization
from component.mtr.mtr_03_rectify_executor import MtrRectifyExecutor
from component.mtr.mtr_04_title_match_executor import MtrTitleMatchExecutor
from component.mtr.mtr_05_time_standardization import MtrTimeStandardization
from component.mtr.mtr_06_amount_standardization import MtrAmountStandardization
from component.mtr.mtr_07_other_info_standardization import MtrOtherInfoStandardization
from component.mtr.mtr_08_raw_data_persistence import MtrRawData


def test_trans_01():
    file_path = "../resource/农行流水.xlsx"
    executors = [TransFileLoadExecutor()]
    execute_common(file_path, executors)


def test_trans_02():
    file_path = "../resource/农行流水.xlsx"
    executors = [
        TransFileLoadExecutor(),
        TransDataStandardization()
    ]
    execute_common(file_path, executors)


def test_trans_03():
    file_path = "../resource/农行流水.xlsx"
    executors = [
        TransFileLoadExecutor(),
        TransDataStandardization(),
        TitleMatchExecutor()
    ]
    execute_common(file_path, executors)


def test_trans_04():
    file_path = "../resource/新建 Microsoft Excel 工作表.xlsx"
    executors = [
        TransFileLoadExecutor(),
        TransDataStandardization(),
        RectifyExecutor(),
        TitleMatchExecutor(),
        TransTimeStandardization(),
        TransAmountStandardization(),
        TransOpponentInfoStandardization(),
        TransOtherInfoStandardization(),
        VerifyAuthenticityExecutor(),
        TransFlowRawData()
    ]
    execute_common(file_path, executors)


def test_mtr_trans_mt_scan():
    # 美团扫码枪
    file_path = "../resource/mtr_file/美团管家_支付明细扫码枪.xlsx"
    executors = [
        MtrFileLoadExecutor(),
        MtrDataStandardization(),
        MtrRectifyExecutor(),
        MtrTitleMatchExecutor(),
        MtrTimeStandardization(),
        MtrAmountStandardization(),
        MtrOtherInfoStandardization(),
        MtrRawData()
    ]
    execute_common(file_path, executors)


def test_mtr_trans_mt_coupons():
    # 美团核销券
    file_path = "../resource/mtr_file/美团2024-10-07 核销券.xlsx"
    executors = [
        MtrFileLoadExecutor(),
        MtrDataStandardization(),
        MtrRectifyExecutor(),
        MtrTitleMatchExecutor(),
        MtrTimeStandardization(),
        MtrAmountStandardization(),
        MtrOtherInfoStandardization(),
        MtrRawData()
    ]
    execute_common(file_path, executors)


def test_mtr_trans_jh():
    # 聚合支付
    file_path = "../resource/mtr_file/聚合支付_营业情况明细_20241008152314.xlsx"
    executors = [
        MtrFileLoadExecutor(),
        MtrDataStandardization(),
        MtrRectifyExecutor(),
        MtrTitleMatchExecutor(),
        MtrTimeStandardization(),
        MtrAmountStandardization(),
        MtrOtherInfoStandardization(),
        MtrRawData()
    ]
    execute_common(file_path, executors)


def test_mtr_trans_xj():
    # 新疆收单
    file_path = "../resource/mtr_file/交易记录(新疆区联社收单）.xlsx"
    executors = [
        MtrFileLoadExecutor(),
        MtrDataStandardization(),
        MtrRectifyExecutor(),
        MtrTitleMatchExecutor(),
        MtrTimeStandardization(),
        MtrAmountStandardization(),
        MtrOtherInfoStandardization(),
        MtrRawData()
    ]
    execute_common(file_path, executors)


def test_mtr_trans_wfq():
    # 微风企
    file_path = "../resource/mtr_file/个体工商户-订单数据-（客如云&微风企）.xlsx"
    executors = [
        MtrFileLoadExecutor(),
        MtrDataStandardization(),
        MtrRectifyExecutor(),
        MtrTitleMatchExecutor(),
        MtrTimeStandardization(),
        MtrAmountStandardization(),
        MtrOtherInfoStandardization(),
        MtrRawData()
    ]
    execute_common(file_path, executors)
