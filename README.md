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

#### Terraform with Google Cloud Platform
1. What is Terraform?
- open-source tool by HashiCorp, used for provisioning infrastructure resources
- supports DevOps best practices for change management
- Managing configuration files in source control to maintain an ideal provisioning state for testing and production environments
2. What is IaC?
- Infrastructure-as-Code
- build, change, and manage your infrastructure in a safe, consistent, and repeatable way by defining resource configurations that you can version, reuse, and share.
3. Some advantages
- Infrastructure lifecycle management
- Version control commits
- Very useful for stack-based deployments, and with cloud providers such as AWS, GCP, Azure, K8S…
- State-based approach to track resource changes throughout deployments  

**Pre-Requisites**
1. Terraform client installation: https://www.terraform.io/downloads
2. Cloud Provider account: https://console.cloud.google.com/

We will create a project on Google Cloud  
![img_5.png](imgs%2Fimg_5.png)

Then we will create a service account:  
![img_6.png](imgs%2Fimg_6.png)  

Set role for that account:
![img_7.png](imgs%2Fimg_7.png)  

Add new key:
![img_8.png](imgs%2Fimg_8.png)  

It will download a json file
![img_9.png](imgs%2Fimg_9.png)  

Set environment variable to point to our downloaded GCP keys:
```text
export GOOGLE_APPLICATION_CREDENTIALS="<path/to/your/service-account-authkeys>.json"

# Refresh token/session, and verify authentication
gcloud auth application-default login
```
##### Setup for Access
 We will use Google Cloud Storage (GCS) for Data Lake and BigQuery for Data Warehouse.
1. [IAM Roles](https://cloud.google.com/storage/docs/access-control/iam-roles) for Service account:
   * Go to the *IAM* section of *IAM & Admin* https://console.cloud.google.com/iam-admin/iam
   * Click the *Edit principal* icon for your service account.
   * Add these roles in addition to *Viewer* : **Storage Admin** + **Storage Object Admin** + **BigQuery Admin**
   ![img_10.png](imgs%2Fimg_10.png)
2. Enable these APIs for your project:
   * https://console.cloud.google.com/apis/library/iam.googleapis.com
   * https://console.cloud.google.com/apis/library/iamcredentials.googleapis.com
   ![img_11.png](imgs%2Fimg_11.png)
   ![img_12.png](imgs%2Fimg_12.png)
In root directory, create a folder `terraform` with 2 files `main.tf` and `variables.tf`
File `main.tf`:
```text
terraform {
  required_version = ">= 1.0"
  backend "local" {}  # Can change from "local" to "gcs" (for google) or "s3" (for aws), if you would like to preserve your tf-state online
  required_providers {
    google = {
      source  = "hashicorp/google"
    }
  }
}

provider "google" {
  project = var.project
  region = var.region
  // credentials = file(var.credentials)  # Use this if you do not want to set env-var GOOGLE_APPLICATION_CREDENTIALS
}

# Data Lake Bucket
# Ref: https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_bucket
resource "google_storage_bucket" "data-lake-bucket" {
  name          = "${local.data_lake_bucket}_${var.project}" # Concatenating DL bucket & Project name for unique naming
  location      = var.region

  # Optional, but recommended settings:
  storage_class = var.storage_class
  uniform_bucket_level_access = true

  versioning {
    enabled     = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 30  // days
    }
  }

  force_destroy = true
}

# DWH
# Ref: https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/bigquery_dataset
resource "google_bigquery_dataset" "dataset" {
  dataset_id = var.BQ_DATASET
  project    = var.project
  location   = var.region
}
```

File `variables.tf`:
```text
locals {
  data_lake_bucket = "de_data_lake"
}

variable "project" {
  description = "Your GCP Project ID"
}

variable "region" {
  description = "Region for GCP resources. Choose as per your location: https://cloud.google.com/about/locations"
  default = "northamerica-northeast1"
  type = string
}

# Not needed for now
# variable "bucket_name" {
#   description = "The name of the GCS bucket. Must be globally unique."
#   default = ""
# }

variable "storage_class" {
  description = "Storage class type for your bucket. Check official docs for more info."
  default = "STANDARD"
}

variable "BQ_DATASET" {
  description = "BigQuery Dataset that raw data (from GCS) will be written to"
  type = string
  default = "trips_data_all"
}

variable "TABLE_NAME" {
  description = "BigQuery Table"
  type = string
  default = "ny_trips"
}
```
##### Execution steps
1. `terraform init`: 
    * Initializes & configures the backend, installs plugins/providers, & checks out an existing configuration from a version control 
2. `terraform plan`:
    * Matches/previews local changes against a remote state, and proposes an Execution Plan.
3. `terraform apply`: 
    * Asks for approval to the proposed plan, and applies changes to cloud
4. `terraform destroy`
    * Removes your stack from the Cloud

This is the result:
```text
(.myenv) (base) sang@sang-desktop:~/Desktop/Learning/Project/nyc-tlc$ cd terraform/
(.myenv) (base) sang@sang-desktop:~/Desktop/Learning/Project/nyc-tlc/terraform$ terraform init

Initializing the backend...

Successfully configured the backend "local"! Terraform will automatically
use this backend unless the backend configuration changes.

Initializing provider plugins...
- Finding latest version of hashicorp/google...
- Installing hashicorp/google v5.3.0...
- Installed hashicorp/google v5.3.0 (signed by HashiCorp)

Terraform has created a lock file .terraform.lock.hcl to record the provider
selections it made above. Include this file in your version control repository
so that Terraform can guarantee to make the same selections by default when
you run "terraform init" in the future.

Terraform has been successfully initialized!

You may now begin working with Terraform. Try running "terraform plan" to see
any changes that are required for your infrastructure. All Terraform commands
should now work.

If you ever set or change modules or backend configuration for Terraform,
rerun this command to reinitialize your working directory. If you forget, other
commands will detect it and remind you to do so if necessary.
(.myenv) (base) sang@sang-desktop:~/Desktop/Learning/Project/nyc-tlc/terraform$ terraform plan
var.project
  Your GCP Project ID

  Enter a value: lexical-list-403307


Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # google_bigquery_dataset.dataset will be created
  + resource "google_bigquery_dataset" "dataset" {
      + creation_time              = (known after apply)
      + dataset_id                 = "trips_data_all"
      + default_collation          = (known after apply)
      + delete_contents_on_destroy = false
      + effective_labels           = (known after apply)
      + etag                       = (known after apply)
      + id                         = (known after apply)
      + is_case_insensitive        = (known after apply)
      + last_modified_time         = (known after apply)
      + location                   = "northamerica-northeast1"
      + max_time_travel_hours      = (known after apply)
      + project                    = "lexical-list-403307"
      + self_link                  = (known after apply)
      + storage_billing_model      = (known after apply)
      + terraform_labels           = (known after apply)
    }

  # google_storage_bucket.data-lake-bucket will be created
  + resource "google_storage_bucket" "data-lake-bucket" {
      + effective_labels            = (known after apply)
      + force_destroy               = true
      + id                          = (known after apply)
      + location                    = "NORTHAMERICA-NORTHEAST1"
      + name                        = "de_data_lake_lexical-list-403307"
      + project                     = (known after apply)
      + public_access_prevention    = (known after apply)
      + self_link                   = (known after apply)
      + storage_class               = "STANDARD"
      + terraform_labels            = (known after apply)
      + uniform_bucket_level_access = true
      + url                         = (known after apply)

      + lifecycle_rule {
          + action {
              + type = "Delete"
            }
          + condition {
              + age                   = 30
              + matches_prefix        = []
              + matches_storage_class = []
              + matches_suffix        = []
              + with_state            = (known after apply)
            }
        }

      + versioning {
          + enabled = true
        }
    }

Plan: 2 to add, 0 to change, 0 to destroy.

─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

Note: You didn't use the -out option to save this plan, so Terraform can't guarantee to take exactly these actions if you run "terraform apply" now.
(.myenv) (base) sang@sang-desktop:~/Desktop/Learning/Project/nyc-tlc/terraform$ terraform apply
var.project
  Your GCP Project ID

  Enter a value: lexical-list-403307


Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # google_bigquery_dataset.dataset will be created
  + resource "google_bigquery_dataset" "dataset" {
      + creation_time              = (known after apply)
      + dataset_id                 = "trips_data_all"
      + default_collation          = (known after apply)
      + delete_contents_on_destroy = false
      + effective_labels           = (known after apply)
      + etag                       = (known after apply)
      + id                         = (known after apply)
      + is_case_insensitive        = (known after apply)
      + last_modified_time         = (known after apply)
      + location                   = "northamerica-northeast1"
      + max_time_travel_hours      = (known after apply)
      + project                    = "lexical-list-403307"
      + self_link                  = (known after apply)
      + storage_billing_model      = (known after apply)
      + terraform_labels           = (known after apply)
    }

  # google_storage_bucket.data-lake-bucket will be created
  + resource "google_storage_bucket" "data-lake-bucket" {
      + effective_labels            = (known after apply)
      + force_destroy               = true
      + id                          = (known after apply)
      + location                    = "NORTHAMERICA-NORTHEAST1"
      + name                        = "de_data_lake_lexical-list-403307"
      + project                     = (known after apply)
      + public_access_prevention    = (known after apply)
      + self_link                   = (known after apply)
      + storage_class               = "STANDARD"
      + terraform_labels            = (known after apply)
      + uniform_bucket_level_access = true
      + url                         = (known after apply)

      + lifecycle_rule {
          + action {
              + type = "Delete"
            }
          + condition {
              + age                   = 30
              + matches_prefix        = []
              + matches_storage_class = []
              + matches_suffix        = []
              + with_state            = (known after apply)
            }
        }

      + versioning {
          + enabled = true
        }
    }

Plan: 2 to add, 0 to change, 0 to destroy.

Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes 

google_bigquery_dataset.dataset: Creating...
google_storage_bucket.data-lake-bucket: Creating...
google_bigquery_dataset.dataset: Creation complete after 1s [id=projects/lexical-list-403307/datasets/trips_data_all]
google_storage_bucket.data-lake-bucket: Creation complete after 3s [id=de_data_lake_lexical-list-403307]

Apply complete! Resources: 2 added, 0 changed, 0 destroyed.
(.myenv) (base) sang@sang-desktop:~/Desktop/Learning/Project/nyc-tlc/terraform$ 

```
![img_13.png](imgs%2Fimg_13.png)  
![img_14.png](imgs%2Fimg_14.png)  


