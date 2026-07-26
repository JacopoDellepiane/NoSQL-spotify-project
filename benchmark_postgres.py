import psycopg2
import time

# configuration parameters
DB_USER = "jacopodellepiane"
DB_NAME = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"

# query descriptions and sql
query_1_desc = "Query 1 (Base Aggregation)"
query_1_sql = """
    SELECT a.name, AVG(a.followers) as avg_followers, COUNT(t.id) as explicit_tracks 
    FROM artists a JOIN collaborations c ON a.id = c.artist_id JOIN tracks t ON c.track_id = t.id 
    WHERE a.popularity > 80 AND t.explicit = 1 
    GROUP BY a.id, a.name 
    ORDER BY explicit_tracks DESC;
"""

# executing and measuring the queries
# performing 10 iterations to calculate the average execution time of
# the 9 remaining iterations after the cold start
def measure_query(cursor, query, description, iterations = 10):
    print(f"Executing: {description}")
    # initializing the array of time results
    execution_times = []
    
    for i in range(iterations):
        # returns a timer value, higher resolution of the system one
        start_time = time.perf_counter()
        cursor.execute(query)
        # returns all the results in a list of tuples, making sure Postgres calculates the entire result
        results = cursor.fetchall()
        end_time = time.perf_counter()
        elapsed_ms = (end_time - start_time) * 1000
        # adding the calculated time to the array
        execution_times.append(elapsed_ms)
        # printing a preview of the data, only on the first iteration
        if i == 0:
            print(f"Preview of the first 5 records:\n{results[:5]}")

    # discarding the cold start to calculate the average
    warm_times = execution_times[1:]
    avg_time = sum(warm_times) / len(warm_times)
    
    print(f"Cold Start (1st execution): {execution_times[0]:.2f} ms")
    print(f"Warm Start (average 9 executions): {avg_time:.2f} ms\n")

def benchmark_postgres():
    # connecting to PostgreSQL
    connection = psycopg2.connect(dbname = DB_NAME, user = DB_USER, host = DB_HOST, port = DB_PORT)
    # setting autocommit to true to automatically save and not just stage every transaction
    connection.autocommit = True
    # initializing the cursor to route SQL queries through the connection
    cursor = connection.cursor()
    
    try:
        measure_query(cursor, query_1_sql, query_1_desc)

        print("Postgres benchmark completed")

    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    benchmark_postgres()