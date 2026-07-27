import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
import time
import statistics
import math

# necessary to read the password in the .env file
load_dotenv()

# establishing a local connection with the database
#7687 standard port for neo4j
uri = "bolt://localhost:7687"
password = os.getenv("neo4j_password")
driver = GraphDatabase.driver(uri, auth=("neo4j", password))
db_name = 'neo4j'

# query descriptions and cypher
query_1_desc = "Query 1 (Base Aggregation)"
query_1_cypher = """
    MATCH (a:Artist)-[:HAS_TRACK]->(t:Track) 
    WHERE a.popularity > 80 AND t.explicit = 1 
    RETURN a.name, avg(a.followers) as avg_followers, count(t) as explicit_tracks 
    ORDER BY explicit_tracks DESC;
"""

query_2_desc = "Query 2 (Explicit Collaborations of an Artist)"
query_2_cypher = """
    MATCH (a1:Artist {name: 'Drake'})-[:HAS_TRACK]->(t:Track)<-[:HAS_TRACK]-(a2:Artist)
    WHERE t.explicit = 1
    RETURN 
        a1.name AS main_artist, 
        count(DISTINCT t) AS explicit_collab_tracks, 
        collect(DISTINCT a2.name) AS collaborators;
"""

# executing and measuring the queries
# performing 30 iterations to calculate the average execution time of
# the 29 remaining iterations after the cold start
def measure_query(query, description, iterations = 30):
    # opening manually the session
    session = driver.session(database = db_name)
    print(f"Executing: {description}")
    # initializing the array of time results
    execution_times = []
    
    for i in range(iterations):
        # returns a timer value, higher resolution of the system one
        start_time = time.perf_counter()
        result = session.run(query)
        # data fetches all results from the database into a list of dictionaries, making sure Neo4j calculates the entire result
        results = result.data()
        end_time = time.perf_counter()
        elapsed_ms = (end_time - start_time) * 1000
        # adding the calculated time to the array
        execution_times.append(elapsed_ms)
        # printing a preview of the data, only on the first iteration
        if i == 0:
            # extracting only the values from the dictionaries and casting them to tuples to match Postgres output
            preview = [tuple(record.values()) for record in results[:5]]
            print(f"Preview of the first 5 records:\n{preview}")
    
    # closing manually the session
    session.close()

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
        

try:
    measure_query(query_1_cypher, query_1_desc)
    measure_query(query_2_cypher, query_2_desc)
    
    print("Neo4j benchmark completed")

finally:
    driver.close()