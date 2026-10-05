/*
 * Extracción usada en este proyecto (transparencia metodológica).
 * Se ejecutó en la consola del navegador, con origen https://repositoriodeis.minsal.cl/,
 * porque el entorno de cómputo no tenía acceso directo al repositorio del DEIS.
 *
 * Archivos de origen (DEIS - Ministerio de Salud de Chile, "Atenciones de urgencia"):
 *   2019-2020: /DatosAbiertos/AtencionesDeUrgencia/AtencionesUrgencia{AAAA}.zip
 *   2021-2026: /SistemaAtencionesUrgencia/AtencionesUrgencia{AAAA}.zip
 * Cada zip trae un CSV separado por ';' (latin-1), una fila por establecimiento, día y causa.
 * El de 2026 pesa 1,5 GB descomprimido, por eso se lee como stream.
 *
 * Resultado: data/raw/urg_chile_hospital_dia.csv (solo GLOSATIPOESTABLECIMIENTO = 'Hospital')
 */
const CAUSAS = { 1: 'atenciones', 2: 'resp', 12: 'circ', 18: 'trauma', 36: 'mental', 25: 'hosp',
                 24: 'cirugias', 27: 'espera_hosp', 28: 'espera_lt12', 34: 'demanda' };
const COLS = ['demanda', 'atenciones', 'resp', 'circ', 'trauma', 'mental', 'hosp', 'cirugias', 'espera_hosp', 'espera_lt12'];
const H = new Map();   // "id|fecha" -> valores

// Abre la entrada .csv del zip (directorio central + DecompressionStream, sin librerías)
function entryStream(buf) {
  const dv = new DataView(buf), u8 = new Uint8Array(buf);
  let e = buf.byteLength - 22; while (e > 0 && dv.getUint32(e, true) !== 0x06054b50) e--;
  const cnt = dv.getUint16(e + 10, true); let p = dv.getUint32(e + 16, true); let ent = null;
  for (let i = 0; i < cnt; i++) {
    const csize = dv.getUint32(p + 20, true), nlen = dv.getUint16(p + 28, true), xlen = dv.getUint16(p + 30, true),
          clen = dv.getUint16(p + 32, true), loff = dv.getUint32(p + 42, true);
    const name = new TextDecoder().decode(u8.slice(p + 46, p + 46 + nlen));
    if (/\.csv$/i.test(name)) ent = { csize, loff };
    p += 46 + nlen + xlen + clen;
  }
  const ln = dv.getUint16(ent.loff + 26, true), lx = dv.getUint16(ent.loff + 28, true);
  const data = new Uint8Array(buf, ent.loff + 30 + ln + lx, ent.csize);
  return new Blob([data]).stream().pipeThrough(new DecompressionStream('deflate-raw')).pipeThrough(new TextDecoderStream('latin1'));
}

async function procYear(y) {
  const url = y < 2021 ? `/DatosAbiertos/AtencionesDeUrgencia/AtencionesUrgencia${y}.zip`
                       : `/SistemaAtencionesUrgencia/AtencionesUrgencia${y}.zip`;
  const buf = await (await fetch(url)).arrayBuffer();
  const rd = entryStream(buf).getReader(); let rest = '', ix = null;
  while (true) {
    const { value, done } = await rd.read(); if (done) break;
    const lines = (rest + value).split('\n'); rest = lines.pop();
    for (const L0 of lines) {
      const L = L0.replace(/\r$/, ''); if (!L) continue;
      if (!ix) {  // cabecera: el nombre de la columna de causa cambia entre años (IdCausa / Idcausa)
        ix = {}; L.replace(/^﻿/, '').split(';').forEach((h, i) => ix[h.trim().toLowerCase()] = i); continue;
      }
      const c = L.split(';');
      if (c[ix['glosatipoestablecimiento']] !== 'Hospital') continue;
      const col = CAUSAS[+c[ix['idcausa']]]; if (!col) continue;
      const [dd, mm, aaaa] = c[ix['fecha']].split('/');
      const k = c[ix['idestablecimiento']] + '|' + `${aaaa}-${mm.padStart(2, '0')}-${dd.padStart(2, '0')}`;
      let a = H.get(k); if (!a) { a = new Array(COLS.length).fill(0); H.set(k, a); }
      a[COLS.indexOf(col)] += +c[ix['total']] || 0;
    }
  }
}

// for (const y of [2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]) await procYear(y);
// Luego se exporta H como CSV: id_establecimiento,fecha,<COLS>
