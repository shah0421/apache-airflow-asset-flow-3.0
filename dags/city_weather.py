from airflow.sdk import asset, Asset, Context, dag, task
import logging
import pandas as pd
from airflow.providers.postgres.hooks.postgres import PostgresHook
import os
import airflow.settings
from airflow.utils.email import send_email
from datetime import datetime
logger = logging.getLogger(__name__)

from config import (
    DAG_SCHEDULE,
    CSV_FILE_PATH,
    OPENWEATHER_API_KEY,
    OPENWEATHER_API_URL,
    API_TIMEOUT,
    OUTPUT_DATA_PATH,
    DB_PATH,
    DB_TABLE_NAME,
    XCOM_CITIES_DATA_KEY,
    XCOM_WEATHER_DATA_KEY,
    XCOM_MERGED_DATA_KEY,
    CREATE_TABLE,
    COLUMN_ORDER,
    LOG_RETENTION_DAYS,
    EMAIL_TO,
    EMAIL_SUBJECT,
    EMAIL_BODY,
)

from weather_client import OpenWeatherMapClient

@asset(
    schedule=DAG_SCHEDULE,
)
def load_csv_file(self, context: Context) -> dict[str]:
    """Load city data from CSV and pass to next task via XCom"""
    try:
        logger.info(f"Loading CSV file from: {CSV_FILE_PATH}")
        df = pd.read_csv(CSV_FILE_PATH, header=0, dtype=str)

        # Clean up any whitespace in city/country names
        df['city'] = df['city'].str.strip()
        df['country'] = df['country'].str.strip()

        # Fix UTF-8 encoding errors
        df['city'] = df['city'].str.replace("SÃ£o Paulo", "São Paulo")

        # Combine population columns if split across multiple.
        # Concatenating any additional population columns
        # get all columns except city and country
        population_columns = [col for col in df.columns if col.startswith("population") or col not in ("city", "country")]

        # convert all population column values to strings, fill missing values, and then concatenate all their values into one string per row
        df['population'] = (df[population_columns].astype(str).fillna("").apply(lambda x: "".join(x), axis=1))
        # Fix population formatting
        df["population"] = (
            df["population"].str.replace(" ", "", regex=False)
            .str.replace(",", "", regex=False)
            .str.replace(".", "", regex=False)
        )

        # Convert to integer
        df["population"] = pd.to_numeric(df["population"], errors="coerce")

        logger.info(f"Successfully loaded {len(df)} cities from CSV")
        
        # Getting rid of duplicates
        df_distinct = df.drop_duplicates(subset=['city', 'country'])
               
        logger.info(f"After removing dups length of df: {len(df_distinct)}")

        # Converting DF to list of dictionaries
        cities_data = df_distinct.to_dict('records')

        # storing cities_data
        ti = context['ti']
        ti.xcom_push(key=XCOM_CITIES_DATA_KEY, value=cities_data)
        

        return f"Loaded {len(df_distinct)} cities successfully"

    except FileNotFoundError:
        logger.error(f"CSV file not found at: {CSV_FILE_PATH}")
        raise
    except Exception as e:
        logger.error(f"Error loading CSV file: {str(e)}")
        raise


@asset(
        schedule=load_csv_file,      
)

def call_weather_api(load_csv_file: Asset, context: Context):
    """Fetch current weather data for each city from OpenWeatherMap API"""
    try:
        logger.info('calling context to pull cities_data from previous asset')
        cities_data = context['ti'].xcom_pull(
            dag_id=load_csv_file.name, 
            key=XCOM_CITIES_DATA_KEY, 
            task_ids=load_csv_file.name, 
            include_prior_dates=True
        )
        logger.info('printing first record of cities_data: ', cities_data[0])
        logger.info(f"cities_data_len: {len(cities_data)}")
        
        if not cities_data:
            raise ValueError("No cities data found in XCom")

        # Initialize weather client
        client = OpenWeatherMapClient(
            api_key=OPENWEATHER_API_KEY,
            api_url=OPENWEATHER_API_URL,
            timeout=API_TIMEOUT,
        )

        # Fetch weather data for all cities
        weather_data, failed_cities = client.get_weather_bulk(cities_data)

        # Pass data to next task
        ti = context['ti']
        ti.xcom_push(key=XCOM_WEATHER_DATA_KEY, value=weather_data)
        ti.xcom_push(key='failed_cities', value=failed_cities)

        return f"Retrieved weather data for {len(weather_data)} cities"

    except Exception as e:
        logger.error(f"Error calling weather API: {str(e)}")
        raise

@asset(
        schedule=call_weather_api,      
)

def merge_data(call_weather_api: Asset, context: Context):
    """Combine city info with weather data into a single dataset"""
    try:
        ti = context['ti']
        cities_data = ti.xcom_pull(
            dag_id=load_csv_file.name, 
            key=XCOM_CITIES_DATA_KEY, 
            task_ids=load_csv_file.name, 
            include_prior_dates=True
        )
        weather_data = ti.xcom_pull(
            dag_id=call_weather_api.name, 
            key=XCOM_WEATHER_DATA_KEY, 
            task_ids=call_weather_api.name, 
            include_prior_dates=True
        )

        if not cities_data or not weather_data:
            raise ValueError("Missing data for merge operation")
        
        logger.info(f"number of cities in CSV {len(cities_data)}")
        logger.info(f"number of cities weather from API {len(weather_data)}")
        logger.info("Merging city data with weather data")

        df_cities = pd.DataFrame(cities_data)
        df_weather = pd.DataFrame(weather_data)

        # Inner join to only keep cities where we got weather data
        merged_df = pd.merge(df_cities, df_weather, on=['city', 'country'], how='inner')
        
        logger.info(f"number of cities after merging {len(merged_df)}")

        # Reorder columns for better readability
        merged_df = merged_df[COLUMN_ORDER]
        
        logger.info(f"first 5 records of merged data {merged_df.head(5)}")

        merged_data = merged_df.to_dict('records')
        
        # Pass data to next task
        ti.xcom_push(key=XCOM_MERGED_DATA_KEY, value=merged_data)

        return f"Merged {len(merged_df)} records successfully"

    except Exception as e:
        logger.error(f"Error merging data: {str(e)}")
        raise

@asset(
        schedule=merge_data,      
)

def load_to_database(merge_data: Asset, context: Context):
    """Write the merged dataset to postgres database"""
    try:
        ti = context['ti']
        merged_data = ti.xcom_pull(
            dag_id=merge_data.name, 
            key=XCOM_MERGED_DATA_KEY, 
            task_ids=merge_data.name, 
            include_prior_dates=True
        )

        if not merged_data:
            raise ValueError("No merged data found for database loading")

        logger.info(f"Loading {len(merged_data)} records to database: {DB_PATH}")
        df = pd.DataFrame(merged_data)
        
        ordered_df = df[COLUMN_ORDER]

        # Instantiate the hook with the connection ID defined in the Airflow UI
        hook = PostgresHook(postgres_conn_id='postgres') 
        
        # Get the actual connection object from the hook
        conn = hook.get_conn()
        
        # To use the connection and cursor
        cursor = conn.cursor()

        try:
            # # Droping and Creating table, assuming versioning is not required.
            hook.run(CREATE_TABLE)

            # # Converting DF into Numpy structured array
            rows = ordered_df.to_records(index=False).tolist()

            # # inserting into postgres table. This way of bulk inserting is very efficient for large DataFrames
            hook.insert_rows(
                table = DB_TABLE_NAME,
                rows=rows,
                commit_every=1000,
            )

            # Verify the load worked
            logger.info(f"executing........ SELECT COUNT(*) FROM PUBLIC.{DB_TABLE_NAME}")
            cursor.execute(f"SELECT COUNT(*) FROM PUBLIC.{DB_TABLE_NAME}")
            count = cursor.fetchone()[0]
            logger.info(f"Total records in {DB_TABLE_NAME}: {count}")
            
            # getting the stored data into a dataframe and saving to CSV for validation
            cursor.execute(f"SELECT * FROM PUBLIC.{DB_TABLE_NAME}")           
            rows = cursor.fetchall()
            cols = [desc[0] for desc in cursor.description]
            pd.DataFrame(rows, columns=cols).to_csv(OUTPUT_DATA_PATH, index=False)

            logger.info("First 5 records in the database:")
            for row in rows[:5]:
                logger.info(row)
            
            logger.info(f"Successfully loaded {count} records to database")
            ti.xcom_push(key='db_path', value=DB_PATH)

            return f"Loaded {count} records to database successfully"

        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        logger.error(f"Error loading data to database: {str(e)}")
        raise

@asset(
        schedule=load_to_database,      
)

def cleanup_operations(call_weather_api: Asset, context:Context):
    """Clean up temporary files and log final status"""
    try:
        logger.info("Starting cleanup operations")
        
        ti = context['ti']
        failed_cities = ti.xcom_pull(
            dag_id=call_weather_api.name, 
            key='failed_cities', 
            task_ids=call_weather_api.name, 
            include_prior_dates=True
        )

        # The base folder where Airflow writes its logs (from airflow.cfg)
        BASE_LOG_FOLDER = airflow.settings.conf.get("logging", "base_log_folder")
        print('BASE_LOG_FOLDER: ', BASE_LOG_FOLDER)
        
        def cleanup_logs():
            """Function that deletes old log files and empty dirs."""
            # Deleting log files older than LOG_RETENTION_DAYS
            cmd_files = (
                f"find {BASE_LOG_FOLDER} -type f -mtime +{LOG_RETENTION_DAYS} "
                f"-name '*.log' -exec rm -f {{}} +"
            )
            os.system(cmd_files)

            # deleting empty directories
            cmd_dirs = f"find {BASE_LOG_FOLDER} -type d -empty -mindepth 1 -delete"
            os.system(cmd_dirs)

            logger.info(f"Cleaned logs older than {LOG_RETENTION_DAYS} days in {BASE_LOG_FOLDER}")
        
        cleanup_logs()

        if failed_cities:
            logger.warning(f"Cleanup complete. Note: {len(failed_cities)} cities failed")
            logger.warning(f"Cleanup complete. cities that have failed: {failed_cities}")
        else:
            logger.info("Cleanup complete. All operations successful.")

        return "Cleanup operations completed successfully"

    except Exception as e:
        # Don't fail the whole pipeline just because cleanup had issues
        logger.error(f"Error during cleanup: {str(e)}")
        return f"Cleanup completed with warnings: {str(e)}"
        

@asset(
    schedule=cleanup_operations,
)
def send_email_notification():
    try:
        execution_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        html_content = EMAIL_BODY.format(execution_date=execution_date)
        send_email(
            to=EMAIL_TO,
            subject=EMAIL_SUBJECT,
            html_content=html_content,
            conn_id="smtp",
        )

        logger.info("Notification email successfully sent.")
        return "Notification email for pipeline completion sent"

    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return f"EMAIL sent with warnings: {e}"
    
# In Airflow 3.0.0 asset-based workflows, dependencies are inferred automatically from function arguments 
# Just for visual understanding here is an example of how it used to be in older airflow version
# load_csv_file >> call_weather_api >> merge_data >> load_to_database >> cleanup_operations >> send_email_notification
