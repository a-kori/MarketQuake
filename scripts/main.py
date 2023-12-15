import sys
from pyspark.sql import SparkSession
from merge_all import merge_stocks_covid
from merge_by_market import merge_by_market

READ = "gs://marketquake_data"
WRITE = "gs://marketquake_results"

# Assign argumetns
stock_column = sys.argv[1]
if sys.argv[2] == 'all':
    stock_markets = ['sp500', 'forbes2000', 'nyse', 'nasdaq']
    analyse = merge_stocks_covid
else:
    stock_markets = [sys.argv[2]]
    analyse = merge_by_market
covid_column = sys.argv[3]
covid_area = (sys.argv[4], sys.argv[5])
sector = sys.argv[6]

# Print arguments
print("========================================================================================")
print(f"Received arguments: stock_column={stock_column}, stock_markets={stock_markets}, covid_column={covid_column}, covid_area={covid_area}, sector={sector}")
print("========================================================================================")

# Initialize Spark session
spark = SparkSession.builder\
    .appName("MarketQuakeAnalysis")\
    .config("spark.driver.memory", "10g") \
    .config("spark.driver.maxResultSize", "5g") \
    .config("spark.executor.memory", "5g") \
    .getOrCreate()
spark.sparkContext.setLogLevel("WARN")

# Start the analysis
analyse(spark, stock_column, stock_markets, covid_column, covid_area, sector, READ, WRITE)

spark.stop()
