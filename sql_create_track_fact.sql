create view music_db.track_fact as
select 
td.track_name, 
attt.artist_id, 
td.album_id, 
td.disc_number, 
td.track_number, 
td.type, 
td.popularity, 
td.duration_ms, 
td.duration_s, 
td.duration_m_s, 
td.explicit, 
td.is_local, 
td.available_markets, 
td.track_id, 
td.spotify_url, 
td.href, 
td.uri, 
td.preview_url,
timestamp
from music_db.track_data as td
left join (
select track_id, artist_id 
from music_db.artist_track_translation_table) as attt on 
td.track_id = attt.track_id;