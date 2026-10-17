# Visor de auditoria

Interface local para consultar as 359 questões e os registros incorporados à entrega.

## Abrir no Ubuntu

Na raiz do projeto:

```bash
python gerar_visor.py
xdg-open visor/index.html
```

Também é possível abrir `visor/index.html` com dois cliques. O arquivo contém os dados, estilos e scripts: pode ser copiado sozinho e aberto sem servidor, instalação de pacotes ou chave de API. A consulta funciona sem internet; os links para fontes e arquivos do GitHub exigem conexão quando abertos.

O GitHub exibe o código de arquivos HTML. Para usar a interface, baixe o arquivo e abra-o no navegador, ou use a cópia local do repositório.

## O que consultar

- Todas as questões ou os recortes publicar, revisar, fora e decisões alteradas.
- Busca por ID, texto e tema, com ou sem acento. `Q97`, `97` e `Q0097` encontram a mesma questão.
- Filtros por ramo do enquadramento, tema central ou extra, evidência da resposta e tipo de mudança.
- Enunciado, comando e todas as alternativas, incluindo Certo/Errado.
- Central, caminho completo, extras, confiança declarada e análise individual.
- Comparação com a consolidação v3. Esta é a referência do campo `antes`; os estágios intermediários permanecem no histórico.
- Gabaritos oficiais, respostas assistidas, pendências e fontes, com seus limites.
- Exportação do recorte filtrado em CSV e download do parecer de uma questão em TXT.

Os cartões representam toda a entrega. O contador acima da lista representa o recorte filtrado. Ramo e tema consideram o enquadramento atual, incluindo extras.

Na lateral estão os exemplos para apresentação: Q0171, Q0353, Q0337, Q0097, Q0355 e Q0298. O atalho `/` leva à busca. As abas aceitam as setas esquerda/direita. O endereço termina com o ID selecionado, por exemplo `index.html#Q0097`.

## Fidelidade e limites

Antes de gerar o HTML, o script reutiliza a validação do exportador e confere se `publicacao.csv` e `previsao.txt` da raiz correspondem à auditoria. Se houver divergência, a geração é interrompida e o visor anterior é preservado.

Os dados vêm das questões preparadas, de `auditoria_v4/reexame_359.json`, do catálogo e dos índices de fontes. Textos são exibidos como texto, sem executar HTML recebido nas questões. Links externos aceitam apenas HTTPS. O CSV de consulta neutraliza conteúdo que poderia ser interpretado como fórmula de planilha.

O visor não altera classificações, não faz chamadas de IA e não mede precisão. A confiança é subjetiva, sem calibração. Gabaritos da prova confirmam respostas, não rótulos temáticos. Os SHA-256 dos arquivos apresentados estão em **Como ler → Identificar os arquivos usados neste visor**.

Ao atualizar classificações, conclua e confira primeiro a nova entrega da raiz; depois regenere o visor. O HTML é uma fotografia dos registros no momento da geração.

## Arquivos

- `gerar_visor.py`: valida e incorpora os dados ao HTML.
- `visor/modelo.html`: estrutura da interface.
- `visor/estilos.css`: apresentação responsiva.
- `visor/filtros.js`: busca, filtros, ordenação e exportação.
- `visor/app.js`: navegação e apresentação dos registros.
- `visor/index.html`: arquivo gerado, pronto para abrir ou compartilhar.
- `tests/test_visor.py`: fidelidade, geração, preservação da entrega e rejeição de divergências.
- `tests/visor_filtros.test.cjs`: testes opcionais de desenvolvimento dos filtros, com Node (`node --test tests/visor_filtros.test.cjs`). Node não é necessário para gerar ou usar o visor.
