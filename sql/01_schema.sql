-- ============================================================
-- Urgencias de la red pública de Chile: modelo de datos
-- Fuente: DEIS - Ministerio de Salud de Chile, "Atenciones de urgencia"
--         (registro DAU), 2019 a 2026 (corte 04/10/2026)
-- Autor: Emiliano Pérez Alaniz
-- ============================================================
DROP SCHEMA IF EXISTS urg CASCADE;
CREATE SCHEMA urg;
SET search_path TO urg;

-- Dimensión hospitales (unidades de emergencia hospitalaria)
CREATE TABLE dim_hospital (
    id_establecimiento VARCHAR(10) PRIMARY KEY,
    nombre             VARCHAR(120),
    region             VARCHAR(40),
    servicio_salud     VARCHAR(80),
    comuna             VARCHAR(60),
    tipo_atencion      VARCHAR(20)      -- Adulto / Infantil / Indiferenciado
);

-- Hechos: un registro por hospital y día
CREATE TABLE fact_hospital_dia (
    id_establecimiento VARCHAR(10),
    fecha              DATE,
    demanda            INTEGER,  -- causa 34 (TOTAL DEMANDA; no se usa: sin definición publicada)
    atenciones         INTEGER,  -- causa 1  total atenciones de urgencia
    resp               INTEGER,  -- causa 2  sistema respiratorio J00-J98
    circ               INTEGER,  -- causa 12 sistema circulatorio I00-I99
    trauma             INTEGER,  -- causa 18 traumatismos y envenenamientos
    mental             INTEGER,  -- causa 36 trastornos mentales
    hosp               INTEGER,  -- causa 25 hospitalizaciones desde urgencia
    cirugias           INTEGER,  -- causa 24 cirugías de urgencia
    espera_hosp        INTEGER,  -- causa 27 (publicado vacío)
    espera_lt12        INTEGER   -- causa 28 (publicado vacío)
);

-- Atenciones de toda la red por tipo de establecimiento y año
CREATE TABLE red_anual_tipo (
    anio               SMALLINT,
    tipo               VARCHAR(10),   -- Hospital, SAPU, SAR, SUR, CEAR
    atenciones         INTEGER,
    atenciones_ene_sep INTEGER
);

-- Atenciones y hospitalizaciones en hospitales por edad (enero a septiembre)
CREATE TABLE hospital_edad (
    anio SMALLINT, seccion VARCHAR(20), total INTEGER,
    menores_1 INTEGER, de_1_a_4 INTEGER, de_5_a_14 INTEGER, de_15_a_64 INTEGER, de_65_y_mas INTEGER
);
