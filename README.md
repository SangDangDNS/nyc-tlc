# NYC Taxi & Limousine Commission  
### Overview
This project will use dataset of [NYC TLC](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) to find meaningful insights from raw data.  
[Yellow Taxi Trip Records](https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2021-01.parquet) (PARQUET) for January 2021.

### Instruction:
#### Ingestion Data
First of all, we need to create a virtual environment for this project by command: `python -m venv .myenv` and then
we activate this enviroment by command: `source .myenv/bin/activate`.  
Add a file `requirements.txt` to install some library/module for the project.
File `requirements.txt`:
```text
pandas
pyarrow
python-dotenv
sqlalchemy
psycopg2
```
We will store sensitive data in file `.env` (Remember that we will ignore this file when upload to cloud)
File `.env`
```text
POSTGRES_USER=sang
POSTGRES_PASSWORD=sang1234
POSTGRES_DB=ny_taxi
url_db="postgresql://sang:sang1234@pgdatabase:5432/ny_taxi"
PGADMIN_DEFAULT_EMAIL=admin@admin.com
PGADMIN_DEFAULT_PASSWORD=root
url="https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2021-01.parquet"
```
Now, we will a `Dockerfile` and a file `docker-compose.yaml` to run 2 images (Postgresql and PgAdmin) and build a images 
`ingestdata`  
File `Dockerfile`:
```text
FROM python:3.11
WORKDIR /app
RUN apt-get install wget
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "ingest_data.py"]
```
File `docker-compose.yaml`:
```text
services:
  pgdatabase:
    image: postgres:13
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    volumes:
      - "./ny_taxi_postgres_data:/var/lib/postgresql/data:rw"
    ports:
      - "5432:5432"
  pgadmin:
    image: dpage/pgadmin4
    environment:
      - PGADMIN_DEFAULT_EMAIL=${PGADMIN_DEFAULT_EMAIL}
      - PGADMIN_DEFAULT_PASSWORD=${PGADMIN_DEFAULT_PASSWORD}
    ports:
      - "8080:80"
  
  ingestdata:
    build:
      context: .
      dockerfile: Dockerfile
    depends_on:
      - pgdatabase
      - pgadmin
```
We add a file `ingest_data.py` to ingest data from NYC_TLC  
File `ingest_data.py`:
```text
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

```
Finally, we run docker-compose by this command: `sudo docker-compose up -d`  
We can connect database by this command: `psql -d ny_taxi -U sang -p 5432 -h localhost`
The result:
```text
(.myenv) (base) sang@sang-desktop:~/Desktop/Learning/Project/nyc-tlc$ psql -d ny_taxi -U sang -p 5432 -h localhost
Password for user sang: 
psql (14.8 (Ubuntu 14.8-0ubuntu0.22.04.1), server 13.11 (Debian 13.11-1.pgdg120+1))
Type "help" for help.

ny_taxi=# \dt
             List of relations
 Schema |       Name        | Type  | Owner 
--------+-------------------+-------+-------
 public | yellow_taxi_trips | table | sang
(1 row)

```
We also connect to PgAdmin, access this url: http://localhost:8080/browser/  
![img.png](imgs%2Fimg.png)  
Enter user: `admin@admin.com` and password: `root`  
Click `Add new server`  
![img_1.png](imgs%2Fimg_1.png)  
![img_2.png](imgs%2Fimg_2.png)  
We have to enter host name as we put in docker-compose file to connect to database: `pgdatabase`, user: `sang`, password: `sang1234`  
![img_3.png](imgs%2Fimg_3.png)  
![img_4.png](imgs%2Fimg_4.png)