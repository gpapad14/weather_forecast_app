import matplotlib.pyplot as plt
plt.switch_backend('agg')
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import os
import glob
import requests
import json
import pandas as pd
import datetime
import sqlite3
from sklearn.linear_model import LinearRegression

cities = ['Paris', 'Brussels', 'London', 'Lisbon', 'Athens']
citycoord={	'Paris': 	['48.85', '2.35'], 
			'Brussels': ['50.85', '4.35'], 
			'London': 	['51.51', '-0.13'], 
			'Lisbon': 	['38.72', '-9.13'], 
			'Athens': 	['37.98', '23.73']} 
# Originally, all data are in GMT+0 timezone (London, Lisbon), and the data should be converted to the local timezone.
timezone = {'Paris': +1, 'Brussels': +1, 'London': +0, 'Lisbon': +0, 'Athens': +2}

#============================================================================================================

def acquireData(city = '', save_to_file = True):
	
	# Get data from API. 
	# Weather data from 3 days before to 3 days after the current date taken hourly, given location coordinates.
	webAPI = 'https://api.open-meteo.com/v1/forecast?' + f'latitude={citycoord[city][0]}&longitude={citycoord[city][1]}&hourly='+'temperature_2m,relativehumidity_2m,precipitation_probability,windspeed_10m&'+'temperature_unit=fahrenheit&past_days=3&forecast_days=3'
	response_API = requests.get(webAPI)
	json_data = response_API.json()
	response_API.close()

	columns = list(json_data['hourly'].keys()) # temperature is F, rel. hum. in %, precipitation in %, windspeed in km/h
	#Ndata = len(json_data['hourly']['time'])

	# Pass data into a dictionary as lists.
	dataNEW = {}
	for icolumn in columns:
		dataNEW[icolumn] = json_data['hourly'][icolumn]

		# Convert the data into the local timezone of the requested city.
		if timezone[city]!=0:
			if icolumn == 'time':
				dataNEW['time'] = dataNEW['time'][timezone[city]:]
			else:
				dataNEW[icolumn] = dataNEW[icolumn][:-timezone[city]]

	# Check that the conversion to local timezone left the data with the same length (not the same as before, but the same with each other).
	if len(dataNEW['time']) != len(dataNEW['temperature_2m']):
		print('ERROR! The data do not have the same length.')

	# Convert the temperature units from Fahrenheit to Celsius
	dataNEW['temperature_2m'] = [ round((i - 32)/1.8, 2) for i in dataNEW['temperature_2m'] ]

	# Convert the json file data into an SQL database.
	df = pd.DataFrame(dataNEW)
	#print(df)
	if save_to_file:
		# Make sure that the new database will not overwrite any older file.
		i = 1
		name = './forecasts/' + city + f'_forecast_{str(i)}.sqlite'
		while os.path.isfile(name):
			i += 1
			name = './forecasts/' + city + f'_forecast_{str(i)}.sqlite'
		# Create .sqlite file.
		connect = sqlite3.connect(name)
		c = connect.cursor()
		df.to_sql(city+'_forecast', connect)
		connect.close()
		return name
	else:
		return df

#============================================================================================================

def plotData(name, city, forecast, comment = '', save = True):
	# Give the real name of the sql attributes (hardcoded).
	forecastCode = {'temperature': 'temperature_2m',  
					'relative humidity': 'relativehumidity_2m',
					'precipitation': 'precipitation_probability',
					'wind speed': 'windspeed_10m'}
	units ={'temperature': '($^\circ$C)',  
			'relative humidity': '(%)',
			'precipitation': '(%)',
			'wind speed': '(km/h)'}

	# Read the database and put the requested data in lists.
	connect = sqlite3.connect(name)
	cur = connect.cursor()
	query = f'SELECT time, {forecastCode[forecast]} FROM ' + city+'_forecast'
	data = pd.read_sql(query, con=connect)
	connect.close()
	xtime = [datetime.datetime.strptime(i, '%Y-%m-%dT%H:%M') for i in data['time']]
	y     = [i for i in data[forecastCode[forecast]]]
	
	# Safety check
	if len(xtime) != len(y):
		print('ERROR! There is some issue with the length of the data to be plotted.')
	
	# Choose to present the data from the current moment and later. The older data will be used for another purpose.
	now = datetime.datetime.strptime(datetime.datetime.now().strftime("%Y-%m-%dT%H:%M"), '%Y-%m-%dT%H:%M')
	cut = 0
	while now > xtime[cut]:
		cut+=1
	
	# Create the plot.
	fig = Figure()
	axis = fig.add_subplot(1, 1, 1)
	axis.plot(xtime[cut-3:], y[cut-3:], linestyle='-') # Arbitrarily (3) chose to show some of the recent data of a few hours ago.
	axis.set_xlabel(city + ' (local time)')
	axis.set_ylabel(forecast+' '+units[forecast])
	axis.set_title(city+comment)
	axis.grid()
	# Datetime axis: only major lines when the day changes.
	axis.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
	axis.xaxis.set_major_locator(mdates.DayLocator())
	fig.autofmt_xdate()

	plotname = './templates/static/weather_forecast.png'
	if save:
		fig.savefig(plotname)
	plt.close()
	print('  >>> A new forecast plot (weather_forecast.png) was created.')
	return plotname

#============================================================================================================

# Find the last created forecast sql file and get also the name of the city.
def get_city_from_last_sqlfile():
	list_of_files = glob.glob('./forecasts/*') # * means all if need specific format then *.csv
	latest_file = max(list_of_files, key=os.path.getctime)
	#print(latest_file)

	city=''
	for icity in cities:
		if icity in latest_file: city = icity
	#print('  >>> City:', city)
	return city, latest_file

#============================================================================================================

def implementSQLdatabase(sqlfilename='', city='', newforecast='apparent_temperature', update_table=False):
	webAPI = 'https://api.open-meteo.com/v1/forecast?' + f'latitude={citycoord[city][0]}&longitude={citycoord[city][1]}&hourly={newforecast}&past_days=7&forecast_days=3'
	
	# Download the new data from API.
	response_API = requests.get(webAPI)
	json_data = response_API.json()
	response_API.close()
	df = pd.DataFrame.from_dict(json_data['hourly']) # The apparent temperature is acquired directly in Celsius degrees.

	# Correct time at local timezone.	
	#print(df)
	dfNEW = pd.DataFrame()
	if timezone[city]!=0:
		dfNEW['time'] = list(df['time'][timezone[city]:])
		dfNEW['apparent_temperature'] = list(df['apparent_temperature'][:-timezone[city]])
	else:
		dfNEW = df
	#print(dfNEW, '\n')
	#print(dfNEW.head(), '\n')
	if len(dfNEW['time']) != len(dfNEW['apparent_temperature']):
		return 'ERROR! There was something wrong with the local timezone correction.'

	# Get previous data from existing file.
	connect = sqlite3.connect(sqlfilename)
	cursor = connect.cursor()
	query = f'SELECT * FROM ' + city+'_forecast'
	dfBase = pd.read_sql(query, con=connect)
	#print(dfBase, '\n')

	# Add new data as a table in the original database
	apptemp_table = 'Apparent_Temperature_Table'
	try:
		if update_table:
			cursor.execute(f'DROP TABLE {apptemp_table}')
		dfNEW.to_sql(apptemp_table, connect)
		print('  >>> The new table containing the apparent temperature data is created in the database.')
	except:
		print('  >>> The apparent temperature table already exist in the database.')

	#-----------------------------------------------------------------------------
	tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", connect)
	#print('The tables in the database are:', tables)
	#-----------------------------------------------------------------------------
	# Merge the new table with the original one (inner join, on "time").
	# Joining based on the time data makes sure that only the overlapped data will remain in the dataset.
	dfjoin = pd.merge(left = dfBase, right = dfNEW, how = 'inner', on = 'time')
	#print(dfjoin)
	connect.close()
	# Return the joined table.
	return dfjoin

#============================================================================================================

def MLprediction(df, city):
	""" This ML model will predict the apparent temperature (real feel), using the data for temperature, humidity, precipitation, and wind."""
	# The joined table is given as input in this function.
	#print(df.head())
	# Choose to present the data from the current moment and later. The past data will be used for another purpose.
	xtime  = [datetime.datetime.strptime(i, '%Y-%m-%dT%H:%M') for i in df['time']]
	now = datetime.datetime.strptime(datetime.datetime.now().strftime("%Y-%m-%dT%H:%M"), '%Y-%m-%dT%H:%M')
	cut = 0
	while now > xtime[cut]:
		cut+=1

	x_feats = df.iloc[:,[1,2,3,4,5]] # time, temperature, humidity, precipitation, and wind attributes 
	#print(x_feats.head())
	x_feats['time'] = pd.to_datetime(x_feats['time']).astype('int64')/ 10**9 # Convert the datetime in int [unit = seconds].
	y_target = df.iloc[:,6] # apparent temperature column
	#print(y_target.head())
	
	X_train = x_feats[:cut]
	y_train = y_target[:cut]
	X_test = x_feats[cut:]
	y_test = y_target[cut:]

	estimator = LinearRegression() 
	estimator.fit(X_train, y_train)
	prediction = estimator.predict(X_test)

	if len(prediction)!=len(y_test):
		print('Error! The predicted dataset does not have the expected length. Prediction =', len(prediciton), ', expected =', len(y_test))

	# Create the plot.
	# Arbitrarily chose to show date for 3 hours ago (recent past) with [cut-3]
	plt.plot(xtime[cut-3:], df.iloc[:,2][cut-3:], linestyle='-', marker='o', label='temperature') # Arbitrarily (3) chose to show some of the recent data of a few hours ago.
	plt.plot(xtime[cut-3:], y_target[cut-3:], linestyle='-', marker='o', label='real feel') # Arbitrarily (3) chose to show some of the recent data of a few hours ago.
	plt.plot(xtime[cut:], prediction, label='real feel ML prediction')
	plt.plot([xtime[cut], xtime[cut]], [min(y_target),max(y_target)], linestyle='--', label='now')
	plt.xlabel(city + ' (local time)')
	plt.ylabel('temperature ($^\circ$C)')
	plt.title(city)
	plt.grid()
	plt.legend()
	# Datetime axis: only major lines when the day changes.
	plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
	plt.gca().xaxis.set_major_locator(mdates.DayLocator())
	plt.gcf().autofmt_xdate()
	
	#plt.show()
	plotname = './templates/static/weather_forecast_feels_like.png'
	plt.savefig(plotname)
	plt.close()

	return plotname

#============================================================================================================

def updateSQLdatabase(city='', sqlfilename='', overwrite = False):
	city, sqlfilename = get_city_from_last_sqlfile() 
	print('  >>> Updating', sqlfilename)
	df = acquireData(city, save_to_file=False) # Download new data to update your database.
	# Get previous data from existing file.
	connect = sqlite3.connect(sqlfilename)
	cursor = connect.cursor()
	query = f'SELECT * FROM ' + city+'_forecast'
	dfBase = pd.read_sql(query, con=connect)
	
	#print(dfBase.iloc[:,1:], '\n')
	#print(df, '\n')
	a = pd.merge(dfBase.iloc[:,1:],df, how='outer') # The outer join will have dublicates in 'time' from the two datasets.
	df_updated = a.drop_duplicates(subset=['time'], keep='last') # I remove the dublicates and by "keeping the last", I make sure I keep the most updated values, because the updated dataset is used second in the merging.
	#print(df_updated, '\n')

	cursor.execute(f'DELETE FROM {city}_forecast;',);
	connect.commit()

	df_updated.to_sql(city+'_forecast', connect, if_exists='replace')

	connect.close()