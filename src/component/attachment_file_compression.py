# @Time : 4/16/22 5:35 PM 
# @Author : lixiaobo
# @File : attachment_file_compression.py 
# @Software: PyCharm
import json

from flask_sqlalchemy_session import current_session

from config.file_type import FileTypeEnum
from model.model import TransAttachment
from util.file_util import get_file_md5


class AttachmentFileCompression(object):
    def __init__(self, session=None):
        self.session = session

    def persistence_file(self, file_path, file_hash, ext):
        with open(file_path, "rb") as f:
            file_content = f.read()
            if not file_hash:
                file_hash = get_file_md5(file_path)

            ta_id = self._exists_file_id(file_hash)
            if ta_id:
                return ta_id

            ta = TransAttachment()
            ta.file_type = ext
            ta.trans_data_content_type = ext
            ta.trans_data = file_content
            ta.file_md_5 = file_hash
            current_session.add(ta)
            current_session.commit()
            return ta.id

    @staticmethod
    def _exists_file_id(file_hash):
        info = current_session.query(TransAttachment.id).filter(TransAttachment.file_md_5 == file_hash).first()
        return info.id if info else None

    @staticmethod
    def persistence_json(flow_data, parse_no):
        json_content = json.dumps(flow_data)
        ta = TransAttachment()
        ta.file_type = FileTypeEnum.JSON.value + ":" + parse_no
        ta.trans_data_content_type = FileTypeEnum.JSON.value
        ta.trans_data = json_content.encode("utf-8")
        current_session.add(ta)
        current_session.commit()
        return ta.id
