# Tibia Boss Detector

[![Testes](https://github.com/FernandoGali/tibia-boss-detector/actions/workflows/testes.yml/badge.svg)](https://github.com/FernandoGali/tibia-boss-detector/actions/workflows/testes.yml)

Projeto pessoal pra ajudar a encontrar criaturas raras e bosses no Tibia.

A ideia é simples: as kill statistics de cada mundo mostram quantas vezes cada criatura morreu no último dia. Se um boss aparece com morte num mundo, é porque ele nasceu lá. Guardando isso todo dia, dá pra montar um histórico de onde e com que frequência cada criatura aparece.

Os dados vêm da [API TibiaData](https://tibiadata.com/).

O projeto coleta e guarda os dados todo dia, e tem um site onde a pessoa escolhe o mundo e as criaturas e vê a chance de cada uma aparecer (alta, média ou baixa), com a última aparição e a próxima prevista. O site tem versão em português e em inglês.

O site está no ar em **https://bossdetector.duckdns.org**.

## Como funciona

Um script roda de hora em hora e faz duas coisas:

1. Consulta alguns mundos "sentinela" pra saber se as kill statistics já foram atualizadas
2. Se atualizaram, coleta as criaturas raras de todos os mundos e salva no banco

As kill statistics atualizam uma vez por dia, de madrugada no horário de Berlim (acompanhei vários dias e foi sempre entre 03:00 e 04:00, todas as regiões juntas). A atualização do dia D traz as mortes do dia D-1, então é essa a data que fica salva. Todas as datas do projeto usam o horário de Berlim, que é o horário do Tibia.

Sentinelas são os mundos mais cheios de cada região: 2 da Europa, 2 da América do Norte, 2 da América do Sul e 1 da Oceania (que só tem 3 mundos). Se a soma das kills de uma sentinela mudou de uma hora pra outra, é porque atualizou.

Se algum mundo falhar ou ainda estiver com os números do dia anterior, ele é coletado de novo na hora seguinte.

### Arquivos

- `main.py` - roda tudo (sentinela e depois coletor)
- `sentinela.py` - descobre quando as kill statistics atualizaram
- `coletor.py` - coleta dos mundos
- `criaturas.py` - lista das criaturas raras
- `tibia.py` - consultas à API do TibiaData
- `tempo.py` - fusos e horários do Tibia
- `registro.py` - log
- `banco.py` - tudo que mexe no PostgreSQL
- `api.py` - API que o site usa (e que também entrega o site)
- `site/` - o site: página de seleção (`index.html`), página de resultado (`resultado.html`), estilo, script e imagens

## Instalação

Precisa de Python 3.13+ e PostgreSQL.

```bash
git clone https://github.com/FernandoGali/tibia-boss-detector.git
cd tibia-boss-detector
python -m venv .venv
source .venv/bin/activate      # Linux
# .venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

### Banco de dados

Criar o usuário e o banco (como administrador no psql, pgAdmin ou DBeaver):

```sql
CREATE USER boss_detector WITH PASSWORD 'sua_senha';
CREATE DATABASE boss_detector OWNER boss_detector;
```

Usa uma senha só com letras e números, porque ela vai dentro de uma URL e símbolos como `@` e `:` quebram a conexão.

Depois cria um arquivo `.env` na pasta do projeto:

```
DATABASE_URL=postgresql://boss_detector:sua_senha@localhost:5432/boss_detector
```

E cria as tabelas:

```bash
python banco.py
```

Tabelas:

- `snapshots` - uma linha por mundo, criatura e dia
- `coletas` - quais mundos já foram coletados em cada dia
- `sentinelas` - os mundos usados como sentinela
- `leituras_sentinela` - as leituras de hora em hora

## Como rodar

```bash
python main.py
```

O que acontece em cada execução fica salvo no `boss_detector.log`.

### De hora em hora no Linux

Uso um timer do systemd no usuário. Cria os dois arquivos em `~/.config/systemd/user/`:

`boss-detector.service`

```ini
[Unit]
Description=Boss Detector - coleta
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=/caminho/do/projeto
ExecStart=/caminho/do/projeto/.venv/bin/python main.py
```

`boss-detector.timer`

```ini
[Unit]
Description=Boss Detector - de hora em hora no minuto 05

[Timer]
OnCalendar=*-*-* *:05:00
Persistent=true

[Install]
WantedBy=timers.target
```

E liga o timer:

```bash
systemctl --user daemon-reload
systemctl --user enable --now boss-detector.timer
```

O `Persistent=true` faz ele rodar assim que o computador ligar se perdeu algum horário. Pra conferir: `systemctl --user list-timers`.

### De hora em hora no Windows

Pra rodar de hora em hora no Windows, eu uso o Agendador de Tarefas com o `pythonw.exe` (que roda sem abrir janela). No PowerShell:

```powershell
$projeto = "C:\caminho\do\projeto"
$pythonw = "C:\caminho\do\Python\pythonw.exe"

$acao    = New-ScheduledTaskAction -Execute $pythonw -Argument "main.py" -WorkingDirectory $projeto
$gatilho = New-ScheduledTaskTrigger -Once -At "00:05" -RepetitionInterval (New-TimeSpan -Hours 1)
$opcoes  = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName "Tibia Sentinela" -Action $acao -Trigger $gatilho -Settings $opcoes
```

### Site e API

```bash
fastapi dev api.py
```

O site abre em `http://127.0.0.1:8000`. A API roda junto, no mesmo endereço, e a documentação com todos os endereços dela fica em `http://127.0.0.1:8000/docs`.

- `/mundos` - lista de mundos
- `/criaturas` - lista de criaturas raras
- `/consulta?mundo=Kalibra&criaturas=Yakchal` - semáforo de cada criatura no mundo (sem `criaturas`, devolve todas)

## Testes

```bash
python -m pytest
```

Os testes não usam a API de verdade. Os que mexem no banco usam um banco separado, o `boss_detector_teste`, que é apagado a cada teste. Para criar (conectado como `postgres`):

```sql
CREATE DATABASE boss_detector_teste OWNER boss_detector;
```

Ele usa o mesmo usuário e senha do `.env`, então não precisa configurar mais nada. Sem esse banco, esses testes são pulados.

## Servidor

O site roda numa VM grátis do Google Cloud (e2-micro, Ubuntu 26.04), com tudo na mesma máquina:

- **PostgreSQL** - acessível só de dentro do servidor
- **Site e API** - `uvicorn` ouvindo só em `127.0.0.1:8000`
- **Caddy** - recebe as visitas e cuida do HTTPS (certificado do Let's Encrypt, renovado sozinho)
- **Domínio** - subdomínio grátis do [DuckDNS](https://www.duckdns.org) apontando para o IP da VM

O projeto fica em `~/boss-detector` e roda com estes serviços do systemd:

| Serviço | O que faz |
|---|---|
| `boss-detector-site.service` | Site e API, sempre ligado (reinicia sozinho se cair) |
| `boss-detector.timer` | Coleta de hora em hora, no minuto 05 |
| `boss-detector-backup.timer` | Backup do banco todo dia às 05:30, guardando os últimos 7 dias em `~/backups` |

### Atualizar o servidor

Depois de mandar as mudanças para o GitHub:

```bash
ssh usuario@servidor
cd ~/boss-detector
git pull
.venv/bin/pip install -r requirements.txt   # só se o requirements.txt mudou
sudo systemctl restart boss-detector-site
```

A coleta não precisa reiniciar: o timer roda o `main.py` atualizado na próxima hora.

### Ver o que está acontecendo

```bash
systemctl status boss-detector-site                 # site e API
systemctl list-timers "boss-detector*"              # próximas coletas e backups
tail -f ~/boss-detector/boss_detector.log           # log da coleta
journalctl -u boss-detector-site -f                 # log do site
```
