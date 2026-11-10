    // TEXTOS //
    // Português e inglês. Os textos que vêm da API (semáforo e mensagens) também são traduzidos aqui //
const textos = {
    pt: {
        subtitulo: "Descubra quais bosses estão prestes a nascer no seu mundo",
        mundo: "Mundo",
        criaturas: "Criaturas",
        dica_criaturas: "Sem nenhuma marcada, a consulta mostra todas.",
        consultar: "Consultar",
        nova_consulta: "Nova consulta",
        carregando: "Carregando...",
        erro_mundos: "Não foi possível carregar os mundos. Tente recarregar a página.",
        erro_consulta: "Não foi possível fazer a consulta. Tente de novo.",
        alta: "Chance alta",
        media: "Chance média",
        baixa: "Chance baixa",
        sem_previsao: "Sem previsão",
        poucos_dados: (intervalos, minimo) => `Ainda poucos dados: ${intervalos} de ${minimo} intervalos`,
        ultima_aparicao: "Última aparição",
        proxima_prevista: "Próxima prevista",
        base_previsao: "Base da previsão",
        base: (aparicoes) => `${aparicoes} ${aparicoes === 1 ? "aparição" : "aparições"} neste mundo`,
        dias_atras: (dias) => dias === 0 ? "no último dia com dados" : dias === 1 ? "1 dia sem aparecer" : `${dias} dias sem aparecer`,
        intervalo: (dias) => `intervalo típico de ${dias.toLocaleString("pt-BR")} ${dias === 1 ? "dia" : "dias"}`,
        regioes: { "Europe": "Europa", "North America": "América do Norte", "South America": "América do Sul", "Oceania": "Oceania" }
    },
    en: {
        subtitulo: "Find out which bosses are about to spawn on your world",
        mundo: "World",
        criaturas: "Creatures",
        dica_criaturas: "With none selected, the search shows all of them.",
        consultar: "Search",
        nova_consulta: "New search",
        carregando: "Loading...",
        erro_mundos: "Could not load the worlds. Try reloading the page.",
        erro_consulta: "Could not run the search. Try again.",
        alta: "High chance",
        media: "Medium chance",
        baixa: "Low chance",
        sem_previsao: "No prediction",
        poucos_dados: (intervalos, minimo) => `Not enough data yet: ${intervalos} of ${minimo} intervals`,
        ultima_aparicao: "Last seen",
        proxima_prevista: "Next expected",
        base_previsao: "Prediction based on",
        base: (aparicoes) => `${aparicoes} ${aparicoes === 1 ? "appearance" : "appearances"} on this world`,
        dias_atras: (dias) => dias === 0 ? "on the latest day with data" : dias === 1 ? "1 day without appearing" : `${dias} days without appearing`,
        intervalo: (dias) => `typical interval of ${dias.toLocaleString("en-US")} ${dias === 1 ? "day" : "days"}`,
        regioes: { "Europe": "Europe", "North America": "North America", "South America": "South America", "Oceania": "Oceania" }
    }
};

    // SEMÁFORO //
    // A API devolve "alta", "média" ou "baixa"; aqui vira a chave do texto //
const chave_semaforo = { "alta": "alta", "média": "media", "baixa": "baixa" };

    // MÍNIMO DE INTERVALOS //
    // A API manda o mínimo em cada criatura; este é só para criaturas que nem vieram na resposta //
const minimo_padrao = 4;

    // RUNAS DO SEMÁFORO //
    // Fogo = alta, Thunderstorm = média, Gelo = baixa. Sem previsão fica sem runa //
const runa_semaforo = {
    "alta": "imagens/runas/fogo.webp",
    "média": "imagens/runas/thunderstorm.webp",
    "baixa": "imagens/runas/gelo.webp"
};


    // ESTADO //
    // aviso_atual: chave do texto do aviso, para traduzir de novo ao trocar o idioma //
    // resultado_atual: a última resposta da consulta, para redesenhar os cards ao trocar o idioma //
let idioma = "pt";
let aviso_atual = null;
let resultado_atual = null;


    // FUNÇÕES : GERAIS //

    // FUNÇÃO : LER E GRAVAR NO NAVEGADOR //
    // O localStorage pode estar bloqueado (aba anônima, por exemplo); aí o site só não lembra //
function ler_salvo(chave) {

    try {
        return JSON.parse(localStorage.getItem(chave));
    } catch {
        return null;
    }
}

function salvar(chave, valor) {

    try {
        localStorage.setItem(chave, JSON.stringify(valor));
    } catch {
        // sem localStorage, segue sem salvar //
    }
}

    // FUNÇÃO : TEXTO NO IDIOMA ATUAL //
function t(chave) {

    return textos[idioma][chave];
}

    // FUNÇÃO : BUSCAR NA API //
    // Devolve o JSON ou dá erro se a API respondeu com falha //
async function buscar(endereco) {

    const resposta = await fetch(endereco);

    if (!resposta.ok) {
        throw new Error(resposta.status);
    }

    return resposta.json();
}

    // FUNÇÃO : FORMATAR DATA //
    // "2026-11-04" -> 04/11/2026 (pt) ou Nov 4, 2026 (en) //
    // Em UTC, para o navegador não mudar o dia por causa do fuso //
function formatar_data(texto) {

    const local = idioma === "pt" ? "pt-BR" : "en-US";

    return new Date(texto + "T00:00:00Z").toLocaleDateString(local, {
        timeZone: "UTC", day: "numeric", month: idioma === "pt" ? "2-digit" : "short", year: "numeric"
    });
}

    // FUNÇÃO : MOSTRAR AVISO //
    // Recebe a chave do texto; erro = true pinta de vermelho //
function mostrar_aviso(chave, erro = false) {

    aviso_atual = chave;

    const aviso = document.getElementById("aviso");
    aviso.classList.toggle("erro", erro);
    aviso.textContent = chave ? t(chave) : "";
}

    // FUNÇÃO : APLICAR IDIOMA //
    // Troca todos os textos fixos da página e redesenha o que depende do idioma //
function aplicar_idioma(novo) {

    idioma = novo;
    salvar("idioma", idioma);

    document.documentElement.lang = idioma === "pt" ? "pt-BR" : "en";

    document.querySelectorAll("[data-texto]").forEach((elemento) => {
        elemento.textContent = t(elemento.dataset.texto);
    });

    document.querySelectorAll("[data-idioma]").forEach((botao) => {
        botao.classList.toggle("ativo", botao.dataset.idioma === idioma);
    });

    document.querySelectorAll("#mundo optgroup").forEach((grupo) => {
        grupo.label = t("regioes")[grupo.dataset.regiao] ?? grupo.dataset.regiao;
    });

    if (resultado_atual) {
        mostrar_resultado(resultado_atual);
    } else if (aviso_atual) {
        document.getElementById("aviso").textContent = t(aviso_atual);
    }
}


    // FUNÇÕES : PÁGINA DE SELEÇÃO //

    // FUNÇÃO : MONTAR SELETOR DE MUNDOS //
    // Agrupado por região //
function montar_mundos(mundos, mundo_salvo) {

    const seletor = document.getElementById("mundo");
    const grupos = {};

    for (const { mundo, regiao } of mundos) {

        if (!grupos[regiao]) {
            grupos[regiao] = document.createElement("optgroup");
            grupos[regiao].dataset.regiao = regiao;
            grupos[regiao].label = t("regioes")[regiao] ?? regiao;
            seletor.append(grupos[regiao]);
        }

        grupos[regiao].append(new Option(mundo, mundo, false, mundo === mundo_salvo));
    }
}

    // FUNÇÃO : MONTAR CHECKBOXES DAS CRIATURAS //
function montar_criaturas(criaturas, marcadas) {

    const lista = document.getElementById("lista-criaturas");

    for (const criatura of criaturas) {

        const rotulo = document.createElement("label");
        const caixa = document.createElement("input");

        caixa.type = "checkbox";
        caixa.name = "criaturas";
        caixa.value = criatura;
        caixa.checked = marcadas.includes(criatura);

        rotulo.append(caixa, criatura);
        lista.append(rotulo);
    }
}

    // FUNÇÃO : CONSULTAR //
    // Salva a escolha no navegador e vai para a página de resultado //
function consultar(evento) {

    evento.preventDefault();

    const mundo = document.getElementById("mundo").value;
    const marcadas = [...document.querySelectorAll("input[name=criaturas]:checked")].map((c) => c.value);

    salvar("escolha", { mundo, criaturas: marcadas });

    window.location.href = "resultado.html";
}

    // INÍCIO : PÁGINA DE SELEÇÃO //
    // Na primeira visita, nada marcado; depois, a última escolha (que pode ser mudada à vontade) //
async function iniciar_selecao() {

    const escolha = ler_salvo("escolha") ?? {};

    try {
        const [mundos, criaturas] = await Promise.all([buscar("mundos"), buscar("criaturas")]);

        montar_mundos(mundos, escolha.mundo);
        montar_criaturas(criaturas, Array.isArray(escolha.criaturas) ? escolha.criaturas : []);

        document.getElementById("formulario").addEventListener("submit", consultar);

    } catch {
        mostrar_aviso("erro_mundos", true);
    }
}


    // FUNÇÕES : PÁGINA DE RESULTADO //

    // FUNÇÃO : NOME DO GIF //
    // "Mr. Punish" -> imagens/criaturas/Mr._Punish.gif //
function caminho_gif(criatura) {

    return "imagens/criaturas/" + criatura.replaceAll(" ", "_") + ".gif";
}

    // FUNÇÃO : LISTA DE DETALHES DO CARD //
function criar_detalhes(linhas) {

    const lista = document.createElement("dl");

    for (const [rotulo, valor] of linhas) {

        const termo = document.createElement("dt");
        const descricao = document.createElement("dd");

        termo.textContent = rotulo;
        descricao.textContent = valor;

        lista.append(termo, descricao);
    }

    return lista;
}

    // FUNÇÃO : CRIAR UM CARD //
function criar_card(dados) {

    const card = document.createElement("article");
    card.className = "card";

    const chave = chave_semaforo[dados.semaforo];

    if (chave) {
        card.dataset.semaforo = dados.semaforo;
    }

    // Topo: GIF, nome e selo do semáforo //
    const topo = document.createElement("div");
    topo.className = "card-topo";

    const imagem = document.createElement("img");
    imagem.src = caminho_gif(dados.criatura);
    imagem.alt = dados.criatura;
    imagem.loading = "lazy";

    const titulo = document.createElement("div");
    const nome = document.createElement("h2");
    nome.textContent = dados.criatura;

    const selo = document.createElement("span");
    selo.className = "selo";

    if (chave) {
        const runa = document.createElement("img");
        runa.src = runa_semaforo[dados.semaforo];
        runa.alt = "";
        selo.append(runa);
    }

    selo.append(t(chave ?? "sem_previsao"));

    titulo.append(nome, selo);
    topo.append(imagem, titulo);
    card.append(topo);

    const ultima = () => `${formatar_data(dados.ultima_aparicao)} · ${t("dias_atras")(dados.dias_sem_aparecer)}`;
    const base = [t("base_previsao"), t("base")(dados.aparicoes ?? 0)];

    // Abaixo do mínimo de intervalos: mostra o progresso e, se tiver, a última aparição neste mundo //
    if ((dados.intervalos ?? 0) < (dados.minimo_intervalos ?? minimo_padrao)) {

        card.append(criar_mensagem(t("poucos_dados")(dados.intervalos ?? 0, dados.minimo_intervalos ?? minimo_padrao)));

        if (dados.ultima_aparicao) {
            card.append(criar_detalhes([[t("ultima_aparicao"), ultima()]]));
        }

        return card;
    }

    card.append(criar_detalhes([
        [t("ultima_aparicao"), ultima()],
        [t("proxima_prevista"), `${formatar_data(dados.proxima_prevista)} · ${t("intervalo")(Number(dados.intervalo_tipico))}`],
        base
    ]));

    return card;
}

    // FUNÇÃO : MENSAGEM DO CARD //
function criar_mensagem(texto) {

    const mensagem = document.createElement("p");
    mensagem.className = "mensagem";
    mensagem.textContent = texto;

    return mensagem;
}

    // ORDEM DOS GRUPOS DE CHANCE //
    // Alta primeiro, depois média, baixa e por fim sem previsão //
const ordem_semaforo = { "alta": 0, "média": 1, "baixa": 2 };

    // FUNÇÃO : MOSTRAR RESULTADO //
    // Criaturas pedidas que não vieram da API (sem nenhum registro ainda) entram como sem histórico //
    // Os cards ficam agrupados por chance e, dentro de cada grupo, em ordem alfabética //
function mostrar_resultado({ resposta, pedidas }) {

    const por_nome = new Map(resposta.criaturas.map((c) => [c.criatura, c]));

    const todas = pedidas.map((nome) => por_nome.get(nome) ?? { criatura: nome, aparicoes: 0 });
    const grupo = (c) => ordem_semaforo[c.semaforo] ?? 3;

    todas.sort((a, b) => grupo(a) - grupo(b) || a.criatura.localeCompare(b.criatura));

    aviso_atual = null;
    const aviso = document.getElementById("aviso");
    aviso.classList.remove("erro");
    aviso.textContent = resposta.mundo;

    document.getElementById("cards").replaceChildren(...todas.map(criar_card));
}

    // INÍCIO : PÁGINA DE RESULTADO //
    // Lê a escolha salva; sem escolha (abriu a página direto), volta para a seleção //
    // Sem criaturas marcadas, mostra todas //
async function iniciar_resultado() {

    const escolha = ler_salvo("escolha");

    if (!escolha?.mundo) {
        window.location.replace("index.html");
        return;
    }

    const marcadas = Array.isArray(escolha.criaturas) ? escolha.criaturas : [];

    // Enquanto carrega: as 3 runas acendendo //
    const carregando = document.getElementById("carregando");
    carregando.setAttribute("aria-label", t("carregando"));
    carregando.hidden = false;

    try {
        const parametros = new URLSearchParams({ mundo: escolha.mundo });
        marcadas.forEach((c) => parametros.append("criaturas", c));

        const [resposta, todas_criaturas] = await Promise.all([
            buscar("consulta?" + parametros),
            marcadas.length ? marcadas : buscar("criaturas")
        ]);

        resultado_atual = { resposta, pedidas: marcadas.length ? marcadas : todas_criaturas };
        mostrar_resultado(resultado_atual);

    } catch {
        mostrar_aviso("erro_consulta", true);

    } finally {
        carregando.hidden = true;
    }
}


    // INÍCIO //
    // Idioma: sempre começa em português, a não ser que a pessoa tenha escolhido inglês antes //
function iniciar() {

    aplicar_idioma(ler_salvo("idioma") === "en" ? "en" : "pt");

    document.querySelectorAll("[data-idioma]").forEach((botao) => {
        botao.addEventListener("click", () => aplicar_idioma(botao.dataset.idioma));
    });

    if (document.body.dataset.pagina === "resultado") {
        iniciar_resultado();
    } else {
        iniciar_selecao();
    }
}

iniciar();
