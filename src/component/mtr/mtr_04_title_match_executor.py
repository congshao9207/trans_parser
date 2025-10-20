# !/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :mtr_04_title_match_executor.py.py
# @Time      :2024/12/19 14:11
# @Author    :chenwen

import re
import logging
from component.parse_context import COL_MAPPING
from config.db_config import sql_to_df
from parser.task_base_executor import TaskBaseExecutor

from logger.logger_util import LoggerUtil

logger = LoggerUtil().logger(__name__)

logging.basicConfig(level=logging.INFO)


class MtrTitleMatchExecutor(TaskBaseExecutor):
    def __init__(self):
        super().__init__()
        self.trans_flow_src_type = None
        # self.trans_flow_src_type = '05'
        self.pat_dict = {}
        self.col_mapping = {
            'time_col': [],
            'amt_col': [],
            'opname_col': [],
            'opacc_col': [],
            'opbank_col': [],
            'chn_col': [],
            'typ_col': [],
            'use_col': [],
            'mark_col': [],
            'status_col': [],
            'order_no_col': [],
            'shop_name_col': [],
            'shop_id_col': [],
            'order_source_col': [],
            'credit_card_col': [],
            'advance_col': [],
            'file_type_col': []
        }

    # 创建函数，查询mtr_type_logic表，拿到文件对应的列名配置参数
    def attach_context_(self):
        try:
            filter_content_sql = """
                select type_code,filter_content from mtr_type_logic where type_code like %(type_code)s
            """
            type_code = str(self.trans_flow_src_type).zfill(2) + '0%'
            fileter_content_df = sql_to_df(filter_content_sql, params={'type_code': type_code})
            if fileter_content_df.empty:
                logging.error("1.mtr_type_logic表未查询到数据，请初始化数据...")
                return

            # 设置匹配字典，形如 {'01001':'支付时间'}
            pat_dict = fileter_content_df.set_index('type_code')['filter_content'].to_dict()
            self.pat_dict.update(pat_dict)
        except Exception as e:
            logging.error(f"处理mtr_type_logic表报错: {e}")

    def execute(self):
        try:
            logger.info("收单流水进行标题标准化...")
            self.trans_flow_src_type = str(self.parse_context.parse_task.trans_flow_src_type)
            df = self.trans_data
            if df is None or df.empty:
                logging.warning("4.进行标题标准化时数据为空.")
                return
            # 拿枚举值，匹配列名
            self.attach_context_()
            if not self.pat_dict:
                logging.error("2.mtr_type_logic表未查询到数据，请初始化数据...")
                return
            # 预编译正则表达式
            patterns = {
                'time_col': self.pat_dict.get('0' + str(self.trans_flow_src_type) + '001'),
                'amt_col': self.pat_dict.get('0' + str(self.trans_flow_src_type) + '003'),
                'opname_col': self.pat_dict.get('0' + str(self.trans_flow_src_type) + '002'),
                'opacc_col': self.pat_dict.get('0' + str(self.trans_flow_src_type) + '004'),
                'opbank_col': self.pat_dict.get('0' + str(self.trans_flow_src_type) + '005'),
                'chn_col': self.pat_dict.get('0' + str(self.trans_flow_src_type) + '006'),
                'typ_col': self.pat_dict.get('0' + str(self.trans_flow_src_type) + '007'),
                'use_col': self.pat_dict.get('0' + str(self.trans_flow_src_type) + '008'),
                'mark_col': self.pat_dict.get('0' + str(self.trans_flow_src_type) + '009'),
                'status_col': self.pat_dict.get('0' + str(self.trans_flow_src_type) + '010'),
                'order_no_col': self.pat_dict.get('0' + str(self.trans_flow_src_type) + '011'),
                'shop_name_col': self.pat_dict.get('0' + str(self.trans_flow_src_type) + '012'),
                'shop_id_col': self.pat_dict.get('0' + str(self.trans_flow_src_type) + '013'),
                'order_source_col': self.pat_dict.get('0' + str(self.trans_flow_src_type) + '014'),
                'credit_card_col': self.pat_dict.get('0' + str(self.trans_flow_src_type) + '015'),
                'advance_col': self.pat_dict.get(str('0' + self.trans_flow_src_type) + '016'),
            }

            # 编译非空的正则表达式
            compiled_patterns = {key: re.compile(pattern) for key, pattern in patterns.items() if pattern}

            for col in df.columns:
                try:
                    # 保留必要的非字母数字字符
                    temp_col = re.sub(r'\s+', '', str(col))
                    matched = False

                    for key, pattern in compiled_patterns.items():
                        if pattern and pattern.search(temp_col):
                            self.col_mapping[key].append(col)
                            matched = True
                            break

                    if not matched:
                        logging.error(f"列'{col}'未匹配到.")
                except Exception as e:
                    logging.error(f"Error processing column '{col}': {e}")

            self.attach_context(COL_MAPPING, self.col_mapping)
        except Exception as e:
            logging.error(f"Error executing title match: {e}")
