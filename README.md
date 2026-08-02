# TaskGame

TaskGame e um MVP local para organizar missoes, objetivos, recompensas e progresso pessoal. O backend serve a interface e a API em `http://localhost:8000`.

## Stack

- Python 3.12, FastAPI, Pydantic e SQLAlchemy.
- MySQL 8.4 em Docker Compose, com dados persistidos no volume `mysql_data`.
- HTML, CSS, TypeScript e JavaScript puro no frontend, sem React ou npm.

## Como rodar

Crie a configuracao local a partir do exemplo e ajuste as senhas antes de iniciar. O arquivo `.env` e local e nao deve ser versionado.

```bash
cp .env.example .env
scripts/build_frontend.sh
docker compose up --build
```

Com os containers em execucao, abra `http://localhost:8000`. O MySQL fica apenas na rede interna do Compose; a aplicacao e publicada somente em `127.0.0.1:8000` por padrao.

O build Docker instala dependencias Python a partir de `vendor/wheels`, entao a etapa da imagem nao precisa de `apt-get`, npm ou acesso ao PyPI. Quando uma dependencia Python mudar no `pyproject.toml`, atualize esse wheelhouse antes de reconstruir a imagem.

`APP_PORT` altera a porta interna e publicada. `APP_HOST` controla o endereco em que o Uvicorn escuta dentro do container. Para acesso intencional pela rede local, defina `APP_BIND_ADDRESS=0.0.0.0` e ajuste `BACKEND_CORS_ORIGINS` para as origens de navegador necessarias. A API nao possui autenticacao, portanto nao use essa opcao em redes nao confiaveis.

Para confirmar que os dados persistem, crie uma missao pela interface, pare os containers com `Ctrl+C`, execute `docker compose up` novamente e confirme que a missao continua visivel.

### Solucao de problemas

Se o build falhar dizendo que nao encontrou um pacote Python, confirme se o wheel correspondente existe em `vendor/wheels`. Recrie o wheelhouse em uma maquina com acesso a internet usando `pip download -d vendor/wheels ...` para as dependencias do `pyproject.toml`.

O script usa `TSC_BIN` quando definido, depois `tsc` no PATH. Sem um compilador instalado, ele copia os modulos JavaScript pre-compilados e versionados em `frontend/prebuilt`, portanto funciona em um clone normal sem npm ou `package.json`.

## Como testar

Compile o frontend e rode a suite do backend:

```bash
scripts/build_frontend.sh
pytest backend/tests -v
```

Os testes definem automaticamente um banco SQLite em memoria antes de importar a aplicacao, portanto o comando acima funciona mesmo depois de criar o `.env` para o Compose.

Depois que a aplicacao estiver ativa, verifique a API:

```bash
curl -s http://localhost:8000/api/health
```

Resposta esperada:

```json
{"status":"ok","app":"TaskGame"}
```

Tambem e possivel validar a configuracao do Compose sem construir imagens:

```bash
docker compose --env-file .env.example config
```

## Backup

Com os containers ativos, crie um dump compactado do MySQL:

```bash
docker compose exec app scripts/backup_mysql.sh
```

O comando imprime um caminho no formato `/app/backups/mysql/taskgame-<timestamp>.sql.gz`. No host, os backups ficam em `backups/mysql/`, fora dos diretorios publicos do frontend. Os scripts usam somente as variaveis injetadas pelo Compose e nao carregam `.env` por conta propria.

Para restaurar manualmente no container, use:

```bash
docker compose exec app scripts/restore_mysql.sh /app/backups/mysql/taskgame-YYYYMMDD-HHMMSS.sql.gz
```

## Seguranca local

- Mantenha `.env` fora do git e substitua as senhas de exemplo antes de usar o ambiente.
- `.env` e suas variantes tambem ficam fora do contexto de build da imagem; apenas `.env.example` e retido.
- O CORS aceita somente `http://localhost:8000` por padrao; altere `BACKEND_CORS_ORIGINS` apenas para origens locais necessarias.
- O servico MySQL nao publica uma porta no host e a API escuta apenas no loopback do host por padrao.
- Backups devem permanecer em `backups/`, que e ignorado pelo git e nao e servido pelo frontend.

## Proximos passos

- Criar backups regulares e testar a restauracao em uma instancia local separada.
- Evoluir recursos planejados fora do MVP, como PWA, calendario visual e estatisticas avancadas.
