# Project Local Setup Guide

This document describes how to set up your local development environment using Docker and `uv` (Astral’s fast Python package manager).

---

## 🛠 Prerequisites

1. **Docker Desktop**  
   - Install Docker Desktop by downloading it from [docker.com](https://www.docker.com/get-started/).  
   - For detailed installation instructions, refer to the [Docker documentation](https://docs.docker.com/desktop/).  

2. **UV (Astral)**  
   - UV is a high-performance Python package and environment manager. (https://docs.astral.sh/uv/getting-started/installation/)
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
    login = airflow
    password = airflow
    port = 5432

    ```
    SMTP Connection
    ```
    Connection Id = smtp
    Connection Type = smtp
    Description = smtp for email service
    Host = smtp.gmail.com
    login = shahriar.email01@gmail.com
    password = <<APP Password is being created>>
    port = 587






