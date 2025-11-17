# Project Local Setup Guide

This document describes how to set up your local development environment using Docker and `uv` (Astral’s fast Python package manager).

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
     :contentReference[oaicite:1]{index=1}  
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
4. **Run the Application / Server**

    Start your Docker-based services (e.g., Airflow) by running:
    ```
    docker compose up
    ```

5. **Create Connections**

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
    password = <<"APP Password is being created">>
    port = 587




## **Findings**

* The initial CSV contains 60 city records.

* After removing duplicates, 59 unique cities remain.

* Four records had commas inside the population column, which caused the CSV to interpret the values as multiple columns. These columns were recombined to correctly form the population value for each affected city.

* One city name contained a text-encoding issue ("SÃ£o Paulo"), which was corrected to "São Paulo".

* One city, Bishkek, KY, did not return any weather data from the API.

* After merging the cleaned population data (CSV) with the weather data (API), the final dataset contains 58 cities.

* During the merge, only the following fields were retained:
  city, country, population, temperature, weather_description.
  All other fields were dropped for consistency.

* These 58 cleaned and enriched records are stored in the PostgreSQL database.
