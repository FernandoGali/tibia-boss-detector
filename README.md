# Tibia Boss Detector

Projeto pessoal pra ajudar a encontrar criaturas raras e bosses no Tibia.

A ideia é simples: as kill statistics de cada mundo mostram quantas vezes cada criatura morreu no último dia. Se um boss aparece com morte num mundo, é porque ele nasceu lá. Guardando isso todo dia, dá pra montar um histórico de onde e com que frequência cada criatura aparece.

Os dados vêm da [API TibiaData](https://tibiadata.com/).

Por enquanto o projeto só coleta e guarda os dados. O plano é ter um site onde a pessoa escolhe o mundo e vê o histórico.

## Como funciona

Um script roda de hora em hora e faz duas coisas:

1. Consulta alguns mundos "sentinela" pra saber se as kill statistics já foram atualizadas
2. Se atualizaram, coleta as criaturas raras de todos os mundos e salva no banco

As kill statistics atualizam uma vez por dia, de madrugada no horário de Berlim (na primeira noite que acompanhei foi entre 03:00 e 04:00, todas as regiões juntas). A atualização do dia D traz as mortes do dia D-1, então é essa a data que fica salva. Todas as datas do projeto usam o horário de Berlim, que é o horário do Tibia.

Sentinelas são os mundos mais cheios de cada região: 2 da Europa, 2 da América do Norte, 2 da América do Sul e 1 da Oceania (que só tem 3 mundos). Se a soma das kills de uma sentinela mudou de uma hora pra outra, é porque atualizou.

Se algum mundo falhar ou ainda estiver com os números do dia anterior, ele é coletado de novo na hora seguinte.

### Arquivos

- `main.py` - roda tudo (sentinela e depois coletor)
- `sentinela.py` - descobre quando as kill statistics atualizaram
- `coletor.py` - lista das criaturas raras e coleta dos mundos
- `tibia.py` - consultas à API e horários do Tibia
- `banco.py` - tudo que mexe no PostgreSQL

## Instalação

Precisa de Python 3.13+ e PostgreSQL.

```bash
git clone https://github.com/FernandoGali/tibia-boss-detector.git
cd tibia-boss-detector
python -m venv .venv
.venv\Scripts\activate
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

Pra rodar de hora em hora no Windows, eu uso o Agendador de Tarefas com o `pythonw.exe` (que roda sem abrir janela). No PowerShell:

```powershell
$projeto = "C:\caminho\do\projeto"
$pythonw = "C:\caminho\do\Python\pythonw.exe"

$acao    = New-ScheduledTaskAction -Execute $pythonw -Argument "main.py" -WorkingDirectory $projeto
$gatilho = New-ScheduledTaskTrigger -Once -At "00:05" -RepetitionInterval (New-TimeSpan -Hours 1)
$opcoes  = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName "Tibia Sentinela" -Action $acao -Trigger $gatilho -Settings $opcoes
```

## Testes

```bash
python -m pytest
```

Os testes não usam a API de verdade nem o banco.

## Próximos passos

- [ ] Acompanhar mais alguns dias pra confirmar o horário da atualização
- [ ] Colocar pra rodar num servidor
- [ ] Criar a API e o site
