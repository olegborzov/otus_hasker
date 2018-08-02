#!/usr/bin/env bash

# Project settings
PROJECT_NAME=hasker
PROJECT_FOLDER=$(pwd)
SECRET_KEY="$(openssl rand -base64 50)"
CONFIG="hasker.settings.production"

# Postgres settings
DB_NAME=${PROJECT_NAME}_db
DB_USER=${PROJECT_NAME}_db_admin
DB_PASSWORD=Hasker1234


echo "1. Try to update/upgrade repositories..."
apt-get -qq -y update
apt-get -qq -y upgrade


echo "2. Try to install required packages..."
PACKAGES=('nginx' 'libpq-dev' 'postgresql' 'python3' 'python3-pip')
for pkg in "${PACKAGES[@]}"
do
    echo "Installing '$pkg'..."
    apt-get -qq -y install ${pkg}
    if [ $? -ne 0 ]; then
        echo "Error installing system packages '$pkg'"
        exit 1
    fi
done


echo "3. Try to install Python3 project dependencies..."
pip3 install -r requirements/production.txt


echo "4. Try to setup PostgreSQL..."
service postgresql start
su postgres -c "psql -c \"CREATE USER ${DB_USER} PASSWORD '${DB_PASSWORD}'\""
su postgres -c "psql -c \"CREATE DATABASE ${DB_NAME} OWNER ${DB_USER}\""


echo "5. Configure uwsgi..."
mkdir -p /run/uwsgi
mkdir -p /usr/local/etc

cat > /usr/local/etc/uwsgi.ini << EOF
[uwsgi]
project = ${PROJECT_NAME}
chdir = ${PROJECT_FOLDER}
module = hasker.wsgi:application

master = true
processes = 1

socket = /run/uwsgi/%(project).sock
chmod-socket = 666
vacuum = true

die-on-term = true
env = DJANGO_SETTINGS_MODULE=${CONFIG}
env = SECRET_KEY=${SECRET_KEY}
env = DB_NAME=${DB_NAME}
env = DB_USER=${DB_USER}
env = DB_PASSWORD=${DB_PASSWORD}
EOF


echo "6. Configure nginx..."
mkdir /var/www/static
mkdir /var/www/media

cat > /etc/nginx/conf.d/${PROJECT_NAME}.conf << EOF
server {
    listen 80;
    server_name localhost 127.0.0.1;
    location /static/ {
        root /var/www;
    }
    location /media/ {
        root /var/www;
    }
    location / {
        include uwsgi_params;
        uwsgi_pass unix:/run/uwsgi/${PROJECT_NAME}.sock;
    }
}
EOF


echo "6. Prepare Django..."
COMMANDS=('collectstatic' 'makemigrations user' 'makemigrations' 'migrate')
for COMMAND in "${COMMANDS[@]}"
do
    DJANGO_SETTINGS_MODULE=${CONFIG} \
    SECRET_KEY=${SECRET_KEY} \
    DB_NAME=${DB_NAME} \
    DB_USER=${DB_USER} \
    DB_PASSWORD=${DB_PASSWORD} \
    python3 manage.py ${COMMAND}
done


echo "8. Start nginx..."
service nginx start
uwsgi --ini /usr/local/etc/uwsgi.ini