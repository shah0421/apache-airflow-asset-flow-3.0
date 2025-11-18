import os

DAG_SCHEDULE = '@daily'  # runs at midnight UTC
DAG_TAGS = ['weather', 'etl', 'api']

# File paths
DAG_FOLDER = os.path.dirname(os.path.abspath(__file__))
CSV_FILE_PATH = os.path.join(DAG_FOLDER, 'cities.csv')
DB_PATH = './weather_data.db'

# OpenWeatherMap API settings
OPENWEATHER_API_KEY = 'effb6c25b72e632a7b3c713828b06b83'
OPENWEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"
API_TIMEOUT = 10  # seconds
OUTPUT_DATA_PATH = '/opt/airflow/dags/final_output.csv'

# Database configuration
DB_TABLE_NAME = 'weather_data'
CREATE_TABLE = """
DROP TABLE IF EXISTS weather_data;
CREATE TABLE weather_data (
    city TEXT,
    country TEXT,
    population INTEGER,
    temperature REAL,
    weather_description TEXT
)
"""
COLUMN_ORDER = ['city', 'country', 'population', 'temperature', 'weather_description']

# Email notification settings
EMAIL_TO = ['shahriar.email01@gmail.com']
EMAIL_SUBJECT = 'Weather Data Pipeline - Execution Complete'
EMAIL_BODY = """
<h3>Weather Data Pipeline Execution Summary</h3>
<p>The weather data pipeline has completed successfully.</p>
<ul>
    <li><strong>Execution Date: </strong> {execution_date}</li>
</ul>
<p>Weather data has been successfully loaded into the database.</p>
<p><strong>Database Location:</strong> ./weather_data.db</p>
"""

# LOG_LEVEL = 'INFO'

# XCom keys for passing data between tasks
XCOM_CITIES_DATA_KEY = 'cities_data'
XCOM_WEATHER_DATA_KEY = 'weather_data'
XCOM_MERGED_DATA_KEY = 'merged_data'

# How many days do we want to keep the logs
LOG_RETENTION_DAYS = 7

