import pdfplumber
import sys

def checkNullValue(pdfPath):
    try:
        with pdfplumber.open(pdfPath) as pdf:
            if len(pdf.pages) >= 1:
                page = pdf.pages[0]
                result = any(item['text'] == '\x00' for item in page.chars)
                return  "true" if result is True else  "false"
            else:
                return "false"
    except:
        return  "false"

if __name__ == "__main__":
    print(checkNullValue(sys.argv[1]))
