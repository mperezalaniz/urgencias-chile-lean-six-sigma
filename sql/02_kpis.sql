-- ============================================================
-- KPIs de urgencia hospitalaria con enfoque Lean Six Sigma
-- ============================================================
SET search_path TO urg;

-- 1. Línea base comparable: enero a septiembre de cada año
CREATE OR REPLACE VIEW v_anual_ene_sep AS
SELECT extract(year FROM fecha)::INT                          AS anio,
       count(DISTINCT fecha)                                  AS dias,
       sum(atenciones)                                        AS atenciones,
       sum(hosp)                                              AS hospitalizaciones,
       sum(cirugias)                                          AS cirugias,
       round(sum(atenciones)::NUMERIC / count(DISTINCT fecha)) AS atenciones_dia,
       round(sum(hosp)::NUMERIC / count(DISTINCT fecha))      AS hosp_dia,
       round(100.0 * sum(hosp) / sum(atenciones), 2)          AS tasa_hosp_pct,
       round(100.0 * sum(resp) / sum(atenciones), 2)         AS resp_pct
FROM fact_hospital_dia
WHERE extract(month FROM fecha) <= 9
GROUP BY 1;

-- 2. Patrón por día de la semana (2023 en adelante): índice vs. promedio
CREATE OR REPLACE VIEW v_dia_semana AS
WITH d AS (SELECT fecha, sum(atenciones) a, sum(hosp) h FROM fact_hospital_dia WHERE fecha >= '2023-01-01' GROUP BY 1)
SELECT extract(isodow FROM fecha)::INT AS dow,
       to_char(fecha, 'TMDay')        AS dia,
       round(avg(a))                  AS atenciones_prom,
       round(avg(a) / (SELECT avg(a) FROM d), 3) AS indice_atenciones,
       round(avg(h) / (SELECT avg(h) FROM d), 3) AS indice_hosp
FROM d GROUP BY 1, 2;

-- 3. Serie semanal nacional (para estacionalidad y cartas de control)
CREATE OR REPLACE VIEW v_semanal AS
SELECT date_trunc('week', fecha)::DATE AS semana,
       sum(atenciones) atenciones, sum(resp) resp, sum(hosp) hosp, count(DISTINCT fecha) dias
FROM fact_hospital_dia GROUP BY 1;

-- 4. Hospitales: volumen y tasa de hospitalización 2025
CREATE OR REPLACE VIEW v_hospital_2025 AS
SELECT h.id_establecimiento, h.nombre, h.region, h.tipo_atencion,
       sum(f.atenciones) atenciones, sum(f.hosp) hosp,
       round(100.0 * sum(f.hosp) / nullif(sum(f.atenciones), 0), 2) tasa_hosp_pct
FROM fact_hospital_dia f JOIN dim_hospital h USING (id_establecimiento)
WHERE f.fecha BETWEEN '2025-01-01' AND '2025-12-31'
GROUP BY 1, 2, 3, 4;

-- 5. Pareto: cuántos hospitales concentran el 50% y el 80% de las atenciones
CREATE OR REPLACE VIEW v_pareto_2025 AS
SELECT *, round(100.0 * sum(atenciones) OVER (ORDER BY atenciones DESC) / sum(atenciones) OVER (), 1) AS acum_pct,
       row_number() OVER (ORDER BY atenciones DESC) AS ranking
FROM v_hospital_2025;

-- 6. Carta de control I-MR de las hospitalizaciones diarias (nacional, 2025-2026)
CREATE OR REPLACE VIEW v_control_hosp AS
WITH d AS (SELECT fecha, sum(hosp) x FROM fact_hospital_dia WHERE fecha >= '2025-01-01' GROUP BY 1),
     mr AS (SELECT fecha, x, abs(x - lag(x) OVER (ORDER BY fecha)) mr FROM d),
     lim AS (SELECT avg(x) xbar, avg(mr) mrbar FROM mr)
SELECT fecha, x, round(xbar) media, round(xbar + 2.66 * mrbar) lcs, round(xbar - 2.66 * mrbar) lci,
       CASE WHEN x > xbar + 2.66 * mrbar OR x < xbar - 2.66 * mrbar THEN 1 ELSE 0 END fuera_control
FROM mr, lim;

-- 7. Edad: adultos mayores vs. niños
CREATE OR REPLACE VIEW v_edad AS
SELECT anio, seccion, total,
       round(100.0 * de_65_y_mas / total, 1) AS pct_65_mas,
       menores_1 + de_1_a_4                  AS menores_5,
       round(100.0 * de_65_y_mas / NULLIF(total,0), 1) AS share_65
FROM hospital_edad;

-- Consultas de salida
SELECT * FROM v_anual_ene_sep ORDER BY anio;
SELECT dow, dia, atenciones_prom, indice_atenciones, indice_hosp FROM v_dia_semana ORDER BY dow;
SELECT count(*) hospitales, count(*) FILTER (WHERE acum_pct <= 50) top50, count(*) FILTER (WHERE acum_pct <= 80) top80 FROM v_pareto_2025;
SELECT min(media) media, min(lcs) lcs, min(lci) lci, sum(fuera_control) dias_fuera, count(*) dias FROM v_control_hosp;
SELECT anio, sum(atenciones) FILTER (WHERE tipo='Hospital') hosp, sum(atenciones) FILTER (WHERE tipo='SAPU') sapu,
       sum(atenciones) FILTER (WHERE tipo='SAR') sar, sum(atenciones) FILTER (WHERE tipo='SUR') sur FROM red_anual_tipo GROUP BY 1 ORDER BY 1;
