FROM python:3.7
RUN apt update && apt install -y build-essential
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY requirements.txt /usr/src/app
RUN pip install -r requirements.txt
COPY app /usr/src/app/app
COPY scripts /usr/src/app/scripts
COPY application.py /usr/src/app/application.py
COPY config.py /usr/src/app/config.py
EXPOSE 5000
ENTRYPOINT [ "python" ]
CMD [ "application.py" ]