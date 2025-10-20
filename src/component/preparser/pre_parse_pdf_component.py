import re

import pdfplumber
import regex
from pdfminer.pdfpage import PDFPage
from pdfplumber.page import Page

from component.preparser.pre_parse_cfg import kw_bank_account, kw_user_name, kw_row_count, kw_bank_name_d, \
    describe_bank_account, content_user_name, content_bank_account
from component.preparser.pre_parse_util import parse_join_info_field, parse_start_end, parse_bank_name
from config.title_matcher import is_trans_flow_title
from logger.logger_util import LoggerUtil
from util.string_util import prune_row_content

logger = LoggerUtil().logger(__name__)


class PreParsePdfComponent(object):

    def __init__(self, ctx):
        self.ctx = ctx

    def pre_parse(self):
        logger.info("begin pre parse......:%s", self.ctx.stand_file_name)
        with pdfplumber.open(self.ctx.stand_file_path, password=self.ctx.file_pwd) as pdf:
            first_page = self._fetch_first_page(pdf)
            rows, threshold = self._fetch_rows(first_page)
            self.parse_head_field(rows, threshold)

            if self._vote_extract_table():
                rows = self._extract_table_info(first_page)
                if rows:
                    self.parse_head_field(rows, threshold)

    def _fetch_rows(self, first_page):
        res = []
        tables = first_page.find_tables()
        if not tables or len(tables) == 0:
            texts = first_page.extract_text(x_tolerance=1)
            rows = texts.split("\n")
            for row in rows:
                if is_trans_flow_title(row):
                    break
                if re.fullmatch(r'(\w\s){3,}\w', row):
                    res.append(re.sub(r'\s', '', row))
                else:
                    res.append(row)
            return res, 4

        lines = first_page.extract_text_lines(x_tolerence=1)
        index = -1
        for table in tables:
            index = index + 1
            ext_tables = first_page.extract_tables()
            rows = ext_tables[index]
            tab_res = []
            for row in rows:
                sl = list(filter(lambda el: el is not None, row))
                if len(sl) >= 6:
                    # 标准表格，则需要对单元格进行格式化
                    sl = list(map(lambda el: re.sub(r'\s', '',  el), sl))
                s = " ".join(sl)
                m = regex.findall(r'\s', s)
                if m:
                    if len(m) >= 5 and is_trans_flow_title(s):
                        break
                    elif len(m) >= 3:
                        tab_res.extend(s.split('\n'))
                    else:
                        tab_res.append(s.replace('\n', ''))
                else:
                    tab_res.append(s.replace('\n', ''))
            if len(tab_res) == 1 and not tab_res[0].strip():
                continue

            point_y = table.bbox[1]
            for line in lines:
                if line['top'] < point_y:
                    if re.fullmatch(r'(\w\s){3,}\w', line['text']):
                        res.append(re.sub(r'\s', '', line['text']))
                    else:
                        text = line['text']
                        if is_trans_flow_title(text):
                            return res, len(res)
                        res.append(line['text'])

            threshold = len(res)
            for e in tab_res:
                res.append(e)

            return res, threshold
        return res, len(res)

    def parse_head_field(self, rows, threshold):
        index = -1
        for r in rows:
            row = re.sub('[a-zA-Z/\n]', '', r)
            row = prune_row_content(row)
            origin_row = prune_row_content(r)
            index += 1
            try:
                # if not self.ctx.bank_name and index <= max(3, threshold):
                if not self.ctx.bank_name:
                    self.ctx.bank_name = parse_bank_name(row)
                    if self.ctx.bank_name == '':
                        self.ctx.bank_name = self._parse_field(row, kw_bank_name_d)
                    self.ctx.bank_name = regex.sub(r'[^\p{Han}]', '', self.ctx.bank_name)
                if not self.ctx.bank_account:
                    self.ctx.bank_account = self._parse_field(origin_row, kw_bank_account,
                                                              field_describe=describe_bank_account,
                                                              content_reg=content_bank_account)
                    self.ctx.bank_account = regex.sub(r'[\p{Han}\/\,\s]', '', self.ctx.bank_account)
                if not self.ctx.user_name:
                    self.ctx.user_name = self._parse_field(origin_row, kw_user_name,
                                                           content_reg=content_user_name)
                    self.ctx.user_name = regex.sub(r'[^\p{Han}]', '', self.ctx.user_name)
                if not self.ctx.start_date or not self.ctx.end_date:
                    start, end = parse_start_end(row)
                    if not self.ctx.start_date:
                        self.ctx.start_date = start
                    if not self.ctx.end_date:
                        self.ctx.end_date = end
                if not self.ctx.row_count:
                    self.ctx.row_count = self._parse_field(row, kw_row_count)
            except Exception as e:
                logger.error(e)

        if not self.ctx.is_parse_succeed():
            logger.warn("parse failed, origin data:%s", rows)

    @staticmethod
    def _parse_field(row, kws, no_title=False, x_tolerance=0, field_describe=None, content_reg=None):
        return parse_join_info_field(row, kws, no_title=no_title, x_tolerance=x_tolerance,
                                     field_describe=field_describe, content_reg=content_reg)

    def _vote_extract_table(self):
        count = 0
        if not self.ctx.bank_name:
            count += 1
        if not self.ctx.bank_account:
            count += 1
        if not self.ctx.user_name:
            count += 1
        return count >= 2

    @staticmethod
    def _extract_table_info(first_page):
        tables = first_page.extract_table()
        if not tables or len(tables) > 6 or (tables[0] and len(tables[0]) > 4):
            return None

        row_val = []
        for row in tables:
            row_con = ''
            i = 0
            for cell in row:
                i += 1
                if cell:
                    info = cell.split("\n")
                    r = info[0] if info else info
                    row_con += r
                    if i % 2 == 0:
                        row_con += '  '
                    else:
                        row_con += ':'

            row_val.append(row_con)
        return row_val

    @staticmethod
    def _fetch_first_page(pdf):
        for i, page in enumerate(PDFPage.create_pages(pdf.doc)):
            return Page(pdf, page, page_number=1, initial_doctop=0)
        return None


