# @Time : 2/15/22 2:33 PM
# @Author : lixiaobo
# @File : util_test.py
# @Software: PyCharm
import os
import re
import zipfile

from config.db_config import sql_to_df


def test_zip():
    result_zip_file = '/Users/lixiaobo/Downloads/aa.zip'
    result_dir = '/Users/lixiaobo/Downloads/a'

    with zipfile.ZipFile(result_zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(result_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arch_name = os.path.relpath(file_path, result_dir)
                zipf.write(file_path, arch_name)


def test_sql_2_df():
    df = sql_to_df('select * from trans_parse_task')
    print(df)


def test_format():
    s = "foo 123 bar 456"
    info = re.sub(r'(\d+)', r'___\1', s)
    print(info)
