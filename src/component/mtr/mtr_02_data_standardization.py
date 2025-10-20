# !/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :mtr_02_data_standardization.py.py
# @Time      :2024/12/19 11:49
# @Author    :chenwen
import re
from parser.task_base_executor import TaskBaseExecutor
from config.trans_config import DTTIME_PATTERN, DATE_PATTERN, SHORT_DATE_PATTERN, AMT_PATTERN, IGNORE_PATTERN, OUTCOME_PATTERN, INCOME_PATTERN, \
    MTR_TRANS_FLOW_SRC_TYPES
from logger.logger_util import LoggerUtil

logger = LoggerUtil().logger(__name__)


class MtrDataStandardization(TaskBaseExecutor):
    """
    流水数据标准化
        将收单流水数据中与标题行相同的数据删除,将流水数据中头部和尾部不符合规范的数据删除
        1.现在会将整行只有<=3个非空单元格的行删除，而不是整行为空的才删除，这样可以直接删除掉存在统计信息的行，同时也可以将多行标题的第二行删除
        2.现在会正确删除掉所有与标题行完全一致的行，不会再造成有标题行没有删掉而存在时间列存在空值的情况
    """

    def __init__(self):
        super().__init__()
        self.title_status = False

    def _title_standard(self):
        """
        若标题行存在两行,将标题行规范化,并将标题状态替换为True,表示标题行发生过替换
        :return:
        """
        df = self.trans_data.copy()
        col_list = list(df.columns)
        try:
            for col_index in range(len(col_list)):
                if '发生额' == col_list[col_index] or '发生额元' == col_list[col_index]:
                    c1 = str(df.iloc[0, col_index]).strip()
                    c2 = str(df.iloc[0, col_index + 1]).strip()
                    if (re.search(OUTCOME_PATTERN, c1) and re.search(INCOME_PATTERN, c2)) or \
                            (re.search(OUTCOME_PATTERN, c2) and re.search(INCOME_PATTERN, c1)):
                        df.rename(columns={col_list[col_index]: c1, col_list[col_index + 1]: c2}, inplace=True)
                        self.title_status = True
                        df.drop(0, axis=0, inplace=True)
                        break
            df.dropna(axis=0, inplace=True, thresh=3)

            # 若存在交易序号列或序号列，先根据交易序号进行排序
            if '交易序号' in col_list or '序号' in col_list:
                num_col = '交易序号' if '交易序号' in col_list else '序号'
                df['交易序号'] = df[num_col].apply(lambda x: int(str(x).strip()) if str(x).strip().isnumeric() else None)
                df['交易序号'].fillna(method='ffill', inplace=True)
                df.sort_values(by='交易序号', ascending=True, inplace=True)
                df.reset_index(drop=True, inplace=True)
        except Exception as e:
            logger.error(f"Error in _title_standard: {e}")

        self.trans_data = df

    def _remove_invalid_rows(self):
        """
        删除不合规的行,包括与标题行完全一致的行以及头部和尾部不符合规范的数据
        :return:
        """
        df = self.trans_data.copy()
        try:
            # 删除与标题行完全一致的行
            title_row = df.columns.tolist()
            df = df[~df.apply(lambda row: row.tolist() == title_row, axis=1)]

            # 删除头部和尾部不符合规范的数据
            df.dropna(axis=0, inplace=True, thresh=3)
            df = df[df.apply(self._entire_row_values_match, axis=1)]
        except Exception as e:
            logger.error(f"Error in _remove_invalid_rows: {e}")

        self.trans_data = df

    @staticmethod
    def _entire_row_values_match(value):
        """
        检查整行值是否匹配特定模式
        :param value: 行值
        :return: 布尔值,表示是否匹配
        """
        dttime_pat = re.compile(DTTIME_PATTERN)
        date_pat = re.compile(DATE_PATTERN)
        short_pat = re.compile(SHORT_DATE_PATTERN)
        amt_pat = re.compile(AMT_PATTERN)
        sum_pat = re.compile(IGNORE_PATTERN)
        # 时间格式计数,累计到1停止,即至少需要包含一列交易时间
        time_cnt = 0
        # 金额格式计数,累计到1停止,即至少需要包含一列交易金额，此处收单流水和普通银行流水不同，无需考虑余额情况
        amt_cnt = 0

        # 遍历给定的值列表，寻找符合特定模式的时间和金额信息
        for val in value:
            temp = str(val)
            # 将该单元格值转换成字符串,取其中是数字的字符连接起来
            string = ''.join([_ for _ in temp if _.isdigit()])
            # 若原始单元格值中包含忽略格式中的字符,则该列不符合要求,返回False
            if re.match(sum_pat, temp):
                return False
            # 若时间格式单元格个数不到1,则需要判断该单元格是否是时间格式,判断通过则直接进行下一个单元格的判断(防止某单元格同时满足时间和金额)
            if time_cnt != 1:
                if re.match(dttime_pat, string) or re.match(date_pat, string) or re.match(short_pat, string):
                    time_cnt += 1
                    continue
            # 若金额格式单元格个数不到2,则需要判断该单元格是否是金额格式
            if amt_cnt != 1:
                if re.match(amt_pat, string):
                    amt_cnt += 1
            # 若已经找到一个时间格式,两个金额格式则返回True
            if time_cnt == 1 and amt_cnt == 1:
                return True
        # 遍历完都没有找到不少于一个的时间格式,和不少于一个的金额格式则返回False
        if time_cnt == 1 and amt_cnt == 1:
            return True
        return False

    def execute(self):
        """
        执行数据标准化操作
        :return:
        """
        try:
            logger.info("收单流水数据标准化...")
            # self._title_standard()
            if self.parse_context.parse_task.trans_flow_src_type in [int(i) for i in MTR_TRANS_FLOW_SRC_TYPES.keys()]:
                self._remove_invalid_rows()
        except Exception as e:
            logger.error(f"Error in execute: {e}")
