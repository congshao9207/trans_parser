# !/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :mtr_01_file_load_executor.py
# @Time      :2024/12/19 9:32
# @Author    :chenwen

import re
import pandas as pd
from config.trans_config import MTR_TRANS_FLOW_SRC_TYPES, MTR_TRANS_TIME_ENUM, MTR_TRANS_AMT_ENUM, MAX_TITLE_NUMBER
from parser.task_base_executor import TaskBaseExecutor
from logger.logger_util import LoggerUtil

logger = LoggerUtil().logger(__name__)


class MtrFileLoadExecutor(TaskBaseExecutor):
    """
    xlsx类型收单流水文件，在此处进行解析
    """

    def __init__(self):
        super().__init__()
        self.sheet_name = None
        self.title = None
        self.trans_flow_src_type = None
        # self.trans_flow_src_type = '09'
        self.file_content = None  # 缓存文件内容

    def execute(self):
        logger.info("加载收单流水...")
        self.trans_flow_src_type = self.parse_context.parse_task.trans_flow_src_type
        if self.trans_flow_src_type not in [int(i) for i in MTR_TRANS_FLOW_SRC_TYPES.keys()]:
            raise ValueError("非收单流水文件，请检查文件类型！")
        self.sheet_name, self.title = self._find_title()
        if not self.sheet_name or self.title is None:
            self.mark_err('文件读取异常' if not self.sheet_name else '上传失败,无法找到标题行,收单流水文件内容有误')
            return
        self.trans_data = self._convert_to_data_frame()
        self.trans_data.rename(columns=lambda x: re.sub(r'[\\/\"\'\s]', '', str(x)), inplace=True)

    def _read_file(self):
        if self.file_content is None:
            try:
                with open(self.file_path, 'rb') as file:
                    self.file_content = file.read()
            except FileNotFoundError:
                logger.error(f"文件未找到: {self.file_path}")
                self.mark_err('文件未找到')
                raise
            except Exception as e:
                logger.error(f"读取文件失败: {str(e)}")
                self.mark_err('文件读取失败')
                raise
        return self.file_content

    def _find_title(self):
        """
        从文件中的所有sheet中寻找存在流水标题行的文件，如果存在则跳出循环
        :return:
        """
        content = self._read_file()
        try:
            title_df = pd.read_excel(content, nrows=MAX_TITLE_NUMBER, header=None, sheet_name=None, engine='openpyxl')
            index_list = title_df.keys()
        except Exception as e:
            logger.info("----1、以标准xlsx读取文件失败:%s----" % str(e))
            try:
                title_df = pd.read_html(content, skiprows=range(MAX_TITLE_NUMBER, 100000), header=None)
                self.read_type = 'html'
                index_list = range(len(title_df))
            except Exception as e:
                logger.info("----2、以html格式读取文件失败:%s----" % str(e))
                return None, None

        if not title_df:
            logger.error("DataFrame为空")
            return None, None

        pattern = re.compile(r'\s')
        # 遍历所有sheet
        for k in index_list:
            v = title_df[k]
            if v.empty:
                continue
            max_len = 0  # 最大列
            title = -1  # 标题行号
            cnt = 0  # 遍历行数计数
            for row in v.itertuples():
                # 过滤掉列名包含 'Unnamed' 的列
                filtered_row = [x for i, x in enumerate(row) if pd.notna(x)]
                temp = [pattern.sub('', str(x)) for x in filtered_row if pattern.sub('', str(x)) != '']
                temp_len = len(temp)
                if temp_len > max_len:
                    title = cnt
                    max_len = temp_len
                cnt += 1
            if title != -1:
                return k, title
        return '', None

    def _convert_to_data_frame(self):
        df = None
        try:
            df = pd.read_excel(self.file_content, header=self.title, dtype=str, sheet_name=self.sheet_name, engine='openpyxl')
        except Exception as e:
            logger.info("----3、读取失败, 将进行重试原因:%s----" % str(e))
            try:
                html_tables = pd.read_html(self.file_content, header=self.title)
                if isinstance(html_tables, list) and len(html_tables) > self.sheet_name:
                    df = html_tables[self.sheet_name]
                else:
                    logger.error("HTML表格解析失败或索引超出范围")
                    self.mark_err('文件读取异常-2')
            except Exception as e2:
                logger.info("----读取失败原因r3:%s----" % str(e2))
                self.mark_err('文件读取异常-2')
        return df
