SET search_path TO urg;
\copy dim_hospital FROM 'data/raw/hospitales.csv' WITH (FORMAT csv, HEADER true)
CREATE TEMP TABLE stg (id VARCHAR(12), fecha DATE, demanda INT, atenciones INT, resp INT, circ INT, trauma INT, mental INT, hosp INT, cirugias INT, espera_hosp INT, espera_lt12 INT);
\copy stg FROM 'data/raw/urg_chile_hospital_dia.csv' WITH (FORMAT csv, HEADER true)
-- Limpieza: los ID vienen con espacios al final en algunos años
INSERT INTO fact_hospital_dia
SELECT trim(id), fecha, sum(demanda), sum(atenciones), sum(resp), sum(circ), sum(trauma), sum(mental),
       sum(hosp), sum(cirugias), sum(espera_hosp), sum(espera_lt12)
FROM stg GROUP BY 1, 2;
\copy red_anual_tipo FROM 'data/raw/red_urgencia_anual_tipo.csv' WITH (FORMAT csv, HEADER true)
\copy hospital_edad FROM 'data/raw/hospital_edad_ene_sep.csv' WITH (FORMAT csv, HEADER true)
CREATE INDEX ON fact_hospital_dia (fecha);
CREATE INDEX ON fact_hospital_dia (id_establecimiento);
