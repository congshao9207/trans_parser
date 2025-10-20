import traceback

import pdfplumber
import sys

from logger.logger_util import LoggerUtil

logger = LoggerUtil().logger(__name__)


def checkCIB(pdfPath):
    logger.info("pdfPath: " + pdfPath)
    strs = ['兴业银行交易流水', "兴业银⾏交易流⽔", "兴业银行交易明细", "单位活期存款账户交易明细","个人账户交易流水(电子版)","华夏银行个人账户交易流水(电子版)","江西·农商银行交易流水"]
    try:
        with pdfplumber.open(pdfPath) as pdf:
            if len(pdf.pages) >= 1:
                page = pdf.pages[0]

                # 去水印
                objects = page.objects

                new_chars = []
                if objects.get("char") is not None:
                    for char in objects['char']:
                        # 字符矩阵存在一个非零的旋转角，则证明该矩阵有旋转倾斜，则基本上可确定是水印
                        if next((item for item in char["matrix"] if item < 0), None) is not None:
                            continue
                        if char['size'] < 20:
                            new_chars.append(char)
                            continue
                        if not char['non_stroking_color']:
                            new_chars.append(char)
                    page.objects['char'] = new_chars

                intersection = list(set(strs) & set(list(map(lambda item: item.get('text'), page.extract_words()[0:3]))))
                return "true" if len(intersection) > 0 else "false"
            else:
                return "false"
    except Exception as e:
        logger.error("trans upload exception:" + str(e))
        stack_trace = traceback.format_exc()
        logger.error(stack_trace)
        return "false"

if __name__ == "__main__":
    print(checkCIB(sys.argv[1]))
