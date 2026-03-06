# Summary of the Project

This project implements a complete ETL (Extract, Transform, Load) data pipeline that integrates data from multiple sources, including CSV files and external weather APIs. The pipeline performs automated data ingestion, cleansing, and transformation to ensure data consistency and quality.

Using Apache Airflow 3.0 for workflow orchestration, the system processes city population data, resolves encoding issues, removes duplicates, and merges it with real-time weather data retrieved from an API. The cleaned and enriched dataset is then stored in a PostgreSQL database for further analysis.

The pipeline is containerized with Docker, enabling easy local setup and reproducible environments. Once the ETL workflow completes, the system automatically sends email notifications via SMTP to report the status of the job.

This project demonstrates practical implementation of data engineering concepts, including workflow orchestration, automated data pipelines, data cleaning, API integration, and containerized development environments.

# Project Local Setup Guide

This document describes how to set up your local development environment using Docker and `uv`.

---

## 🛠 Prerequisites

1. **Docker Desktop**  
   - Install Docker Desktop by downloading it from [docker.com](https://www.docker.com/get-started/).  
   - For detailed installation instructions, refer to the [Docker documentation](https://docs.docker.com/desktop/).  

2. **UV (Astral)**  
   - UV is a high-performance Python package and environment manager. [UV Installation](https://docs.astral.sh/uv/getting-started/installation/)
   - Install UV by running:  
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```  

   - After installation, verify with:  
     ```bash
     uv --version
     ```

---

## ✅ Local Setup Steps

3. **Create a Virtual Environment**  
    Use `uv` to create a virtual environment with a specific Python version:  
    ```bash
    uv venv --python 3.11
    ```

    Activate virtual environment:
    ```
    source .venv/bin/activate
    ```

    Install dependencies:
    ```
    uv pip install apache-airflow==3.0.0
    uv pip install pandas
    uv pip install apache-airflow-providers-postgres
    ```

---

## ✅ **Run the Application / Server**

    Start your Docker-based services (e.g., Airflow) by running:
    ```
    docker compose up
    ```

---

## ✅ **Create Connections**

    From airflow UI, click "Admin" >> "Connections" >> "Add Connection"
    ```
    Postgres Connection
    ```
    Connection Id = postgres
    Connection Type = postgres
    Description = This is airflow Database
    Host = postgres
    login = your_login
    password = your_password
    port = 5432

    ```
    SMTP Connection
    ```
    Connection Id = smtp
    Connection Type = smtp
    Description = smtp for email service
    Host = smtp.gmail.com
    login = shahriar.email01@gmail.com
    password = rfqw chwq zgvx wcjw
    port = 587



<img src="images/Screenshot 2025-11-18 at 2.21.20 PM.png" alt ="App homepage" width="400"/>
<img src="images/Screenshot 2025-11-18 at 2.22.13 PM.png" alt ="App homepage" width="400"/>

---


## ✅  **Data Cleansing**

* The initial CSV contains 60 city records.

* After removing duplicates, 59 unique cities remain.

* One city name contained a text-encoding issue ("SÃ£o Paulo"), which was corrected to "São Paulo".

* Four records had commas inside the population column, which caused the CSV to interpret the values as multiple columns. These columns were recombined to correctly form the population value for each affected city.

* One city, Bishkek, KY, did not return any weather data from the API.

* After merging the cleaned population data (CSV) with the weather data (API), the final dataset contains 58 cities.

* During the merge, only the following fields were retained:
  city, country, population, temperature, weather_description.
  All other fields were dropped for consistency.

* These 58 cleaned and enriched records are stored in the PostgreSQL database.

## ✅  **Materialize Airflow Assets**

First you need to click on the asset tab on the left pane and click on any asset to see the diagram and then click on the toggle buttons in the diagram to activate all the assets.

<img src="images/Screenshot 2025-11-18 at 2.20.09 PM.png" alt ="App homepage" width="400"/>

---

You can materialize airflow assets either from UI (Selecting the asset tab choosing the asset and clicking Trigger button from the top right)

<img src="images/Screenshot 2025-11-18 at 2.18.21 PM.png" alt ="App homepage" width="400"/>
<img src="images/Screenshot 2025-11-18 at 2.20.35 PM.png" alt ="App homepage" width="400"/>

---

or from docker desktop in Containers section, click airflow-scheduler then click Exec tab then:
type /bin/bash 
execute command: airflow dags trigger load_csv_file

<img src="images/Screenshot 2025-11-18 at 3.10.20 PM.png" alt ="App homepage" width="400"/>
<img src="images/Screenshot 2025-11-18 at 3.09.44 PM.png" alt ="App homepage" width="400"/>

---

## ✅  **Data Stored and Email Sample**

<img src="images/Screenshot 2025-11-18 at 5.08.34 PM.png" alt ="App homepage" width="400"/>
<img src="images/Screenshot 2025-11-18 at 6.04.30 PM.png" alt ="App homepage" width="400"/>

---

