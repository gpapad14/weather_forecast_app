# Weather forecast app using Python, Flask, Flask-SocketIO
This microservice allows the user to get the weather forecast of a city using data from an API. 

### Proper use of this code
This code was developed in Python 3.9.13.

1. Clone the git repository in your desired directory of your local unit and set current directory (cd) to the local repository.
2. Upgrade your pip version.
```
python -m pip install --upgrade pip
```
3. Create a virtual environment and activated.
```
pip install virtualenv
mkdir venv
cd venv
python -m venv ./
cd ..
```
4. Install the necessary packages with the specific version they were used for this code.
```
pip install -r requirements.txt
```
5. You are now ready to start the app.
```
python app.py
```
6. Use a browser to experience this application.

The data are downloaded by [Open-Meteo weather forecast API](https://open-meteo.com/en/docs).
