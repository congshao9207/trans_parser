# @Time : 2/23/22 3:38 PM
# @Author : lixiaobo
# @File : string_util.py
# @Software: PyCharm
import re

from component.preparser.pre_parse_cfg import pre_remove_reg


def is_empty(info):
    return info is None or info == ""


def prune_row_content(info):
    res = re.sub(r'(\d)\s+(\d)', r'\1\2', info)
    res = re.sub(r'(\d)\s+(\d)', r'\1\2', res)
    for r in pre_remove_reg:
        res = re.sub(r, '', res)
    return res
