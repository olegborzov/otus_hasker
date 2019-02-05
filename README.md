# Hasker: Poor Man's Stackoverflow
Homework for Otus course - https://otus.ru/lessons/razrabotchik-python/
Q&A analog of stackoverflow on Django 2.0

### Author
Борзов Олег
slack: Oleg Borzov (olegborzov)

### Requirements
<ul>
    <li>Python 3</li>
    <li>Django 2.0</li>
    <li>PostgreSQL</li>
</ul>
<b>Python packages</b>:
<ul>
    <li>django-debug-toolbar (on development)</li>
    <li>psycopg2 (on production)</li>
    <li>django-crispy-forms</li>
    <li>django-rest-swagger</li>
    <li>djangorestframework-simplejwt</li>
    <li>Pillow</li>
</ul>

### Run Docker container
```
docker run --rm -it -p 8000:80 ubuntu /bin/bash
```

### Prepare
```
apt-get update
apt-get upgrade
apt-get install -y git
git clone https://github.com/olegborzov/otus_hasker.git
```

### Build
```
cd otus_hasker
make prod
```
