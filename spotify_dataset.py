import pandas as pd
import ast

# using pandas read_csv function to convert csv files in pandas DataFrame structures
print("Reading the csv files")
df_tracks = pd.read_csv('tracks.csv')                              
df_artists = pd.read_csv('artists.csv')

# create the cleaned csv file for the tracks
print("Creating the cleaned csv file for the tracks")
# selecting only the columns we actually need
df_tracks_clean = df_tracks[['id', 'name', 'explicit', 'release_date']].copy()
# drop possible duplicate to use later the id as primary key
df_tracks_clean = df_tracks_clean.drop_duplicates(subset = ['id'])
# drop possible row with no value for id
df_tracks_clean = df_tracks_clean.dropna(subset = ['id'])
# eliminate ' " ' 
df_tracks_clean['name'] = df_tracks_clean['name'].astype(str).str.replace('"', '')
# creating the csv file, index = False to not have the default pandas numbering
df_tracks_clean.to_csv('tracks_clean.csv', index = False)

# creating the cleaned csv file for the artists
print("Creating the cleaned csv file for the artists")
df_artists_clean = df_artists[['id', 'name', 'popularity', 'followers']].copy()
df_artists_clean = df_artists_clean.drop_duplicates(subset = ['id'])
df_artists_clean = df_artists_clean.dropna(subset = ['id'])
df_artists_clean['name'] = df_artists_clean['name'].astype(str).str.replace('"', '')
df_artists_clean.to_csv('artists_clean.csv', index = False)

# creating the third table for the relations
print("Creating the third table for the artists to tracks relation")
df_tracks_rel = df_tracks[['id', 'id_artists']].copy()
df_tracks_rel = df_tracks_rel.dropna(subset = ['id', 'id_artists'])
# modify the string containing all the artists into a list, to be able to select all the artists individually
# using the ast.literal_eval that distinguishes between real comma and python comma
df_tracks_rel['id_artists'] = df_tracks_rel['id_artists'].apply(ast.literal_eval)
# using explode to create an entry for every artists that collaborated to a track
collaborations = df_tracks_rel.explode('id_artists')
# renaming the columns for better understanding
collaborations = collaborations.rename(columns = {
    'id': 'track_id',
    'id_artists': 'artist_id'
})
# check that all the artists in collaborations, and previous in tracks, are in artists_clean
collaborations = collaborations[collaborations['artist_id'].isin(df_artists_clean['id'])]
# remove possible duplicate in the artists field that after the explode could generate two identical rows
collaborations = collaborations.drop_duplicates(subset=['artist_id', 'track_id'])
collaborations.to_csv('collaborations.csv', index = False)