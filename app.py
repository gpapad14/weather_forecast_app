from flask import Flask, render_template, request
from flask_socketio import SocketIO
from datetime import datetime
from threading import Lock

from mylib.functions import acquireData, plotData, implementSQLdatabase, MLprediction, get_city_from_last_sqlfile, updateSQLdatabase

app = Flask(__name__, static_folder="./templates/static")
socketio = SocketIO(app, cors_allowed_origins='*')

#============================================================================================================

@app.route("/author")
def author():
	return '''This application was developed by Georgios Papadopoulos in March 2023 for Nemeon. 
	If you want to go back to the main page, just erase the word "author" from the url.
	The data are provided for free from the Open-Meteo weather API.'''

#============================================================================================================

@app.route("/")
def weatherHome():
	return render_template('weatherHome.html')
@app.route('/city_forecast', methods = ['POST', 'GET'])
def result():
	output = request.form.to_dict()
	if output=={}:
		return 'No input values have been given. Go back to give proper values, erase the "city_forecast".'
	city, forecast = output['city'], output['forecast']
	if type(city)!=type('string') or type(forecast)!=type('string'):
		return 'The input you have given is not in string form.'
	#print(city)
	
	# Acquire requested data.
	sqlfilename = acquireData(city) # The function, as is, returns the dir/sqlfilename.sqlite
	
	# Retrieve data from dataset and create plot.
	#plotname = plotData(sqlfilename, city, forecast, comment = ' - ' + datetime.now().strftime("%m/%d/%Y %H:%M:%S")) # the comment=datetime goes to the title of the plot as a timestamp.
	plotname = plotData(sqlfilename, city, forecast)

	return render_template('forecast.html', forecastInput = forecast, cityInput = city, plot='./static/weather_forecast.png', now = datetime.now().strftime("%m/%d/%Y %H:%M:%S"), onlytemp=True)

#============================================================================================================

@app.route('/city_forecast+real_feel', methods = ['POST'])
def temperatureMLprediction():
	city, latest_file = get_city_from_last_sqlfile()

	# Download data for apparent temperature, load the original data, and return a join database.
	df = implementSQLdatabase(sqlfilename=latest_file, city=city)
	#print(df.head())
	
	# Create an ML model to predict the apparent temperature and plot the temperature, the apparent temprature and the prediction in one graph.
	plotname = MLprediction(df, city)
	forecast = 'temperature'

	return render_template('forecast.html', forecastInput = forecast, cityInput = city, plot='./static/weather_forecast_feels_like.png', now = datetime.now().strftime("%m/%d/%Y %H:%M:%S"))

#============================================================================================================

thread = None
thread_lock = Lock()
def background_thread():
	while True:
		city, sqlfilename = get_city_from_last_sqlfile()
		#plotname = plotData(filename, city, 'sqlfilename', comment = datetime.now().strftime("%m/%d/%Y %H:%M:%S"))
		#socketio.emit('loop', {'plot': '/static/weather_forecast.png', 'now': datetime.now().strftime("%m/%d/%Y %H:%M:%S")})
		
		updateSQLdatabase() # Update the database, runs in a loop.

		socketio.emit('loop', {'now': datetime.now().strftime("%m/%d/%Y %H:%M:%S")})
		socketio.sleep(300)
		
@socketio.on('connect')
def connect():
	global thread
	with thread_lock:
		if thread is None:
			thread = socketio.start_background_task(background_thread)


if __name__ == "__main__":
	#app.run(debug=True) # Without using socketIO.
	socketio.run(app)
