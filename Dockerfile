FROM python:3.11-slim

ADD requirements.txt /requirements.txt
RUN pip install -r requirements.txt

ADD main.py /main.py

CMD ["python3", "/main.py"]
