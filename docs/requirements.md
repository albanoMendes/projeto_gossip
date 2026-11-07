# requirements.md — Mural Distribuído com Gossip Push-Pull (Anti-Entropia)

> Grupo 7 — Autores: Albano Mendes, Gustavo Cunha, Arthur Bastos.

## 1. Introdução

Este documento especifica os requisitos de um mural de avisos replicado entre 6 processos independentes (nós A–F), utilizando um protocolo **gossip push-pull** na variante **anti-entropia (SI — Susceptible-Infected)**. O objetivo é demonstrar, em um seminário de 10–12 minutos com demo ao vivo, a disseminação epidêmica de informação sem servidor central, com tolerância a perdas de mensagens e parada de processos.

Os requisitos usam a sintaxe EARS (Easy Approach to Requirements Syntax). Convenções:
- **Ubíquo**: "O sistema DEVE ..."
- **Dirigido a evento**: "QUANDO <evento>, o sistema DEVE ..."
- **Dirigido a estado**: "ENQUANTO <estado>, o sistema DEVE ..."
- **Condicional/opcional**: "SE <condição>, ENTÃO o sistema DEVE ..."

**Desvio registrado em relação ao Albano_Design.md:** a Seção 8 daquele documento lista "Pull e push-pull" como fora de escopo e descreve um envio periódico apenas push. Esta especificação adota **push-pull** por ser a escolha academicamente mais robusta — a referência Gossip_Medium afirma que "the push-pull model is optimal to disseminate update messages quickly and reliably", e Kermarrec & van Steen descrevem a troca bidirecional (thread ativa + thread passiva) como o modelo geral de gossip. A justificativa completa está no design.

## 2. Glossário

- **Nó**: processo participante, identificado por letra de A a F.
- **Aviso (notice)**: unidade imutável de informação, identificada por `origem:contador` (ex.: `A:1`).
- **Ciclo**: disparo periódico do timer de gossip (~300 ms).
- **Fanout**: número de pares contatados por ciclo (= 2).
- **GOSSIP**: mensagem que inicia a troca push-pull (envia o conjunto do iniciador).
- **REPLY**: resposta da troca push-pull (envia o conjunto do par contatado).
- **Anti-entropia (SI)**: variante de gossip em que nós trocam estado periodicamente, sem marcar avisos como "removidos"; a troca continua indefinidamente.
- **Convergência / consistência eventual**: estado em que, cessadas novas inserções e havendo comunicação suficiente, todos os nós ativos conhecem o mesmo conjunto de avisos.

## 3. Requisitos

### RF-01 — Membership fixo
- **RF-01.1** O sistema DEVE operar com exatamente 6 nós identificados por A, B, C, D, E e F.
- **RF-01.2** O sistema DEVE carregar a lista de participantes (identificador, endereço, porta de gossip, porta de status) a partir de uma configuração na inicialização.
- **RF-01.3** O sistema NÃO DEVE suportar entrada ou saída dinâmica de participantes em tempo de execução.

### RF-02 — Modelo de aviso e identificação
- **RF-02.1** O sistema DEVE representar cada aviso com os campos: `id` (`origem:contador`), `origem`, `contador` e `texto`.
- **RF-02.2** QUANDO um nó cria um aviso, o sistema DEVE atribuir `origem` igual ao próprio identificador e `contador` igual ao próximo inteiro sequencial local da origem (iniciando em 1).
- **RF-02.3** O sistema DEVE tratar avisos como imutáveis: NÃO DEVE haver edição nem exclusão de avisos.

### RF-03 — Deduplicação por ID
- **RF-03.1** QUANDO um nó recebe um aviso cujo `id` ainda não está no seu conjunto local, o sistema DEVE incorporá-lo ao conjunto local.
- **RF-03.2** QUANDO um nó recebe um aviso cujo `id` já está no seu conjunto local, o sistema DEVE ignorá-lo sem criar cópia.
- **RF-03.3** O sistema DEVE manter o conjunto local de avisos sem duplicatas sob qualquer ordem de recebimento.

### RF-04 — Comunicação UDP
- **RF-04.1** O sistema DEVE trocar mensagens de gossip via UDP.
- **RF-04.2** O sistema DEVE serializar mensagens em JSON no formato `{ "type": "GOSSIP"|"REPLY", "sender": "<id>", "notices": [ ... ] }`.
- **RF-04.3** QUANDO um nó recebe uma mensagem malformada ou não decodificável, o sistema DEVE descartá-la sem encerrar o processo.

### RF-05 — Ciclo gossip push-pull
- **RF-05.1** ENQUANTO um nó está ativo, o sistema DEVE executar um ciclo de gossip a cada intervalo configurável (padrão ~300 ms).
- **RF-05.2** QUANDO um ciclo inicia, o nó iniciador DEVE enviar uma mensagem `GOSSIP` contendo seu conjunto completo de avisos ao(s) par(es) selecionado(s). COM fanout=2, o iniciador DEVE enviar um `GOSSIP` a cada um dos 2 pares selecionados, caracterizando **2 trocas push-pull independentes por ciclo** (cada uma com seu próprio `GOSSIP` → `REPLY`).
- **RF-05.3** QUANDO um nó recebe uma mensagem `GOSSIP`, o sistema DEVE mesclar os avisos recebidos ao seu conjunto local e responder com uma mensagem `REPLY` contendo seu próprio conjunto completo de avisos.
- **RF-05.4** QUANDO o iniciador recebe uma mensagem `REPLY`, o sistema DEVE mesclar os avisos recebidos ao seu conjunto local.
- **RF-05.5** O sistema NÃO DEVE usar ACK por aviso nem retransmissão dirigida; a reparação de diferenças DEVE ocorrer pelas trocas periódicas subsequentes.
- **RF-05.6** O sistema DEVE continuar executando ciclos indefinidamente (anti-entropia pura), sem condição de término por convergência.

### RF-06 — Seleção aleatória de pares com fanout 2
- **RF-06.1** QUANDO um ciclo inicia, o sistema DEVE selecionar 2 pares uniformemente ao acaso dentre os 5 outros nós.
- **RF-06.2** O sistema DEVE garantir que os 2 pares selecionados no mesmo ciclo sejam distintos entre si.
- **RF-06.3** O sistema NÃO DEVE selecionar o próprio nó como par.
- **RF-06.4** O sistema DEVE selecionar pares independentemente de o par estar vivo ou parado (não há detector de falhas).

### RF-07 — Perda simulada de mensagens
- **RF-07.1** O sistema DEVE suportar uma probabilidade configurável de descarte simulado no envio (padrão configurável, ex.: 0.0 a 1.0). O descarte simulado DEVE poder ser aplicado a **qualquer mensagem enviada (GOSSIP ou REPLY)**.
- **RF-07.2** QUANDO o descarte simulado ocorre em um envio, o sistema DEVE registrar o evento e NÃO DEVE entregar a mensagem.
- **RF-07.3** ENQUANTO houver perdas, o sistema DEVE permitir que trocas futuras e caminhos alternativos disseminem os avisos (sem retransmissão dirigida).

### RF-08 — Falha fail-stop (parada de processo)
- **RF-08.1** O sistema DEVE permitir o encerramento de um nó durante a execução (via Ctrl+C / sinal).
- **RF-08.2** QUANDO um nó é encerrado, o sistema NÃO DEVE recuperá-lo nem restaurar seu estado (sem persistência, estado apenas em memória).
- **RF-08.3** ENQUANTO um nó estiver parado, os demais nós ativos DEVEM continuar executando ciclos e convergindo entre si.
- **RF-08.4** SE um nó criar um aviso e for encerrado antes de compartilhar qualquer cópia, ENTÃO o aviso DEVE ser considerado perdido.

### RF-09 — Garantia de consistência eventual
- **RF-09.1** ENQUANTO não forem inseridos novos avisos, houver comunicação suficiente e pelo menos um nó ativo retiver cada aviso, o sistema DEVE fazer com que todos os nós ativos convirjam para o mesmo conjunto de avisos.
- **RF-09.2** O sistema NÃO DEVE prometer entrega dentro de um prazo fixo nem garantir entrega sob qualquer condição de rede.

### RF-10 — Criação de avisos via CLI
- **RF-10.1** O sistema DEVE permitir que qualquer nó crie um aviso por meio de um comando de linha (ex.: `post <texto>`) lido da entrada padrão.
- **RF-10.2** QUANDO o comando de criação é recebido, o sistema DEVE adicionar o novo aviso ao conjunto local imediatamente, tornando-o elegível à próxima troca.
- **RF-10.3** ENQUANTO aguarda comandos da entrada padrão, o sistema DEVE continuar executando os ciclos de gossip normalmente (CLI não bloqueante).

### RF-11 — Logging
- **RF-11.1** O sistema DEVE registrar eventos relevantes com identificação do nó, incluindo: criação de aviso, envio, recebimento de aviso novo, descarte simulado.
- **RF-11.2** O formato de log DEVE ser legível e consistente (ex.: `[A] ENVIADO destino=B avisos=1`).

### RF-12 — Painel de observação (observer)
- **RF-12.1** O sistema DEVE fornecer um painel textual que apresenta, por aviso, quais nós o conhecem e a cobertura observada (ex.: "3 de 6 nós").
- **RF-12.2** O painel DEVE obter o estado consultando cada nó em uma porta de status dedicada, somente leitura, separada do gossip.
- **RF-12.3** O painel NÃO DEVE distribuir avisos, escolher pares nem participar da replicação.
- **RF-12.4** SE o painel for encerrado, ENTÃO a comunicação de gossip entre os nós DEVE continuar sem interrupção.
- **RF-12.5** SE um nó não responder à consulta de status, ENTÃO o painel DEVE exibi-lo como indisponível sem encerrar.

## 4. Requisitos não funcionais

### RNF-01 — Simplicidade e escopo didático
- O sistema DEVE priorizar clareza e demonstrabilidade sobre otimização; DEVE enviar o conjunto completo de avisos (sem digests, hashes ou Merkle trees), justificado pelo volume pequeno.

### RNF-02 — Configurabilidade
- O intervalo de gossip, o fanout e a probabilidade de perda DEVEM ser configuráveis sem recompilar/alterar código-fonte dos nós (ex.: arquivo de config / argumentos).

### RNF-03 — Linguagem e organização
- O código DEVE ser implementado em Python, com identificadores e comentários em inglês, organizado em `src/aplicacao`, `src/estado`, `src/gossip`, `src/comunicacao`, `src/monitoramento`.

### RNF-04 — Testabilidade
- A lógica de domínio (modelo de aviso, deduplicação, merge, seleção de pares, decisão de perda) DEVE ser testável de forma isolada (sem dependência de rede real).

### RNF-05 — Autoria
- Os artefatos (código e slides) DEVEM conter os nomes dos 3 integrantes do grupo.

## 5. Fora de escopo

Entrada/saída dinâmica de participantes; recuperação após reinício; persistência; edição/exclusão de avisos; eleição de líder e consenso; detector de falhas (heartbeats/suspeitas); ACK por aviso; digests/hashes/Merkle trees/Scuttlebutt; envio somente de diferenças; variante SIR (rumor-mongering) e tombstones; criptografia/autenticação; interface gráfica ou web; grandes volumes de dados; views parciais / peer sampling. A lista completa de participantes é usada em vez de *partial views* / *peer sampling* (Newscast, Cyclon); trata-se de simplificação permitida pelo enunciado.

## 6. Critérios de aceitação (cenários de demonstração)

| # | Cenário | Resultado esperado | Requisitos cobertos |
|---|---------|--------------------|--------------------|
| CA-01 | Aviso criado em A | Aviso aparece inicialmente só em A | RF-02, RF-10 |
| CA-02 | Propagação normal (push-pull) | Os 6 nós passam a conhecer o aviso | RF-05, RF-06, RF-09 |
| CA-03 | Recepção repetida | Aviso não é duplicado no estado local | RF-03 |
| CA-04 | Avisos em nós diferentes | Conjuntos locais passam a conter ambos | RF-03, RF-05 |
| CA-05 | Perda simulada de mensagens | Trocas futuras disseminam mesmo assim | RF-07 |
| CA-06 | Um nó encerrado | Os demais continuam propagando e convergindo | RF-08 |
| CA-07 | Painel encerrado | Gossip entre nós continua | RF-12 |
| CA-08 | Troca push-pull bidirecional | Iniciador e par ficam com o mesmo conjunto após uma troca bem-sucedida | RF-05.3, RF-05.4 |

## 7. Entregáveis e Apresentação

| # | Entregável | Descrição |
|---|-----------|-----------|
| E-01 | README.md | DEVE conter instruções de compilação/execução de **cada processo** (nós A–F e painel), configuração (intervalo, fanout, perda) e roteiro da demo. |
| E-02 | README — seção teórica | DEVE explicar SI (anti-entropia) vs. SIR (rumor-mongering), por que push-pull, e consistência eventual, citando as referências. |
| E-03 | Slides | DEVEM cobrir: (a) breve introdução à técnica; (b) funcionamento em alto nível do protocolo; (c) garantias e modelo de falha adotados; (d) demonstração da aplicação de exemplo destacando o protocolo subjacente. |
| E-04 | Duração | A apresentação DEVE durar entre **10 e 12 minutos**. |
| E-05 | Autoria e empacotamento | Os nomes dos **3 integrantes** DEVEM aparecer no código e nos slides; o pacote DEVE ser um `.zip` no formato `GrupoN-NomeA-NomeB.zip`. |
| E-06 | Vídeo | DEVE ser produzido um vídeo apresentando o trabalho. |
