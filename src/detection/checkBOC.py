import traceback

import pdfplumber
import sys

from logger.logger_util import LoggerUtil

logger = LoggerUtil().logger(__name__)


def checkBC(pdfPath):
    try:
        with pdfplumber.open(pdfPath) as pdf:
            if len(pdf.pages) >= 1:
                page = pdf.pages[0]
                return  "true" if "中国银行" in  page.extract_words()[5].get("text") else  "false"
                # res = next(item for item in page.extract_words() if "中国银行" in item.get("text")), [None]
            else:
                return "false"
    except Exception as e:
        logger.error("trans upload exception:" + str(e))
        stack_trace = traceback.format_exc()
        logger.error(stack_trace)
        return "false"

if __name__ == "__main__":
    print(checkBC(sys.argv[1]))
