#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :mtr_06_amount_standardization.py.py
# @Time      :2024/12/19 14:13
# @Author    :chenwen


from config.trans_config import INCOME_PATTERN, OUTCOME_PATTERN
import re

from parser.task_base_executor import TaskBaseExecutor
from logger.logger_util import LoggerUtil

logger = LoggerUtil().logger(__name__)


class MtrAmountStandardization(TaskBaseExecutor):
    """
    将流水文件中交易金额标准化
    author:汪腾飞
    created_time:20200630
    updated_time_v1:20200911,搜索标签列时,要同时包含进账关键字和出账关键字,避免只有一类关键字;去除金额列不符合要求的字符的时候
        先删除空格,再删除负号结尾的字符
    updated_time_v2:20201223,将所有正则匹配格式都纳入配置文件
    updated_time_v3:20220420,新增智能删除及智能纠偏功能
    """

    def __init__(self):
        super().__init__()
        self.df = None
        self.amt_col = None
        self.tag = None
        self.typ_col = None

    def _trans_use(self):
        type_col = self.col_mapping()['use_col']
        if len(type_col):
            string = ''
            for col in type_col:
                string += "self.df['" + col + "'].fillna('').astype(str)+"
            string = string[:-1]
            self.df['trans_use'] = eval(string).apply(lambda x: re.sub(r'[\\\"\'\s^-]', '', x))
        else:
            self.df['trans_use'] = ''

    def _find_tag_col(self):
        """
        在金额列中寻找是否有标签列,如果存在标签列则新增一列'tag'将标签列对应的出账表示为-1,进账表示为1
        :return:
        """
        # length = len(self.amt_col)
        # 检查typ_col是否包含“消费|退款”字段

        if not self.typ_col:
            self.df['tag'] = 1
            return 0
        typ_col = self.typ_col[0]
        self.df['tag'] = self.df[typ_col].astype(str).str.contains('退款', na=False).map({True: -1, False: 1})
        return 1

    def _remove_amt_col(self):
        """
        去除金额列中不符合规范的列，仅保留非0值最多的一列或者两列
        :return:
        """
        length = len(self.amt_col)
        col_map = {}
        income_cnt, outcome_cnt, amt_cnt, tbd_cnt = 0, 0, 0, 0
        for index in range(-length, 0):
            col = self.amt_col[index]
            col1 = re.sub(r'[(（/]', ' ', col)
            col_list = col1.split(maxsplit=2)
            if len(col_list) == 2 and \
                    ((re.search(INCOME_PATTERN, col_list[0]) and re.search(OUTCOME_PATTERN, col_list[1])) or
                     (re.search(INCOME_PATTERN, col_list[1]) and re.search(OUTCOME_PATTERN, col_list[0]))):
                col1 = col_list[1]
            else:
                col1 = col
            # 将每个金额列数据类型都替换为字符串,先将字符串中的空格都替换为空,再将字符串中的非数字小数点负号替换为空,或者以负号结尾的数据替换为空
            self.df[col] = self.df[col].apply(self.value_trans)
            temp_cnt = self.df[self.df[col] != 0].shape[0]
            if re.search(INCOME_PATTERN, col1) and re.search(OUTCOME_PATTERN, col1):
                if temp_cnt - self.df.shape[0] * 0.5 > 0 and temp_cnt > amt_cnt:
                    col_map['amt_index'], amt_cnt = index, temp_cnt
                elif temp_cnt > tbd_cnt:
                    col_map['tbd_index'], tbd_cnt = index, temp_cnt
            elif re.search(INCOME_PATTERN, col1) and temp_cnt > income_cnt:
                col_map['income_index'], income_cnt = index, temp_cnt
            elif re.search(OUTCOME_PATTERN, col1) and temp_cnt > outcome_cnt:
                col_map['outcome_index'], outcome_cnt = index, temp_cnt
            elif temp_cnt > amt_cnt:
                col_map['amt_index'], amt_cnt = index, temp_cnt
        if 'amt_index' in col_map:
            self.amt_col = [self.amt_col[col_map['amt_index']]]
        elif 'income_index' in col_map and 'outcome_index' in col_map:
            self.amt_col = [self.amt_col[col_map['income_index']], self.amt_col[col_map['outcome_index']]]
        elif 'income_index' in col_map and 'outcome_index' not in col_map and 'tbd_index' in col_map:
            self.amt_col = [self.amt_col[col_map['income_index']], self.amt_col[col_map['tbd_index']]]
        elif 'income_index' not in col_map and 'outcome_index' in col_map and 'tbd_index' in col_map:
            self.amt_col = [self.amt_col[col_map['tbd_index']], self.amt_col[col_map['out_come_index']]]
        elif 'income_index' in col_map and 'outcome_index' not in col_map and income_cnt - self.df.shape[0] * 0.5 > 0:
            self.amt_col = [self.amt_col[col_map['income_index']]]
        elif 'income_index' not in col_map and 'outcome_index' in col_map and outcome_cnt - self.df.shape[0] * 0.5 > 0:
            self.amt_col = [self.amt_col[col_map['outcome_index']]]
        else:
            raise ValueError("缺失交易金额列或进账金额列或出账金额列")
        return

    def _one_col_match(self, col: str, col_name='trans_amt'):
        """
        将对应的金额列转化为标准浮点型数据
        :param col: 需要转化的列名
        :param col_name: 转化后的列名
        :return:
        """
        if not self.tag:
            self.df[col_name] = self.df.apply(lambda x: self.value_trans(x[col]), axis=1)
            return
        # if self.df[self.df['tag'] == -1][col].sum() < 0:
        #     self.df['tag'] = 1
        self.df[col_name] = self.df.apply(lambda x: self.value_trans(x[col]) * x['tag'], axis=1)
        self.df = self.df[self.df[col_name] != 0]
        return

    def _multi_col_match(self):
        """
        交易金额列存在多列时的处理
        :return:
        """
        for col in self.amt_col:
            self.df[col] = self.df[col].apply(self.value_trans)
        length = len(self.amt_col)
        if length == 1:
            if self.tag:
                if self.df.loc[self.df['tag'] == -1][self.amt_col[0]].sum() < 0:
                    self.df['trans_amt'] = self.df[self.amt_col[0]]
                else:
                    self.df['trans_amt'] = self.df['tag']*self.df[self.amt_col[0]]
            else:
                self.df['trans_amt'] = self.df[self.amt_col[0]]
        elif length == 2:
            if self.tag:
                self.df['trans_amt'] = self.df[self.amt_col[0]] + self.df[self.amt_col[1]]
                if self.df.loc[self.df['tag'] == -1]['trans_amt'].sum() >= 0:
                    self.df['trans_amt'] = self.df['tag'] * self.df['trans_amt']
            else:
                neg = self.df[self.amt_col[1]].sum()
                multi = 1 if neg < 0 else -1
                self.df['trans_amt'] = self.df[self.amt_col[0]] + multi * self.df[self.amt_col[1]]
        self.df = self.df[self.df['trans_amt'] != 0]
        return

    def execute(self):
        logger.info("收单流水金额标准化...")
        self.df = self.trans_data
        self._trans_use()  # 提前清洗交易用途列，提供给微信流水使用
        self.amt_col = self.col_mapping()['amt_col']
        self.typ_col = self.col_mapping()['typ_col']
        self.tag = self._find_tag_col()
        self._remove_amt_col()
        length = len(self.amt_col)
        try:
            if length == 1:
                self._one_col_match(self.amt_col[0])
            else:
                self._multi_col_match()
            self.trans_data = self.df
            if self.df.shape[0] == 0:
                self.mark_err("解析失败：未找到交易金额列")
            elif self.df[(self.df['trans_amt'] > 1e8) | (self.df['trans_amt'] < -1e8)].shape[0] > 0:
                self.mark_err("流水中出现超限交易金额，请联系管理员解决")
        except ValueError as e:
            self.mark_err("解析失败：" + str(e))
