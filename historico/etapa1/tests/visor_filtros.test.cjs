// Verificação de desenvolvimento: node --test tests/visor_filtros.test.cjs
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const C = require('../visor/filtros.js');
const html = fs.readFileSync(path.join(__dirname, '../visor/index.html'), 'utf8');
const dados = JSON.parse(html.match(/<script type="application\/json" id="base-auditoria">(.*?)<\/script>/s)[1]);
const registros = dados.registros;

test('os recortes correspondem ao CSV e preservam os cinco fora', () => {
  for (const [decisao, quantidade] of Object.entries(dados.meta.decisoes)) {
    assert.equal(C.filtrar(registros, {decisao}).length, quantidade);
  }
  assert.deepEqual(C.filtrar(registros, {decisao: 'fora'}).map(r => r.id),
    ['Q0039', 'Q0113', 'Q0142', 'Q0168', 'Q0298']);
  assert.equal(C.filtrar(registros, {mudanca: 'decisao'}).length, 107);
  assert.equal(C.filtrar(registros, {mudanca: 'central'}).length, 79);
  assert.equal(C.filtrar(registros, {mudanca: 'extras'}).length, 64);
});
test('a busca aceita ID abreviado, acentos e todos os termos', () => {
  assert.deepEqual(C.filtrar(registros, {busca: 'q97'}).map(r => r.id), ['Q0097']);
  assert.deepEqual(C.filtrar(registros, {busca: '97'}).map(r => r.id), ['Q0097']);
  assert.deepEqual(C.filtrar(registros, {busca: 'TRÁFICO'}).map(r => r.id),
    C.filtrar(registros, {busca: 'trafico'}).map(r => r.id));
  assert.ok(C.filtrar(registros, {busca: 'organizações concurso'}).some(r => r.id === 'Q0097'));
  assert.equal(C.filtrar(registros, {busca: 'expressaoquejamaisconstanabase'}).length, 0);
});
test('tema também encontra extras e os filtros podem ser combinados', () => {
  assert.ok(C.filtrar(registros, {tema: '5067'}).some(r => r.id === 'Q0097'));
  assert.deepEqual(C.filtrar(registros, {evidencia: 'gabarito_oficial_definitivo'}).map(r => r.id), ['Q0097', 'Q0355']);
  assert.deepEqual(C.filtrar(registros, {evidencia: 'gabarito_oficial_definitivo', decisao: 'revisar'}).map(r => r.id), ['Q0355']);
  for (const r of C.filtrar(registros, {disciplina: 'Processo Penal'})) {
    assert.ok([r.atual.central, ...r.atual.extras].filter(Boolean).some(t => t.disciplina === 'Processo Penal'));
  }
});
test('ordenar e exportar não modificam as decisões ou a ordem original', () => {
  const antes = JSON.stringify(registros);
  const ordem = C.ordenar(registros, 'decisao');
  assert.equal(ordem[0].atual.decisao, 'revisar');
  assert.ok(C.exportarCsv(ordem).startsWith('"id","decisao","tema_central_id","extras_ids","confianca","motivo"'));
  assert.equal(JSON.stringify(registros), antes);
});
test('o CSV escapa aspas/quebras e neutraliza fórmulas de planilha', () => {
  const r = {...registros[0], atual: {...registros[0].atual, motivo: 'á, "texto"\nsegunda linha'}};
  assert.ok(C.exportarCsv([r]).includes('"á, ""texto""\nsegunda linha"'));
  r.atual.motivo = '=1+1';
  assert.ok(C.exportarCsv([r]).includes('"\'=1+1"'));
});
test('somente HTTPS é transformado em link externo', () => {
  assert.equal(C.urlSegura('javascript:alert(1)'), null);
  assert.equal(C.urlSegura('data:text/html,abc'), null);
  assert.equal(C.urlSegura('http://example.org'), null);
  assert.equal(C.urlSegura('https://www.planalto.gov.br/'), 'https://www.planalto.gov.br/');
});
