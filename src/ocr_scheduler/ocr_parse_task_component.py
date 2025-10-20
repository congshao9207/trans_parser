import uuid
from datetime import datetime

from config.process_status import ProcessStatusEnum
from model.models import FileParseRecord


class OcrParseTaskComponent(object):
    def __init__(self, session, group_no, password):
        self.session = session
        self.group_no = group_no
        self.password = password
        self.parse_no = "FP" + str(uuid.uuid1())

    def process(self):
        fpr = FileParseRecord()
        fpr.file_parse_no = self.parse_no
        fpr.out_req_no = self.group_no
        fpr.status = ProcessStatusEnum.RECEIVED.name
        fpr.create_date = datetime.now()
        fpr.last_modified_date = datetime.now()

        self.session.add(fpr)
        self.session.commit()

        return self.parse_no
