import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
import time

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

# executing and measuring the queries
# performing 10 iterations to calculate the average execution time of
# the 9 remaining iterations after the cold start
def measure_query(query, description, iterations = 10):
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
    avg_time = sum(warm_times) / len(warm_times)
    
    print(f"Cold Start (1st execution): {execution_times[0]:.2f} ms")
    print(f"Warm Start (average 9 executions): {avg_time:.2f} ms\n")

try:
    measure_query(query_1_cypher, query_1_desc)
    
    print("Neo4j benchmark completed")

finally:
    driver.close()