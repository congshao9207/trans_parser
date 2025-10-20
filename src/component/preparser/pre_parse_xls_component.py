import datetime
import re
from functools import reduce

import xlrd

from component.preparser.pre_parse_cfg import kw_user_name, kw_start, kw_end, kw_row_count, kw_sep, \
    x_kw_bank_account, trans_header_max_rows, ignore_content, kw_bank_name_d, x_kw_bank_account_d, \
    x_kw_usr_name_d
from component.preparser.pre_parse_util import parse_join_info_field, parse_start_end, \
    parse_bank_name
from config.title_matcher import is_trans_flow_title
from logger.logger_util import LoggerUtil

logger = LoggerUtil().logger(__name__)


def decl_field_val(fun):
    def warp(self, *args, **kwargs):
        v = fun(self, *args, **kwargs)
        if v and type(v) == datetime.datetime:
            return v.strftime("%Y-%m-%d")
        return v

    return warp


class PreParseXlsComponent(object):
    def __init__(self, ctx):
        self.ctx = ctx

    def pre_parse(self):
        # book = openpyxl.load_workbook(self.ctx.stand_file_path, read_only=True)
        # sheet = book.active
        workbook = xlrd.open_workbook(self.ctx.stand_file_path)
        sheet = workbook.sheet_by_index(0)
        index = 0
        for row in sheet:
            index += 1
            if index > trans_header_max_rows:
                break
            try:
                row_val = [re.sub('[a-zA-Z/\n]', '', cell.value) for cell in row if cell and cell.value]
                if not row_val:
                    continue
                if len(row_val) == 1 and re.search(ignore_content, row_val[0]):
                    continue

                traversed_title = is_trans_flow_title(row_val)
                if traversed_title:
                    if not self.ctx.bank_name and not self.ctx.bank_account:
                        self._parse_from_content(sheet, row, index)
                    break
                join_info = self._is_join_info(row_val)

                if join_info and not self.ctx.bank_name:
                    self.ctx.bank_name = parse_bank_name(row_val[0])
                    if self.ctx.bank_name == '':
                        self.ctx.bank_name = self._parse_field(row_val, kw_bank_name_d, join_info)
                    if self.ctx.bank_name in ['交易用途']:
                        self.ctx.bank_name = ''
                    self.ctx.bank_name = re.sub('[^\u4e00-\u9fa5]', '', self.ctx.bank_name)
                if not self.ctx.bank_account:
                    self.ctx.bank_account = self._parse_field(row_val, x_kw_bank_account, join_info)
                    self.ctx.bank_account = re.sub('[\u4e00-\u9fa5]', '', self.ctx.bank_account)
                if not self.ctx.user_name:
                    self.ctx.user_name = self._parse_field(row_val, kw_user_name, join_info)
                    self.ctx.user_name = re.sub('[^\u4e00-\u9fa5]', '', self.ctx.user_name)
                if not self.ctx.start_date:
                    self.ctx.start_date = self._parse_field(row_val, kw_start, join_info)
                if not self.ctx.end_date:
                    self.ctx.end_date = self._parse_field(row_val, kw_end, join_info)
                if not self.ctx.start_date and not self.ctx.end_date:
                    self.ctx.start_date, self.ctx.end_date \
                        = parse_start_end(reduce(lambda e1, e2: e1 + "  " + e2, row_val))

                if not self.ctx.row_count:
                    self.ctx.row_count = self._parse_field(row_val, kw_row_count, join_info)
            except Exception as e:
                logger.error(e)

    @staticmethod
    def _is_join_info(row_val):
        if len(row_val) == 1:
            return True
        for sep in kw_sep:
            if re.search(sep + "[\\s]*[\\S]+", row_val[0]):
                return True
        return False

    @decl_field_val
    def _parse_field(self, row_val, kw_info, join_info):
        kw, ex_kx = (kw_info, None) if type(kw_info) is list else (kw_info['include'], kw_info['exclude'])
        if join_info:
            row_con = reduce(lambda e1, e2: e1 + "  " + e2, row_val)
            field_val = parse_join_info_field(row_con, kw_info)
            return field_val

        for k in kw:
            matched = False
            for val in row_val:
                if matched:
                    if val:
                        return val
                    continue
                if type(val) is str and re.search(k, val) and self._is_exclude(val, ex_kx):
                    matched = True
        return ''

    @staticmethod
    def _is_exclude(val, ex_kw):
        if not ex_kw:
            return True
        return len([x for x in ex_kw if re.search(x, val)]) == 0

    def _parse_from_content(self, sheet, row, index):
        usr_name_index = -1
        account_no_index = -1
        row_index = -1
        for cell in row:
            row_index += 1
            if cell.value in x_kw_bank_account_d:
                account_no_index = row_index
            elif cell.value in x_kw_usr_name_d:
                usr_name_index = row_index
        if usr_name_index == -1 and account_no_index == -1:
            return
        i = 0
        for row in sheet:
            i += 1
            if i <= index:
                continue
            if self.ctx.bank_account and self.ctx.user_name:
                break
            if account_no_index >= 0 and not self.ctx.bank_account:
                self.ctx.bank_account = row[account_no_index].value
            if usr_name_index >= 0 and not self.ctx.user_name:
                self.ctx.user_name = row[usr_name_index].value
