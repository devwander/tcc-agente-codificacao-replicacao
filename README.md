# Pacote de replicação: estudo de caso com um agente de codificação

Material de replicação do Trabalho de Graduação **"Esforço, Produtividade e Percepção de
Qualidade no Desenvolvimento de Software com um Agente de Codificação por IA: um Estudo de Caso
Longitudinal"** (Bacharelado em Sistemas de Informação, Universidade de Pernambuco, Campus
Caruaru, 2026). O estudo analisa o desenvolvimento de uma plataforma clínica real com o
Claude Code, de 29 de julho a 31 de outubro de 2026: 327 sessões do agente e 282 merge requests.

Versão atual: **v1.2**. DOI de todas as versões (aponta sempre para a mais recente): [10.5281/zenodo.24278834](https://doi.org/10.5281/zenodo.24278834). Os dados e os resultados são os mesmos das versões anteriores; na v1.2, o produto estudado e a empresa titular foram anonimizados (ver `integridade/`), e as versões anteriores, que traziam o nome do produto, foram retiradas.

A ferramenta de coleta é publicada à parte, em
<https://github.com/devwander/ai-development-analytics> (tag `v1.0.1-tcc`, DOI de todas as versões
[10.5281/zenodo.24278832](https://doi.org/10.5281/zenodo.24278832)).

## Conteúdo

| Pasta | O que tem | Seção da monografia |
|---|---|---|
| `analise/` | Scripts de extração e análise, dependências e guia de reprodução (`COMO-REPRODUZIR.md`) | 4.5, 4.7, Apêndice C |
| `resultados/` | Todos os números do Capítulo 5 (`resultados_v3.json`), a análise de sensibilidade com a reorganização incluída, a tabela por módulo (`modulos.csv`) e as figuras | Cap. 5 |
| `instrumentos/` | Instrumento de percepção respondido e congelado (com SHA-256), livro de códigos v1.2, exemplos sintéticos, prompt-protocolo (texto exato) e prompt de classificação | 4.6, Apêndices A e B |
| `integridade/` | Resumos SHA-256 dos dados brutos não publicados e referências Git do caso | Apêndice C |

## O que não está aqui, e por quê

O produto estudado pertence a uma empresa e é uma plataforma clínica, sujeita à Lei Geral de
Proteção de Dados Pessoais (LGPD). Por isso **não são publicados**: o código-fonte do produto, os
transcritos das sessões, a base da ferramenta de coleta, os prompts do desenvolvedor (inclusive a
amostra de 60 intervenções codificada para o kappa) e a cópia do repositório Git. Os resumos
SHA-256 em `integridade/` identificam cada um desses artefatos, o que permite uma auditoria
autorizada. Essa restrição segue as diretrizes de Baltes et al. (2027) para estudos com modelos
de linguagem, que admitem resumos e exemplos quando registros de sessão não podem ser divulgados.

## Reprodução

Sem os dados brutos, é possível conferir: (1) as definições operacionais, lendo os scripts; (2) os
números da monografia, que estão todos em `resultados/`; (3) as correlações da Seção 5.6, a partir
de `modulos.csv` e do instrumento respondido; e (4) a integridade, pelos resumos SHA-256. Com
acesso aos dados, `analise/COMO-REPRODUZIR.md` descreve a sequência completa.

## Licenças e citação

Código: MIT (`LICENSE`). Dados agregados, instrumentos e documentos: CC BY 4.0
(`LICENSE-DADOS.md`). Para citar, use `CITATION.cff`.
