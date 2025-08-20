create table music_db.track_data (
	track_name varchar(255),
    artists varchar(255),
    artist_ids varchar(255),
    album_id varchar(100),
    disc_number int,
    track_number int,
    `type` varchar(100),
    popularity int,
    duration_ms int,
    duration_s float,
    duration_m_s varchar(5),
    explicit tinyint,
    is_local tinyint,
    available_markets varchar(10000),
    track_id varchar(100),
    spotify_url varchar(150),
    href varchar(150),
    uri varchar(150),
    preview_url varchar(150),
    `timestamp` datetime
    );
    
drop table music_db.track_data;