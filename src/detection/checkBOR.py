import traceback

import pdfplumber
import sys

from logger.logger_util import LoggerUtil

logger = LoggerUtil().logger(__name__)


def checkBOR(pdfPath):
    try:
        with pdfplumber.open(pdfPath) as pdf:
            if len(pdf.pages) >= 1:
                page = pdf.pages[0]
                # for word in page.extract_words():
                #     print(word)
                if len(page.extract_words()) > 16:
                    return  "true" if "开户机构" in page.extract_words()[15].get("text") and "日照银行" in  page.extract_words()[16].get("text") else  "false"
            else:
                return "false"
    except Exception as e:
        logger.error("trans upload exception:" + str(e))
        stack_trace = traceback.format_exc()
        logger.error(stack_trace)
        return "false"
