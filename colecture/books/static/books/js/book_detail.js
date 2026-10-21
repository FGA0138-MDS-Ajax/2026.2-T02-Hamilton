// ---------------------------------------------------------
// DADOS DO LIVRO
// A view book_detail (Django) manda os dados do livro para o HTML
// dentro de <script id="dados-livro">. Aqui a gente so le.
// ---------------------------------------------------------
const CAPA_PADRAO = "data:image/svg+xml;utf8," + encodeURIComponent(
  '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="300" viewBox="0 0 200 300">' +
  '<rect width="200" height="300" rx="8" fill="#1D1A2A"/>' +
  '<text x="100" y="155" font-family="sans-serif" font-size="18" fill="#7C7692" text-anchor="middle">Sem capa</text>' +
  '</svg>'
);

function buscarLivro(id) {
  return new Promise(function (resolve) {
    const dados = JSON.parse(document.getElementById("dados-livro").textContent);
    resolve(dados);
  });
}

// Ainda nao esta ligado ao banco (falta o models.py de BookReview)
function enviarResenha(id, nota, texto) {
  return new Promise(function (resolve, reject) {
    reject(new Error("Envio de avaliacao ainda nao esta ligado ao banco."));
  });
}

// ---------------------------------------------------------
// FRONT
// ---------------------------------------------------------
const idLivro = document.body.dataset.id;

let notaSelecionada = 0;

function estrelasTexto(nota) {
  const cheias = Math.round(nota);
  return "★".repeat(cheias) + "☆".repeat(5 - cheias);
}

function formatarData(dataIso) {
  const partes = dataIso.split("-");
  return partes[2] + "/" + partes[1] + "/" + partes[0];
}

function mostrarErro() {
  document.getElementById("erro").classList.remove("escondido");
  document.getElementById("livro").classList.add("escondido");
}

function mostrarLivro(livro) {
  document.getElementById("erro").classList.add("escondido");
  document.getElementById("livro").classList.remove("escondido");

  document.title = livro.titulo;
  document.getElementById("titulo").textContent = livro.titulo;
  document.getElementById("autor").textContent = livro.autor;
  document.getElementById("genero").textContent = livro.genero;
  document.getElementById("data").textContent = livro.ano ? livro.ano : "-";
  document.getElementById("paginas").textContent = livro.paginas ? livro.paginas : "-";
  document.getElementById("sinopse").textContent = livro.sinopse ? livro.sinopse : "Sem sinopse disponível.";

  // Capa com imagem padrao
  const capa = document.getElementById("capa");
  capa.src = livro.capa ? livro.capa : CAPA_PADRAO;

  // Media e quantidade (o front so exibe)
  if (livro.totalAvaliacoes === 0) {
    document.getElementById("media-estrelas").textContent = estrelasTexto(0);
    document.getElementById("media-texto").textContent = "Sem avaliações";
  } else {
    document.getElementById("media-estrelas").textContent = estrelasTexto(livro.media);
    document.getElementById("media-texto").textContent =
      livro.media.toFixed(1) + " (" + livro.totalAvaliacoes + " avaliações)";
  }

  mostrarResenhas(livro.resenhas);
}

function mostrarResenhas(resenhas) {
  const lista = document.getElementById("lista-resenhas");
  const vazio = document.getElementById("vazio");
  lista.innerHTML = "";

  if (resenhas.length === 0) {
    vazio.classList.remove("escondido");
    return;
  }
  vazio.classList.add("escondido");

  resenhas.forEach(function (r) {
    const item = document.createElement("li");
    item.className = "resenha";

    const cabecalho = document.createElement("div");
    cabecalho.className = "resenha-cabecalho";

    const nome = document.createElement("strong");
    nome.textContent = r.usuario;

    const estrelas = document.createElement("span");
    estrelas.className = "estrelas";
    estrelas.textContent = estrelasTexto(r.nota);

    const data = document.createElement("span");
    data.className = "data";
    data.textContent = formatarData(r.data);

    cabecalho.appendChild(nome);
    cabecalho.appendChild(estrelas);
    cabecalho.appendChild(data);

    const texto = document.createElement("p");
    texto.textContent = r.texto;

    item.appendChild(cabecalho);
    item.appendChild(texto);
    lista.appendChild(item);
  });
}

function carregarPagina() {
  buscarLivro(idLivro).then(function (livro) {
    if (livro === null) {
      mostrarErro();
    } else {
      mostrarLivro(livro);
    }
  });
}

// Seletor de estrelas clicavel
function pintarSeletor() {
  const botoes = document.querySelectorAll("#seletor button");
  botoes.forEach(function (botao) {
    const valor = Number(botao.dataset.valor);
    if (valor <= notaSelecionada) {
      botao.classList.add("ativa");
    } else {
      botao.classList.remove("ativa");
    }
  });
}

document.querySelectorAll("#seletor button").forEach(function (botao) {
  botao.addEventListener("click", function () {
    notaSelecionada = Number(botao.dataset.valor);
    pintarSeletor();
  });
});

// Enviar avaliacao: atualiza a lista e a media
document.getElementById("form-resenha").addEventListener("submit", function (evento) {
  evento.preventDefault();

  const texto = document.getElementById("texto-resenha").value.trim();
  const aviso = document.getElementById("aviso");

  if (notaSelecionada === 0) {
    aviso.textContent = "Escolha uma nota de 1 a 5 estrelas.";
    return;
  }
  if (texto === "") {
    aviso.textContent = "Escreva sua resenha.";
    return;
  }
  aviso.textContent = "";

  enviarResenha(idLivro, notaSelecionada, texto).then(function () {
    document.getElementById("texto-resenha").value = "";
    notaSelecionada = 0;
    pintarSeletor();
    carregarPagina();
  }).catch(function (erro) {
    aviso.textContent = "Ainda não é possível enviar avaliações por aqui.";
  });
});

carregarPagina();