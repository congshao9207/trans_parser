# -*- coding: utf-8 -*-
# @Project : trans-parser
# @IDE : PyCharm
# @Author : lixiaobo
# @Date : 12/13/24 4:38 PM
# @Version : 1.0
# @Description :
import os
import uuid

import openpyxl
import pytest
import requests

from componentt.preparse_test import pre_parse


def _download_file(url):
    resp = requests.get(url)
    if resp.status_code == 200:
        data = resp.content
        file_name = str(uuid.uuid4()) + ".pdf"
        with open('/Users/lixiaobo/Downloads/pdfs/' + file_name, 'wb') as f:
            f.write(data)
    else:
        print("file download failed, url: %s" % url)


def test_download():
    w = openpyxl.load_workbook('/Users/lixiaobo/Downloads/top1000.xlsx')
    s = w.worksheets[0]
    index = -1
    for r in s.rows:
        index += 1
        if index >= 1:
            url = r[0].value
            print(url)
            _download_file(url)
            print("progress: %s/%s" % (s.max_row, index))


@pytest.mark.parametrize('file_path', os.listdir('/Users/lixiaobo/Downloads/pdfs'))
def test_pre_parse_pdf(file_path, perf_stats):
    if file_path.endswith('pdf'):
        data = pre_parse('/Users/lixiaobo/Downloads/pdfs/' + file_path)
        perf_stats.add_per_data(file_path, data['bank_name'], data['bank_account'], data['user_name'])
