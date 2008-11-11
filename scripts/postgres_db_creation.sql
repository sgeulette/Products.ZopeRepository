--
-- PostgreSQL database dump
--

-- Started on 2008-11-11 23:19:01 CET

SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

--
-- TOC entry 1811 (class 1262 OID 16467)
-- Name: zoperepos; Type: DATABASE; Schema: -; Owner: zoperepos
--

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
-- TOC entry 1493 (class 1259 OID 16468)
-- Dependencies: 6
-- Name: apaches_id_seq; Type: SEQUENCE; Schema: public; Owner: zoperepos
--

CREATE SEQUENCE apaches_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.apaches_id_seq OWNER TO zoperepos;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- TOC entry 1494 (class 1259 OID 16470)
-- Dependencies: 1779 6
-- Name: apaches; Type: TABLE; Schema: public; Owner: zoperepos; Tablespace: 
--

CREATE TABLE apaches (
    id integer DEFAULT nextval('apaches_id_seq'::regclass) NOT NULL,
    name character varying(20),
    conf_file character varying(250),
    creationdate timestamp without time zone
);


ALTER TABLE public.apaches OWNER TO zoperepos;

--
-- TOC entry 1495 (class 1259 OID 16474)
-- Dependencies: 6
-- Name: instances_id_seq; Type: SEQUENCE; Schema: public; Owner: zoperepos
--

CREATE SEQUENCE instances_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.instances_id_seq OWNER TO zoperepos;

--
-- TOC entry 1496 (class 1259 OID 16476)
-- Dependencies: 1780 6
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
    server_id integer NOT NULL
);


ALTER TABLE public.instances OWNER TO zoperepos;

--
-- TOC entry 1497 (class 1259 OID 16480)
-- Dependencies: 6
-- Name: instances_products_id_seq; Type: SEQUENCE; Schema: public; Owner: zoperepos
--

CREATE SEQUENCE instances_products_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.instances_products_id_seq OWNER TO zoperepos;

--
-- TOC entry 1498 (class 1259 OID 16482)
-- Dependencies: 1781 6
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
    repository_address character varying(250)
);


ALTER TABLE public.instances_products OWNER TO zoperepos;

--
-- TOC entry 1499 (class 1259 OID 16489)
-- Dependencies: 6
-- Name: mountpoints_id_seq; Type: SEQUENCE; Schema: public; Owner: zoperepos
--

CREATE SEQUENCE mountpoints_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.mountpoints_id_seq OWNER TO zoperepos;

--
-- TOC entry 1500 (class 1259 OID 16491)
-- Dependencies: 1782 6
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
-- TOC entry 1501 (class 1259 OID 16495)
-- Dependencies: 6
-- Name: plonesites_id_seq; Type: SEQUENCE; Schema: public; Owner: zoperepos
--

CREATE SEQUENCE plonesites_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.plonesites_id_seq OWNER TO zoperepos;

--
-- TOC entry 1502 (class 1259 OID 16497)
-- Dependencies: 1783 6
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
-- TOC entry 1503 (class 1259 OID 16501)
-- Dependencies: 6
-- Name: plonesites_products_id_seq; Type: SEQUENCE; Schema: public; Owner: zoperepos
--

CREATE SEQUENCE plonesites_products_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.plonesites_products_id_seq OWNER TO zoperepos;

--
-- TOC entry 1504 (class 1259 OID 16503)
-- Dependencies: 1784 6
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
-- TOC entry 1505 (class 1259 OID 16510)
-- Dependencies: 6
-- Name: products_id_seq; Type: SEQUENCE; Schema: public; Owner: zoperepos
--

CREATE SEQUENCE products_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.products_id_seq OWNER TO zoperepos;

--
-- TOC entry 1506 (class 1259 OID 16512)
-- Dependencies: 1785 6
-- Name: products; Type: TABLE; Schema: public; Owner: zoperepos; Tablespace: 
--

CREATE TABLE products (
    id integer DEFAULT nextval('products_id_seq'::regclass) NOT NULL,
    product character varying(50) NOT NULL
);


ALTER TABLE public.products OWNER TO zoperepos;

--
-- TOC entry 1507 (class 1259 OID 16516)
-- Dependencies: 6
-- Name: rewrites_id_seq; Type: SEQUENCE; Schema: public; Owner: zoperepos
--

CREATE SEQUENCE rewrites_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.rewrites_id_seq OWNER TO zoperepos;

--
-- TOC entry 1508 (class 1259 OID 16518)
-- Dependencies: 1786 6
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
-- TOC entry 1512 (class 1259 OID 16551)
-- Dependencies: 6
-- Name: servers; Type: TABLE; Schema: public; Owner: zoperepos; Tablespace: 
--

CREATE TABLE servers (
    id integer NOT NULL,
    server character varying(50) NOT NULL,
    ip_address character varying(30)
);


ALTER TABLE public.servers OWNER TO zoperepos;

--
-- TOC entry 1509 (class 1259 OID 16525)
-- Dependencies: 6
-- Name: virtualhosts_id_seq; Type: SEQUENCE; Schema: public; Owner: zoperepos
--

CREATE SEQUENCE virtualhosts_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.virtualhosts_id_seq OWNER TO zoperepos;

--
-- TOC entry 1510 (class 1259 OID 16527)
-- Dependencies: 1787 6
-- Name: virtualhosts; Type: TABLE; Schema: public; Owner: zoperepos; Tablespace: 
--

CREATE TABLE virtualhosts (
    id integer DEFAULT nextval('virtualhosts_id_seq'::regclass) NOT NULL,
    apache_id integer,
    virtualhost character varying(25),
    servername character varying(100),
    logfile character varying(250),
    redirect character varying(100)
);


ALTER TABLE public.virtualhosts OWNER TO zoperepos;

--
-- TOC entry 1511 (class 1259 OID 16549)
-- Dependencies: 6 1512
-- Name: servers_id_seq; Type: SEQUENCE; Schema: public; Owner: zoperepos
--

CREATE SEQUENCE servers_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.servers_id_seq OWNER TO zoperepos;

--
-- TOC entry 1814 (class 0 OID 0)
-- Dependencies: 1511
-- Name: servers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: zoperepos
--

ALTER SEQUENCE servers_id_seq OWNED BY servers.id;


--
-- TOC entry 1788 (class 2604 OID 16554)
-- Dependencies: 1511 1512 1512
-- Name: id; Type: DEFAULT; Schema: public; Owner: zoperepos
--

ALTER TABLE servers ALTER COLUMN id SET DEFAULT nextval('servers_id_seq'::regclass);


--
-- TOC entry 1790 (class 2606 OID 16532)
-- Dependencies: 1494 1494
-- Name: apache_pk; Type: CONSTRAINT; Schema: public; Owner: zoperepos; Tablespace: 
--

ALTER TABLE ONLY apaches
    ADD CONSTRAINT apache_pk PRIMARY KEY (id);


--
-- TOC entry 1792 (class 2606 OID 16534)
-- Dependencies: 1496 1496
-- Name: instance_pk; Type: CONSTRAINT; Schema: public; Owner: zoperepos; Tablespace: 
--

ALTER TABLE ONLY instances
    ADD CONSTRAINT instance_pk PRIMARY KEY (id);


--
-- TOC entry 1794 (class 2606 OID 16536)
-- Dependencies: 1498 1498
-- Name: instance_product_pk; Type: CONSTRAINT; Schema: public; Owner: zoperepos; Tablespace: 
--

ALTER TABLE ONLY instances_products
    ADD CONSTRAINT instance_product_pk PRIMARY KEY (id);


--
-- TOC entry 1796 (class 2606 OID 16538)
-- Dependencies: 1500 1500
-- Name: mountpoint_id; Type: CONSTRAINT; Schema: public; Owner: zoperepos; Tablespace: 
--

ALTER TABLE ONLY mountpoints
    ADD CONSTRAINT mountpoint_id PRIMARY KEY (id);


--
-- TOC entry 1798 (class 2606 OID 16540)
-- Dependencies: 1502 1502
-- Name: plonesite_pk; Type: CONSTRAINT; Schema: public; Owner: zoperepos; Tablespace: 
--

ALTER TABLE ONLY plonesites
    ADD CONSTRAINT plonesite_pk PRIMARY KEY (id);


--
-- TOC entry 1800 (class 2606 OID 16542)
-- Dependencies: 1504 1504
-- Name: plonesite_product_pk; Type: CONSTRAINT; Schema: public; Owner: zoperepos; Tablespace: 
--

ALTER TABLE ONLY plonesites_products
    ADD CONSTRAINT plonesite_product_pk PRIMARY KEY (id);


--
-- TOC entry 1802 (class 2606 OID 16544)
-- Dependencies: 1506 1506
-- Name: product_pk; Type: CONSTRAINT; Schema: public; Owner: zoperepos; Tablespace: 
--

ALTER TABLE ONLY products
    ADD CONSTRAINT product_pk PRIMARY KEY (id);


--
-- TOC entry 1804 (class 2606 OID 16546)
-- Dependencies: 1508 1508
-- Name: rewrite_pk; Type: CONSTRAINT; Schema: public; Owner: zoperepos; Tablespace: 
--

ALTER TABLE ONLY rewrites
    ADD CONSTRAINT rewrite_pk PRIMARY KEY (id);


--
-- TOC entry 1808 (class 2606 OID 16556)
-- Dependencies: 1512 1512
-- Name: servers_pkey; Type: CONSTRAINT; Schema: public; Owner: zoperepos; Tablespace: 
--

ALTER TABLE ONLY servers
    ADD CONSTRAINT servers_pkey PRIMARY KEY (id);


--
-- TOC entry 1806 (class 2606 OID 16548)
-- Dependencies: 1510 1510
-- Name: virtualhost_pk; Type: CONSTRAINT; Schema: public; Owner: zoperepos; Tablespace: 
--

ALTER TABLE ONLY virtualhosts
    ADD CONSTRAINT virtualhost_pk PRIMARY KEY (id);


--
-- TOC entry 1813 (class 0 OID 0)
-- Dependencies: 6
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


-- Completed on 2008-11-11 23:19:02 CET

--
-- PostgreSQL database dump complete
--

