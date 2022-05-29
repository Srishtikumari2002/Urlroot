# Urlroot

Urlroot is a free url shortener.

## Features

* Url preview before redirect
* Long url security details on the preview page
* Warns the user if long url is insecure
* Creator of the short url can write custom message for the users.
* Face authorization for staff and admin.
* custom backhalf

## Demo
You can try the web app at [urlroot.herokuapp.com](https://urlroot.herokuapp.com)
If you create staff account you can login to admin site but can view or edit can information. If you want to change this behaviour then do local setup.
## Local Setup
* clone the github repo to your machine
* using virtual environment is recommended
* run ```pip install -r requirements.txt```
* create .env file in Urlroot folder
* add all the environment variables (you can use sqlite database while in development)
* run ``` python manage.py makemigrations```
* ```python manage.py migrate```
* ```python manage.py runserver```
* now create new staff account with your face and then login
* don't forget to replace azure api and endpoints for face api
 
## Tech Stack

* Django
* Microsoft Azure face api :- for face authorization
* Google Safe Browsing api :- for security check of urls
* Vs code
* Heroku

## Requirements

* Latest Browser (any)
* Any Device with camera
* Proper internet connection
* Proper lighting
