# Tibia Boss Detector

Ferramenta para ajudar jogadores de Tibia a encontrar **criaturas raras e bosses** com mais facilidade.

O projeto consulta as kill statistics de cada mundo pela [API TibiaData](https://tibiadata.com/) e guarda um histórico diário. Se uma criatura rara aparece com mortes num mundo, é porque ela nasceu lá. Juntando esse histórico, dá para mostrar onde e com que frequência cada uma aparece.

> **Situação atual:** coleta automática de todos os mundos funcionando, gravando no PostgreSQL. O objetivo final é um site onde o usuário escolhe o mundo numa lista e vê o histórico das criaturas raras.

## Como funciona

De hora em hora, o `main.py` roda duas etapas:

1. **Sentinela:** consulta alguns mundos de cada região para descobrir **quando** as kill statistics foram atualizadas.
2. **Coletor:** para cada região, coleta as criaturas raras de todos os mundos que ainda não têm o dia da última atualização.

| Arquivo | O que faz |
|---|---|
| [main.py](main.py) | Roda tudo na ordem (sentinela e depois coletor) e grava o log |
| [sentinela.py](sentinela.py) | Escolhe as sentinelas e detecta quando as kill statistics mudaram |
| [coletor.py](coletor.py) | Lista das criaturas raras, coleta dos mundos pendentes |
| [tibia.py](tibia.py) | Consultas à API TibiaData, horários do Tibia e cálculo da data da atividade |
| [banco.py](banco.py) | Conexão com o PostgreSQL, tabelas e todas as gravações e consultas |

### Horários do Tibia

- O **server save** acontece todo dia às 10:00 no horário de Berlim, igual para todos os mundos.
- As **kill statistics** são atualizadas de madrugada em Berlim. Na primeira noite medida (26/10/2026), a atualização aconteceu **entre 03:04 e 04:05 de Berlim**, para **todas as regiões ao mesmo tempo**.
- A atualização da madrugada do dia D traz as mortes do **dia D-1**. Essa é a `data_atividade` gravada.
- Todas as datas do projeto usam o fuso `Europe/Berlin`, e não o horário do computador.

### Sentinela

O sentinela usa os mundos mais cheios de cada região:

| Região | Sentinelas |
|---|---|
| Europe | 2 |
| North America | 2 |
| South America | 2 |
| Oceania | 1 (a região só tem 3 mundos) |

A cada execução, ele soma as kills de 24h e de 7 dias de cada sentinela e compara com a leitura anterior. Se a soma mudou, as kill statistics daquela região foram atualizadas.

As sentinelas ficam fixas na tabela `sentinelas` e só são escolhidas de novo se algum mundo deixar de existir.

### Coletor

- A data da atividade vem do **horário em que o sentinela detectou a atualização**, e não de um horário fixo. Se a atualização atrasar, a coleta se adapta sozinha.
- Uma atualização detectada antes das 02:00 de Berlim (por exemplo, com o computador desligado de madrugada) ainda conta como a do dia anterior (`hora_virada` no [tibia.py](tibia.py)).
- **Proteção por mundo:** se o resumo de kills de um mundo for igual ao da coleta anterior, ele ainda não atualizou. O coletor não grava e tenta de novo na próxima hora.
- Um mundo que falhar (API fora do ar, por exemplo) também é tentado de novo na próxima hora.

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
| `snapshots` | Uma linha por mundo, criatura rara e dia. `UNIQUE (mundo, criatura, data_atividade)` faz o banco recusar o mesmo dia duas vezes |
| `coletas` | Uma linha por mundo e dia, com o resumo de kills do mundo inteiro. Serve para saber o que já foi coletado e para a proteção por mundo |
| `sentinelas` | Mundos escolhidos como sentinela |
| `leituras_sentinela` | Todas as leituras de hora em hora do sentinela |

Exemplo de consulta: quais criaturas raras morreram num dia, e onde:

```sql
SELECT criatura, mundo, kills_24h
FROM snapshots
WHERE data_atividade = '2026-10-25' AND kills_24h > 0
ORDER BY criatura, mundo;
```

## Como usar

**Uma execução (sentinela + coletor):**

```bash
python main.py
```

O que acontece em cada execução fica em `boss_detector.log`, com data e hora em cada linha.

**De hora em hora no Windows:** rode no **PowerShell**, ajustando os dois caminhos:

```powershell
$projeto = "C:\caminho\do\projeto"
$pythonw = "C:\caminho\do\Python\pythonw.exe"

$acao     = New-ScheduledTaskAction -Execute $pythonw -Argument "main.py" -WorkingDirectory $projeto
$gatilho  = New-ScheduledTaskTrigger -Once -At "00:05" -RepetitionInterval (New-TimeSpan -Hours 1)
$opcoes   = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName "Tibia Sentinela" -Action $acao -Trigger $gatilho -Settings $opcoes
```

- O `pythonw.exe` fica na mesma pasta do `python.exe` (`python -c "import sys; print(sys.executable)"` mostra onde está). Ele roda o Python **sem abrir janela**: com o `python.exe`, fechar a janela ou apertar `Ctrl + C` interrompe a execução no meio.
- `StartWhenAvailable` roda assim que possível se o computador estava desligado no horário.
- Para remover: `Unregister-ScheduledTask -TaskName "Tibia Sentinela" -Confirm:$false`.

## Testes

```bash
python -m pytest
```

Os testes não chamam a API de verdade (as respostas são simuladas com o `monkeypatch` do pytest) e não precisam do banco.

## Próximos passos

- [x] Confirmar o horário real de atualização das kill statistics (primeira noite: 03:04 a 04:05 de Berlim, todas as regiões juntas)
- [x] Trocar os arquivos JSON pelo PostgreSQL
- [x] Coletar todos os mundos automaticamente, disparado pelo sentinela
- [x] Definir a data da atividade pelo horário real da atualização
- [ ] Acompanhar mais alguns dias para confirmar o horário da atualização
- [ ] Rodar em um servidor, sem depender do computador ligado
- [ ] Criar a API e o site
