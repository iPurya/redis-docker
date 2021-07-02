FROM redis:latest


WORKDIR /redis
COPY . /redis/

RUN apt-get update && apt-get -y install \
    python3 \
    python3-pip \
    cron

RUN pip3 install -U \
    pip \
    setuptools \
    redis \
    dropbox

RUN cp crontab /etc/cron.d/backup && chmod 0644 /etc/cron.d/backup

CMD cron && redis-server