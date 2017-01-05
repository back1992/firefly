 FROM registry.tjoomla.com:5000/mezzaninedocker_web:v4
# FROM kakadadroid/python-talib

 ENV PYTHONUNBUFFERED 1
 RUN mkdir -p /code
 WORKDIR /code
 ADD requirements.txt /code/
 RUN pip install -r requirements.txt
# RUN python manage.py makemigrations --noinput
# RUN python manage.py migrate --noinput
 RUN python manage.py collectstatic --noinput