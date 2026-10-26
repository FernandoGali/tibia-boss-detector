# Tibia Boss Detector

Ferramenta para ajudar jogadores de Tibia a encontrar **criaturas raras e bosses** com mais facilidade.

O projeto consulta as kill statistics de cada mundo pela [API TibiaData](https://tibiadata.com/) e guarda um histórico diário. Se uma criatura rara aparece com mortes num mundo, é porque ela nasceu lá. Juntando esse histórico, dá para mostrar onde e com que frequência cada uma aparece.

> **Situação atual:** fase de coleta de dados, rodando pelo terminal. O objetivo final é um site onde o usuário escolhe o mundo numa lista e vê o histórico das criaturas raras.

## Como funciona

O projeto tem duas partes:

| Parte | Arquivo | O que faz |
|---|---|---|
| Coletor | [main.py](main.py) | Consulta as kill statistics de um mundo e salva um snapshot por mundo e por dia no PostgreSQL |
| Banco | [banco.py](banco.py) | Conexão com o PostgreSQL, criação das tabelas e gravação dos snapshots |
| Sentinela | [sentinela.py](sentinela.py) | De hora em hora, consulta alguns mundos de cada região para descobrir **quando** as kill statistics foram atualizadas |

### Horários do Tibia

- O **server save** acontece todo dia às 10:00 no horário de Berlim, igual para todos os mundos.
- As **kill statistics** são atualizadas cerca de 7 horas antes, por volta das 03:00 de Berlim (23:00 de Brasília no inverno europeu).
- Por isso todas as datas do projeto usam o fuso `Europe/Berlin`, e não o horário do computador.

### Sentinela

O sentinela escolhe os mundos mais cheios de cada região:

| Região | Sentinelas |
|---|---|
| Europe | 2 |
| North America | 2 |
| South America | 2 |
| Oceania | 1 (a região só tem 3 mundos) |

A cada execução, ele soma as kills de 24h e de 7 dias de cada sentinela e compara com a leitura anterior. Se a soma mudou, as kill statistics daquela região foram atualizadas.

As sentinelas ficam fixas em `sentinelas.json` e só são escolhidas de novo se algum mundo deixar de existir.

## Instalação

Precisa do **Python 3.13** ou mais novo.

```bash
git clone https://github.com/FernandoGali/tibia-boss-detector.git
cd tibia-boss-detector

python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux / macOS

pip install -r requirements.txt
```

## Banco de dados (PostgreSQL)

Precisa do **PostgreSQL** instalado (o projeto foi feito com a versão 18).

**1. Criar o usuário e o banco do projeto.** Entre como administrador (`postgres`) pelo psql, pgAdmin ou DBeaver e rode:

```sql
CREATE USER boss_detector WITH PASSWORD 'sua_senha';
CREATE DATABASE boss_detector OWNER boss_detector;
```

Use uma senha só com letras e números: ela vai dentro de um endereço no `.env`, e símbolos como `@`, `:` e `/` confundem a conexão.

**2. Criar o arquivo `.env`.** Na pasta do projeto, crie um arquivo chamado `.env` com esta linha, trocando `sua_senha` pela senha do passo 1:

```
DATABASE_URL=postgresql://boss_detector:sua_senha@localhost:5432/boss_detector
```

O `.env` fica fora do git e nunca deve ser enviado para o GitHub.

**3. Criar as tabelas:**

```bash
python banco.py
```

Pode rodar quantas vezes quiser: só cria o que ainda não existe.

| Tabela | Conteúdo |
|---|---|
| `snapshots` | Uma linha por mundo, criatura e dia. A regra `UNIQUE (mundo, criatura, data_atividade)` faz o banco recusar o mesmo dia duas vezes |
| `sentinelas` | Mundos escolhidos como sentinela |
| `leituras_sentinela` | Leituras de hora em hora do sentinela |

> O sentinela ainda grava em JSON. As tabelas `sentinelas` e `leituras_sentinela` já existem e vão ser usadas quando o experimento de horário terminar.

## Como usar

**Coletor (um mundo):**

```bash
python main.py
```

Digite o nome do mundo no formato oficial, por exemplo `Antica`.

**Sentinela (uma leitura):**

```bash
python sentinela.py
```

**Sentinela de hora em hora no Windows:** o sentinela grava cada execução em `sentinela_saida.txt`, com data e hora em cada linha. Para agendar no Agendador de Tarefas, rode no **PowerShell**, ajustando os dois caminhos:

```powershell
$projeto = "C:\caminho\do\projeto"
$pythonw = "C:\caminho\do\Python\pythonw.exe"

$acao     = New-ScheduledTaskAction -Execute $pythonw -Argument "sentinela.py" -WorkingDirectory $projeto
$gatilho  = New-ScheduledTaskTrigger -Once -At "00:05" -RepetitionInterval (New-TimeSpan -Hours 1)
$opcoes   = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName "Tibia Sentinela" -Action $acao -Trigger $gatilho -Settings $opcoes
```

- O `pythonw.exe` fica na mesma pasta do `python.exe` (`python -c "import sys; print(sys.executable)"` mostra onde está). Ele roda o Python **sem abrir janela**: com o `python.exe`, fechar a janela ou apertar `Ctrl + C` interrompe o sentinela e a leitura se perde.
- `StartWhenAvailable` roda assim que possível se o computador estava desligado no horário.
- Para remover: `Unregister-ScheduledTask -TaskName "Tibia Sentinela" -Confirm:$false`.

## Testes

```bash
python -m pytest
```

Os testes não chamam a API de verdade: as respostas são simuladas com o `monkeypatch` do pytest.

## Arquivos gerados

Ficam fora do git (estão no `.gitignore`):

| Arquivo | Quem gera | Conteúdo |
|---|---|---|
| `sentinelas.json` | Sentinela | Mundos escolhidos como sentinela |
| `sentinela_log.json` | Sentinela | Todas as leituras, com horário de Berlim e de Brasília |
| `sentinela_saida.txt` | Sentinela | Resumo de cada execução, com data e hora, e os erros, se houver |

## Próximos passos

- [ ] Confirmar pelo log do sentinela o horário real de atualização de cada região
- [ ] Coletar todos os mundos automaticamente, disparado pelo sentinela
- [x] Trocar o `historico.json` pelo PostgreSQL no coletor
- [ ] Passar o sentinela para o PostgreSQL
- [ ] Definir a data da atividade pelo horário real da atualização (hoje, coletar entre 00:00 e ~03:00 de Berlim grava o dia errado)
- [ ] Rodar em um servidor, sem depender do computador ligado
- [ ] Criar a API e o site
