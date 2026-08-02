# TaskGame Design Spec

## Objetivo

TaskGame sera um webapp pessoal de tarefas, rotinas e objetivos em formato de dashboard gamer serio. O usuario registra missoes reais, cumpre rotinas, acompanha progresso por nivel e recebe XP, ouro e medalhas por consistencia. A primeira versao sera um MVP completo e evolutivo: util para uso diario, simples de manter, e preparado para crescer depois para uma experiencia mais ambiciosa.

## Referencias

- Habitica: inspira a divisao entre tarefas, rotinas recorrentes, recompensas, XP, ouro e conquistas.
- Todoist Karma: inspira metas diarias/semanais, streaks, graficos de produtividade e niveis.
- Finch: inspira recompensas pessoais leves, sem punicao agressiva por falhas.
- SuperBetter: inspira a linguagem de missoes, progresso pessoal, obstaculos e vitorias.

Links de referencia:

- https://apps.apple.com/us/app/habitica-gamified-taskmanager/id994882113
- https://www.todoist.com/karma
- https://finchcare.com/
- https://healthify.nz/apps/s/superbetter-app

## Escopo Do MVP

O MVP inclui:

- Missoes diarias.
- Missoes semanais.
- Objetivos longos.
- XP por dificuldade.
- Bonus por sequencia.
- Sistema de nivel.
- Ouro como moeda interna.
- Loja pessoal com recompensas reais definidas pelo usuario.
- Medalhas por marcos.
- Relatorio semanal.
- Exportacao de backup em JSON e CSV.
- Dump seguro do MySQL por script.
- Backend Python com FastAPI.
- Banco MySQL em Docker.
- Frontend em HTML, CSS, TypeScript e JavaScript puro, sem React e sem npm.
- Sem login e sem registro.
- Seguranca de dados adequada para app pessoal/local.

Fora do MVP, mas planejado para depois:

- PWA/offline-first.
- Calendario visual.
- Sistema de temas.
- Estatisticas avancadas.
- Importacao de backups.
- Modo foco.
- Obstaculos/inimigos pessoais.
- Integracoes externas.

## Produto

### Personalidade

O app deve parecer um painel de comando pessoal, nao um RPG infantil. A linguagem visual deve comunicar foco, progresso e recompensa. A fantasia de jogo aparece em termos como missao, XP, ouro, nivel, medalhas, loja e relatorio, mas a interface permanece limpa e pratica.

### Paleta

- Preto: fundo principal e superficies profundas.
- Azul: destaque operacional, links, foco, progresso e botoes primarios.
- Dourado: XP, ouro, medalhas, recompensas e estados de conquista.
- Cinza frio: bordas, texto secundario e separadores.
- Estados: verde para concluido, vermelho para falha/atraso, amarelo/dourado para recompensa.

### Responsividade

Desktop:

- Layout em dashboard com sidebar ou navegacao lateral compacta.
- Cards/painels para resumo, missoes e progresso.
- Tabelas ou listas densas para missoes.

Mobile:

- Navegacao inferior ou topo compacto.
- Secoes empilhadas.
- Acoes principais sempre acessiveis.
- Cards de missao com botoes grandes o suficiente para toque.

## Telas

### Dashboard

Primeira tela do app.

Conteudo:

- Nivel atual.
- Barra de XP ate o proximo nivel.
- Ouro atual.
- Streak atual.
- Missoes concluidas hoje.
- Progresso semanal.
- Proximas missoes.
- Medalha mais recente.
- Atalho para criar missao.

### Missoes

Tela principal para criar, editar, filtrar e concluir missoes.

Tipos:

- Diaria: aparece em dias configurados e conta para rotina.
- Semanal: aparece dentro da semana e vence no fim do periodo configurado.
- Objetivo longo: tem progresso parcial, etapas opcionais e data alvo.

Campos:

- Titulo.
- Descricao opcional.
- Tipo.
- Dificuldade: facil, media, dificil, epica.
- Categoria opcional.
- Data de inicio.
- Data alvo opcional.
- Dias da semana para recorrencia diaria.
- Status: ativa, concluida, arquivada.
- Progresso atual e progresso alvo para objetivos longos.

### Objetivos

Visao focada em objetivos longos.

Conteudo:

- Objetivos ativos.
- Percentual de progresso.
- Objetivos concluidos.

### Medalhas

Galeria de conquistas.

Medalhas iniciais:

- Sequencia de 7 dias.
- Sequencia de 30 dias.
- 100 missoes concluidas.
- Primeiro objetivo concluido.
- Rotina perfeita da semana.
- Primeira compra na loja.
- 1000 XP acumulados.
- 10000 XP acumulados.

Cada medalha tera:

- Nome.
- Descricao.
- Icone visual via CSS/HTML ou asset local.
- Condicao de desbloqueio.
- Data de desbloqueio.

### Loja Pessoal

Area para transformar ouro em recompensas reais.

Exemplos:

- 1h de jogo.
- Pizza.
- Filme.
- Comprar algo pequeno.
- Pausa sem culpa.

Campos:

- Nome.
- Descricao opcional.
- Custo em ouro.
- Status: ativa, comprada, arquivada.

Regras:

- Comprar recompensa reduz ouro.
- Compras ficam no historico.
- Nao existe compra com saldo negativo.

### Relatorio Semanal

Tela com resumo da semana atual e historico de semanas anteriores.

Dados:

- Missoes concluidas.
- Missoes vencidas ou nao concluidas.
- XP ganho.
- Ouro ganho.
- Melhor dia da semana.
- Streak atual e maior streak.
- Categorias mais fortes.
- Objetivos concluidos na semana.

Visual:

- Graficos simples feitos com HTML/CSS/JS puro.
- Barras por dia da semana.
- Indicadores numericos claros.

### Backup

Tela administrativa local para exportar dados.

Acoes:

- Exportar JSON completo.
- Exportar CSV de missoes.
- Exportar CSV de historico de conclusoes.
- Ver data do ultimo dump MySQL.

Scripts fora da UI:

- `scripts/backup_mysql.sh`: cria dump compactado do MySQL.
- `scripts/restore_mysql.sh`: restaura dump manualmente.

Backups nunca ficam dentro da pasta publica servida pelo frontend.

## Regras De Jogo

### Dificuldade

Recompensas base:

- Facil: 10 XP e 5 ouro.
- Media: 25 XP e 12 ouro.
- Dificil: 50 XP e 25 ouro.
- Epica: 100 XP e 60 ouro.

### Streak

Uma sequencia aumenta quando o usuario conclui pelo menos uma missao diaria no dia e nao deixa missoes diarias obrigatorias vencidas.

Bonus:

- 3 dias: +5% XP.
- 7 dias: +10% XP.
- 14 dias: +15% XP.
- 30 dias: +25% XP.

O bonus aplica apenas em conclusoes futuras enquanto a sequencia estiver ativa.

### Nivel

Nivel inicial: 1.

Formula:

```text
xp_necessario_para_proximo_nivel = 100 * nivel_atual
```

Exemplo:

- Nivel 1 para 2: 100 XP.
- Nivel 2 para 3: 200 XP.
- Nivel 3 para 4: 300 XP.

O XP total nunca diminui. O nivel e calculado a partir do XP acumulado.

### Medalhas

Medalhas sao desbloqueadas automaticamente apos eventos relevantes:

- Concluir missao.
- Avancar objetivo.
- Comprar recompensa.
- Fechar semana.

As medalhas desbloqueadas nao sao removidas.

### Falhas

O MVP nao tera dano, perda de XP ou punicao pesada. Missao vencida aparece como pendencia/falha no relatorio. A escolha evita que o app vire uma fonte de culpa e mantem foco em retomada.

## Arquitetura

### Backend

Framework: FastAPI.

Responsabilidades:

- Servir API REST.
- Validar entrada com Pydantic.
- Persistir dados no MySQL.
- Calcular XP, ouro, nivel, streak e medalhas.
- Gerar exportacoes JSON/CSV.
- Expor arquivos estaticos do frontend ou rodar separado em desenvolvimento.

Bibliotecas previstas:

- `fastapi`
- `uvicorn`
- `sqlalchemy`
- `pydantic`
- `pydantic-settings`
- `pymysql` ou `mysqlclient`
- `python-dotenv`
- `pytest`
- `httpx`

### Frontend

Tecnologias:

- HTML.
- CSS.
- TypeScript.
- JavaScript gerado pelo TypeScript.

Sem:

- React.
- Vue.
- Angular.
- npm como dependencia obrigatoria.

Compilacao TypeScript:

- Preferencia por TypeScript instalado globalmente ou alternativa simples documentada.
- Se TypeScript nao estiver disponivel, o MVP pode manter JS escrito de forma compativel e adicionar tipos via JSDoc em uma etapa posterior.

Responsabilidades:

- Renderizar telas.
- Chamar API com `fetch`.
- Controlar estados de carregamento, erro e sucesso.
- Fazer validacao basica antes de enviar formularios.
- Manter navegacao simples entre secoes.

### Docker

Servicos:

- `app`: backend FastAPI.
- `db`: MySQL.

Volumes:

- Volume Docker para dados do MySQL.
- Pasta local `backups/` ignorada pelo git.

Arquivos esperados:

- `docker-compose.yml`
- `Dockerfile`
- `.env.example`
- `.gitignore`

## Modelo De Dados

### `missions`

- `id`
- `title`
- `description`
- `type`: `daily`, `weekly`, `long_term`
- `difficulty`: `easy`, `medium`, `hard`, `epic`
- `category`
- `status`: `active`, `completed`, `archived`
- `start_date`
- `target_date`
- `repeat_days`
- `progress_current`
- `progress_target`
- `created_at`
- `updated_at`

### `mission_completions`

- `id`
- `mission_id`
- `completed_at`
- `xp_awarded`
- `gold_awarded`
- `streak_bonus_percent`
- `note`

### `player_stats`

- `id`
- `total_xp`
- `gold`
- `current_streak`
- `best_streak`
- `last_active_date`
- `created_at`
- `updated_at`

O MVP assume um unico registro de jogador.

### `badges`

- `id`
- `code`
- `name`
- `description`
- `condition_type`
- `threshold`
- `created_at`

### `earned_badges`

- `id`
- `badge_id`
- `earned_at`

### `rewards`

- `id`
- `name`
- `description`
- `cost`
- `status`: `active`, `archived`
- `created_at`
- `updated_at`

### `reward_purchases`

- `id`
- `reward_id`
- `purchased_at`
- `cost_paid`

### `weekly_snapshots`

- `id`
- `week_start`
- `week_end`
- `missions_completed`
- `missions_failed`
- `xp_gained`
- `gold_gained`
- `best_day`
- `created_at`

## API

Base: `/api`

### Missoes

- `GET /missions`
- `POST /missions`
- `GET /missions/{id}`
- `PATCH /missions/{id}`
- `POST /missions/{id}/complete`
- `POST /missions/{id}/progress`
- `POST /missions/{id}/archive`

### Dashboard

- `GET /dashboard`

Retorna nivel, XP, ouro, streak, resumo do dia, resumo semanal, proximas missoes e medalha recente.

### Objetivos

- `GET /goals`

Retorna missoes `long_term` com progresso e historico.

### Medalhas

- `GET /badges`

### Loja

- `GET /rewards`
- `POST /rewards`
- `PATCH /rewards/{id}`
- `POST /rewards/{id}/purchase`
- `POST /rewards/{id}/archive`

### Relatorios

- `GET /reports/weekly`
- `GET /reports/weekly/{week_start}`

### Backup

- `GET /backup/export.json`
- `GET /backup/missions.csv`
- `GET /backup/completions.csv`

## Seguranca

Mesmo sem login, o app deve proteger os dados pessoais.

Regras:

- `.env` nunca entra no git.
- `.env.example` documenta variaveis sem segredos reais.
- CORS restrito a `http://localhost` e porta configurada.
- API nao deve aceitar origem aberta em producao/local.
- Validacao forte com Pydantic.
- SQLAlchemy usado com parametros, sem concatenar SQL manualmente.
- Backups ficam fora de diretorios publicos.
- Endpoints de backup exportam apenas dados esperados.
- Configuracao de banco vem de variaveis de ambiente.
- MySQL nao deve expor porta publicamente fora do necessario para desenvolvimento local.
- Docker Compose usa senha configuravel via `.env`.

## Backup E Restauracao

### Exportacao Pela UI

JSON completo:

- Missoes.
- Conclusoes.
- Estatisticas.
- Medalhas.
- Recompensas.
- Compras.
- Relatorios.

CSV:

- Missoes.
- Conclusoes.

### Dump Do MySQL

Script:

```bash
scripts/backup_mysql.sh
```

Comportamento:

- Le variaveis do `.env`.
- Cria pasta `backups/mysql/` se nao existir.
- Gera arquivo com timestamp.
- Compacta em `.sql.gz`.
- Nao remove backups automaticamente no MVP.

Restauracao:

```bash
scripts/restore_mysql.sh backups/mysql/<arquivo>.sql.gz
```

Restaurar sempre sera uma acao manual para evitar perda acidental de dados.

## Estrutura Prevista

```text
TaskGame/
  backend/
    app/
      main.py
      config.py
      database.py
      models.py
      schemas.py
      services/
        game_rules.py
        reports.py
        backup.py
      routers/
        dashboard.py
        missions.py
        rewards.py
        badges.py
        reports.py
        backup.py
    tests/
  frontend/
    index.html
    styles/
      app.css
    src/
      api.ts
      app.ts
      dashboard.ts
      missions.ts
      rewards.ts
      reports.ts
    dist/
      app.js
  scripts/
    backup_mysql.sh
    restore_mysql.sh
  docs/
    superpowers/
      specs/
      plans/
  docker-compose.yml
  Dockerfile
  .env.example
  .gitignore
```

## Testes

Backend:

- Testes unitarios para regras de XP, ouro, nivel e streak.
- Testes para desbloqueio de medalhas.
- Testes de API para criar, editar e concluir missoes.
- Testes de compra de recompensa com saldo suficiente e insuficiente.
- Testes de exportacao JSON/CSV.

Frontend:

- Testes manuais documentados no MVP.
- Validacao visual em desktop e mobile.
- Fluxos minimos:
  - Criar missao.
  - Concluir missao.
  - Ver XP/ouro subir.
  - Comprar recompensa.
  - Exportar backup.

Docker:

- `docker compose up --build` deve iniciar app e MySQL.
- API deve responder em `/api/health`.
- Banco deve manter dados apos reiniciar containers.

## Fases De Implementacao

### Fase 1: Base

- Docker Compose.
- FastAPI.
- MySQL.
- Configuracao `.env`.
- Health check.
- Estrutura do frontend.

### Fase 2: Missoes E Regras De Jogo

- CRUD de missoes.
- Conclusao de missoes.
- XP, ouro, nivel e streak.
- Dashboard basico.

### Fase 3: Medalhas E Loja

- Seed de medalhas iniciais.
- Desbloqueio automatico.
- CRUD de recompensas.
- Compra de recompensas.

### Fase 4: Relatorio E Backup

- Relatorio semanal.
- Exportacao JSON.
- Exportacao CSV.
- Scripts de dump e restore MySQL.

### Fase 5: Polimento Responsivo

- Layout final preto, azul e dourado.
- Responsividade mobile.
- Estados vazios.
- Estados de erro.
- Ajustes de acessibilidade.

## Criterios De Aceite

- O app inicia com `docker compose up --build`.
- O MySQL persiste dados em volume.
- O usuario consegue criar missoes diarias, semanais e objetivos longos.
- O usuario consegue concluir missao e receber XP/ouro.
- O nivel e recalculado corretamente pelo XP total.
- Streak e bonus funcionam conforme regra definida.
- Medalhas sao desbloqueadas por marcos.
- A loja permite criar e comprar recompensas com ouro.
- Relatorio semanal mostra progresso, falhas e melhor sequencia.
- Backup JSON e CSV baixa dados reais.
- Script de dump MySQL gera arquivo compactado fora da pasta publica.
- Nao ha login nem registro.
- CORS e variaveis de ambiente estao configurados com seguranca local.
- Interface funciona bem em desktop e mobile.

## Decisoes Abertas Para Futuro

- Transformar em PWA.
- Adicionar calendario.
- Adicionar importacao de backup pela UI.
- Adicionar modo foco com timer.
- Adicionar estatisticas mensais.
- Criar sistema de temas.
- Adicionar obstaculos pessoais como mecanica opcional.
- Evoluir para central de vida com areas como saude, estudo, trabalho e financas pessoais.
