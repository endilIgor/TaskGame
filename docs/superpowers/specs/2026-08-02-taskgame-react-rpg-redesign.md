# TaskGame React RPG Redesign Spec

## Objetivo

Transformar a interface atual do TaskGame em uma experiencia visual de RPG/fantasia premium, mantendo o backend FastAPI, MySQL, Docker, regras de jogo e endpoints existentes. O app deve parecer uma "Guild Hall" pessoal: um painel de aventureiro para missoes, XP, ouro, medalhas, objetivos e recompensas reais.

Esta etapa substitui o frontend TypeScript manual por React + TypeScript. A aplicacao continua sendo servida pelo backend Python a partir de `frontend/dist`, para nao alterar o fluxo principal do Docker Compose.

## Direcao Visual

### Tema

Direcao aprovada: **Guild Hall Premium**.

O visual deve combinar:

- Fundo preto profundo com textura/iluminacao sutil.
- Azul arcano para progresso, foco e estados ativos.
- Dourado para ouro, XP, medalhas, recompensas e conquistas.
- Painels escuros com bordas refinadas, brilho controlado e hierarquia forte.
- Elementos de fantasia adulta: brasao, runas discretas, placas de conquista, cartas de missao e loja como inventario pessoal.

O app nao deve virar uma landing page. A primeira tela continua sendo o dashboard utilizavel.

### Centralizacao

O conteudo principal deve ficar centralizado em todas as telas:

- Desktop: app shell com largura maxima, sidebar/topbar refinada e area central com grid.
- Ultrawide: fundo continua preenchendo a tela, mas os paineis uteis nao esticam indefinidamente.
- Mobile: navegacao compacta, conteudo empilhado, botoes grandes e cards legiveis.

## Arquitetura Frontend

### Stack

- React.
- TypeScript.
- Vite para build.
- CSS moderno sem framework visual obrigatorio.
- Sem React Router no primeiro passo; navegacao pode continuar por estado interno, preservando a simplicidade do app pessoal.

### Build E Servico

O build React deve gerar arquivos em `frontend/dist`.

O backend FastAPI continua servindo:

- `frontend/index.html`
- `frontend/dist/assets` ou arquivos equivalentes gerados pelo Vite
- CSS e JS estaticos gerados

O Dockerfile deve continuar construindo e servindo o app pelo Compose. Se forem adicionadas dependencias Node, o build do Docker precisa ser testado de ponta a ponta.

### Organizacao Proposta

Arquivos esperados:

- `frontend/package.json`
- `frontend/vite.config.ts`
- `frontend/tsconfig.json` ou ajuste do `tsconfig.json` existente
- `frontend/src/main.tsx`
- `frontend/src/App.tsx`
- `frontend/src/api/client.ts`
- `frontend/src/components/*`
- `frontend/src/views/*`
- `frontend/src/styles/*`
- `frontend/public/vendor/liquidGL.js` ou caminho equivalente

## Experiencia Por Tela

### Dashboard

A tela inicial deve parecer um painel de personagem:

- Card hero com nivel, XP, ouro e streak.
- Barra de XP com estilo premium.
- Resumo de hoje: concluidas, ativas e atrasadas.
- Resumo semanal: XP, ouro, melhor dia e missoes concluidas.
- Lista de proximas missoes em formato de cartas.
- Medalha recente em destaque.

### Missoes

A tela de missoes deve parecer um quadro de contratos:

- Cards com dificuldade visual: facil, media, dificil, epica.
- Tipo da missao evidente: diaria, semanal, objetivo longo.
- Acao de concluir bem destacada.
- Criacao/edicao em painel ou dialog visualmente integrado.
- Filtros simples por status/tipo.

### Objetivos

Objetivos longos devem parecer campanhas:

- Barra de progresso grande.
- Percentual claro.
- Data alvo quando existir.
- Acao de avancar progresso.

### Medalhas

A galeria de medalhas deve parecer vitrine de conquistas:

- Medalhas ganhas com dourado vivo.
- Medalhas bloqueadas com baixo contraste.
- Condicao e data de desbloqueio claras.

### Loja

A loja pessoal deve parecer inventario/recompensas:

- Recompensas em cards de item.
- Custo em ouro com destaque.
- Compra com confirmacao simples.
- Historico de compras visivel.

### Relatorio

O relatorio semanal deve parecer uma cronica de progresso:

- Numeros principais em cards.
- Barras por dia da semana.
- Categorias mais fortes.
- Falhas sem tom punitivo.

### Backup

Backup continua como area administrativa, mas com visual consistente:

- Exportacoes JSON/CSV como acoes claras.
- Ultimo dump MySQL visivel.
- Texto objetivo, sem excesso de explicacao na UI.

## Uso Do liquidGL

Referencia: `naughtyduk/liquidGL`.

O `liquidGL` deve ser usado apenas em elementos decorativos ou paineis que nao sejam essenciais para interacao. A biblioteca transforma elementos fixos em vidro refrativo via WebGL, entao o uso deve ser contido para evitar custo visual ou problemas de legibilidade.

Usos aprovados:

- Placas de vidro fixas no fundo.
- Ornamentos laterais.
- Pequeno painel atmosferico sem clique.
- Brilho/refracao atras do dashboard hero.

Usos proibidos:

- Botoes.
- Inputs.
- Selects.
- Textareas.
- Listas de missoes.
- Cards com texto essencial.
- Qualquer area onde falha do WebGL prejudique o uso do app.

Fallback:

- Se `window.liquidGL` nao existir, o app continua funcionando.
- Se WebGL falhar, os elementos decorativos permanecem como CSS glass comum.

## Seguranca E Dados

O redesign nao altera o modelo de seguranca:

- Sem login/register.
- App local/privado.
- CORS restrito.
- `.env` fora do git e fora do contexto publico.
- Backups fora da pasta publica.
- API continua validando dados no backend.

O frontend React nao deve expor segredos. Todas as credenciais continuam somente no ambiente do backend/Compose.

## Acessibilidade E Responsividade

Requisitos:

- Contraste suficiente em preto/azul/dourado.
- Estados de foco visiveis.
- Botoes e acoes com tamanho adequado em mobile.
- Layout sem sobreposicao em 360px de largura.
- Texto sem estourar cards.
- `prefers-reduced-motion` reduz animacoes decorativas.
- Efeitos WebGL nao bloqueiam leitura ou navegacao.

## Testes E Verificacao

Antes de concluir a implementacao:

- Build React/Vite passa.
- Backend tests passam.
- `docker compose --env-file .env.example up -d --build` passa.
- `GET /api/health` retorna 200.
- `/` retorna 200.
- Assets do frontend retornam 200.
- Dashboard carrega dados reais da API.
- Criar e concluir missao funciona no container com MySQL.
- Tela responsiva verificada em desktop e mobile.
- Verificacao visual confirma que o app nao esta em branco, nao tem texto sobreposto e o visual esta claramente mais premium que o MVP anterior.

## Fora Do Escopo Desta Etapa

- Login/register.
- PWA/offline-first.
- Sincronizacao cloud.
- Calendario avancado.
- Temas alternativos.
- Migracao de backend.
- Mudanca nas regras de XP/ouro/medalhas.
