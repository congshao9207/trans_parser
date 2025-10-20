# -*- coding: utf-8 -*-
# @Project : trans-parser
# @IDE : PyCharm
# @Author : lixiaobo
# @Date : 12/17/24 5:20 PM
# @Version : 1.0
# @Description :
import re

from config.trans_config import *

title_matcher = [re.compile(TRANS_TIME_PATTERN), re.compile(TRANS_AMT_PATTERN), re.compile(TRANS_BAL_PATTERN),
                 re.compile(TRANS_CUR_PATTERN), re.compile(TRANS_OPNAME_PATTERN), re.compile(TRANS_OPACCT_PATTERN),
                 re.compile(TRANS_OPBANK_PATTERN), re.compile(TRANS_CHANNEL_PATTERN), re.compile(TRANS_TYP_PATTERN),
                 re.compile(TRANS_USE_PATTERN), re.compile(TRANS_REMARK_PATTERN), re.compile(ACCOUNTING_DATE_PATTERN),
                 re.compile(TRANS_PLACE)]


def is_trans_flow_title(infos):
    if not infos:
        return False
    row_info = infos
    if type(infos) == list:
        row_info = " ".join(infos)
    matched = 0
    for m in title_matcher:
        if re.search(m, row_info):
            matched += 1
    return matched > 4
