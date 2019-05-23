from pyspark.streaming import StreamingContext
from pyspark import SparkConf, SparkContext, Row
from pyspark.sql import SQLContext
from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import *
from datetime import datetime

## CREATE SparkContext sc
conf = (SparkConf()
        .setMaster("local[4]")
        .setAppName("NetworkWordCount")
        .set("spark.executor.memory", "6g"))
sc = SparkContext(conf=conf)
## CREATE SQLContext
sqlContext = SQLContext(sc)

## CREATE SparkSession
spark = SparkSession(sc) \
    .builder \
    .appName("StructuredStreamingTest") \
    .getOrCreate()


def stream_kafka_test():
    global sqlContext, spark

    # spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.11:2.1.1 main_pyspark_streaming_apachelogs_kafka.py


    regex_pattern = '^(\S+) (\S+) (\S+) \[([\w:/]+\s[+\-]\d{4})\] "(\S+) (\S+) (\S+)" (\d{3}) (\d+)'
    def parse_apache_log(df_raw):

      df = df_raw.select(regexp_extract('value', regex_pattern, 1).alias('Host'),
                       regexp_extract('value', regex_pattern, 2).alias('ClientID'),
                       regexp_extract('value', regex_pattern, 3).alias('UserID'),
                       regexp_extract('value', regex_pattern, 4).alias('DateTime'),
                       regexp_extract('value', regex_pattern, 5).alias('Method'),
                       regexp_extract('value', regex_pattern, 6).alias('Endpoint'),
                       regexp_extract('value', regex_pattern, 7).alias('Protocol'),
                       regexp_extract('value', regex_pattern, 8).alias('Response').cast(IntegerType()),
                       regexp_extract('value', regex_pattern, 9).alias('SizeBytes').cast(FloatType()))

      df = df.select([c for c in df.columns if c not in ['ClientID', 'UserID', 'Method']])
      # print('Length of DataFrame: ', df.count())
      return df


    """
    subscribe to kafka topic
    """

    while True:
        print("Kafka streaming running")
        ds0 = spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", "localhost:9092") \
            .option("subscribe", "testlogs") \
            .load()

        # incoming values are in bytes, the next line deserializes the bytes and regular df operations can be applied
        ds0 = ds0.selectExpr("CAST(value AS STRING)", "CAST(timestamp AS STRING)")
        ds1 = parse_apache_log(ds0.select("value"))

        query = ds1.writeStream \
            .format("console") \
            .start()


        query.awaitTermination()


def main():

    stream_kafka_test()


if __name__ == '__main__':
    main()

"""
# Integration with Spark Structured Streaming
http://spark.apache.org/docs/latest/structured-streaming-programming-guide.html
http://spark.apache.org/docs/latest/structured-streaming-kafka-integration.html

"""
