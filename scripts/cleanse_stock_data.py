'''This script merges the Stock Market dataset into 4 Dataframes for each market and cleanses them by 
calculating average prices and total volume for each week between January 2020 and December 2022.
It disregards files with missing information for at least one week.'''

import os, sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, weekofyear, year, avg, sum, to_date, lit

class MissingDataException(Exception):
    pass

def clean_and_group_by_week(file_path):
    '''Groups stock prices and volume by week from January 2020 to December 2022.'''
    # Read the CSV file
    df = spark.read.csv(file_path, header=True, inferSchema=True)
    file_name = file_path[file_path.rfind('/')+1 : -4] 

    # Add 'Name' column to DataFrame
    df = df.withColumn("Name", lit(file_name))

    # Convert Date string to PySpark date type
    df = df.withColumn("Date", to_date(col("Date"), "dd-MM-yyy"))

    # Filter data for relevant period (January 2020 to December 2022)
    df = df.filter((col("Date") >= "2020-01-01") & (col("Date") <= "2022-12-31"))

    # Calculate weekly average prices
    df = df.withColumn("Week", weekofyear("Date"))
    df = df.withColumn("Year", year("Date"))
    df = df.groupBy("Name", "Year", "Week").agg(
        sum("Volume").alias("Volume"),
        avg("Low").alias("Low"),
        avg("High").alias("High"),
        avg("Open").alias("Open"),
        avg("Close").alias("Close"),
        avg("Adjusted Close").alias("Adjusted Close"))
    
    # Check if any column has a null value in any row
    if df.na.drop().count() == df.count():
        return df
    else:
        raise MissingDataException("DataFrame missing information for at least one week.")

# Read folder name from argument
if len(sys.argv) != 2:
    raise Exception("No folder name passed!")
elif len(sys.argv[1]) == 0:
    raise Exception("Empty string passed as folder name!")
folder = sys.argv[1]

# Initialize Spark session
spark = SparkSession.builder \
    .appName("StockDataCleansing") \
    .config("spark.driver.maxResultSize", "8g") \
    .config("spark.executor.memory", "8g") \
    .getOrCreate()
dataset_path = "gs://marketquake_data/stock_market_data"

# Load file paths from GCS bucket
files = [line.strip() for line in os.popen(f'gsutil ls {dataset_path}/{folder}/*.csv')]
final_df = None

# Cleanse and merge dataframes
for file_path in files:
    try:
        df = clean_and_group_by_week(file_path)
        if final_df is None:
            final_df = df
        else:
            final_df = final_df.union(df)
        print(f"File {file_path} processed.")
    except MissingDataException:
        print(f"File {file_path} disregarded due to missing data.")

# Write to GCS
write_path = f"{dataset_path}_clean/{folder}.csv"
print(f"Writing to {write_path} ...")
final_df.write.option("header","true").csv(write_path)

# Stop Spark session
spark.stop()
