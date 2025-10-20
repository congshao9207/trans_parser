# pymupdf -version = 1.19.6
# 脚本调用，必须上传全部参数，防止出现索引溢出异常
import os
import sys
import traceback

from logger.logger_util import LoggerUtil

logger = LoggerUtil().logger(__name__)


def pdf_image(pdfPath, imagePath, zoom_x = 5, zoom_y = 5, rotation_angle = 0):
    import fitz
    try:
        pdf = fitz.open(pdfPath)
        print("len(pdf):", len(pdf))
        for pg in range(len(pdf)):
            page = pdf[pg]
            trans = fitz.Matrix(zoom_x, zoom_y).prerotate(rotation_angle)
            pm = page.get_pixmap(matrix = trans, alpha=False)
            pm.save(imagePath + os.path.sep + str(pg) + '.png')
        pdf.close()
        return "true"
    except Exception as e:
        e_info = traceback.format_exc()
        logger.warn(e_info)
        return "false"

if __name__ == "__main__":
    print(pdf_image(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]))
