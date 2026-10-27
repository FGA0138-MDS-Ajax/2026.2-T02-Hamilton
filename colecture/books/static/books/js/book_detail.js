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

// ---------------------------------------------------------
// FRONT
// O envio da avaliacao e feito pelo proprio formulario (POST para a
// mesma URL, tratado pela view book_detail com o BookReviewForm).
// ---------------------------------------------------------
const idLivro = document.body.dataset.id;

// Campo "rating" do Django (select escondido) e formulario
const campoNota = document.getElementById("id_rating");
const formResenha = document.getElementById("form-resenha");

// Ja comeca com a nota que o Django renderizou (avaliacao anterior do usuario)
let notaSelecionada = campoNota ? Number(campoNota.value) || 0 : 0;

function estrelasTexto(nota) {
  const cheias = Math.round(nota);
  return "★".repeat(cheias) + "☆".repeat(5 - cheias);
}

function formatarData(dataIso) {
  if (!dataIso) return "";
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
  pintarSeletor();
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
    item.appendChild(cabecalho);

    // A resenha em texto e opcional
    if (r.texto) {
      const texto = document.createElement("p");
      texto.textContent = r.texto;
      item.appendChild(texto);
    }

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

// Grava a nota escolhida no campo "rating" do formulario Django
function definirNotaNoForm(nota) {
  if (!campoNota) return;

  if (campoNota.tagName === "SELECT") {
    // procura a opcao cujo valor numerico e igual a nota (ex.: "4", "4.0" ou "4,0")
    const opcao = Array.from(campoNota.options).find(function (o) {
      return o.value !== "" && Number(o.value) === nota;
    });
    if (opcao) {
      campoNota.value = opcao.value;
    } else {
      campoNota.add(new Option(nota, nota, true, true));
    }
  } else {
    campoNota.value = nota;
  }
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
    definirNotaNoForm(notaSelecionada);
    pintarSeletor();
  });
});

// Enviar avaliacao: valida no navegador e deixa o formulario seguir para o Django
if (formResenha) {
  formResenha.addEventListener("submit", function (evento) {
    const aviso = document.getElementById("aviso");

    if (notaSelecionada === 0) {
      evento.preventDefault();
      aviso.textContent = "Escolha uma nota de 1 a 5 estrelas.";
      return;
    }
    aviso.textContent = "";
    // sem preventDefault: o navegador faz o POST e a view salva a avaliacao
  });
}

carregarPagina();