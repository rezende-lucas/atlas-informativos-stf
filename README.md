# Atlas dos Informativos STF

Ferramenta de estudo dos Informativos do Supremo Tribunal Federal (1995–2026): 10.657 julgados, com busca, filtros, leitor, flashcards, índice por dispositivo legal e painel de temas de repercussão geral.

**Acesse:** https://rezende-lucas.github.io/atlas-informativos-stf/

## O que tem

- **Explorar**: busca sem acentos (aspas para frase, `-` para excluir), busca opcional no inteiro teor, filtros por ano, informativo, órgão, ramo, relator(a), classe, repercussão geral, tese e dispositivo legal. Leitor com tese, resumo, notícia completa, cópia da citação ou do julgado inteiro e modo tela cheia.
- **Revisar**: flashcards a partir dos julgados filtrados.
- **Panorama**: gráficos por ano, ramo, relatoria, classe e órgão.
- **Legislação**: diplomas e artigos citados nos julgados. Clique num artigo para ver os julgados que o citam.
- **Temas RG**: temas de repercussão geral com a tese e os julgados de cada um.

Julgados publicados no mesmo informativo com notícia idêntica (processos julgados em conjunto) aparecem unificados.

Favoritos, marcações de estudado e anotações ficam salvos apenas no navegador de quem usa.

## Estrutura

```
src/atlas.html        fonte da página
docs/                 site publicado no GitHub Pages (gerado)
  index.html
  data/               índice e inteiro teor em JSON
scripts/
  prep.py             planilha → docs/data
  legis.py            extração de diplomas e artigos do campo "Legislação"
  build_pages.py      src/atlas.html → docs/index.html
```

## Atualizar com uma planilha nova

Requer Python 3 com `pandas` e `openpyxl`.

```bash
python scripts/prep.py caminho/para/Dados_InformativosSTF.xlsx
python scripts/build_pages.py
git add -A && git commit -m "Atualiza dados" && git push
```

## Fonte dos dados

Planilha de dados dos Informativos do STF. Os textos são de autoria do Supremo Tribunal Federal. Este projeto não é oficial nem tem vínculo com o STF.
