(function () {
  "use strict";
  const $ = id => document.getElementById(id);
  const C = window.VicioVisor;
  const ROTULOS = {publicar: "Publicar", revisar: "Revisar", fora: "Fora do recorte"};
  const EVIDENCIAS = {
    gabarito_oficial_definitivo: ["Gabarito oficial definitivo", "official"],
    gabarito_oficial_preliminar: ["Gabarito oficial preliminar", "preliminary"],
    resposta_assistida_sem_gabarito_oficial_confirmado: ["Resposta assistida", "assisted"],
    resposta_nao_confirmada: ["Resposta não confirmada", "unconfirmed"]
  };
  function el(tag, classe, texto) {
    const item = document.createElement(tag);
    if (classe) item.className = classe;
    if (texto !== undefined && texto !== null) item.textContent = String(texto);
    return item;
  }
  function icon(nome) {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    const use = document.createElementNS(svg.namespaceURI, "use");
    svg.setAttribute("aria-hidden", "true");
    use.setAttribute("href", "#i-" + nome);
    svg.append(use);
    return svg;
  }
  function pct(valor, casas = 0) {
    return new Intl.NumberFormat("pt-BR", {style: "percent", maximumFractionDigits: casas}).format(valor);
  }
  function badge(decisao) { return el("span", "badge " + decisao, ROTULOS[decisao]); }
  function tagEvidencia(estado) {
    const [texto, classe] = EVIDENCIAS[estado] || EVIDENCIAS.resposta_nao_confirmada;
    return el("span", "badge " + classe, texto);
  }
  function link(texto, url) {
    const segura = C.urlSegura(url);
    if (!segura) return el("span", "muted-note", texto + " — endereço indisponível");
    const a = el("a", "", texto);
    a.href = segura;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    return a;
  }
  let dados;
  try {
    dados = JSON.parse($("base-auditoria").textContent);
    if (!Array.isArray(dados.registros) || dados.registros.length !== dados.meta.total) throw new Error("Base incompleta");
  } catch (_) {
    $("detail-panel").append(el("div", "fatal", "Não foi possível ler os dados deste visor. Gere o arquivo novamente com python gerar_visor.py."));
    $("result-count").textContent = "Dados indisponíveis";
    $("export-csv").disabled = true;
    return;
  }
  const porId = new Map(dados.registros.map(r => [r.id, r]));
  for (const r of dados.registros) r._busca = C.textoBusca(r);
  const filtrosVazios = () => ({busca: "", decisao: "", disciplina: "", tema: "", evidencia: "", mudanca: ""});
  const estado = {filtros: filtrosVazios(), ordem: "id", selecionado: null, aba: "questao", resultados: []};
  let avisoTimer;
  function aviso(texto) {
    clearTimeout(avisoTimer);
    $("toast").textContent = texto;
    $("toast").hidden = false;
    avisoTimer = setTimeout(() => { $("toast").hidden = true; }, 3500);
  }
  function arquivoRepositorio(caminho) {
    return dados.meta.repositorio + "/blob/main/" + caminho.split("/").map(encodeURIComponent).join("/");
  }
  function baixar(nome, texto, tipo) {
    const url = URL.createObjectURL(new Blob([texto], {type: tipo}));
    const a = el("a");
    a.href = url;
    a.download = nome;
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    aviso("Arquivo preparado: " + nome);
  }
  function sincronizarControles() {
    const ids = {busca: "search", decisao: "decision", disciplina: "discipline", tema: "theme", evidencia: "evidence", mudanca: "change"};
    for (const [campo, id] of Object.entries(ids)) $(id).value = estado.filtros[campo];
    $("sort").value = estado.ordem;
  }
  function atualizarNavegacao() {
    document.querySelectorAll("[data-scope]").forEach(b => {
      const scope = b.dataset.scope;
      const ativo = scope === "alteradas" ? estado.filtros.mudanca === "decisao" && !estado.filtros.decisao
        : scope === estado.filtros.decisao && !estado.filtros.mudanca;
      b.classList.toggle("active", ativo);
      b.setAttribute("aria-pressed", String(ativo));
    });
  }
  function atualizarHash() {
    if (!estado.selecionado) return;
    const hash = "#" + estado.selecionado;
    if (location.hash === hash) return;
    try { history.replaceState(null, "", hash); }
    catch (_) { location.hash = hash; }
  }
  function renderizarLista() {
    const lista = $("question-list");
    const fragmento = document.createDocumentFragment();
    if (!estado.resultados.length) {
      const vazio = el("div", "empty");
      vazio.append(el("strong", "", "Nenhuma questão neste recorte"), el("span", "", "Tente outro termo ou limpe os filtros."));
      fragmento.append(vazio);
    }
    for (const r of estado.resultados) {
      const b = el("button", "question-row" + (r.id === estado.selecionado ? " selected" : ""));
      b.type = "button";
      b.dataset.id = r.id;
      b.setAttribute("aria-pressed", String(r.id === estado.selecionado));
      const topo = el("span", "row-top");
      topo.append(el("span", "row-id", r.id), badge(r.atual.decisao));
      b.append(topo, el("span", "row-title", r.atual.central?.titulo || "Sem tema ativo compatível"),
        el("span", "row-excerpt", r.questao.enunciado));
      if (r.mudancas.qualquer) {
        const campos = [];
        if (r.mudancas.decisao) campos.push("decisão");
        if (r.mudancas.central) campos.push("central");
        if (r.mudancas.extras) campos.push("extras");
        const mudanca = el("span", "row-change");
        mudanca.append(icon("change"), document.createTextNode("Mudou: " + campos.join(", ")));
        b.append(mudanca);
      }
      fragmento.append(b);
    }
    lista.replaceChildren(fragmento);
  }
  function linhaTema(tema) {
    const frag = document.createDocumentFragment();
    if (!tema) {
      frag.append(el("p", "theme-title", "Sem tema selecionado"));
      return frag;
    }
    const titulo = el("p", "theme-title", tema.titulo);
    titulo.append(el("span", "theme-id", "ID " + tema.tema_id));
    frag.append(titulo, el("p", "theme-path", tema.caminho));
    return frag;
  }
  function secao(titulo) {
    const div = el("section", "subsection");
    div.append(el("h3", "", titulo));
    return div;
  }
  function confianca(classificacao) {
    if (classificacao.decisao === "fora") return "Confiança no central: 0,00 — convenção de ausência de tema.";
    return "Confiança declarada no central: " + pct(Number(classificacao.confianca)) + " · julgamento subjetivo, não calibrado.";
  }
  function respostaTexto(r) {
    if (!r.resposta) return "Resposta não confirmada";
    const alternativas = r.questao.alternativas;
    if (Object.keys(alternativas).join("") === "CE") return r.resposta + " · " + (alternativas[r.resposta] || "Resposta registrada");
    return "Alternativa " + r.resposta;
  }
  function conteudoQuestao(r) {
    const frag = document.createDocumentFragment();
    if (r.questao.alertas_preparacao.length) {
      frag.append(el("p", "alert", "Atenção ao conteúdo: " + r.questao.alertas_preparacao.map(x => typeof x === "string" ? x : JSON.stringify(x)).join("; ")));
    }
    frag.append(el("p", "section-label", "ENUNCIADO"), el("p", "question-text", r.questao.enunciado || "Enunciado ausente no dado preparado."));
    if (r.questao.comando) frag.append(el("p", "command", r.questao.comando));
    if (Object.keys(r.questao.alternativas).length) {
      frag.append(el("p", "section-label", "ALTERNATIVAS"));
      const opcoes = el("div", "options");
      const evidencia = EVIDENCIAS[r.estado_resposta][1];
      for (const [chave, texto] of Object.entries(r.questao.alternativas)) {
        const marcada = chave === r.resposta;
        const item = el("div", "option" + (marcada ? " marked " + evidencia : ""));
        if (marcada) item.setAttribute("aria-label", respostaTexto(r) + "; " + EVIDENCIAS[r.estado_resposta][0]);
        item.append(el("span", "option-key", chave), el("p", "option-text", texto));
        opcoes.append(item);
      }
      frag.append(opcoes);
    }
    const resposta = el("div", "answer-box");
    resposta.append(tagEvidencia(r.estado_resposta), el("p", "answer-value", respostaTexto(r)));
    const nota = r.gabarito ? "A confirmação refere-se à resposta da prova. Ela não certifica o ID temático do catálogo."
      : r.resposta ? "Resolução formulada pelo assistente, sem gabarito oficial da prova confirmado."
      : "A pendência está preservada. Não foi atribuído um gabarito para preencher a lacuna.";
    resposta.append(el("p", "", nota));
    frag.append(resposta);
    const enquadramento = secao("Enquadramento proposto");
    const box = el("div", "classification-box");
    box.append(el("p", "section-label", "TEMA CENTRAL"), linhaTema(r.atual.central));
    enquadramento.append(box);
    if (r.atual.extras.length) {
      const extras = el("div", "extra-list");
      for (const t of r.atual.extras) {
        const div = el("div", "extra-item");
        div.append(el("p", "section-label", "CONTEÚDO ADICIONAL"), linhaTema(t));
        if (r.justificativas_extras[t.tema_id]) div.append(el("p", "extra-reason", r.justificativas_extras[t.tema_id]));
        extras.append(div);
      }
      enquadramento.append(extras);
    }
    enquadramento.append(el("p", "confidence", confianca(r.atual)));
    frag.append(enquadramento);
    const analise = secao("Por que essa decisão?");
    analise.append(el("p", "analysis", r.analise));
    frag.append(analise);
    const metadados = el("details", "details-meta");
    metadados.append(el("summary", "", "Metadados de origem e descrição do catálogo"),
      el("p", "", "Disciplina de origem: " + (r.questao.disciplina_origem || "não informada")),
      el("p", "", "Assunto de origem: " + (r.questao.assunto_origem || "não informado")),
      el("p", "", "Os metadados de origem são pistas; não são rótulos temáticos validados."));
    if (r.atual.central) metadados.append(el("p", "", "Descrição do tema central: " + (r.atual.central.descricao || "ausente no catálogo")));
    frag.append(metadados);
    return frag;
  }
  function conteudoComparacao(r) {
    const frag = document.createDocumentFragment();
    frag.append(el("p", "muted-note", "A comparação usa a consolidação v3 e o reexame incorporado à entrega atual. Etapas intermediárias estão preservadas no histórico. Mudanças não comprovam, por si só, aumento de precisão."));
    const resumo = el("div", "change-summary");
    for (const [campo, titulo] of [["decisao", "Decisão alterada"], ["central", "Central alterado"], ["extras", "Extras alterados"]]) {
      if (r.mudancas[campo]) resumo.append(el("span", "change-pill", titulo));
    }
    if (!r.mudancas.qualquer) resumo.append(el("span", "change-pill", "Decisão, central e extras preservados"));
    frag.append(resumo);
    const colunas = el("div", "comparison");
    for (const [chave, titulo] of [["antes", "CONSOLIDAÇÃO V3"], ["atual", "ENTREGA ATUAL"]]) {
      const c = r[chave];
      const card = el("div", "comparison-card" + (chave === "atual" ? " current" : ""));
      card.append(el("p", "section-label", titulo), badge(c.decisao), linhaTema(c.central));
      const extras = secao("Extras");
      if (!c.extras.length) extras.append(el("p", "analysis", "Nenhum extra registrado."));
      for (const t of c.extras) {
        const item = el("div", "extra-item");
        item.append(linhaTema(t));
        extras.append(item);
      }
      card.append(extras, el("p", "confidence", confianca(c)));
      const motivo = secao("Justificativa registrada");
      motivo.append(el("p", "analysis", c.motivo));
      card.append(motivo);
      colunas.append(card);
    }
    frag.append(colunas);
    return frag;
  }
  function conteudoFontes(r) {
    const frag = document.createDocumentFragment();
    frag.append(el("h3", "", "Resposta e evidências registradas"));
    const status = el("div", "source-card");
    status.append(tagEvidencia(r.estado_resposta), el("p", "answer-value", respostaTexto(r)));
    if (r.gabarito) {
      const g = r.gabarito;
      status.append(el("p", "", g.banca + " · " + g.concurso),
        el("p", "", "Prova tipo " + g.tipo + ", questão " + g.numero + ". Resposta registrada: " + g.resposta + "."),
        el("p", "", "Página da prova (PDF): " + g.pagina_prova_pdf + "; página do gabarito: " + g.pagina_gabarito_pdf + "."),
        el("p", "", g.conferencia));
      const links = el("div", "source-links");
      links.append(link("Prova oficial (PDF) ↗", g.prova_url), link("Gabarito da prova (PDF) ↗", g.gabarito_url));
      status.append(links);
    } else status.append(el("p", "", "Não há gabarito oficial de prova confirmado neste registro. A resposta, quando presente, permanece assistida."));
    status.append(el("p", "", "Nenhum desses estados equivale ao rótulo temático reservado pelos especialistas da empresa."));
    frag.append(status);
    const fundamento = secao("Fundamento indicado no parecer");
    fundamento.append(el("p", "analysis", r.fundamento), el("p", "muted-note", "Referências indicadas e consultas efetivamente registradas têm alcances distintos. Não se presume validação integral de todos os fundamentos."));
    frag.append(fundamento);
    if (r.conferencias.length) {
      const consultas = secao("Conferências dirigidas registradas");
      const lista = el("ul", "reference-list");
      for (const texto of r.conferencias) lista.append(el("li", "", texto));
      consultas.append(lista);
      frag.append(consultas);
    }
    if (r.fontes.length) {
      const fontes = secao("Fontes da reavaliação dirigida");
      for (const f of r.fontes) {
        const item = el("div", "source-card");
        item.append(el("h4", "", f.fonte), el("p", "", "Alcance registrado: " + String(f.estado).replace(/_/g, " ")));
        if (f.artigos?.length) item.append(el("p", "", "Referências: " + f.artigos.join("; ")));
        if (f.limite) item.append(el("p", "", "Limite da consulta: " + f.limite));
        const links = el("div", "source-links");
        links.append(link("Consultar fonte ↗", f.url));
        item.append(links);
        fontes.append(item);
      }
      frag.append(fontes);
    }
    const pesquisa = secao("Rastreabilidade da pesquisa");
    pesquisa.append(el("p", "muted-note", "O registro de busca contém pistas. Quantidade de resultados e correspondências com PDFs não confirmam gabaritos."));
    const links = el("div", "source-links");
    links.append(link("Registro de busca deste ID ↗", arquivoRepositorio(r.busca)),
      link("Índices de fontes ↗", arquivoRepositorio("auditoria_v4/fontes")),
      link("Protocolo da auditoria ↗", arquivoRepositorio("auditoria_v4/PROTOCOLO_FINAL.md")));
    pesquisa.append(links);
    frag.append(pesquisa);
    return frag;
  }
  function parecerTexto(r) {
    return ["CASE VÍCIO IA — REGISTRO DE AUDITORIA", r.id, "",
      "Decisão: " + ROTULOS[r.atual.decisao], "Central: " + (r.atual.central?.caminho || "nenhum"),
      "Extras: " + (r.atual.extras.map(t => t.caminho).join("; ") || "nenhum"),
      "Resposta: " + respostaTexto(r), "Estado: " + EVIDENCIAS[r.estado_resposta][0],
      confianca(r.atual), "", "ENUNCIADO", r.questao.enunciado, "", r.questao.comando,
      ...Object.entries(r.questao.alternativas).map(([k, t]) => k + ") " + t),
      "", "ANÁLISE", r.analise, "", "FUNDAMENTO INDICADO", r.fundamento,
      "", "CONFERÊNCIAS REGISTRADAS", ...r.conferencias,
      "", "ANTES (V3)", "Decisão: " + ROTULOS[r.antes.decisao],
      "Central: " + (r.antes.central?.caminho || "nenhum"),
      "Extras: " + (r.antes.extras.map(t => t.caminho).join("; ") || "nenhum"),
      "Motivo: " + r.antes.motivo, "",
      "Precisão temática não medida. Respostas de prova não certificam os IDs temáticos.",
      "Classificação de " + r.data_reexame + ". CSV SHA-256: " + dados.meta.arquivos_sha256["publicacao.csv"],
      "Repositório: " + dados.meta.repositorio].join("\n");
  }
  function selecionarAba(nome, foco = false) {
    estado.aba = nome;
    document.querySelectorAll(".tab").forEach(b => {
      const ativa = b.dataset.tab === nome;
      b.setAttribute("aria-selected", String(ativa));
      b.tabIndex = ativa ? 0 : -1;
      if (ativa && foco) b.focus();
    });
    document.querySelectorAll(".tab-panel").forEach(p => { p.hidden = p.id !== "painel-" + nome; });
  }
  function renderizarDetalhe() {
    const painel = $("detail-panel");
    const r = porId.get(estado.selecionado);
    if (!r) {
      const vazio = el("div", "empty");
      vazio.append(el("strong", "", "O recorte está vazio"), el("p", "", "Altere a busca ou limpe os filtros para consultar um registro."));
      const b = el("button", "button", "Limpar filtros");
      b.type = "button";
      b.addEventListener("click", limpar);
      vazio.append(b);
      painel.replaceChildren(vazio);
      return;
    }
    const cabecalho = el("header", "detail-heading");
    const topo = el("div", "detail-topline");
    topo.append(el("span", "detail-id", r.id), badge(r.atual.decisao));
    cabecalho.append(topo, el("h2", "detail-title", r.atual.central?.titulo || "Sem tema ativo compatível"),
      el("p", "detail-breadcrumb", r.atual.central?.caminho || "A análise não identificou um enquadramento ativo adequado no catálogo."));
    const abas = el("div", "detail-tabs");
    abas.setAttribute("role", "tablist");
    abas.setAttribute("aria-label", "Conteúdo da questão " + r.id);
    const nomes = [["questao", "Questão e parecer"], ["comparacao", "Antes e depois"], ["fontes", "Evidências"]];
    const paineis = [];
    for (const [nome, titulo] of nomes) {
      const b = el("button", "tab", titulo);
      b.type = "button";
      b.id = "aba-" + nome;
      b.dataset.tab = nome;
      b.setAttribute("role", "tab");
      b.setAttribute("aria-controls", "painel-" + nome);
      b.addEventListener("click", () => selecionarAba(nome));
      b.addEventListener("keydown", evento => {
        if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(evento.key)) return;
        evento.preventDefault();
        let i = nomes.findIndex(n => n[0] === estado.aba);
        i = evento.key === "Home" ? 0 : evento.key === "End" ? nomes.length - 1 : (i + (evento.key === "ArrowRight" ? 1 : -1) + nomes.length) % nomes.length;
        selecionarAba(nomes[i][0], true);
      });
      abas.append(b);
      const conteudo = el("section", "tab-panel");
      conteudo.id = "painel-" + nome;
      conteudo.setAttribute("role", "tabpanel");
      conteudo.setAttribute("aria-labelledby", b.id);
      conteudo.tabIndex = 0;
      conteudo.append(nome === "questao" ? conteudoQuestao(r) : nome === "comparacao" ? conteudoComparacao(r) : conteudoFontes(r));
      const acoes = el("div", "detail-actions");
      const baixarParecer = el("button", "button");
      baixarParecer.type = "button";
      baixarParecer.append(icon("download"), document.createTextNode("Baixar parecer"));
      baixarParecer.addEventListener("click", () => baixar(r.id + "_parecer.txt", parecerTexto(r), "text/plain;charset=utf-8"));
      acoes.append(baixarParecer, link("Registro completo da auditoria ↗", arquivoRepositorio("auditoria_v4/reexame_359.json")));
      conteudo.append(acoes);
      paineis.push(conteudo);
    }
    painel.replaceChildren(cabecalho, abas, ...paineis);
    selecionarAba(estado.aba);
  }
  function renderizar() {
    estado.resultados = C.ordenar(C.filtrar(dados.registros, estado.filtros), estado.ordem);
    if (!estado.resultados.some(r => r.id === estado.selecionado)) estado.selecionado = estado.resultados[0]?.id || null;
    const n = estado.resultados.length;
    $("result-count").textContent = n + (n === 1 ? " questão encontrada" : " questões encontradas") + " · " + dados.meta.total + " no total";
    $("export-csv").disabled = !n;
    atualizarNavegacao();
    renderizarLista();
    renderizarDetalhe();
    atualizarHash();
  }
  function limpar() {
    estado.filtros = filtrosVazios();
    sincronizarControles();
    renderizar();
  }
  const meta = dados.meta;
  $("nav-total").textContent = meta.total;
  for (const d of ["publicar", "revisar", "fora"]) {
    $("nav-" + d).textContent = meta.decisoes[d] || 0;
    $("metric-" + d).textContent = meta.decisoes[d] || 0;
    const segmento = el("span", d);
    segmento.style.width = (((meta.decisoes[d] || 0) / meta.total) * 100).toFixed(8) + "%";
    $("coverage-track").append(segmento);
  }
  $("nav-alteradas").textContent = meta.mudancas.decisao;
  $("metric-cobertura").textContent = pct(meta.cobertura, 2);
  $("coverage-caption").textContent = meta.decisoes.publicar + " de " + meta.total + " questões";
  $("forecast").textContent = pct(meta.precisao_prevista_subjetiva);
  $("snapshot-info").textContent = "Dados de 16/10/2026 · CSV " + meta.arquivos_sha256["publicacao.csv"].slice(0, 12);
  $("repo-link").href = meta.repositorio;
  for (const d of [...new Set(dados.temas.map(t => t.disciplina))].sort()) $("discipline").append(new Option(d, d));
  for (const t of dados.temas) $("theme").append(new Option(t.caminho + " · ID " + t.tema_id, t.tema_id));
  for (const [nome, hash] of Object.entries(meta.arquivos_sha256)) {
    const p = el("p", "", nome + "\n");
    p.append(el("code", "", hash));
    $("source-hashes").append(p);
  }
  const abrirGuia = () => $("help-dialog").showModal();
  $("help-open").addEventListener("click", abrirGuia);
  $("limits-open").addEventListener("click", abrirGuia);
  $("help-close").addEventListener("click", () => $("help-dialog").close());
  $("help-dialog").addEventListener("click", e => { if (e.target === $("help-dialog")) $("help-dialog").close(); });
  document.querySelectorAll("[data-scope]").forEach(b => b.addEventListener("click", () => {
    estado.filtros = filtrosVazios();
    if (b.dataset.scope === "alteradas") estado.filtros.mudanca = "decisao";
    else estado.filtros.decisao = b.dataset.scope;
    estado.aba = "questao";
    sincronizarControles();
    renderizar();
  }));
  document.querySelectorAll("[data-example]").forEach(b => b.addEventListener("click", () => {
    estado.filtros = {...filtrosVazios(), busca: b.dataset.example};
    estado.selecionado = b.dataset.example;
    estado.aba = "questao";
    sincronizarControles();
    renderizar();
  }));
  for (const [id, campo] of [["search", "busca"], ["decision", "decisao"], ["discipline", "disciplina"], ["theme", "tema"], ["evidence", "evidencia"], ["change", "mudanca"]]) {
    $(id).addEventListener(id === "search" ? "input" : "change", () => {
      estado.filtros[campo] = $(id).value;
      renderizar();
    });
  }
  $("sort").addEventListener("change", () => { estado.ordem = $("sort").value; renderizar(); });
  $("clear").addEventListener("click", limpar);
  $("question-list").addEventListener("click", evento => {
    const b = evento.target.closest("[data-id]");
    if (!b || !porId.has(b.dataset.id)) return;
    estado.selecionado = b.dataset.id;
    $("question-list").querySelectorAll("[data-id]").forEach(linha => {
      const selecionada = linha.dataset.id === estado.selecionado;
      linha.classList.toggle("selected", selecionada);
      linha.setAttribute("aria-pressed", String(selecionada));
    });
    renderizarDetalhe();
    atualizarHash();
  });
  $("export-csv").addEventListener("click", () => {
    if (!estado.resultados.length) return;
    baixar("recorte_" + estado.resultados.length + "_questoes.csv", "\uFEFF" + C.exportarCsv(estado.resultados), "text/csv;charset=utf-8");
  });
  document.addEventListener("keydown", e => {
    const tag = document.activeElement?.tagName;
    if (e.key === "/" && !["INPUT", "TEXTAREA", "SELECT"].includes(tag) && !$("help-dialog").open) {
      e.preventDefault();
      $("search").focus();
    }
  });
  function idHash() { return /^#Q[0-9]{4}$/i.test(location.hash) ? location.hash.slice(1).toUpperCase() : null; }
  const inicial = idHash();
  if (porId.has(inicial)) estado.selecionado = inicial;
  window.addEventListener("hashchange", () => {
    const id = idHash();
    if (!id || !porId.has(id) || id === estado.selecionado) return;
    if (!estado.resultados.some(r => r.id === id)) { estado.filtros = filtrosVazios(); sincronizarControles(); }
    estado.selecionado = id;
    renderizar();
  });
  renderizar();
})();
