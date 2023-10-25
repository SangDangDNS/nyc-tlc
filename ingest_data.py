import os
from time import time
from dotenv import load_dotenv

# Load the environment variables from .env file
load_dotenv()

import pandas as pd
from sqlalchemy import create_engine


def ingest():
    # the backup files are gzipped, and it's important to keep the correct extension
    # for pandas to be able to open the file
    url = os.getenv("url")
    url_db = os.getenv("url_db")
    table_name = "yellow_taxi_trips"

    if url.endswith('.csv.gz'):
        file_name = 'output.csv.gz'
    elif url.endswith('.parquet'):
        file_name = 'output.parquet'
    else:
        file_name = 'output.csv'

    os.system(f"wget {url} -O {file_name}")

    engine = create_engine(url_db)

    if url.endswith('.parquet'):
        df = pd.read_parquet(file_name)
        file_name = 'output.csv.gz'
        df.to_csv(file_name, index=False, compression="gzip")

    df_iter = pd.read_csv(file_name, iterator=True, chunksize=100000)

    df.head(n=0).to_sql(name=table_name, con=engine, if_exists='replace')

    while True:

        try:
            t_start = time()

            df = next(df_iter)

            df.tpep_pickup_datetime = pd.to_datetime(df.tpep_pickup_datetime)
            df.tpep_dropoff_datetime = pd.to_datetime(df.tpep_dropoff_datetime)

            df.to_sql(name=table_name, con=engine, if_exists='append')

            t_end = time()

            print('inserted another chunk, took %.3f second' % (t_end - t_start))

        except StopIteration:
            print("Finished ingesting data into the postgres database")
            break


if __name__ == '__main__':
    ingest()
