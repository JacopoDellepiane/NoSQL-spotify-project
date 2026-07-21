import os
import psycopg2

# configuration parameters
DB_USER = "jacopodellepiane"
DB_NAME = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"

artists_csv = 'artists_clean.csv'
tracks_csv = 'tracks_clean.csv'
collaborations_csv = 'collaborations.csv'

# loading the csv files
def load_csv(cursor, file_path, table_name, message):
    f = open(file_path, 'r', encoding = 'utf-8')
    try:
        sql = f"COPY {table_name} FROM STDIN WITH CSV HEADER"
        cursor.copy_expert(sql, f)
    finally:
        f.close()
    print(f"{message}")

# helper function to execute the queries
def execute_query(cursor, query, description):
    print(f"Executing: {description}")
    cursor.execute(query)

# reset queries
query_drop_collaborations = "DROP TABLE IF EXISTS collaborations;"
query_drop_artists = "DROP TABLE IF EXISTS artists;"
query_drop_tracks = "DROP TABLE IF EXISTS tracks;"

# create queries
query_artists = """
    CREATE TABLE artists (
        id VARCHAR PRIMARY KEY,
        name VARCHAR,
        popularity INT,
        followers FLOAT
    );
"""

query_tracks = """
    CREATE TABLE tracks (
        id VARCHAR PRIMARY KEY,
        name VARCHAR,
        explicit INT,
        release_date VARCHAR
    );
"""

query_collaborations = """
    CREATE TABLE collaborations (
        track_id VARCHAR REFERENCES tracks(id),
        artist_id VARCHAR REFERENCES artists(id),
        PRIMARY KEY (artist_id, track_id)
    );
"""

def setup_rel_spotify_db():
    # connecting to PostgreSQL
    connection = psycopg2.connect(dbname = DB_NAME, user = DB_USER, host = DB_HOST, port = DB_PORT)
    # setting autocommit to true to automatically save and not just stage every transaction
    connection.autocommit = True
    # initializing the cursor to route SQL queries through the connection
    cursor = connection.cursor()
    
    try:
        execute_query(cursor, query_drop_collaborations, "Drop collaborations table")
        execute_query(cursor, query_drop_artists, "Drop artists table")
        execute_query(cursor, query_drop_tracks, "Drop tracks table")

        execute_query(cursor, query_artists, "Creating artists table")
        execute_query(cursor, query_tracks, "Creating tracks table")
        execute_query(cursor, query_collaborations, "Creating collaborations table")

        load_csv(cursor, artists_csv, 'artists', "Artists csv imported")
        load_csv(cursor, tracks_csv, 'tracks', "Tracks csv imported")
        load_csv(cursor, collaborations_csv, 'collaborations', "Collaborations csv imported")

    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    setup_rel_spotify_db()