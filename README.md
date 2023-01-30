# Calendar Assistant

### Overview
This has support for 2 portals, one for the simple form to set events and other for the chat assistant to set events. I have used the recurrent package to map text to event time to accomplish this task. Using Google's OAuth2 and Calendar APIs, I have first fetched the access tokens which are then later used to set and get user/events info. I have used Flask Python framework for the APIs and interaction with the backend.  2 of the endpoints render an HTML page that use JS to handle the FE logic. The chats for the second portal are stored on a PostgreSQL database accordingly so that they can be fetched appropriately for each user. The recurrent allows us to conveniently parse single as well as recurring events, so I have used that to parse user queries to set events.

I have created a calendar-test.py file to set an event and retrieve that as specified in the requirement doc. I have also mentioned the demo links and setup and running steps below.

### Demos
```
Simple Calendar Assistant
https://drive.google.com/file/d/1PUULJIsOHPAKuVjtbqNHFu8Glsy7VlTX/view

Chat Calendar Assistant
https://drive.google.com/file/d/1vSNkw-Zj6-KxzfLLnDYF--jWWMsmSAvv/view

Calendar-test.py demo
https://drive.google.com/file/d/1a9rP_jEs55XUzcAyBlvFCr5GQIoUpW_E/view
```

### Setup and Run instructions
##### Install:
```
Python 3.10
Flask
```

##### Create an python environment and activate it (use below steps if using virtualenv)
```
virtualenv -p python3 ${env_name}
source ${env_name}/bin/activate
pip install -r requirements.txt
```

#### Install and setup postgresql
```
sudo -iu postgres psql
CREATE DATABASE test;
CREATE USER test WITH PASSWORD 'test';
GRANT ALL PRIVILEGES ON DATABASE test TO test;
```

##### populate .env with your environment variables data and run below commands
```
export $(grep -v '^#' .env | xargs -d '\n')
cd app
python init_db.py
```

##### This will bring up the local server at 127.0.0.1:5000
```
flask run
```

##### Testing the calendar-test.py:
> python calendar-test.py

##### this will ask for required input after user is authenticated and set the event if no conflict is there
##### recurrent package is used to parse time queries, this allows us to set recuuring as well normal events

