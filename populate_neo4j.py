import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# necessary to read the password in the .env file
load_dotenv()

# establishing a local connection with the database
#7687 standard port for neo4j
uri = "bolt://localhost:7687"
password = os.getenv("neo4j_password")
driver = GraphDatabase.driver(uri, auth=("neo4j", password))
db_name = 'neo4j'

artists_csv = 'file:///artists_clean.csv'
tracks_csv = 'file:///tracks_clean.csv'
collaborations_csv = 'file:///collaborations.csv'

def create_spotify_db(query, description):
    # opening manually the session
    session = driver.session(database = db_name)
    # run the query (f-string for the comment)
    print(f"Executing: {description}")
    session.run(query)
    # closing manually the session
    session.close()

query_reset = """
MATCH (n)
CALL (n) { DETACH DELETE n } IN TRANSACTIONS OF 10000 ROWS;
"""

# using an f-string to dynamically insert the CSV file path
query_artists = f"""
LOAD CSV WITH HEADERS FROM '{artists_csv}' AS row
CALL (row) {{
    CREATE (a:Artist {{
        id: row.id,
        name: row.name,
        popularity: toInteger(row.popularity),
        followers: toFloat(row.followers)
    }})
}} IN TRANSACTIONS OF 10000 ROWS;
"""

query_tracks = f"""
LOAD CSV WITH HEADERS FROM '{tracks_csv}' AS row
CALL (row) {{
    CREATE (t:Track {{
        id: row.id,
        name: row.name,
        explicit: toInteger(row.explicit),
        release_date: row.release_date
    }})
}} IN TRANSACTIONS OF 10000 ROWS;
"""

query_index_artists = "CREATE INDEX IF NOT EXISTS FOR (a:Artist) ON (a.id);"
query_index_tracks = "CREATE INDEX IF NOT EXISTS FOR (t:Track) ON (t.id);"

query_relations = f"""
LOAD CSV WITH HEADERS FROM '{collaborations_csv}' AS row
CALL (row) {{
    MATCH (a:Artist {{id: row.artist_id}})
    MATCH (t:Track {{id: row.track_id}})
    CREATE (a)-[:HAS_TRACK]->(t)
}} IN TRANSACTIONS OF 10000 ROWS;
"""

try:
    create_spotify_db(query_reset, "Database clean-up for reset")
    
    create_spotify_db(query_artists, "Artists import")
    create_spotify_db(query_tracks, "Tracks import")
    
    create_spotify_db(query_index_artists, "Create artists indexes")
    create_spotify_db(query_index_tracks, "Create tracks indexes")
        
    create_spotify_db(query_relations, "Collaborations import")
    
    print("Neo4j spotifyDB database fully loaded")

finally:
    driver.close()