import traceback

import pdfplumber
import sys

from logger.logger_util import LoggerUtil

logger = LoggerUtil().logger(__name__)

def checkPHB(pdfPath):
    with pdfplumber.open(pdfPath) as pdf:
        strs = ['个人账户交易流水(电子版)','查询起止日期']
        try:
            if len(pdf.pages) >= 1:
                page = pdf.pages[0]
                # lst = list(map(lambda item: item.get('text'), page.extract_words()[0:3]))
                # for item in lst:
                #     if '查询起止日期' in item:
                #         return "true"
                # return "false"
                #return "true" if "个人账户交易流水(电子版)" in page.extract_words(x_tolerance=1)[0].get("text") else "false"

                # print(list(map(lambda item: item.get('text'), page.extract_words()[0:3])))
                intersection = list(
                    set(strs) & set(list(map(lambda item: item.get('text'), page.extract_words()[0:3]))))
                return "true" if len(intersection) > 0 else "false"
            else:
                return "false"
        except Exception as e:
            logger.error("trans upload exception:" + str(e))
            stack_trace = traceback.format_exc()
            logger.error(stack_trace)
            return "false"

if __name__ == "__main__":
    print(checkPHB(sys.argv[1]))
