Las urgencias de Chile no están más llenas. Están más graves. Y ahora el análisis se actualiza solo.

Trabajé años en emergencias y siempre escuché lo mismo: "la urgencia colapsa". Quise ver qué dicen los datos, así que tomé los registros oficiales del Ministerio de Salud de Chile: 52 millones de atenciones en 186 hospitales públicos, día por día, de 2019 a la semana pasada.

Lo analicé con Lean Six Sigma (DMAIC), SQL y Python. Esto es lo que encontré:

🔸 Hoy llegan 6,6% menos consultas por día que en 2019, pero se internan 11,4% más pacientes.
🔸 1 de cada 11 consultas termina en una cama (era 1 de cada 13).
🔸 Cambió el paciente: 37% menos consultas de menores de 5 años y 15% más de mayores de 65.
🔸 La edad explica solo un tercio de esa suba. El resto pasa dentro de cada grupo de edad.
🔸 El lunes llega 14% más gente que el promedio. El fin de semana, 14% menos.
🔸 Según la región, la tasa de internación va de 4,8% a 12%.
🔸 En la carta de control, las internaciones pasaron el techo 5 semanas seguidas en agosto y septiembre de 2026. Eso ya no es ruido, es un cambio de nivel.

Lo nuevo: armé un monitor en Make. Todos los lunes revisa si el Minsal publicó datos nuevos, deja registro en una planilla y me manda un mail si hay que recalcular. Make no procesa el archivo de 1,5 GB: vigila, registra y avisa. El cálculo queda en SQL y Python. Cada herramienta en lo que mejor hace.

Mi conclusión: para que la urgencia atienda más rápido no alcanza con reforzarla en invierno. Hay que mirar las camas, las altas y los turnos según la curva real de la semana.

Una limitación que me llamó la atención: el registro tiene un campo para los pacientes que esperan cama más de 12 horas, pero se publica vacío. Sin ese dato no hay forma de controlar lo que más sufre el paciente: la espera.

En el carrusel están los gráficos, el método y el circuito de Make.
Tablero interactivo, código y datos: github.com/mperezalaniz/urgencias-chile-lean-six-sigma

Si trabajás en una guardia, ¿lo ves igual desde adentro?

Fuente: DEIS, Ministerio de Salud de Chile, Atenciones de urgencia 2019-2026.

#LeanSixSigma #DataAnalytics #Automatizacion #Make #SaludPublica #Urgencias #SQL #Python #Chile
