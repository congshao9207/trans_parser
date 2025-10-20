import traceback

import pdfplumber
import sys

from logger.logger_util import LoggerUtil

logger = LoggerUtil().logger(__name__)


def checkBank(pdfPath):
    try:
        with pdfplumber.open(pdfPath) as pdf:
            try:
                if len(pdf.pages) < 1:
                    return ""

                page = pdf.pages[0]
                if (True if "支付宝" in page.extract_words(x_tolerance=1)[2].get("text") else False):
                    return "LINE_ALIPAY"

                if (True if "微信" in page.extract_words(x_tolerance=1)[1].get("text") else False):
                    return "LINE_WECHAT_PAY"

                return ""
            except:
                return ""
    except Exception as e:
        logger.error("trans upload exception:" + str(e))
        stack_trace = traceback.format_exc()
        logger.error(stack_trace)
        return ""


if __name__ == "__main__":
    print(checkBank(sys.argv[1]))
