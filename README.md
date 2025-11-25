
# Simulador de Tomasulo

Este repositório contém o projeto do Simulador de Tomasulo

- Simulador_de_tomasulo → versão principal do aplicativo com a main e
  
# Integrantes
- Juan Pablo Ramos de Oliveira
- Júlia Pinheiro Roque
- Luís Fernando Rodrigues Braga
- Luiz Gabriel Milione Assis

---

## Pré-requisitos

Antes de rodar os projetos, certifique-se de ter instalado:

- [Python](https://www.python.org/)

---
Estrutura do repositório
Simulador_de_tomasulo/
├── Exemplos/              # Alguns arquivos de teste em .ASM
├── gui/                   # Interface gráfica do Simulador
├── Simulador/             # Simulador em si junto com as instruções
main.py

## Executando o Simulador
Executar deiratamente o arquivo main.py na pasta atravez do icone de executar no VScode

OU

````powershell
python main.py
````
## Exemplos Disponiveis

long_test1_deep_dependencies.asm — Dependências EXTREMAS (cadeia longa)
Cada instrução depende da anterior → enorme tempo total.
- Longa cadeia de dependências RAW (criando MUITOS ciclos)

long_test2_parallel_pressure.asm — Pressão extrema nas unidades funcionais
Mistura pesada: vários MUL, LOAD e ADD simultâneos.
- Gera pressão nas unidades funcionais: ADD, MUL, LOAD, STORE
- Repete padrão para gerar ainda mais ciclos

long_test3_branch_storm.asm — Tempestade de branches (branch storm)
Projeto para gerar flush, stall, predição quebrada, e MUITOS ciclos desperdiçados.
- Tempestade de branches para gerar FLUSH + misprediction

## Observações

- Corrigido o bug do contador de bolhas no simulador, agora ele contabiliza todas elas corretamente

