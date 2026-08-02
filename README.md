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

Com os containers em execucao, abra `http://localhost:8000`. O MySQL fica apenas na rede interna do Compose; a aplicacao e exposta na porta `8000`.

Para confirmar que os dados persistem, crie uma missao pela interface, pare os containers com `Ctrl+C`, execute `docker compose up` novamente e confirme que a missao continua visivel.

### Solucao de problemas

O build da imagem instala pacotes Debian a partir de `deb.debian.org`. Em ambientes onde esse host nao resolve por DNS, `docker compose up --build` falha antes de iniciar os containers. Corrija a conectividade ou a resolucao DNS do ambiente e execute o comando novamente.

Se o compilador `tsc` nao estiver no PATH do host, rode a compilacao dentro da imagem Docker durante `docker compose up --build`, ou disponibilize um compilador TypeScript compativel localmente.

## Como testar

Compile o frontend e rode a suite do backend:

```bash
scripts/build_frontend.sh
pytest backend/tests -v
```

O `.env` de desenvolvimento aponta para o MySQL do Compose (`db`). Para executar a suite no host sem os containers, use o banco SQLite de teste:

```bash
DATABASE_URL=sqlite+pysqlite:///:memory: pytest backend/tests -v
```

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

O comando imprime um caminho no formato `/app/backups/mysql/taskgame-<timestamp>.sql.gz`. No host, os backups ficam em `backups/mysql/`, fora dos diretorios publicos do frontend. Para restaurar manualmente, use `scripts/restore_mysql.sh` com o caminho do arquivo `.sql.gz` e as mesmas variaveis do `.env`.

## Seguranca local

- Mantenha `.env` fora do git e substitua as senhas de exemplo antes de usar o ambiente.
- O CORS aceita somente `http://localhost:8000` e `http://127.0.0.1:8000` por padrao; altere `BACKEND_CORS_ORIGINS` apenas para origens locais necessarias.
- O servico MySQL nao publica uma porta no host. Use a API em `http://localhost:8000` para acesso local.
- Backups devem permanecer em `backups/`, que e ignorado pelo git e nao e servido pelo frontend.

## Proximos passos

- Configurar uma resolucao DNS funcional para permitir builds Docker em ambientes restritos.
- Criar backups regulares e testar a restauracao em uma instancia local separada.
- Evoluir recursos planejados fora do MVP, como PWA, calendario visual e estatisticas avancadas.
