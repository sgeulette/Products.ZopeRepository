--
-- PostgreSQL database dump : can be run with command 'psql -f postgres_db_creation.sql'
--

SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

--
-- Name: zoperepos; Type: DATABASE; Schema: -; Owner: zoperepos
--

CREATE ROLE zoperepos LOGIN ENCRYPTED PASSWORD 'md5a095aaa07ae998bbf536829d2c517c87'
  CREATEDB
   VALID UNTIL 'infinity';

CREATE DATABASE zoperepos WITH TEMPLATE = template0 ENCODING = 'UTF8';


ALTER DATABASE zoperepos OWNER TO zoperepos;

\connect zoperepos

SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

SET search_path = public, pg_catalog;

--
-- Name: apaches_id_seq; Type: SEQUENCE; Schema: public; Owner: zoperepos
--

CREATE SEQUENCE apaches_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.apaches_id_seq OWNER TO zoperepos;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: apaches; Type: TABLE; Schema: public; Owner: zoperepos; Tablespace: 
--

CREATE TABLE apaches (
    id integer DEFAULT nextval('apaches_id_seq'::regclass) NOT NULL,
    name character varying(20),
    conf_file character varying(250),
    creationdate timestamp without time zone,
    server_id integer NOT NULL
);


ALTER TABLE public.apaches OWNER TO zoperepos;

--
-- Name: instances_id_seq; Type: SEQUENCE; Schema: public; Owner: zoperepos
--

CREATE SEQUENCE instances_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.instances_id_seq OWNER TO zoperepos;

--
-- Name: instances; Type: TABLE; Schema: public; Owner: zoperepos; Tablespace: 
--

CREATE TABLE instances (
    id integer DEFAULT nextval('instances_id_seq'::regclass) NOT NULL,
    instance character varying(40) NOT NULL,
    port smallint,
    creationdate timestamp without time zone NOT NULL,
    zope_version character varying(30),
    plone_version character varying(30),
    type character(20),
    zope_path character(150),
    server_id integer NOT NULL,
    repository_address character varying(250),
    svn_diff character varying(5),
    local_revision integer,
    repository_revision integer,
    awstats_path character varying(150)    
);


ALTER TABLE public.instances OWNER TO zoperepos;

--
-- Name: instances_products_id_seq; Type: SEQUENCE; Schema: public; Owner: zoperepos
--

CREATE SEQUENCE instances_products_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.instances_products_id_seq OWNER TO zoperepos;

--
-- Name: instances_products; Type: TABLE; Schema: public; Owner: zoperepos; Tablespace: 
--

CREATE TABLE instances_products (
    id integer DEFAULT nextval('instances_products_id_seq'::regclass) NOT NULL,
    instance_id integer NOT NULL,
    product_id integer NOT NULL,
    local_version text,
    repository_version text,
    local_revision integer,
    repository_revision integer,
    svn_diff character varying(5),
    svn_diff_lines integer,
    repository_address character varying(250),
    is_egg character varying(5)
);


ALTER TABLE public.instances_products OWNER TO zoperepos;

--
-- Name: mountpoints_id_seq; Type: SEQUENCE; Schema: public; Owner: zoperepos
--

CREATE SEQUENCE mountpoints_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.mountpoints_id_seq OWNER TO zoperepos;

--
-- Name: mountpoints; Type: TABLE; Schema: public; Owner: zoperepos; Tablespace: 
--

CREATE TABLE mountpoints (
    id integer DEFAULT nextval('mountpoints_id_seq'::regclass) NOT NULL,
    instance_id integer,
    name character varying(50),
    path character varying(50),
    fs character varying(50),
    size integer,
    fspath character(150)
);


ALTER TABLE public.mountpoints OWNER TO zoperepos;

--
-- Name: plonesites_id_seq; Type: SEQUENCE; Schema: public; Owner: zoperepos
--

CREATE SEQUENCE plonesites_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.plonesites_id_seq OWNER TO zoperepos;

--
-- Name: plonesites; Type: TABLE; Schema: public; Owner: zoperepos; Tablespace: 
--

CREATE TABLE plonesites (
    id integer DEFAULT nextval('plonesites_id_seq'::regclass) NOT NULL,
    instance_id integer,
    plonesite character varying(50),
    path character varying(100),
    mountpoint_id integer
);


ALTER TABLE public.plonesites OWNER TO zoperepos;

--
-- Name: plonesites_products_id_seq; Type: SEQUENCE; Schema: public; Owner: zoperepos
--

CREATE SEQUENCE plonesites_products_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.plonesites_products_id_seq OWNER TO zoperepos;

--
-- Name: plonesites_products; Type: TABLE; Schema: public; Owner: zoperepos; Tablespace: 
--

CREATE TABLE plonesites_products (
    id integer DEFAULT nextval('plonesites_products_id_seq'::regclass) NOT NULL,
    plonesite_id integer,
    product_id integer,
    status character varying(50),
    installed_version text,
    errors smallint
);


ALTER TABLE public.plonesites_products OWNER TO zoperepos;

--
-- Name: products_id_seq; Type: SEQUENCE; Schema: public; Owner: zoperepos
--

CREATE SEQUENCE products_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.products_id_seq OWNER TO zoperepos;

--
-- Name: products; Type: TABLE; Schema: public; Owner: zoperepos; Tablespace: 
--

CREATE TABLE products (
    id integer DEFAULT nextval('products_id_seq'::regclass) NOT NULL,
    product character varying(50) NOT NULL
);


ALTER TABLE public.products OWNER TO zoperepos;

--
-- Name: rewrites_id_seq; Type: SEQUENCE; Schema: public; Owner: zoperepos
--

CREATE SEQUENCE rewrites_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.rewrites_id_seq OWNER TO zoperepos;

--
-- Name: rewrites; Type: TABLE; Schema: public; Owner: zoperepos; Tablespace: 
--

CREATE TABLE rewrites (
    id integer DEFAULT nextval('rewrites_id_seq'::regclass) NOT NULL,
    virtualhost_id integer,
    port integer,
    protocol character varying(10),
    domain character varying(250),
    inst_path character varying(250)
);


ALTER TABLE public.rewrites OWNER TO zoperepos;

--
-- Name: servers; Type: TABLE; Schema: public; Owner: zoperepos; Tablespace: 
--

CREATE TABLE servers (
    id integer NOT NULL,
    creationdate timestamp without time zone NOT NULL,
    server character varying(50) NOT NULL,
    ip_address character varying(30)
);


ALTER TABLE public.servers OWNER TO zoperepos;

--
-- Name: servers_id_seq; Type: SEQUENCE; Schema: public; Owner: zoperepos
--

CREATE SEQUENCE servers_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.servers_id_seq OWNER TO zoperepos;

--
-- Name: servers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: zoperepos
--

ALTER SEQUENCE servers_id_seq OWNED BY servers.id;


--
-- Name: virtualhosts_id_seq; Type: SEQUENCE; Schema: public; Owner: zoperepos
--

CREATE SEQUENCE virtualhosts_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.virtualhosts_id_seq OWNER TO zoperepos;

--
-- Name: virtualhosts; Type: TABLE; Schema: public; Owner: zoperepos; Tablespace: 
--

CREATE TABLE virtualhosts (
    id integer DEFAULT nextval('virtualhosts_id_seq'::regclass) NOT NULL,
    apache_id integer,
    virtualhost character varying(25),
    servername character varying(100),
    logfile character varying(250),
    redirect character varying(100),
    real_ip character varying(24),
    protocol character varying(10),
    virtualhost_ip character varying(24)
);


ALTER TABLE public.virtualhosts OWNER TO zoperepos;

--
-- Name: id; Type: DEFAULT; Schema: public; Owner: zoperepos
--

--
-- Name: fsfiles_id_seq; Type: SEQUENCE; Schema: public; Owner: zoperepos
--
CREATE SEQUENCE fsfiles_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.fsfiles_id_seq OWNER TO zoperepos;

--
-- Name: fsfiles; Type: TABLE; Schema: public; Owner: zoperepos; Tablespace: 
--

CREATE TABLE fsfiles (
    id integer DEFAULT nextval('fsfiles_id_seq'::regclass) NOT NULL,
    fs character varying(50),
    path character varying(100),
    instance_id integer,
    size integer
);


ALTER TABLE public.fsfiles OWNER TO zoperepos;

--
-- Name: lastProduct_Version_id_seq; Type: SEQUENCE; Schema: public; Owner: zoperepos
--

CREATE SEQUENCE lastProduct_Version_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.lastProduct_Version_id_seq OWNER TO zoperepos;

--
-- Name: instances; Type: TABLE; Schema: public; Owner: zoperepos; Tablespace: 
--

CREATE TABLE lastProduct_Version (
    id integer DEFAULT nextval('instances_id_seq'::regclass) NOT NULL,
    product character varying(40) NOT NULL,
    creationdate timestamp without time zone NOT NULL,
    repository_revision character varying(50)
);


ALTER TABLE public.lastProduct_Version OWNER TO zoperepos;
--
-- Name: id; Type: DEFAULT; Schema: public; Owner: zoperepos
--

ALTER TABLE servers ALTER COLUMN id SET DEFAULT nextval('servers_id_seq'::regclass);


--
-- Name: apache_pk; Type: CONSTRAINT; Schema: public; Owner: zoperepos; Tablespace: 
--

ALTER TABLE ONLY apaches
    ADD CONSTRAINT apache_pk PRIMARY KEY (id);


--
-- Name: instance_pk; Type: CONSTRAINT; Schema: public; Owner: zoperepos; Tablespace: 
--

ALTER TABLE ONLY instances
    ADD CONSTRAINT instance_pk PRIMARY KEY (id);


--
-- Name: instance_product_pk; Type: CONSTRAINT; Schema: public; Owner: zoperepos; Tablespace: 
--

ALTER TABLE ONLY instances_products
    ADD CONSTRAINT instance_product_pk PRIMARY KEY (id);


--
-- Name: mountpoint_id; Type: CONSTRAINT; Schema: public; Owner: zoperepos; Tablespace: 
--

ALTER TABLE ONLY mountpoints
    ADD CONSTRAINT mountpoint_id PRIMARY KEY (id);


--
-- Name: plonesite_pk; Type: CONSTRAINT; Schema: public; Owner: zoperepos; Tablespace: 
--

ALTER TABLE ONLY plonesites
    ADD CONSTRAINT plonesite_pk PRIMARY KEY (id);


--
-- Name: plonesite_product_pk; Type: CONSTRAINT; Schema: public; Owner: zoperepos; Tablespace: 
--

ALTER TABLE ONLY plonesites_products
    ADD CONSTRAINT plonesite_product_pk PRIMARY KEY (id);


--
-- Name: product_pk; Type: CONSTRAINT; Schema: public; Owner: zoperepos; Tablespace: 
--

ALTER TABLE ONLY products
    ADD CONSTRAINT product_pk PRIMARY KEY (id);


--
-- Name: rewrite_pk; Type: CONSTRAINT; Schema: public; Owner: zoperepos; Tablespace: 
--

ALTER TABLE ONLY rewrites
    ADD CONSTRAINT rewrite_pk PRIMARY KEY (id);


--
-- Name: servers_pkey; Type: CONSTRAINT; Schema: public; Owner: zoperepos; Tablespace: 
--

ALTER TABLE ONLY servers
    ADD CONSTRAINT servers_pkey PRIMARY KEY (id);


--
-- Name: virtualhost_pk; Type: CONSTRAINT; Schema: public; Owner: zoperepos; Tablespace: 
--

ALTER TABLE ONLY virtualhosts
    ADD CONSTRAINT virtualhost_pk PRIMARY KEY (id);

ALTER TABLE ONLY fsfiles
    ADD CONSTRAINT fsfile_pk PRIMARY KEY (id); 

--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

