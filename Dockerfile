FROM python:3.5-onbuild

MAINTAINER George Cushen
ADD sources.list /etc/apt/sources.list
# Install Mezzanine dependencies.
RUN DEBIAN_FRONTEND=noninteractive apt-get clean && apt-get update && \
    apt-get install -y \
    libsox-fmt-mp3 \
    libsox-fmt-all \
    mpg321 \
    dir2ogg \
    sox \
    libav-tools
#RUN easy_install pip

# Handle urllib3 InsecurePlatformWarning
#RUN apt-get install -y libffi-dev libssl-dev libpython2.7-dev
#RUN pip install urllib3[security] requests[security] ndg-httpsclient pyasn1
# Install Mezzanine dependencies.


# install packages
#RUN apt-get update && apt-get install -y \
#    && rm -rf /var/lib/apt/lists/*
RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip freeze --local | grep -v '^\-e' | cut -d = -f 1  | xargs -n1 pip install -U
RUN pip install django-celery

ADD . /code/