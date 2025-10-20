FROM registry.cn-shanghai.aliyuncs.com/transformer/trans-parser-py-base:3.9.12

COPY . /usr/src/app

ENV PYTHONUNBUFFERED 1
ENV PYTHONIOENCODING utf-8
EXPOSE 8011
ENV PYTHONIOENCODING utf-8

# RUN pip install pymupdf==1.24.10 -i https://mirrors.aliyun.com/pypi/simple

CMD ["gunicorn", "--workers=5", "--bind=0.0.0.0:8011", "app:app", "-t=600"]

# CMD ["uwsgi", "--ini", "uwsgi.ini"]
