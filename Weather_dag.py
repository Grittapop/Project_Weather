from airflow import DAG
from datetime import timedelta, datetime
from airflow.providers.http.sensors.http import HttpSensor
from airflow.operators.python import PythonOperator
import pandas as pd
import requests
import json

# URL
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather?q=Bangkok&appid=d69585a88935d2a759a90a77d406e260"



def kelvin_to_celsius(temp_in_kelvin): 
    temp_in_celsius = temp_in_kelvin - 273.15
    return temp_in_celsius



def transform_load_data():
    r = requests.get(WEATHER_API_URL)
    data = r.json()
   
    city = data["name"]
    weather_description = data["weather"][0]['description']
    temp_celsius = kelvin_to_celsius(data["main"]["temp"])
    feels_like_celsius= kelvin_to_celsius(data["main"]["feels_like"])
    min_temp_celsius = kelvin_to_celsius(data["main"]["temp_min"])
    max_temp_celsius= kelvin_to_celsius(data["main"]["temp_max"])
    pressure = data["main"]["pressure"]
    humidity = data["main"]["humidity"]
    wind_speed = data["wind"]["speed"]
    time_of_record = datetime.utcfromtimestamp(data["dt"] + data["timezone"])
    sunrise_time = datetime.utcfromtimestamp(data["sys"]["sunrise"] + data["timezone"])
    sunset_time = datetime.utcfromtimestamp(data["sys"]["sunset"] + data["timezone"])

    transformed_data = {"Time of Record": time_of_record,
                        "City": city,
                        "Description": weather_description,
                        "Temperature (C)": temp_celsius,
                        "Feels Like (C)": feels_like_celsius,
                        "Minimun Temp (C)":min_temp_celsius,
                        "Maximum Temp (C)": max_temp_celsius,
                        "Pressure": pressure,
                        "Humidty": humidity,
                        "Wind Speed": wind_speed,
                        "Sunrise (Local Time)":sunrise_time,
                        "Sunset (Local Time)": sunset_time                        
                        }
    
    transformed_data_list = [transformed_data]
    df_data = pd.DataFrame(transformed_data_list)
    
    now = datetime.now()
    dt_string = now.strftime("%d%m%Y%H%M%S")
    dt_string = "current_weather_data_portland_" + dt_string
    
    df_data.to_csv(f"s3://bucket-weather-data/Bangkok/Data/{dt_string}.csv", index=False,)

    
    

default_args = {
    "owner": "stellar",
    "depends_on_past": False,
    "start_date": datetime(2024, 2, 9),
    "retries": 2,
    "retry_delay": timedelta(minutes=2)

}
    


with DAG("weather_dag",
        default_args=default_args,
        schedule_interval = "*/30 * * * *",
        catchup=False) as dag:


        t1 = HttpSensor(
            task_id ="weather_api_ready",
            http_conn_id="weather_conn_id",
            endpoint="/data/2.5/weather?q=Bangkok&appid=d69585a88935d2a759a90a77d406e260"
        
        )




        t2 = PythonOperator(
            task_id= "transform_load_weather_data_to_S3",
            python_callable=transform_load_data
        
        )


t1 >> t2
