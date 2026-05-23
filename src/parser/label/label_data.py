import datetime
import json
import re

import pandas as pd
from pandas.tseries import offsets
from flask_sqlalchemy_session import current_session

from config.db_config import sql_to_df
from config.process_status import ProcessStatusEnum
from config.res_code import ResCodeEnum
from entity.resp_entity import RespEntity
from logger.logger_util import LoggerUtil
from model.model import transform_flow_str, transform_update_str, TransParseTask
from config.label_config import *

logger = LoggerUtil().logger(__name__)


class LabelData(object):

    def __init__(self, app_id, param):
        self.app_id = app_id
        self.param = json.loads(param)
        self.out_req_no = self.param.get("outReqNo")
        self.cus_type = self.param.get('cusType')
        self.create_time = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
        self.reclean_id = []
        self.delete_id = []

        self.resp = None
        self.logger = LoggerUtil().logger(__name__)

        self.parse_context = {}

    def pre_check(self) -> bool:
        res_msg = ""
        if self.app_id is None:
            res_msg = "app_id is required"
        elif self.param is None:
            res_msg = "param is required"

        res_code = 0 if res_msg == '' else ResCodeEnum.PARAM_ERROR.value[0]

        if res_code != 0:
            self.resp = RespEntity.response(res_code, res_msg)
            return False

        return self._init_trans_task(self.out_req_no)

    def _init_trans_task(self, out_req_no):
        task = current_session.query(TransParseTask).filter(TransParseTask.out_req_no == out_req_no).first()
        if not task:
            self.logger.info("outReqNo is exists:" + out_req_no)
            self.resp = RespEntity.response(ResCodeEnum.PARAM_ERROR.value[0], "outReqNo is exists:" + out_req_no)
            return False
        self.parse_context["parse_task"] = task
        task.label_process_status = ProcessStatusEnum.PROCESSING.name
        current_session.add(task)
        current_session.commit()
        return True

    def get_last_resp(self):
        if not self.resp:
            self.resp = RespEntity.response(0, "SUCCEED")
        return self.resp

    def tear_down(self, have_exception):
        task = self.parse_context.get('parse_task')
        if not task:
            return

        if have_exception:
            task.label_process_status = ProcessStatusEnum.FAILED.name
        else:
            task.label_process_status = ProcessStatusEnum.DONE.name
        current_session.add(task)
        current_session.commit()

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

    def _drop_duplicate_data(self, data=None):
        # sql = """select * from trans_report_flow where out_req_no in
        #     (select out_req_no from trans_account where account_name='%s' and id_card_no='%s' and
        #     account_no='%s' and bank='%s' and task_no = '%s' order by id desc)""" % \
        #       (self.param.get('cusName'), self.param.get('idNo'), self.param.get('bankAccount'),
        #        self.param.get('bankName'), self.param.get('taskNo'))
        # df = sql_to_df(sql)
        params = {
            'cusName': self.param.get('cusName'),
            'idNo': self.param.get('idNo'),
            'bankAccount': self.param.get('bankAccount'),
            'bankName': self.param.get('bankName'),
            'taskNo': self.param.get('taskNo')
        }

        # 优化后的 SQL（仅查询 out_req_no，去掉无意义的 ORDER BY）
        sql = """
            SELECT trf.*
            FROM trans_report_flow trf
            INNER JOIN trans_account ta 
                ON trf.out_req_no = ta.out_req_no
            WHERE ta.account_name = %(cusName)s
              AND ta.id_card_no = %(idNo)s
              AND ta.account_no = %(bankAccount)s
              AND ta.bank = %(bankName)s
              AND ta.task_no = %(taskNo)s
        """

        # 执行查询（假设 sql_to_df 支持 params 参数）
        df = sql_to_df(sql, params=params)
        if df.shape[0] == 0:
            return
        df['trans_time'] = pd.to_datetime(df['trans_time'])
        df['trans_date'] = df['trans_time'].apply(lambda x: x.date())
        data['trans_date'] = data['trans_time'].apply(lambda x: x.date())
        full_date_list = df.groupby('out_req_no')['trans_date'].agg({'min', 'max'})[['min', 'max']].values.tolist()
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
            if self.parse_context.get('parse_task').trans_flow_src_type in [1, '1']:
                exist_df = exist_df[exist_df['account_balance'] == account_balance]
            if exist_df.shape[0] > 0:
                not_full_date_df.drop(getattr(row, 'Index'), inplace=True)
        full_date_df = pd.concat([full_date_df, not_full_date_df], axis=0, sort=False)
        index_list = data.loc[~data.index.isin(full_date_df.index.tolist())].index.tolist()
        data.drop(index_list, axis=0, inplace=True)

    def _update_trans_report(self, update_df):
        params = {
            'cusName': self.param.get('cusName'),
            'idNo': self.param.get('idNo'),
            'bankAccount': self.param.get('bankAccount'),
            'bankName': self.param.get('bankName'),
            'taskNo': self.param.get('taskNo')
        }
        sql = """
            SELECT trf.*
            FROM trans_report_flow trf
            INNER JOIN trans_account ta 
                ON trf.out_req_no = ta.out_req_no
            WHERE ta.account_name = %(cusName)s
              AND ta.id_card_no = %(idNo)s
              AND ta.account_no = %(bankAccount)s
              AND ta.bank = %(bankName)s
              AND ta.task_no = %(taskNo)s
        """

        # 执行查询（假设 sql_to_df 支持 params 参数）
        rep_df = sql_to_df(sql, params=params)
        # sql = """select * from trans_report_flow where out_req_no in
        #     (select out_req_no from trans_account where account_name='%s' and id_card_no='%s' and
        #     account_no='%s' and bank='%s' and task_no = '%s' order by id desc)""" % \
        #       (self.param.get('cusName'), self.param.get('idNo'), self.param.get('bankAccount'),
        #        self.param.get('bankName'), self.param.get('taskNo'))
        # rep_df = sql_to_df(sql)
        if rep_df.shape[0] == 0:
            return
        update_df['trans_date'] = update_df['trans_time'].apply(lambda x: x.date())
        rep_df['trans_date'] = rep_df['trans_time'].apply(lambda x: x.date())
        label_df = pd.DataFrame(columns=rep_df.columns)
        for row in update_df.itertuples():
            mut_label = getattr(row, 'mutual_exclusion_label')
            com_label = getattr(row, 'compatibility_label')
            flow_id = getattr(row, 'flow_id')
            exist_df = rep_df[rep_df['flow_id'] == flow_id]
            if exist_df.shape[0] > 0:
                exist_df['mutual_exclusion_label'] = mut_label
                exist_df['compatibility_label'] = com_label
                label_df = pd.concat([label_df, exist_df])
                continue
            trans_date = getattr(row, 'trans_date')
            trans_amt = getattr(row, 'trans_amt')
            account_balance = getattr(row, 'account_balance', None)
            opponent_name = getattr(row, 'opponent_name')
            exist_df = rep_df[(rep_df['trans_amt'] == trans_amt) &
                              (rep_df['trans_date'] == trans_date) &
                              (rep_df['opponent_name'] == opponent_name)]
            if self.parse_context.get('parse_task').trans_flow_src_type in [1, '1']:
                exist_df = exist_df[exist_df['account_balance'] == account_balance]
            if exist_df.shape[0] > 0:
                exist_df['mutual_exclusion_label'] = mut_label
                exist_df['compatibility_label'] = com_label
                label_df = pd.concat([label_df, exist_df])
        return label_df

    def _relationship_mid_var(self, df):
        relation_list = self.param.get('relations')
        df['relationship'] = ''
        if relation_list is None:
            return
        relation_mapping = {
            "PER": "关联个人",
            "ENT": "关联企业",
            "GUAR_PER": "担保个人",
            "GUAR_ENT": "担保企业",
            "MAIN": "主体",
            "SPOUSE": "配偶"
        }
        relation_dict = {}
        for rela in relation_list:
            cus_name = rela.get('cusName')
            rela_type = relation_mapping.get(rela.get('relationType'))
            if cus_name not in relation_dict:
                relation_dict[cus_name] = rela_type
        for k, v in relation_dict.items():
            df.loc[df['opponent_name'].astype(str).str.contains(k), 'relationship'] = v

    # 清洗中间变量
    def _mid_variable_cleaning(self, df):
        df['concat_str'] = df['opponent_name'] + ';' + df['trans_channel'] + ';' + \
            df['trans_type'] + ';' + df['trans_use'] + ';' + df['remark']
        df['if_thousands'] = df['trans_amt'].apply(lambda x: 1 if x % 10000 == 0 else 0)
        self._loan_mid_var(df)
        self._relationship_mid_var(df)
        self._usual_trans_type(df)
        df.drop(columns=['month', 'day'], inplace=True)
        var_sql = """select * from label_variable where variable_type = 'UNION'"""
        var_df = sql_to_df(var_sql)
        # 将所有组合变量清洗出来
        for row in var_df.itertuples():
            var_name = getattr(row, 'variable_code')
            var_cont = getattr(row, 'filter_content')
            try:
                # 执行清洗逻辑，在df上新增一列
                exec(f"df.loc[{var_cont}, '{var_name}'] = 1")
            except Exception as e:
                logger.error(f"组合变量{var_name}清洗发生错误：{e}")
                # 若清洗发生错误，同样需要新增一列，否则会报keyerror
                df[var_name] = 0

    def _loan_mid_var(self, df):
        df['loan_mid_var'] = 0
        df['month'] = df['trans_time'].apply(lambda x: x.month)
        df['day'] = df['trans_time'].apply(lambda x: x.day)
        df.loc[(df['trans_amt'].apply(lambda x: abs(x)) > 500) &
               (~df['concat_str'].str.contains(str(self.param.get('cusName')))) &
               ((((df['concat_str'].str.contains(PRIVATE_LENDING)) |
                  ((df['concat_str'].str.contains(PRIVATE_LENDING_COMPATIBLE)) &
                   (df['opponent_name'] != ''))) &
                 (~df['concat_str'].str.contains(PRIVATE_LENDING_EXCEPT_1))) |
                ((df['trans_amt'] < 0) & (df['concat_str'].str.contains(PRIVATE_LENDING_INTEREST)) &
                 (~df['concat_str'].str.contains(PRIVATE_LENDING_INTEREST_EXCEPT)))) &
               (~df['opponent_name'].str.contains(PRIVATE_LENDING_OPPONENT_NAME)) &
               (df['opponent_name'] != ''), 'loan_mid_var'] = 1
        amt_group = df[
            (df['trans_amt'].apply(lambda x: abs(x)) > MIN_PRIVATE_LENDING) &
            (~df['concat_str'].str.contains(str(self.param.get('cusName')))) &
            (pd.notnull(df['opponent_type'])) &
            (~df['concat_str'].str.contains(PRIVATE_LENDING_EXCEPT_2)) &
            (df['opponent_name'] != '') &
            (~df['opponent_name'].str.contains(PRIVATE_LENDING_OPPONENT_NAME))
            ].groupby(['opponent_name', 'trans_amt'], as_index=False).agg({'month': len})
        amt_group = amt_group[amt_group['month'] >= MIN_CONTI_MONTHS]
        if amt_group.shape[0] > 0:
            for row in amt_group.itertuples():
                temp_name = getattr(row, 'opponent_name')
                temp_amt = getattr(row, 'trans_amt')
                temp_df = df[(df['opponent_name'] == temp_name) &
                             (df['trans_amt'] == temp_amt)]
                temp_df.reset_index(drop=False, inplace=True)
                last_month = temp_df['trans_time'].tolist()[0]
                temp_df.loc[0, 'conti'] = 1
                conti_list = set()
                temp_cnt = 1
                now_index = 1
                for index in temp_df.index.tolist()[1:]:
                    this_month = temp_df.loc[index, 'trans_time']
                    temp_interval = (this_month.year - last_month.year) * 12 + this_month.month - last_month.month
                    if temp_interval <= 1:
                        temp_df.loc[index, 'conti'] = now_index
                        if temp_interval == 1:
                            temp_cnt += 1
                            if temp_cnt >= MIN_CONTI_MONTHS:
                                conti_list.add(now_index)
                    else:
                        now_index += 1
                        temp_df.loc[index, 'conti'] = now_index
                        temp_cnt = 1
                    last_month = this_month
                conti_list = list(conti_list)
                if len(conti_list) == 0:
                    continue
                for i in conti_list:
                    conti_df = temp_df[temp_df['conti'] == i]
                    max_interval = conti_df['day'].max() - conti_df['day'].min()
                    if max_interval <= MAX_INTERVAL_DAYS:
                        df.loc[conti_df['index'].tolist(), 'loan_mid_var'] = 1

    @staticmethod
    def _usual_trans_type(df):
        df['date'] = df['trans_time'].apply(lambda x: datetime.datetime.strftime(x, '%Y-%m-%d'))
        no_oppo_list = ['trans_channel', 'trans_type', 'trans_use', 'remark']
        df[no_oppo_list] = df[no_oppo_list].fillna('').astype(str)
        # 将字符串列合并到一起
        df['no_oppo_str'] = df['trans_channel'] + ';' + df['trans_type'] + ';' + \
            df['trans_use'] + ';' + df['remark']

        # 其他画像之是否整进整出标签
        big_in_out_df = df[(df.trans_amt.apply(lambda x: abs(x)) >= 100000) &
                           (df.trans_amt.apply(lambda x: x % 10000) == 0) &
                           (~df.concat_str.str.contains(BIG_IN_OUT_EXCEPT)) &
                           (df.relationship != '主体')]
        big_in_date = big_in_out_df[big_in_out_df.trans_amt > 0]['date'].tolist()
        big_out_date = big_in_out_df[big_in_out_df.trans_amt < 0]['date'].tolist()
        big_in_out_date = list(set(big_in_date).intersection(set(big_out_date)))
        big_in_out_list = big_in_out_df[big_in_out_df.date.isin(big_in_out_date)].index.tolist()
        df.loc[big_in_out_list, 'big_in_out_var'] = 1

        # 其他画像之快进快出标签
        fast_in_out_df = df[(df.trans_amt.apply(lambda x: abs(x)) >= 200000) &
                            (df.opponent_name != '') &
                            (~df.opponent_name.str.contains(FAST_IN_OUT_OPPONENT_NAME_EXCEPT)) &
                            (~df.concat_str.str.contains(FAST_IN_OUT_EXCEPT)) &
                            (df.relationship != '主体')]
        fast_in_date = fast_in_out_df[fast_in_out_df.trans_amt > 0]['date'].tolist()
        fast_out_date = fast_in_out_df[fast_in_out_df.trans_amt < 0]['date'].tolist()
        fast_in_out_date = list(set(fast_in_date).intersection(set(fast_out_date)))
        fast_in_out_list = fast_in_out_df[fast_in_out_df.date.isin(fast_in_out_date)].index.tolist()
        df.loc[fast_in_out_list, 'fast_in_out_var'] = 1

        # 其他画像之同进同出标签
        op_name_list = df[(pd.notna(df['opponent_type'])) &
                          ((pd.isna(df['relationship'])) | (df['relationship'] == ''))].opponent_name.unique().tolist()
        temp_ind_list = []
        for op_name in op_name_list:
            temp_df = df[df['opponent_name'] == op_name][['trans_time', 'trans_amt']]
            temp_df['income'] = temp_df['trans_amt'].apply(lambda x: x if x > 0 else 0)
            temp_df['income_cnt'] = temp_df['trans_amt'].apply(lambda x: 1 if x > 0 else 0)
            temp_df['expense'] = temp_df['trans_amt'].apply(lambda x: x if x < 0 else 0)
            temp_df['expense_cnt'] = temp_df['trans_amt'].apply(lambda x: 1 if x < 0 else 0)
            temp_df.sort_values(by=['trans_time'], ascending=True, inplace=True)
            temp_df = temp_df.rolling('3D', closed='both', on='trans_time').sum()
            key_time = temp_df[((temp_df['income_cnt'] > 4) & (temp_df['expense_cnt'] > 4)) |
                               ((temp_df['income'] >= 1e5) & (temp_df['expense'] <= -1e5))]['trans_time'].tolist()
            for k_t in key_time:
                temp_ind_list += temp_df.loc[(temp_df['trans_time'] >= k_t - offsets.DateOffset(days=3)) &
                                             (temp_df['trans_time'] <= k_t)].index.tolist()
        df.loc[temp_ind_list, 'same_in_out_var'] = 1

        # 其他画像之家庭不稳定标签
        df.loc[((pd.isna(df['relationship'])) | (df['relationship'] == '')) &
               (df['opponent_type'] == 1) &
               (~df['no_oppo_str'].str.contains("二维码")) &
               (df['trans_amt'].abs().isin(FAMILY_RISK_AMT)) &
               (~df['opponent_name'].isin(FAMILY_NO_RISK_APPELLATION)), 'family_risk_var'] = 1

        # 其他画像之大额进出账
        income_std, expense_std = df[df['trans_amt'] > 0].trans_amt.std(), df[df['trans_amt'] < 0].trans_amt.std()
        income_mean, expense_mean = df[df['trans_amt'] > 0].trans_amt.mean(), df[df['trans_amt'] < 0].trans_amt.mean()
        df.loc[(df.relationship != '主体') &
               (((df['trans_amt'] > income_mean + 2 * income_std) &
                 (df['trans_amt'] > income_mean * 5)) |
                ((df['trans_amt'] < expense_mean - 2 * expense_std) &
                 (df['trans_amt'] < expense_mean * 5))), 'large_trans_amt_var'] = 1

        # 其他画像之理财行为标签
        financing_df = df[(df.relationship != '主体') &
                          (((df.trans_amt > 0) & (df.no_oppo_str.str.contains(FINANCING_INCOME))) |
                           ((df.trans_amt < 0) & (df.no_oppo_str.str.contains(FINANCING_EXPENSE))))]
        financing_list = financing_df.index.tolist()
        df.loc[financing_list, 'financing_var'] = 1

        # 其他画像之房产买卖
        house_sale_df = df[(df.concat_str.str.contains(HOUSE_TRADE)) &
                           (~df.concat_str.str.contains(HOUSE_TRADE_EXCEPT_1)) &
                           (df.opponent_name.astype(str).str.contains(HOUSE_OPPO)) &
                           (df.trans_amt.abs() >= 2e4) &
                           (df.relationship != '主体')]
        house_sale_list = house_sale_df.index.tolist()
        df.loc[house_sale_list, 'house_sale_var'] = 1

        # 其他画像之单天大额进账
        df['trans_date'] = pd.to_datetime(df['trans_time'].dt.date)
        # 按日期和账号分组，统计大额交易次数
        large_mask = df['trans_amt'] >= 100000
        df['large_count'] = df[large_mask].groupby(['trans_date', 'opponent_account_bank', 'opponent_account_no'])['trans_amt'].transform('count')
        # 设置标签
        df['large_amount_1d'] = 0
        df.loc[(df['large_count'] >= 3) & large_mask, 'large_amount_1d'] = 1
        df.drop('large_count', axis=1, inplace=True)

    # 清洗标签子类
    def _sub_label_cleaning(self, label_df, column_name='mutual_exclusion_label', df=None):
        # 若未传需要清洗的标签子类，则直接返回
        if label_df.shape[0] == 0:
            return
        for row in label_df.itertuples():
            label_name = getattr(row, 'label_explanation')
            label_code = getattr(row, 'label_code')
            label_cont = re.sub('借款人姓名', str(self.param.get('cusName')), getattr(row, 'filter_content'))
            label_cont = re.sub('空字符串', '', label_cont)
            df['temp_col'] = 0
            try:
                exec(f"df.loc[{label_cont}, 'temp_col'] = 1")
            except Exception as e:
                logger.error(f"标签{label_name}：{label_code}清洗发生错误：{e}")
                df['temp_col'] = 0
            if column_name == 'mutual_exclusion_label':
                temp_id = df[pd.isna(df[column_name]) & (df['temp_col'] == 1)].index.tolist()
                df.loc[temp_id, column_name] = label_code
            else:
                na_id = df[(df['temp_col'] == 1) & (pd.isna(df[column_name]))].index.tolist()
                notna_id = df[(df['temp_col'] == 1) & (pd.notna(df[column_name]))].index.tolist()
                df.loc[na_id, column_name] = label_code
                df.loc[notna_id, column_name] += ',' + label_code

    # 标签清洗/标签重新清洗
    def _label_cleaning(self, reclean=0, df=None, alter_id=0):
        # 将所有标签清洗出来
        # 1.按照业务类型获取经营客群标签或者消费客群标签，对应标签编码第1-2位，01为经营，02为消费
        # 2.将标签分为互斥标签和兼容标签，对应标签编码第5-6位，01或者02为互斥，03或04为兼容
        # 3.互斥标签优先清洗非经营/其他收入/其他支出，后清洗经营/劳动收入/刚性支出，优先02，次01
        # 4.已经打上过互斥标签的行不参与后续互斥标签清洗
        # 5.兼容标签对所有流水进行清洗
        if reclean == 0:
            label_sql = """
                select * from label_logic 
                where label_type = 'LABEL' and valid_status = 1
                order by label_code asc
            """
        else:
            label_sql = f"""select * from label_logic where label_type = 'LABEL' and valid_status = 1 and id in
            (select label_id from label_logic_alter a where id > {alter_id}) order by label_code asc"""
        label_df = sql_to_df(label_sql)
        if label_df.shape[0] == 0:
            return
        # 记录标签现存位置，后续全部清空
        if reclean == 1:
            delete_label_code = label_df['label_code'].tolist()
            self.delete_id = df[df['mutual_exclusion_label'].isin(delete_label_code)]['flow_id'].tolist()

        df['mutual_exclusion_label'] = None
        df['compatibility_label'] = None
        if reclean == 0:
            df['create_time'] = self.create_time
            df['update_time'] = self.create_time
        start_str = '01' if self.cus_type == 1 else '02'
        label_df['cus_type'] = label_df['label_code'].apply(lambda x: x[:2])
        label_df['uni_type'] = label_df['label_code'].apply(lambda x: x[4:6])
        cus_label_df = label_df[label_df['cus_type'] == start_str]
        mutual_exclusion_label_df1 = cus_label_df[cus_label_df['uni_type'] == '02']
        mutual_exclusion_label_df2 = cus_label_df[cus_label_df['uni_type'] == '01']
        # 将二维码收款优先级调整为经营活动下最高
        mutual_exclusion_label_df2['priority'] = mutual_exclusion_label_df2.apply(
            lambda x: x['label_column'][-7:] if x['label_explanation'] != '二维码收款' else '1110100', axis=1)
        mutual_exclusion_label_df2.sort_values(by='priority',ascending=True,inplace=True)
        compatibility_label_df = cus_label_df[cus_label_df['uni_type'].isin(['03', '04'])]
        # 清洗互斥标签中的非经营/非劳动收入/其他支出
        self._sub_label_cleaning(mutual_exclusion_label_df1, df=df)
        # 清洗互斥标签中的经营/劳动收入/刚性支出
        self._sub_label_cleaning(mutual_exclusion_label_df2, df=df)
        # 若为重新清洗标签，则需要将调整前的标签先进行删除，然后进行下列标签清洗，并获取调整的列
        if reclean == 1:
            mutual_label_list = cus_label_df[cus_label_df['uni_type'].isin(['01', '02'])]['label_code'].tolist()
            self.reclean_id = df[df['mutual_exclusion_label'].isin(mutual_label_list)]['flow_id'].tolist()

        # 经营客群，进账打上进账-经营-其他经营-其他经营，消费客群，进账打上进账-非劳动收入-其他收入-其他收入
        df.loc[pd.isna(df['mutual_exclusion_label']) & (df['trans_amt'] > 0),
               'mutual_exclusion_label'] = '0101019901' if self.cus_type == 1 else '0201029901'
        # 经营客群，出账打上出账-经营-其他经营-其他经营，消费客群，出账打上出账-其他支出-其他支出-其他支出
        df.loc[pd.isna(df['mutual_exclusion_label']) & (df['trans_amt'] < 0),
               'mutual_exclusion_label'] = '0102019901' if self.cus_type == 1 else '0202029901'
        if reclean == 1:
            if compatibility_label_df.shape[0] == 0:
                return
            compat_label_str = '|'.join(compatibility_label_df['label_code'].tolist()) + '|,'
            df['compatibility_label'] = df['compatibility_label'].apply(
                lambda x: ','.join(re.sub(compat_label_str, ' ', x).split()))
        if 'temp_col' in df.columns.tolist():
            df['temp_col'] = 0
        self._sub_label_cleaning(compatibility_label_df, column_name='compatibility_label', df=df)
        # 取修改数据id做覆盖使用
        if reclean == 1 and compatibility_label_df.shape[0] > 0:
            compat_label_str = '|'.join(compatibility_label_df['label_code'].tolist())
            self.reclean_id.append(df[(df['compatibility_label'].str.contains(compat_label_str))]['flow_id'].tolist())
            compat_label_str += '|,'
            df['compatibility_label'] = df['compatibility_label'].apply(
                lambda x: ','.join(re.sub(compat_label_str, ' ', x).split()))



    def _save_data(self, df):
        df.rename(columns={'id': 'flow_id'}, inplace=True)
        alter_sql = f"""select max(id) as max_id from label_logic_alter"""
        alter_df = sql_to_df(alter_sql)
        df['out_req_no'] = self.out_req_no
        if alter_df.shape[0] > 0 and alter_df['max_id'][0] is not None and alter_df['max_id'].tolist()[0] > 0:
            max_id = alter_df['max_id'].tolist()[0]
        else:
            max_id = 0
        df['alter_id'] = max_id
        trans_label_df = df[['flow_id', 'out_req_no', 'mutual_exclusion_label', 'compatibility_label',
                             'alter_id', 'create_time', 'update_time']]
        label_df_list = trans_label_df.to_dict('records')
        transform_flow_str(current_session, label_df_list, 'TransLabel')
        self._drop_duplicate_data(data=df)
        report_flow_list = df.to_dict('records')
        transform_flow_str(current_session, report_flow_list, 'TransReportFlow')

    def _update_data(self, df):
        id_li = list(set(self.reclean_id + self.delete_id))
        label_update_df = df[df['flow_id'].isin(id_li)]
        report_update_df = self._update_trans_report(label_update_df)
        label_update_df.set_index('id', drop=True, inplace=True)
        report_update_df.set_index('id', drop=True, inplace=True)
        transform_update_str(current_session, label_update_df[['mutual_exclusion_label', 'compatibility_label']],
                             'TransLabel', label_update_df.index.astype(str).tolist())
        transform_update_str(current_session, report_update_df[['mutual_exclusion_label', 'compatibility_label']],
                             'TransReportFlow', report_update_df.index.astype(str).tolist())

    @staticmethod
    def _opponent_type(op_name):
        if len(op_name) > 6 and re.search(ENT_TYPE, op_name) is not None:
            return 2
        else:
            if len(op_name) <= 15:
                cleaned_name = re.sub(TYPE_EXCEPT_1, '', op_name)
                if re.match(TYPE_START_1, cleaned_name):
                    cleaned_name = re.sub(TYPE_EXCEPT_2, '', cleaned_name)
                elif re.match(TYPE_START_2, cleaned_name):
                    cleaned_name = cleaned_name.split()[-1]
                else:
                    cleaned_name = re.sub(r' ', '', cleaned_name)
                if 2 <= len(cleaned_name) <= 3:
                    if re.search(TYPE_EXCEPT_3, cleaned_name) is None and \
                            re.match(TYPE_EXCEPT_4, cleaned_name) is None:
                        return 1

    def execute(self):
        parse_task = self.parse_context.get('parse_task')
        self.param = json.loads(parse_task.req_raw_data)
        # 获取原始流水数据
        flow_sql = f"""select * from trans_flow where out_req_no = '{self.out_req_no}'"""
        df = sql_to_df(flow_sql)
        # 若从数据库中未找到上传的流水数据，则不用清洗标签
        if df.shape[0] == 0:
            return
        df.drop(['out_req_no', 'create_time', 'update_time'], axis=1, inplace=True)
        df.rename(columns={'id': 'flow_id'}, inplace=True)
        col = ['opponent_name', 'currency', 'opponent_account_bank', 'opponent_account_no', 'trans_channel',
               'trans_type', 'trans_use', 'remark']
        df[col] = df[col].fillna('')
        df['opponent_type'] = df['opponent_name'].apply(self._opponent_type)
        df['trans_flow_src_type'] = 1 if str(parse_task.trans_flow_src_type) in ['2', '3'] else 0
        # 判断是首次清洗标签还是重新清洗标签
        flow_id_list = df['flow_id'].unique().tolist()
        reclean_sql = f"""select * from trans_label where flow_id in %(flow_id_list)s"""
        clean_df = sql_to_df(reclean_sql, params={"flow_id_list": flow_id_list})
        if clean_df.shape[0] > 0:
            df = pd.merge(df, clean_df, how='left', on='flow_id')
            alter_id = clean_df['alter_id'].max()
            self._mid_variable_cleaning(df=df)
            self._label_cleaning(reclean=1, df=df, alter_id=alter_id)
            self._update_data(df=df)
        else:
            self._mid_variable_cleaning(df=df)
            self._label_cleaning(reclean=0, df=df)
            self._save_data(df=df)
