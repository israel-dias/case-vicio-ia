/* Funções de consulta. Não alteram as decisões nem calculam precisão. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.VicioVisor = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const COLUNAS = ["id", "decisao", "tema_central_id", "extras_ids", "confianca", "motivo"];
  function normalizar(valor) {
    return String(valor ?? "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  }
  function textoBusca(registro) {
    const q = registro.questao;
    return normalizar([registro.id, q.enunciado, q.comando,
      ...Object.values(q.alternativas), registro.atual.central?.caminho,
      ...registro.atual.extras.map(t => t.caminho), registro.analise, registro.fundamento,
      q.disciplina_origem, q.assunto_origem].join(" "));
  }
  function termosBusca(valor) {
    const busca = String(valor ?? "").trim();
    const id = busca.match(/^q?([0-9]{1,4})$/i);
    return normalizar(id ? "Q" + id[1].padStart(4, "0") : busca).split(/\s+/).filter(Boolean);
  }
  function filtrar(registros, filtros = {}) {
    const termos = termosBusca(filtros.busca);
    return registros.filter(r => {
      if (filtros.decisao && r.atual.decisao !== filtros.decisao) return false;
      const temas = [r.atual.central, ...r.atual.extras].filter(Boolean);
      if (filtros.disciplina && !temas.some(t => t.disciplina === filtros.disciplina)) return false;
      if (filtros.tema && !temas.some(t => t.tema_id === filtros.tema)) return false;
      if (filtros.evidencia && r.estado_resposta !== filtros.evidencia) return false;
      if (filtros.mudanca && !r.mudancas[filtros.mudanca]) return false;
      const texto = r._busca ?? textoBusca(r);
      return termos.every(t => texto.includes(t));
    });
  }
  function ordenar(registros, criterio = "id") {
    const ordem = {revisar: 0, fora: 1, publicar: 2};
    return [...registros].sort((a, b) => {
      const delta = criterio === "decisao" ? ordem[a.atual.decisao] - ordem[b.atual.decisao] : 0;
      return delta || a.id.localeCompare(b.id);
    });
  }
  function celulaCsv(valor) {
    let texto = String(valor ?? "");
    // Protege exportações abertas em planilhas; não modifica o CSV oficial.
    if (/^[\s]*[=+@-]/.test(texto)) texto = "'" + texto;
    return '"' + texto.replace(/"/g, '""') + '"';
  }
  function exportarCsv(registros) {
    return [COLUNAS.map(celulaCsv).join(","),
      ...registros.map(r => COLUNAS.map(c => celulaCsv(r.atual[c])).join(","))].join("\r\n") + "\r\n";
  }
  function urlSegura(valor) {
    try { const u = new URL(String(valor)); return u.protocol === "https:" ? u.href : null; }
    catch (_) { return null; }
  }
  return {COLUNAS, normalizar, textoBusca, termosBusca, filtrar, ordenar, exportarCsv, urlSegura};
});
