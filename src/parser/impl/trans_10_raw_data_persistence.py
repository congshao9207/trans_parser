import datetime
import json

from logger.logger_util import LoggerUtil
from model.model import transform_class_str, transform_flow_str
from parser.task_base_executor import TaskBaseExecutor
from config.db_config import sql_to_df
from config.trans_config import MONTH_LIMIT
import pandas as pd
import numpy as np
import re
from config.column_mapping import CONTENT_MAPPING

logger = LoggerUtil().logger(__name__)


class TransFlowRawData(TaskBaseExecutor):
    """
    将流水账户表和流水数据表落库
    updated_time_v1:20200707新增是否有新增数据字段,若有则有所有后续操作,若无,则无后续操作
    updated_time_v2:20200818添加commit的事务性,若发生错误则全部不提交
    updated_time_v3:20240621太阿系统增加文件画像，文件画像校验后再进行存储
    """

    def __init__(self):
        super().__init__()
        self.df = None
        self.param = {}
        self.raw_list = []
        self.create_time = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')

    def _mark_duplicate_data(self):
        sql = """select * from trans_flow where account_id in (select id from trans_account where account_name='%s' 
            and id_card_no='%s' and account_no='%s' and bank='%s' and create_time > date_sub(now(), interval %d month))
            and repeated = 0 order by id desc""" % \
              (self.param.get('cusName'), self.param.get('idNo'), self.param.get('bankAccount'),
               self.param.get('bankName'), MONTH_LIMIT)
        df = sql_to_df(sql)
        # 重复标签打上默认值
        data = self.trans_data
        data['repeated'] = 0
        if df.shape[0] == 0:
            return data
        df['trans_time'] = pd.to_datetime(df['trans_time'])
        df['trans_date'] = df['trans_time'].apply(lambda x: x.date())
        data['trans_date'] = data['trans_time'].apply(lambda x: x.date())
        full_date_list = df.groupby('account_id')['trans_date'].agg({'min', 'max'})[['min', 'max']].values.tolist()
        merge_date_list = self.interval_merge(full_date_list)
        not_full_date_list = []
        full_date_string = "data[(data['trans_date'] < pd.to_datetime('%s').date()) | " % \
                           format(merge_date_list[0][0], '%Y-%m-%d')
        for i in range(len(merge_date_list) - 1):
            not_full_date_list.extend(merge_date_list[i])
            temp_str = "((data['trans_date'] > pd.to_datetime('%s').date()) & " \
                       "(data['trans_date'] < pd.to_datetime('%s').date())) | " % \
                       (format(merge_date_list[i][1], '%Y-%m-%d'), format(merge_date_list[i + 1][0], '%Y-%m-%d'))
            full_date_string += temp_str
        full_date_string += "(data['trans_date'] > pd.to_datetime('%s').date())]" % \
                            format(merge_date_list[-1][-1], '%Y-%m-%d')
        not_full_date_list.extend(merge_date_list[-1])
        full_date_df = eval(full_date_string)
        not_full_date_df = data[data['trans_date'].isin(not_full_date_list)]
        if not_full_date_df.shape[0] == 0:
            return full_date_df
        not_full_date_df1 = df[df['trans_date'].isin(not_full_date_list)]
        for row in not_full_date_df.itertuples():
            trans_date = getattr(row, 'trans_date')
            trans_amt = getattr(row, 'trans_amt')
            account_balance = getattr(row, 'account_balance', None)
            opponent_name = getattr(row, 'opponent_name')
            exist_df = not_full_date_df1[(not_full_date_df1['trans_amt'] == trans_amt) &
                                         (not_full_date_df1['trans_date'] == trans_date) &
                                         (not_full_date_df1['opponent_name'] == opponent_name)]
            if self.parse_context.parse_task.trans_flow_src_type in [1, '1']:
                exist_df = exist_df[exist_df['account_balance'] == account_balance]
            if exist_df.shape[0] > 0:
                not_full_date_df.drop(getattr(row, 'Index'), inplace=True)
        full_date_df = pd.concat([full_date_df, not_full_date_df], axis=0, sort=False)
        data.loc[~data.index.isin(full_date_df.index.tolist()), 'repeated'] = 1
        return

    @staticmethod
    def interval_merge(intervals):
        if len(intervals) <= 1:
            return intervals
        intervals.sort()
        result = [intervals[0]]
        for x in intervals[1:]:
            if x[0] >= result[-1][-1]:
                result.append(x)
            else:
                result[-1][-1] = max(result[-1][-1], x[-1])
        return result

    @staticmethod
    def benford_ratio(df):
        expect_frequency = [0.301, 0.176, 0.125, 0.097, 0.079, 0.067, 0.058, 0.051, 0.046]
        first_num_list = [str(abs(_))[:1] for _ in df[abs(df.trans_amt) >= 1].trans_amt.tolist()]
        rate = 0
        for _ in range(1, 10):
            actual_frequency = first_num_list.count(str(_)) / len(first_num_list) if len(first_num_list) > 0 else 0
            if actual_frequency == 0:
                actual_frequency = 1e-6
            rate += (actual_frequency - expect_frequency[_ - 1]) * np.log(actual_frequency / expect_frequency[_ - 1])
        return (1 - rate) * 100

    def _trans_file_label(self):
        task_no = self.param['taskNo']
        self.df['trans_date'] = self.df['trans_time'].apply(lambda x: x.date())
        trans_cnt = self.df.shape[0]
        trans_days = self.df['trans_date'].nunique()
        income_cnt = self.df[self.df['trans_amt'] > 0].shape[0]
        file_dict = {
            'trans_cnt': trans_cnt, 'trans_days': trans_days, 'income_cnt': income_cnt,
            'trans_span': (self.df['trans_date'].max() - self.df['trans_date'].min()).days,
            'income_amt': self.df[self.df['trans_amt'] > 0]['trans_amt'].sum(),
            'expense_amt': self.df[self.df['trans_amt'] < 0]['trans_amt'].sum(),
            'trans_freq': trans_cnt / trans_days if trans_days > 0 else 0,
            'benford_coefficient': self.benford_ratio(self.df),
            'top3_opponent': ''.join([str(x)[0] if str(x) != '' else '' for x in
                                      self.df.groupby('opponent_name')['trans_amt'].agg({'count'}).
                                     sort_values(by='count', ascending=False).head(3).index.tolist()]),
            'top3_remark': ''.join([str(x)[0] if str(x) != '' else '' for x in
                                    self.df.groupby('remark')['trans_amt'].agg({'count'}).
                                   sort_values(by='count', ascending=False).head(3).index.tolist()])
        }
        file_label_sql = f"""select a.*, b.start_time, b.end_time from trans_file_label a 
            left join trans_account b on a.out_req_no = b.out_req_no where 
            a.task_no = '{task_no}' and
            a.trans_cnt > {int(trans_cnt * 0.9)} and a.trans_cnt < {int(trans_cnt * 1.1)} and 
            a.trans_days > {int(trans_days * 0.9)} and a.trans_days < {int(trans_days * 1.1)} and 
            a.income_cnt > {int(income_cnt * 0.9)} and a.income_cnt < {int(income_cnt * 1.1)}"""
        file_label_df = sql_to_df(file_label_sql)
        # 处理历史脏数据，把file_label_df中start_time和end_time为空的都去掉
        file_label_df = file_label_df[pd.notna(file_label_df['start_time']) & pd.notna(file_label_df['end_time'])]
        file_label_df['start_month'] = file_label_df['start_time'].apply(lambda x: format(pd.to_datetime(x), '%Y-%m'))
        file_label_df['end_month'] = file_label_df['end_time'].apply(lambda x: format(pd.to_datetime(x), '%Y-%m'))
        start_month = format(self.df['trans_time'].min(), '%Y-%m')
        end_month = format(self.df['trans_time'].max(), '%Y-%m')
        file_label_df = file_label_df[(file_label_df['start_month'] == start_month) &
                                      (file_label_df['end_month'] == end_month)]
        if file_label_df.shape[0] > 0:
            for row in file_label_df.itertuples():
                simi_cnt = 3
                for col in ['trans_span', 'income_amt', 'expense_amt', 'trans_freq', 'benford_coefficient']:
                    if abs(file_dict[col] * 0.9) <= abs(getattr(row, col)) <= abs(file_dict[col] * 1.1):
                        simi_cnt += 1
                for col in ['top3_opponent', 'top3_remark']:
                    if file_dict[col] == getattr(row, col):
                        simi_cnt += 1
                if simi_cnt >= 8:
                    account_id = getattr(row, 'account_id')
                    err_msg = f'文件重复上传，id={account_id}'
                    logger.error(err_msg)
                    self.mark_err(err_msg)
                    return
        return file_dict

    def _save_account_data(self):
        """
        将处理过后的流水数据的基本信息存入trans_account表,并将得到的account_id传入trans_flow表
        :return:
        """
        min_trans_time = self.df['trans_time'].min()
        max_trans_time = self.df['trans_time'].max()
        min_trans_time = datetime.datetime.strftime(min_trans_time, '%Y-%m-%d %H:%M:%S')
        max_trans_time = datetime.datetime.strftime(max_trans_time, '%Y-%m-%d %H:%M:%S')
        account_dict = dict()
        account_dict["out_req_no"] = self.parse_context.parse_task.out_req_no
        account_dict['account_name'] = self.param.get('cusName')
        account_dict['id_card_no'] = self.param.get('idNo')
        account_dict['id_type'] = self.param.get('idType')
        account_dict['bank'] = self.param.get('bankName')
        account_dict['account_no'] = self.param.get('bankAccount')
        account_dict['start_time'] = min_trans_time
        account_dict['end_time'] = max_trans_time
        account_dict['trans_flow_type'] = 1 if self.param.get('cusType') == 'PERSONAL' else 2
        account_dict['trans_flow_src_type'] = self.parse_context.parse_task.trans_flow_src_type
        account_dict['file_id'] = self.param.get('fileId', None)
        account_dict['update_time'] = self.create_time
        account_dict['create_time'] = self.create_time
        account_dict['account_state'] = 1
        account_dict['task_no'] = self.param.get('taskNo')
        trans_account = transform_class_str(account_dict, 'TransAccount')
        # self.raw_list.append(trans_account)
        self.session.add(trans_account)
        self.session.commit()
        return trans_account.id

    @staticmethod
    def replace_in_char(df, column_name, mapping):
        # 正则匹配
        pattern = re.compile('|'.join(map(re.escape, [item for sublist in mapping.values() for item in sublist])))
        replacement = {old: new for new, olds in mapping.items() for old in olds}

        # 使用正则表达式进行替换
        def replace_function(x):
            if pd.isna(x) or x == '':
                return x
            return pattern.sub(lambda m: replacement[m.group(0)], x)

        df[column_name] = df[column_name].apply(replace_function)
        return df

    def execute(self):
        self.df = self.trans_data
        parse_task = self.parse_context.parse_task
        self.param = json.loads(parse_task.req_raw_data)

        file_label = self._trans_file_label()
        if file_label is None:
            return

        account_id = self._save_account_data()
        self.parse_context.account_id = account_id

        # 原始数据列名
        col_list = ['trans_time', 'opponent_name', 'trans_amt', 'account_balance', 'currency',
                    'opponent_account_no', 'opponent_account_bank', 'trans_channel', 'trans_type',
                    'trans_use', 'remark', 'verif_label']
        varchar64_list = ['opponent_account_no', 'opponent_account_bank', 'trans_channel', 'trans_type']
        # 新增对内容特殊字符的兼容
        char_col_list = ['opponent_name', 'opponent_account_bank', 'trans_channel', 'trans_type', 'trans_use', 'remark']
        for col in char_col_list:
            self.df = self.replace_in_char(self.df, col, CONTENT_MAPPING)
        for row in self.df.itertuples():
            flow_dict = dict()
            flow_dict['account_id'] = account_id
            flow_dict['out_req_no'] = self.parse_context.parse_task.out_req_no
            # flow_dict['file_id'] = self.param.get('fileId', None)
            for col in col_list:
                flow_dict[col] = getattr(row, col, None)
                if col in varchar64_list and pd.notna(flow_dict[col]):
                    flow_dict[col] = str(flow_dict[col])[:64]
            flow_dict['create_time'] = self.create_time
            flow_dict['update_time'] = self.create_time
            # 将原始数据落库
            self.raw_list.append(flow_dict)
        logger.info("save_raw_data begin")
        e = transform_flow_str(self.session, self.raw_list, 'TransFlow')
        logger.info("save_raw_data end")

        file_label['account_id'] = account_id
        file_label['out_req_no'] = self.parse_context.parse_task.out_req_no
        file_label['task_no'] = self.param['taskNo']
        file_label['create_time'] = self.create_time
        # 存储文件画像数据
        logger.info("save_file_label_data begin")
        trans_file_label = transform_class_str(file_label, 'TransFileLabel')
        self.session.add(trans_file_label)
        self.session.commit()
        logger.info("save_file_label_data end")

        if e is not None:
            err_msg = '导入数据库失败,失败原因:%s' % str(e)
            logger.error(err_msg)
            self.mark_err('导入数据库失败')
