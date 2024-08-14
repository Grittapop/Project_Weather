# Project_Weather_S3
## Overview
This project defines an Apache Airflow DAG that fetches weather data from the OpenWeatherMap API for Bangkok, transforms it, and uploads it to an AWS S3 bucket. After successful upload, a notification is sent to a Discord channel. This pipeline is configured to run within Docker containers.

## Components
1. Data Extraction: Retrieves weather data from the OpenWeatherMap API.
2. Data Transformation and Loading: Converts the data to Celsius, creates a CSV file, and uploads it to S3.
3. Notification: Sends a notification to a Discord channel upon successful data upload.

## Prerequisites
- Docker: Ensure Docker is installed on your machine.
- Docker Compose: Ensure Docker Compose is installed for multi-container setups.
- AWS Account: Configure AWS credentials for S3 access.
- Discord: Obtain a Discord webhook URL.

## Architecture

![Weather](https://github.com/user-attachments/assets/11aa8209-5115-4e27-897e-0d954e8eb0a3)

## Setup

1. Clone the Repository
```yaml
git clone https://github.com/Grittapop/Project_Weather_S3.git
```

```yaml
cd Project_Weather_S3
```

2. Configuration
Edit the dags/weather_dag.py file to include your configuration:
- **OpenWeatherMap API Key:** Replace **YOUR_API_KEY** with your actual OpenWeatherMap API key.
- **Discord Webhook URL**: Replace **YOUR_DISCORD_WEBHOOK_URL** with your Discord webhook URL.
- **S3 Credentials:** Update the **aws_access_key_id** and **aws_secret_access_key** with your AWS **IAM** credentials.
- **S3 Bucket Name:** Update the bucket name to your actual bucket.

3. Build and Start Docker Containers
```yaml
docker-compose up -d --build
```

4. Access Airflow UI
Open your web browser and navigate to **http://localhost:8080**.

5. Trigger the DAG
In the Airflow UI, find the **Weather_dag**, and trigger it manually or let it run based on its schedule.

## Troubleshooting
- API Errors: Ensure the API key and URL are correct.
- S3 Upload Issues: Verify AWS credentials and S3 bucket permissions.
- Discord Notifications: Confirm the webhook URL is correct and accessible.

Feel free to modify the instructions and configurations according to your specific setup and requirements.

## References
- [Apache Airflow Docker Compose Documentation](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html)- Learn how to set up and configure Apache Airflow using Docker Compose.
- [OpenWeatherMap Current Weather API Documentation](https://openweathermap.org/current)- Learn how to fetch current weather data using the OpenWeatherMap API




