import logging
import os
import time

import openpyxl
import pytest

from component.preparser.pre_parse_scheduler import PreParseScheduler
from componentt.perf_stats import PerfStats

logging.getLogger('pdfminer').setLevel(logging.ERROR)


ps = PerfStats()


def assert_result(data, file_list):
    result, predicate = data, [file_list[1], file_list[2], file_list[3]]
    assert result['bank_name'] == predicate[0]
    assert result['bank_account'] == predicate[1]
    assert result['user_name'] == predicate[2]


def obtain_file_list(file_path):
    if not os.path.exists(file_path):
        return []
    workbook = openpyxl.load_workbook(file_path)
    sheet = workbook.worksheets[0]
    res = []
    for r in sheet.rows:
        res.append(list(map(lambda x: x if x else '', [r[0].value, r[1].value, r[2].value, r[3].value])))
    return res


def pre_parse(file_path):
    pps = PreParseScheduler()
    res_code, res_msg, data = pps.dispatch_pre_parse(file_path, None)
    print("file_path: ", file_path)
    print("res_code: ", res_code)
    print("res_msg: ", res_msg)
    print("data ", data)
    return data


@pytest.fixture()
def perf_stats():
    start = time.time() * 1000
    yield ps
    cost_mill = time.time() * 1000 - start
    ps.add_stats(int(cost_mill))


'''
@pytest.mark.usefixtures("perf_stats")
@pytest.mark.parametrize('file_path', list(filter(lambda x: x[1] <= 3, pdf_file_path_list)))
def test_pre_parse_pdf(file_path, perf_stats):
    data = pre_parse("../resource/pdf/" + file_path[0])
    perf_stats.add_per_data(file_path[0], data['bank_name'], data['bank_account'], data['user_name'])


@pytest.mark.usefixtures("perf_stats")
@pytest.mark.parametrize('file_path', list(filter(lambda x: x[1] <= 3, xlsx_file_path_list)))
def test_pre_parse_xlsx(file_path, perf_stats):
    data = pre_parse("../resource/xlsx/" + file_path[0])
    perf_stats.add_per_data(file_path[0], data['bank_name'], data['bank_account'], data['user_name'])
'''


@pytest.mark.parametrize('file_list', obtain_file_list('../resource/pdf/pdf_file_list.xlsx'))
def test_pre_parse_pdf(file_list):
    data = pre_parse("../resource/pdf/" + file_list[0])
    print(data)
    assert_result(data, file_list)


@pytest.mark.parametrize('file_list', obtain_file_list('/Users/lixiaobo/Doc/流水项目/流水预解析/batch03/pdf_list.xlsx'))
def test_pre_parse_pdf_batch03(file_list):
    data = pre_parse("/Users/lixiaobo/Doc/流水项目/流水预解析/batch03/" + file_list[0])
    print(data)
    assert_result(data, file_list)


# @pytest.mark.usefixtures("perf_stats")
@pytest.mark.parametrize('file_list', obtain_file_list('../resource/xlsx/excel_file_list_v2.xlsx'))
def test_pre_parse_xlsx(file_list):
    data = pre_parse("../resource/xlsx/" + file_list[0])
    assert_result(data, file_list)
    # perf_stats.add_per_data(file_list[0], data['bank_name'], data['bank_account'], data['user_name'])

