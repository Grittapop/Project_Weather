from airflow import DAG
from datetime import timedelta, datetime
from airflow.providers.http.sensors.http import HttpSensor
from airflow.operators.python import PythonOperator
from airflow.contrib.operators.snowflake_operator import SnowflakeOperator
import pandas as pd
import requests
import json
import boto3




# URL
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather?q=Bangkok&appid=d69585a88935d2a759a90a77d406e260"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1211338624939851836/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"



s3_client = boto3.client("s3",
                        aws_access_key_id= 'xxxxxxxxxxxxxxxxxxxxxxxxxxxx',
                        aws_secret_access_key= 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')




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

    csv_data = df_data.to_csv(index=False)
    
    now = datetime.now()
    dt_string = now.strftime("%d%m%Y%H%M%S")
    dt_string = "current_weather_data_portland_" + dt_string
    
    # Upload CSV to S3
    bucket_name = "bucket-weather-data"
    object_key = f"{dt_string}.csv"
    s3_client.put_object(Bucket=bucket_name, Key=object_key, Body=csv_data)
     
    S3_DATA_URL = f"s3://bucket-weather-data/{dt_string}.csv"
    
    return S3_DATA_URL 


def notify_discord():
    data = {"content": "Your pipeline has loaded data into snowflake successfully on  " + datetime.now().strftime('%Y-%m-%d')}    
    response = requests.post(DISCORD_WEBHOOK_URL, json=data)



default_args = {
    "owner": "stellar",
    "depends_on_past": False,
    "start_date": datetime(2024, 2, 9),
    "retries": 2,
    "retry_delay": timedelta(minutes=2)

}
    


with DAG("weather_dag",
        default_args=default_args,
        schedule_interval = "* */6 * * *",
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


        t3 = SnowflakeOperator(
            task_id = "create_snowflake_database",
            snowflake_conn_id = "conn_id_snowflake",           
            sql = """
                    CREATE DATABASE IF NOT EXISTS Project ;
            """
        )


        t4 = SnowflakeOperator(
            task_id = "create_snowflake_schema",
            snowflake_conn_id = "conn_id_snowflake",           
            sql = """
                    CREATE SCHEMA IF NOT EXISTS Weather ;
            """
        )


        t5 = SnowflakeOperator(
            task_id = "create_snowflake_table",
            snowflake_conn_id = "conn_id_snowflake",           
            sql = """
                    CREATE TABLE IF NOT EXISTS Bangkok (
                        "Time of Record" datetime,
                        City varchar(25),
                        Description varchar(25),
                        "Temperature (C)" float,
                        "Feels Like (C)" float,
                        "Minimun Temp (C)" float,
                        "Maximum Temp (C)" float,
                        Pressure integer,
                        Humidty integer,
                        "Wind Speed" float,
                        "Sunrise (Local Time)" datetime,
                        "Sunset (Local Time)" datetime
                    );
            """
        )


        t6 = SnowflakeOperator(
            task_id = "create_snowflake_external_stage",
            snowflake_conn_id = "conn_id_snowflake",           
            sql = """
                    CREATE OR REPLACE STAGE s3_stage
                        URL = "{{ti.xcom_pull("transform_load_weather_data_to_S3")}}"
                        credentials=(aws_key_id='xxxxxxxxxxxxxxxxxxxxxx' aws_secret_key='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx');
                
            """
        )


        t7 = SnowflakeOperator(
            task_id = "create_snowflake_file_format",
            snowflake_conn_id = "conn_id_snowflake",           
            sql = """
                    CREATE OR REPLACE file format csv_format type = 'csv' compression = 'auto' 
                        field_delimiter = ',' record_delimiter = '\n'
                        skip_header = 1 trim_space = false;
                                    
            """
        )


        t8 = SnowflakeOperator(
            task_id = "load_data_into_the_table",
            snowflake_conn_id = "conn_id_snowflake",           
            sql = """
                    COPY INTO Bangkok from @s3_stage file_format=csv_format;

            """
        )


        t9 = PythonOperator(
            task_id= "notify_by_discord",
            python_callable=notify_discord 
        )


t1 >> t2 >> t3 >> t4 >> t5 >> t6 >> t7 >> t8 >> t9
