# coding: utf-8
from sqlalchemy import Column, DateTime, Index, String
from sqlalchemy.dialects.mysql import BIGINT, MEDIUMTEXT
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class DownloadRecord(Base):
    __tablename__ = 'download_record'
    __table_args__ = (
        Index('idx_parse_no_file_type', 'file_parse_no', 'result_file_type'),
        {'comment': '解析结果下载记录表'}
    )

    id = Column(BIGINT(20), primary_key=True, comment='主键ID')
    file_parse_no = Column(String(40), nullable=False, comment='文件解析请求的文件解析编号')
    result_file_type = Column(String(10), nullable=False, comment='下载文件类型')
    result_file_url = Column(String(200), nullable=False, comment='结果文件Url')
    result_file_persistence_mode = Column(String(25), nullable=False, comment='结果文件存储类型')
    create_date = Column(DateTime, nullable=False, comment='创建时间')
    last_modified_date = Column(DateTime, nullable=False, comment='更新时间')


class FileParseRecord(Base):
    __tablename__ = 'file_parse_record'
    __table_args__ = {'comment': '文件解析请求记录表'}

    id = Column(BIGINT(20), primary_key=True, comment='主键ID')
    file_parse_no = Column(String(36), nullable=False, index=True, comment='文件解析编号, 业务主键')
    source_file_url = Column(String(200), comment='源文件路径')
    source_file_persistence_mode = Column(String(25), comment='源文件存储方式')
    parse_engine_type = Column(String(25), comment='解析引擎类型')
    status = Column(String(20), nullable=False, comment='文件解析状态')
    message = Column(String(100), comment='文件解析结果描述')
    create_date = Column(DateTime, nullable=False, comment='创建时间')
    last_modified_date = Column(DateTime, nullable=False, comment='更新时间')
    out_req_no = Column(String(64), comment='外部请求编号')


class JobRecord(Base):
    __tablename__ = 'job_record'
    __table_args__ = {'comment': '内部解析器任务表'}

    id = Column(BIGINT(20), primary_key=True, comment='主键ID')
    file_parse_no = Column(String(40), nullable=False, index=True, comment='文件解析请求中的文件解析编号')
    job_file_url = Column(String(200), comment='任务文件路径')
    job_file_persistence_mode = Column(String(25), comment='任务文件存储方式')
    result_data_id = Column(BIGINT(20), comment='任务文件解析结果数据ID')
    status = Column(String(20), nullable=False, comment='任务状态')
    message = Column(String(100), comment='任务结果描述')
    create_date = Column(DateTime, nullable=False, comment='创建时间')
    last_modified_date = Column(DateTime, nullable=False, comment='更新时间')


class JobResult(Base):
    __tablename__ = 'job_result'
    __table_args__ = {'comment': '内部解析器解析结果表'}

    id = Column(BIGINT(20), primary_key=True, comment='主键ID')
    data = Column(MEDIUMTEXT, nullable=False, comment='解析结果')
