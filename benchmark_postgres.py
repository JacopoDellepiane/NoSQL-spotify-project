import psycopg2
import time
import statistics
import math

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

query_2_desc = "Query 2 (Explicit Collaborations of an Artist)"
query_2_sql = """
    SELECT a1.name AS main_artist, COUNT(DISTINCT t.id) AS explicit_collab_tracks, ARRAY_AGG(DISTINCT a2.name) AS collaborators
    FROM artists a1 JOIN collaborations c1 ON a1.id = c1.artist_id JOIN tracks t ON c1.track_id = t.id JOIN collaborations c2 ON t.id = c2.track_id JOIN artists a2 ON c2.artist_id = a2.id
    WHERE a1.name = 'Drake' AND t.explicit = 1 AND a1.id != a2.id
    GROUP BY a1.id, a1.name;
"""

query_3_desc = "Query 3 (Top 5 Most Collaborative Artists)"
query_3_sql = """
    SELECT a.name AS artist_name, COUNT(DISTINCT c2.artist_id) AS total_collaborators
    FROM artists a JOIN collaborations c1 ON a.id = c1.artist_id JOIN collaborations c2 ON c1.track_id = c2.track_id
    WHERE c1.artist_id != c2.artist_id
    GROUP BY a.id, a.name
    ORDER BY total_collaborators DESC
    LIMIT 5;
"""

# executing and measuring the queries
# performing 30 iterations to calculate the average execution time of
# the 29 remaining iterations after the cold start
def measure_query(cursor, query, description, iterations = 30):
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
    avg_time = statistics.mean(warm_times)
    # calculating the median to check for any random spike values that could skew the mean
    median_time = statistics.median(warm_times)
    # computing the standard deviation and the coefficient of variation to see how much the values in the iterations differ from each other,
    # a large dispersion of data leads to a result that is difficult to replicate
    stdev_time = statistics.stdev(warm_times)
    cv = stdev_time / avg_time
    
    print(f"\nCold Start (1st execution): {execution_times[0]:.2f} ms")
    print(f"Warm Start (average {len(warm_times)} executions): {avg_time:.2f} ms")
    print(f"Warm Start (median): {median_time:.2f} ms")
    print(f"Warm Start (stdev): {stdev_time:.2f} ms")
    print(f"Warm Start (coefficient of variation): {cv:.2%}")
    if cv > 0.15:
        print(f"CV > 15%, high variability. Consider more iterations for '{description}'")
    else:
        print("Coefficient of variation in the range")
    if math.isclose(avg_time, median_time, rel_tol = 0.10):
        print("Mean and median are consistent, no anomalous executions\n")
    else:
        print(f"Mean and median diverge more than 10%, likely outlier execution in '{description}'\n")

def benchmark_postgres():
    # connecting to PostgreSQL
    connection = psycopg2.connect(dbname = DB_NAME, user = DB_USER, host = DB_HOST, port = DB_PORT)
    # setting autocommit to true to automatically save and not just stage every transaction
    connection.autocommit = True
    # initializing the cursor to route SQL queries through the connection
    cursor = connection.cursor()
    
    try:
        measure_query(cursor, query_1_sql, query_1_desc)
        measure_query(cursor, query_2_sql, query_2_desc)
        measure_query(cursor, query_3_sql, query_3_desc)

        print("Postgres benchmark completed")

    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    benchmark_postgres()