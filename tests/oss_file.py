# -*- coding: utf-8 -*-
# @Project : trans-parser
# @IDE : PyCharm
# @Author : lixiaobo
# @Date : 1/6/25 2:29 PM
# @Version : 1.0
# @Description :
import openpyxl
import re
import requests
import os

failed_count = 0


def read_file_list():
    p = '/Users/lixiaobo/Downloads/file_list_v3.xlsx'
    w = openpyxl.load_workbook(p)
    s = w.worksheets[0]
    index = -1
    res = []
    for r in s.rows:
        index += 1
        if index >= 1:
            res.append(r[1].value)

    return res


def download(p, k):
    global failed_count
    u = 'https://apply.magfin.cn/contract/queryPdf?ossKey=' + k
    r = requests.get(u)
    if r.status_code == 200:
        url = r.content
        r = requests.get(url)
        with open(p + os.path.sep + re.sub(r'[\s\/]', '', k), 'wb') as f:
            f.write(r.content)
    else:
        print("request failed, status_code:", r.status_code)
        failed_count += 1


if __name__ == '__main__':
    print("oss file download....")
    dest_dir = '/Users/lixiaobo/Downloads/files'
    keys = read_file_list()
    total = len(keys)
    index = 0
    for k in keys:
        index += 1
        print("progress----------: %s/%s" % (index, total))
        download(dest_dir, k)

    print("all finished, failed count:", failed_count)
