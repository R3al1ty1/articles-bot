SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

CREATE TABLE public.sessions (
    session_id bigint NOT NULL,
    length integer NOT NULL,
    count integer NOT NULL
);


CREATE SEQUENCE public.sessions_session_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE public.users (
    user_id bigint NOT NULL,
    username text,
    tg_id bigint
);

CREATE TABLE public.users_sessions (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    session_id bigint NOT NULL
);

CREATE SEQUENCE public.users_sessions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE public.users_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE ONLY public.sessions ALTER COLUMN session_id SET DEFAULT nextval('public.sessions_session_id_seq'::regclass);


ALTER TABLE ONLY public.users ALTER COLUMN user_id SET DEFAULT nextval('public.users_user_id_seq'::regclass);

ALTER TABLE ONLY public.users_sessions ALTER COLUMN id SET DEFAULT nextval('public.users_sessions_id_seq'::regclass);

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (session_id);

ALTER TABLE ONLY public.users
    ADD CONSTRAINT user_id_uq UNIQUE (tg_id);

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);

ALTER TABLE ONLY public.users_sessions
    ADD CONSTRAINT users_sessions_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.users_sessions
    ADD CONSTRAINT sessions_fk FOREIGN KEY (session_id) REFERENCES public.sessions(session_id) NOT VALID;

ALTER TABLE ONLY public.users_sessions
    ADD CONSTRAINT users_fk FOREIGN KEY (user_id) REFERENCES public.users(tg_id) NOT VALID;
