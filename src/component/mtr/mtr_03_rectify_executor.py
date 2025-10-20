# !/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :mtr_03_rectify_executor.py.py
# @Time      :2024/12/19 14:11
# @Author    :chenwen

from config.column_mapping import TITLE_RECTIFY, CHAR_MAPPING
from parser.task_base_executor import TaskBaseExecutor
import pandas as pd
import re
from logger.logger_util import LoggerUtil

logger = LoggerUtil().logger(__name__)


class MtrRectifyExecutor(TaskBaseExecutor):
    """
        标题行中部分识错表头根据枚举值来修正
        对手账户中非数字用*替代去除
    """

    def __init__(self):
        super().__init__()

    def _rectify_title(self):
        if self.trans_data is None or self.trans_data.empty:
            return
        df = self.trans_data.copy(deep=True)
        rename_dict = {}

        for title in df.columns:
            new_title = title

            # 根据 TITLE_RECTIFY 进行重命名
            for k, v in TITLE_RECTIFY.items():
                if title in v and k not in df.columns:
                    new_title = k
                    break
            # 根据 CHAR_MAPPING 替换字符
            for k, v_list in CHAR_MAPPING.items():
                for v in v_list:
                    new_title = new_title.replace(v, k)
            # 只在新旧标题不同的情况下添加到 rename_dict
            if new_title != title:
                rename_dict[title] = new_title
        # 一次性进行重命名
        if rename_dict:
            df.rename(columns=rename_dict, inplace=True)
        self.trans_data = df

    def _rectify_op_acc(self):
        try:
            if '对方账户' not in self.trans_data.columns:
                return

            df = self.trans_data.copy()
            df['对方账户'] = df['对方账户'].astype(str).replace('nan', None).apply(
                lambda x: re.sub(self.pattern, '*', x) if pd.notna(x) else None
            )
            self.trans_data = df
        except Exception as e:
            print(f"Error in rectifying opponent account: {e}")

    def execute(self):
        try:
            logger.info("收单流水枚举值修正...")
            self._rectify_title()
            if '对方账户' in self.trans_data.columns and \
                    str(self.parse_context.parse_task.trans_flow_src_type) in ['2', '3']:
                self._rectify_op_acc()
        except Exception as e:
            print(f"Error in execution: {e}")
