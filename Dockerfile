FROM python:3.8.12-bullseye
COPY . /code
WORKDIR /code
ENV PYTHONPATH=.
ENV PATH=$PATH:/code/driver
RUN cp ./sources.list /etc/apt/sources.list
RUN apt install apt-transport-https ca-certificates
RUN apt-get update --fix-missing \
    && apt-get install --fix-missing libsm6 libxext-dev tzdata chromium-driver -y \
    && apt-get clean all
RUN pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
ENV TZ="Asia/Shanghai"
CMD ["python", "main.py"]
