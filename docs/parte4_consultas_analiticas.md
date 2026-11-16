# PARTE 4 — CONSULTAS ANALÍTICAS EM SQL, RESULTADOS E INTERPRETAÇÕES DE NEGÓCIO

Todas as 10 consultas estão armazenadas individualmente em `queries/consulta_01.sql` a `queries/consulta_10.sql` e foram executadas sobre o esquema `dw` completo (`112.650` itens em `dw.fato_vendas_itens` e `103.886` transações em `dw.fato_pagamentos_pedido`).

---

## Consulta 01 — Evolução Anual e Trimestral de Vendas e Frete (`ROLLUP`)
- **Arquivo:** `queries/consulta_01.sql`
- **Pergunta de Negócio:** Qual é a evolução anual e trimestral da receita de produtos, do valor total de frete e do faturamento bruto dos itens vendidos, incluindo subtotais por ano e total geral (`ROLLUP`)?
- **Resultado Real Obtido:**
  - Subtotal 2016: `370` itens | Receita: `R$ 49.785,92` | Frete: `R$ 7.397,29` | Total: `R$ 57.183,21`
  - Subtotal 2017: `50.864` itens | Receita: `R$ 6.155.806,98` | Frete: `R$ 986.865,45` | Total: `R$ 7.142.672,43`
  - Subtotal 2018: `61.416` itens | Receita: `R$ 7.386.050,80` | Frete: `R$ 1.257.646,80` | Total: `R$ 8.643.697,60`
  - **TOTAL GERAL:** `112.650` itens | Receita: `R$ 13.591.643,70` | Frete: `R$ 2.251.909,54` | Total: `R$ 15.843.553,24`
- **Interpretação de Negócio:** O marketplace apresentou crescimento acelerado e contínuo ao longo de todos os trimestres de 2017 (saltando de R$ 855,5 mil no 1º trimestre para R$ 2,81 milhões no 4º trimestre, impulsionado pela Black Friday e Natal) e atingiu seu pico histórico no 2º trimestre de 2018 com R$ 3,33 milhões de faturamento bruto. No acumulado geral de 112.650 itens vendidos (R$ 15,84 milhões), o valor do frete (R$ 2,25 milhões) representa 14,21% do faturamento bruto total dos pedidos.

---

## Consulta 02 — Top 10 Categorias por Receita de Vendas e Ticket Médio
- **Arquivo:** `queries/consulta_02.sql`
- **Pergunta de Negócio:** Quais são as 10 categorias de produtos (em português e inglês) com maior receita acumulada de vendas, qual o volume de itens vendidos e o ticket médio por item em cada categoria?
- **Resultado Real Obtido (Top 5 de 10):**
  1. `beleza_saude` (`health_beauty`): `9.670` itens | `8.836` pedidos | Receita: `R$ 1.258.681,34` | Ticket médio/item: `R$ 130,16`
  2. `relogios_presentes` (`watches_gifts`): `5.991` itens | `5.624` pedidos | Receita: `R$ 1.205.005,68` | Ticket médio/item: `R$ 201,14`
  3. `cama_mesa_banho` (`bed_bath_table`): `11.115` itens | `9.417` pedidos | Receita: `R$ 1.036.988,68` | Ticket médio/item: `R$ 93,30`
  4. `esporte_lazer` (`sports_leisure`): `8.641` itens | `7.720` pedidos | Receita: `R$ 988.048,97` | Ticket médio/item: `R$ 114,34`
  5. `informatica_acessorios` (`computers_accessories`): `7.827` itens | `6.689` pedidos | Receita: `R$ 911.954,32` | Ticket médio/item: `R$ 116,51`
- **Interpretação de Negócio:** Apenas três categorias (`beleza_saude`, `relogios_presentes` e `cama_mesa_banho`) superam individualmente a marca de R$ 1 milhão em receita de produtos, somando juntas R$ 3,50 milhões (25,7% da receita total da plataforma). Observa-se uma distinção clara de posicionamento: enquanto `cama_mesa_banho` lidera em volume físico com 11.115 itens vendidos de ticket mais baixo (R$ 93,30), `relogios_presentes` alcança a vice-liderança de faturamento com quase metade do volume (5.991 itens) graças ao seu alto valor agregado (ticket médio de R$ 201,14 por item).

---

## Consulta 03 — Distribuição Geográfica de Receita e Frete por Região e UF (`GROUPING SETS`)
- **Arquivo:** `queries/consulta_03.sql`
- **Pergunta de Negócio:** Como se distribuem a receita de produtos e o gasto com frete por Região e UF de destino do cliente, considerando os subtotais por Região e o total geral (`GROUPING SETS`)?
- **Resultado Real Obtido (Subtotais Regionais e Principais UFs):**
  - **Sudeste:** `77.413` itens | Receita: `R$ 8.887.393,06` | Frete: `R$ 1.344.930,44` (`R$ 17,37`/item; `13,14%` do total) — destaque para `SP` com `47.449` itens e `R$ 5.202.955,05` (frete médio de `R$ 15,15`).
  - **Sul:** `16.151` itens | Receita: `R$ 1.953.941,12` | Frete: `R$ 343.034,68` (`R$ 21,24`/item; `14,93%` do total).
  - **Nordeste:** `10.409` itens | Receita: `R$ 1.545.493,75` | Frete: `R$ 335.305,79` (`R$ 32,21`/item; `17,83%` do total).
  - **Centro-Oeste:** `6.613` itens | Receita: `R$ 870.462,06` | Frete: `R$ 152.599,94` (`R$ 23,08`/item; `14,92%` do total).
  - **Norte:** `2.064` itens | Receita: `R$ 334.353,71` | Frete: `R$ 76.038,69` (`R$ 36,84`/item; `18,53%` do total).
- **Interpretação de Negócio:** A região Sudeste concentra 65,39% de toda a receita de produtos da Olist (R$ 8,89 milhões), sendo o estado de São Paulo responsável sozinho por 38,28% do faturamento nacional e pelo menor custo médio de frete por item (R$ 15,15, equivalente a 12,14% do total pago). Em contrapartida, os clientes das regiões Norte e Nordeste enfrentam um frete médio por item mais que o dobro do paulista (R$ 36,84 no Norte e R$ 32,21 no Nordeste, chegando a R$ 42,98 em RR e R$ 42,72 na PB), o que eleva o peso do frete para cerca de 18% a 22% do desembolso total e restringe a conversão de vendas nessas regiões.

---

## Consulta 04 — Ranking dos 10 Maiores Vendedores e Localização
- **Arquivo:** `queries/consulta_04.sql`
- **Pergunta de Negócio:** Quais são os 10 vendedores com maior receita acumulada de produtos, quantos itens e pedidos atenderam e qual a sua localização (cidade, UF e região)?
- **Resultado Real Obtido (Top 5 de 10):**
  1. `4869f7a5dfa277a7dca6462dcf3b52b2` (Guariba/SP - Sudeste): `1.132` pedidos | `1.156` itens | Receita: `R$ 229.472,63` | Preço médio: `R$ 198,51`
  2. `53243585a1d6dc2643021fd1853d8905` (Lauro de Freitas/BA - Nordeste): `358` pedidos | `410` itens | Receita: `R$ 222.776,05` | Preço médio: `R$ 543,36`
  3. `4a3ca9315b744ce9f8e9374361493884` (Ibitinga/SP - Sudeste): `1.806` pedidos | `1.987` itens | Receita: `R$ 200.472,92` | Preço médio: `R$ 100,89`
  4. `fa1c13f2614d7b5c4749cbc52fecda94` (Sumaré/SP - Sudeste): `585` pedidos | `586` itens | Receita: `R$ 194.042,03` | Preço médio: `R$ 331,13`
  5. `7c67e1448b00f6e969d365cea6b010ab` (Itaquaquecetuba/SP - Sudeste): `982` pedidos | `1.364` itens | Receita: `R$ 187.923,89` | Preço médio: `R$ 137,77`
- **Interpretação de Negócio:** Dos 10 maiores vendedores em faturamento da plataforma, 9 estão sediados no estado de São Paulo (Sudeste) e apenas 1 está localizado no Nordeste (Lauro de Freitas/BA), o que explica por que os fretes para o Norte e Nordeste são mais caros (a mercadoria parte majoritariamente de SP). Além disso, nota-se a coexistência de dois perfis de lojistas de sucesso: vendedores de alto giro como o de Ibitinga/SP (1.987 itens a R$ 100,89 em média) e vendedores especializados em alto ticket como o de Lauro de Freitas/BA (410 itens a R$ 543,36 em média).

---

## Consulta 05 — Desempenho de Vendas: Dias Úteis vs. Finais de Semana e Feriados Nacionais
- **Arquivo:** `queries/consulta_05.sql`
- **Pergunta de Negócio:** Qual é o faturamento total, o volume de itens vendidos e a média de faturamento por dia em dias úteis em comparação com finais de semana e feriados nacionais?
- **Resultado Real Obtido:**
  - `Dia Util`: `425` dias c/ venda | `74.085` pedidos | `84.935` itens | Total: `R$ 11.936.047,88` | Média/dia: `R$ 28.084,82`
  - `Fim de Semana`: `173` dias c/ venda | `22.289` pedidos | `25.131` itens | Total: `R$ 3.547.424,27` | Média/dia: `R$ 20.505,34`
  - `Feriado Nacional`: `18` dias c/ venda | `2.292` pedidos | `2.584` itens | Total: `R$ 360.081,09` | Média/dia: `R$ 20.004,51`
- **Interpretação de Negócio:** Os dias úteis concentram 75,34% de todo o faturamento da plataforma (R$ 11,94 milhões) e apresentam uma média de faturamento diário de R$ 28.084,82 por dia ativo. Nos finais de semana (R$ 20.505,34/dia) e feriados nacionais (R$ 20.004,51/dia), o ritmo diário de vendas recua cerca de 27% a 28,8%, indicando que o consumidor brasileiro no e-commerce realiza compras prioritariamente durante a rotina de segunda a sexta-feira.

---

## Consulta 06 — Taxa de Recompra e Fidelidade de Clientes (`customer_unique_id`)
- **Arquivo:** `queries/consulta_06.sql`
- **Pergunta de Negócio:** Quantos clientes reais (`customer_unique_id`) realizaram mais de um pedido na plataforma e qual é o valor médio gasto por cliente recorrente em comparação aos clientes de compra única?
- **Resultado Real Obtido:**
  - `Cliente Compra Unica (1 pedido)`: `92.507` clientes (`96,95%`) | `92.507` pedidos | Total: `R$ 14.939.106,99` | Gasto médio/cliente: `R$ 161,49`
  - `Cliente Recorrente (2+ pedidos)`: `2.913` clientes (`3,05%`) | `6.159` pedidos | Total: `R$ 904.446,25` | Gasto médio/cliente: `R$ 310,49`
- **Interpretação de Negócio:** A análise pelo identificador real do cliente (`customer_unique_id`) revela que apenas 3,05% da base (2.913 clientes entre os 95.420 clientes com itens faturados) realizaram mais de uma compra, evidenciando uma baixa retenção típica de compras avulsas em marketplaces. Todavia, cada cliente recorrente gera um gasto médio acumulado de R$ 310,49 — valor 92,3% superior ao cliente de compra única (R$ 161,49) — demonstrando alto potencial de aumento de receita caso a diretoria invista em campanhas de fidelização e CRM.

---

## Consulta 07 — Logística de Entrega: Prazos Reais e Taxa de Atraso por Região
- **Arquivo:** `queries/consulta_07.sql`
- **Pergunta de Negócio:** Qual é o tempo médio real de entrega (em dias) e a diferença média em relação ao prazo estimado por Região de destino do cliente nos pedidos entregues?
- **Resultado Real Obtido:**
  - `Norte`: `2.018` itens entregues | Prazo real: `22,55` dias | Diferença p/ estimativa: `-15,76` dias | Atrasados: `176` (`8,72%`)
  - `Nordeste`: `10.087` itens entregues | Prazo real: `19,85` dias | Diferença p/ estimativa: `-11,51` dias | Atrasados: `1.266` (`12,55%`)
  - `Centro-Oeste`: `6.480` itens entregues | Prazo real: `14,88` dias | Diferença p/ estimativa: `-12,49` dias | Atrasados: `419` (`6,47%`)
  - `Sul`: `15.879` itens entregues | Prazo real: `13,93` dias | Diferença p/ estimativa: `-13,24` dias | Atrasados: `912` (`5,74%`)
  - `Sudeste`: `75.725` itens entregues | Prazo real: `10,62` dias | Diferença p/ estimativa: `-11,70` dias | Atrasados: `4.491` (`5,93%`)
- **Interpretação de Negócio:** Existe forte disparidade logística regional: enquanto entregas no Sudeste levam em média 10,62 dias com taxa de atraso de 5,93%, entregas para o Norte e Nordeste demoram cerca do dobro do tempo (22,55 e 19,85 dias, respectivamente). Embora a plataforma trabalhe com prazos estimados conservadores (entregando em média de 11,5 a 15,7 dias antes da data limite prometida), a região Nordeste apresenta o maior gargalo operacional, registrando 12,55% de entregas fora do prazo estimado (mais que o dobro do Sul e Sudeste).

---

## Consulta 08 — Evolução Trimestral da Taxa de Atraso nas Entregas e Frete Médio
- **Arquivo:** `queries/consulta_08.sql`
- **Pergunta de Negócio:** Qual é o percentual trimestral de itens entregues com atraso (entregues após a data estimada) e como se comporta o valor médio de frete nesses períodos?
- **Resultado Real Obtido (Principais Trimestres de 2017 e 2018):**
  - `2017 - 1o ao 3o Trimestre`: Taxa de atraso estável entre `3,40%` e `3,89%` | Prazo médio: `11,28` a `13,10` dias | Frete médio: `R$ 19,02` a `R$ 19,46`
  - `2017 - 4o Trimestre`: `19.875` itens | `1.665` atrasados (`8,38%`) | Prazo médio: `14,13` dias | Frete médio: `R$ 19,40`
  - `2018 - 1o Trimestre`: `23.572` itens | `2.956` atrasados (`12,54%`) | Prazo médio: `15,58` dias | Frete médio: `R$ 19,52`
  - `2018 - 2o e 3o Trimestres`: Queda do atraso para `3,95%` e `4,68%` | Redução do prazo para `10,56` e `8,21` dias | Frete médio sobe para `R$ 20,60` e `R$ 21,75`
- **Interpretação de Negócio:** A operação logística sofreu forte estresse entre o 4º trimestre de 2017 (alta demanda de Black Friday/Natal, com atrasos subindo para 8,38%) e o 1º trimestre de 2018, quando a taxa de atraso atingiu o pico crítico de 12,54% (2.956 itens atrasados e prazo médio de 15,58 dias). A partir do 2º e 3º trimestres de 2018, houve recuperação expressiva da eficiência logística — reduzindo o prazo médio de entrega para 8,21 dias e estabilizando o atraso em ~4% — acompanhada de um reajuste no frete médio por item de R$ 19,52 para R$ 21,75.

---

## Consulta 09 — Participação dos Meios de Pagamento e Parcelamento
- **Arquivo:** `queries/consulta_09.sql`
- **Pergunta de Negócio:** Qual é a participação de cada meio de pagamento no valor total transacionado, na quantidade de transações e qual é o número médio de parcelas contratadas?
- **Resultado Real Obtido:**
  - `Cartao de Credito` (`Credito/Parcelavel`): `76.795` transações | `76.505` pedidos | `R$ 12.542.084,19` (`78,34%`) | Média parcelas: `3,51` | Ticket médio: `R$ 163,32`
  - `Boleto Bancario` (`A Vista`): `19.784` transações | `19.784` pedidos | `R$ 2.869.361,27` (`17,92%`) | Média parcelas: `1,00` | Ticket médio: `R$ 145,03`
  - `Voucher / Vale` (`A Vista`): `5.775` transações | `3.866` pedidos | `R$ 379.436,87` (`2,37%`) | Média parcelas: `1,00` | Ticket médio: `R$ 65,70`
  - `Cartao de Debito` (`A Vista`): `1.529` transações | `1.528` pedidos | `R$ 217.989,79` (`1,36%`) | Média parcelas: `1,00` | Ticket médio: `R$ 142,57`
- **Interpretação de Negócio:** O cartão de crédito domina amplamente as preferências de pagamento na Olist, respondendo por 78,34% de todo o volume financeiro transacionado (R$ 12,54 milhões) e apresentando o maior ticket médio por transação (R$ 163,32), impulsionado pelo parcelamento médio em 3,51 vezes. O boleto bancário consolida-se como o segundo principal meio de pagamento à vista (17,92% do valor total), enquanto os vouchers (2,37%) destacam-se pelo uso combinado em múltiplas transações de um mesmo pedido (5.775 transações distribuídas em 3.866 pedidos).

---

## Consulta 10 — Impacto da Pontualidade de Entrega na Satisfação do Cliente
- **Arquivo:** `queries/consulta_10.sql`
- **Pergunta de Negócio:** Qual é o impacto da pontualidade logística de entrega (`No Prazo` vs. `Atrasado` vs. `Nao Entregue`) sobre a nota média de avaliação dos clientes (`nota_avaliacao`) e o tempo médio de espera?
- **Resultado Real Obtido:**
  - `No Prazo`: `89.941` pedidos | `102.285` itens avaliados | Nota média: **`4,21`** | Entrega média: `10,90` dias (`-13,62` dias antes do estimado)
  - `Atrasado`: `6.535` pedidos | `7.084` itens avaliados | Nota média: **`2,26`** | Entrega média: `33,75` dias (`+10,49` dias após o estimado)
  - `Nao Entregue`: `2.190` pedidos | `2.339` itens avaliados | Nota média: **`1,75`** | Entrega média: `NULL` (não entregues)
- **Interpretação de Negócio:** Os resultados comprovam que o cumprimento do prazo logístico é o principal fator determinante da satisfação do cliente na plataforma: pedidos entregues no prazo (média de 10,90 dias) alcançam excelente avaliação média de 4,21 estrelas (em 5,0). Quando ocorre atraso na entrega (tempo médio de espera salta para 33,75 dias, superando a estimativa em 10,49 dias), a nota média despenca quase pela metade para 2,26 estrelas, caindo ainda mais para 1,75 estrela nos pedidos cancelados ou não entregues.