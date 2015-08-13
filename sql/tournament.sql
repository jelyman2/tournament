-- Use this SQL file for general app usage.
-- Create tournament database


CREATE DATABASE tournament;
\c tournament;

-- Table: players

-- DROP TABLE players;

CREATE TABLE players
(
  id serial NOT NULL,
  name text NOT NULL,
  country text NOT NULL,
  code text,
  CONSTRAINT players_pkey PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);


-- Table: matches

-- DROP TABLE matches;

CREATE TABLE matches
(
  id serial NOT NULL,
  player_1 text NOT NULL,
  player_2 text NOT NULL,
  "timestamp" text NOT NULL,
  CONSTRAINT matches_pkey PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);
