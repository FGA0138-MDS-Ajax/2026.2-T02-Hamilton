var searchInput = document.getElementById("searchInput");
var genreFilter = document.getElementById("genreFilter");
var searchButton = document.getElementById("searchButton");
var resultsInfo = document.getElementById("resultsInfo");
var bookList = document.getElementById("bookList");
// Procura pelo atributo (e não pela tag <main>): o sidebar.html já envolve a página em um <main>.
var searchUrl = document.querySelector("[data-search-url]").dataset.searchUrl;
var communitiesUrl = document.querySelector("[data-communities-url]").dataset.communitiesUrl;
// Estante do usuário (tags Lendo/Lido/Quero ler): o banco (BookStatus) é a única fonte de verdade
var shelfUrl = document.querySelector("[data-shelf-url]").dataset.shelfUrl;
var tabBooks = document.getElementById("tabBooks");
var tabCommunities = document.getElementById("tabCommunities");
var currentTab = "books";
var emptyImg = document.querySelector("[data-empty-img]").dataset.emptyImg;


var statusOptions = [
  { value: "READING", label: "Lendo" },
  { value: "READ", label: "Lido" },
  { value: "WANT_TO_READ", label: "Quero ler" }
];
// Cache em memória da estante ({ idDoLivro: "READ" | "READING" | "WANT_TO_READ" }).
// Só é preenchido com o que o servidor devolveu (busca) ou confirmou (setStatus);
// nada é gravado no navegador.
var userShelf = {};


function getShelf() {
  return userShelf;
}

// Avisa o usuário (toast do main/js/toast.js; cai no console se não estiver carregado)
function notify(type, title, description) {
  if (typeof window.showToast === "function") {
    window.showToast(type, title, description || "");
  } else {
    (type === "error" ? console.error : console.log)(title, description || "");
  }
}

// Função auxiliar do Django para pegar o CSRF Token dos cookies
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Grava a tag no banco (POST books:manage_bookshelf; status "" remove da estante).
// Devolve uma Promise: só rejeita se o servidor NÃO gravou, e o cache local
// (userShelf) só muda depois da confirmação.
function setStatus(bookId, status) {
  return fetch(shelfUrl, {
        method: "POST",
        credentials: "same-origin",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken") // Obrigatório no Django para POST
        },
        body: JSON.stringify({ book_id: bookId, status: status })
    })
    .then(function (response) {
        if (!response.ok) {
            throw new Error("O servidor respondeu com status " + response.status);
        }

        if (status === "") {
            delete userShelf[bookId];
        } else {
            userShelf[bookId] = status;
        }

        // Igual à estante do perfil: "Lido" também grava data de conclusão e progresso 100%
        if (status === "READ") {
            return fetch(shelfUrl + bookId + "/mark-read/", {
                method: "POST",
                credentials: "same-origin",
                headers: { "X-CSRFToken": getCookie("csrftoken") }
            }).then(function (markResponse) {
                if (!markResponse.ok) {
                    console.error("Não foi possível registrar a data de conclusão do livro.");
                }
            });
        }
    });
}

// A busca (/books/search/) já devolve o status de cada livro na estante do usuário,
// lido do BookStatus no banco. Aqui só guardamos esses status para os botões e o pop-up.
function updateShelfFromResults(books) {
  for (var i = 0; i < books.length; i++) {
    if (books[i].status) {
      userShelf[books[i].id] = books[i].status;
    } else {
      delete userShelf[books[i].id];
    }
  }
}

function getStatusLabel(status) {
  for (var i = 0; i < statusOptions.length; i++) {
    if (statusOptions[i].value === status) {
      return statusOptions[i].label;
    }
  }
  return "";
}

var modalParts = {};          
var modalOptionButtons = []; 
var currentBook = null;       
var currentOnSave = null;     
var selectedStatus = "";      

function refreshModal() {
  for (var i = 0; i < modalOptionButtons.length; i++) {
    var item = modalOptionButtons[i];

    if (item.value === selectedStatus) {
      item.button.classList.add("selected");
    } else {
      item.button.classList.remove("selected");
    }
  }

  modalParts.saveButton.disabled = (selectedStatus === "");
}


function closeModal() {
  modalParts.overlay.classList.remove("open");
}

function addModalOption(option) {
  var button = document.createElement("button");
  button.className = "modal-option";
  button.textContent = option.label;

  button.addEventListener("click", function () {
    selectedStatus = option.value;
    refreshModal();
  });

  modalParts.optionsBox.appendChild(button);
  modalOptionButtons.push({ button: button, value: option.value });
}

function buildModal() {
  var overlay = document.createElement("div");
  overlay.className = "modal-overlay";

  var box = document.createElement("div");
  box.className = "modal-box";

  var header = document.createElement("div");
  header.className = "modal-header";

  var heading = document.createElement("h2");
  heading.textContent = "Adicionar livro";

  var closeButton = document.createElement("button");
  closeButton.className = "modal-close";
  closeButton.textContent = "×";
  closeButton.addEventListener("click", closeModal);

  header.appendChild(heading);
  header.appendChild(closeButton);


  var body = document.createElement("div");
  body.className = "modal-body";

  var bookName = document.createElement("p");
  bookName.className = "modal-book-name";

  var question = document.createElement("p");
  question.className = "modal-question";
  question.textContent = "Em qual estante o livro vai ficar?";

  var optionsBox = document.createElement("div");
  optionsBox.className = "modal-options";

  var removeButton = document.createElement("button");
  removeButton.className = "modal-remove";
  removeButton.textContent = "Remover da lista";

  body.appendChild(bookName);
  body.appendChild(question);
  body.appendChild(optionsBox);
  body.appendChild(removeButton);

  var footer = document.createElement("div");
  footer.className = "modal-footer";

  var cancelButton = document.createElement("button");
  cancelButton.className = "modal-cancel";
  cancelButton.textContent = "Cancelar";
  cancelButton.addEventListener("click", closeModal);

  var saveButton = document.createElement("button");
  saveButton.className = "modal-save";
  saveButton.textContent = "Salvar";

  footer.appendChild(cancelButton);
  footer.appendChild(saveButton);

  box.appendChild(header);
  box.appendChild(body);
  box.appendChild(footer);
  overlay.appendChild(box);
  document.body.appendChild(overlay);


  modalParts.overlay = overlay;
  modalParts.bookName = bookName;
  modalParts.optionsBox = optionsBox;
  modalParts.removeButton = removeButton;
  modalParts.saveButton = saveButton;


  for (var i = 0; i < statusOptions.length; i++) {
    addModalOption(statusOptions[i]);
  }

  
  // Salva/remove no banco e só então atualiza o botão do card e fecha o pop-up
  function commitStatus(status) {
    var book = currentBook;
    var onSave = currentOnSave;

    saveButton.disabled = true;
    removeButton.disabled = true;

    setStatus(book.id, status)
      .then(function () {
        onSave();
        closeModal();
      })
      .catch(function (error) {
        console.log("Erro ao salvar a estante:", error);
        notify("error", "Não foi possível atualizar a estante", "Tente novamente em instantes.");
      })
      .then(function () {
        removeButton.disabled = false;
        refreshModal();
      });
  }

  saveButton.addEventListener("click", function () {
    commitStatus(selectedStatus);
  });

  removeButton.addEventListener("click", function () {
    commitStatus("");
  });

  overlay.addEventListener("click", function (event) {
    if (event.target === overlay) {
      closeModal();
    }
  });
}

function openModal(book, onSave) {
  if (!modalParts.overlay) {
    buildModal();
  }

  currentBook = book;
  currentOnSave = onSave;

  var currentStatus = getShelf()[book.id];
  if (currentStatus) {
    selectedStatus = currentStatus;
    modalParts.removeButton.classList.remove("hidden");
  } else {
    selectedStatus = "";
    modalParts.removeButton.classList.add("hidden");
  }

  modalParts.bookName.textContent = book.title;
  refreshModal();
  modalParts.overlay.classList.add("open");
}


function createActions(book) {
  var actions = document.createElement("div");
  actions.className = "book-actions";

  var addButton = document.createElement("button");
  addButton.className = "add-button";

   function updateButton() {
    var status = getShelf()[book.id];

    if (status) {
      addButton.textContent = getStatusLabel(status);
      addButton.classList.add("added");
    } else {
      addButton.textContent = "+ Adicionar";
      addButton.classList.remove("added");
    }
  }

  addButton.addEventListener("click", function () {
    openModal(book, updateButton);
  });

  updateButton();

  actions.appendChild(addButton);

  return actions;
}



function createCover(book) {
  var cover = document.createElement("img");
  cover.className = "book-cover";
  cover.src = book.icon;
  cover.alt = "Capa de " + book.title;
  cover.loading = "lazy";

  cover.addEventListener("error", function () {
    cover.remove();
  });

  return cover;
}

function showBooks(books, total) {
  bookList.innerHTML = "";

  if (books.length === 0) {
    resultsInfo.textContent = "Nenhum livro encontrado.";

    var registerLink = document.createElement("a");
    registerLink.href = "/books/register/";
    registerLink.className = "register-button";
    registerLink.textContent = "Cadastrar livro";
    bookList.appendChild(registerLink);

    return;
  }

  if (total > books.length) {
    resultsInfo.textContent = "Mostrando " + books.length + " de " + total + " livros";
  } else {
    resultsInfo.textContent = total === 1 ? "1 livro encontrado" : total + " livros encontrados";
  }

  for (var i = 0; i < books.length; i++) {
    bookList.appendChild(createBookCard(books[i]));
  }
}

// "4,7 (12)" / "4,7 (12k)"; livro sem avaliação mostra "Sem avaliações"
function formatCount(count) {
  if (count >= 1000) {
    return (Math.round(count / 100) / 10).toString().replace(".", ",") + "k";
  }
  return String(count);
}

function createRating(book) {
  var rating = document.createElement("p");
  rating.className = "book-rating";

  if (book.rating === null || book.rating === undefined) {
    rating.classList.add("book-rating-empty");
    rating.textContent = "Sem avaliações";
    return rating;
  }

  var star = document.createElement("i");
  star.className = "bx bxs-star";
  star.setAttribute("aria-hidden", "true");

  var value = document.createElement("span");
  value.textContent = book.rating.toFixed(1).replace(".", ",") + " (" + formatCount(book.rating_count) + ")";

  rating.appendChild(star);
  rating.appendChild(value);
  rating.title = book.rating_count + " avaliação(ões)";
  return rating;
}

// Card de livro (usado na lista da busca e em "Recomendados para você").
// variant "compact": versão do carrossel, sem o botão da estante.
// Clicar em qualquer parte do card abre a página do livro, menos no botão da estante.
function createBookCard(book, variant) {
    var compact = variant === "compact";
    var card = document.createElement("div");
    card.className = "book-card book-card-clickable" + (compact ? " book-card-compact" : "");
    var bookUrl = "/books/" + book.id + "/";

    card.addEventListener("click", function (event) {
      if (event.target.closest("a, button")) {
        return;
      }
      window.location.href = bookUrl;
    });

  if (book.icon) {
      var coverLink = document.createElement("a");
      coverLink.href = bookUrl;
      coverLink.className = "book-link";
      coverLink.appendChild(createCover(book));
      card.appendChild(coverLink);
  } else {
      var noCover = document.createElement("div");
      noCover.className = "book-cover book-cover-empty";
      card.appendChild(noCover);
  }

    var info = document.createElement("div");
    info.className = "book-info";

    var title = document.createElement("h3");
    title.className = "book-title";

    var titleLink = document.createElement("a");
    titleLink.href = bookUrl;
    titleLink.className = "book-link";
    titleLink.textContent = book.title;
    // texto completo ao passar o mouse (o CSS corta com "...")
    title.title = book.title;

    title.appendChild(titleLink);

    var author = document.createElement("p");
    author.className = "book-author";
    author.textContent = book.author;
    author.title = book.author;

    info.appendChild(title);
    info.appendChild(author);
    // Só mostra a nota se o back mandar esse campo (hoje a busca não manda)
    if (book.rating !== undefined) {
      info.appendChild(createRating(book));
    }

    if (!compact) {
      info.appendChild(createActions(book));
    }

    card.appendChild(info);
    return card;
}

// ---------------------------------------------------------------------------
// "Recomendados para você": aparece ao entrar na pesquisa (aba Livros, sem
// termo nem gênero). A lista já vem ordenada do back; aqui só exibimos.
// ---------------------------------------------------------------------------
var recommendationsUrl = document.querySelector("[data-recommendations-url]").dataset.recommendationsUrl;
var recommendationsSection = document.getElementById("recommendations");
var recommendationsList = document.getElementById("recommendationsList");
var recommendationsLoaded = false;

function showRecommendations(books) {
  recommendationsList.innerHTML = "";
  recommendationsList.classList.toggle("is-empty", books.length === 0);

  if (books.length === 0) {
    var empty = document.createElement("p");
    empty.className = "recommendations-empty";
    empty.textContent = "Marque livros como lidos para receber recomendações.";
    recommendationsList.appendChild(empty);
    return;
  }

  for (var i = 0; i < books.length; i++) {
    recommendationsList.appendChild(createBookCard(books[i], "compact"));
  }
}

// Setas do carrossel: rolam quase uma "tela" da faixa por clique.
// Ficam desabilitadas no começo/fim e somem se tudo couber sem rolar.
var recommendationsPrev = document.getElementById("recommendationsPrev");
var recommendationsNext = document.getElementById("recommendationsNext");

function scrollRecommendations(direction) {
  recommendationsList.scrollBy({
    left: direction * recommendationsList.clientWidth * 0.8,
    behavior: "smooth"
  });
}

function updateCarouselArrows() {
  var maxScroll = recommendationsList.scrollWidth - recommendationsList.clientWidth;
  var scrollable = maxScroll > 1;

  recommendationsPrev.classList.toggle("invisible", !scrollable);
  recommendationsNext.classList.toggle("invisible", !scrollable);
  recommendationsPrev.disabled = recommendationsList.scrollLeft <= 1;
  recommendationsNext.disabled = recommendationsList.scrollLeft >= maxScroll - 1;
}

recommendationsPrev.addEventListener("click", function () { scrollRecommendations(-1); });
recommendationsNext.addEventListener("click", function () { scrollRecommendations(1); });
recommendationsList.addEventListener("scroll", updateCarouselArrows);
window.addEventListener("resize", updateCarouselArrows);

function loadRecommendations() {
  fetch(recommendationsUrl, { credentials: "same-origin" })
    .then(function (response) {
      if (!response.ok) {
        throw new Error("O servidor respondeu com status " + response.status);
      }
      return response.json();
    })
    .then(function (data) {
      recommendationsLoaded = true;
      updateShelfFromResults(data.results);
      showRecommendations(data.results);
      updateRecommendationsVisibility();
    })
    .catch(function (error) {
      // Sem recomendações a busca continua funcionando: só some a seção
      console.log("Erro ao carregar recomendações:", error);
      recommendationsSection.classList.add("hidden");
    });
}

function updateRecommendationsVisibility() {
  var isInitialView = currentTab === "books"
    && searchInput.value.trim() === ""
    && genreFilter.value === "";

  if (recommendationsLoaded && isInitialView) {
    recommendationsSection.classList.remove("hidden");
    updateCarouselArrows();
  } else {
    recommendationsSection.classList.add("hidden");
  }
}

// Busca no banco de dados do CoLecture (tabela books_book)
var lastRequest = 0;

function showEmptyState(titleText, messageText) {
  var box = document.createElement("div");
  box.className = "empty-state";

  var title = document.createElement("h2");
  title.className = "empty-title";
  title.textContent = titleText;

  var message = document.createElement("p");
  message.className = "empty-message";
  message.textContent = messageText;

  var backButton = document.createElement("button");
  backButton.type = "button";
  backButton.className = "empty-button";
  backButton.textContent = "Limpar busca";
  backButton.addEventListener("click", function () {
    searchInput.value = "";
    runSearch();
  });

  var image = document.createElement("img");
  image.className = "empty-img";
  image.src = emptyImg;
  image.alt = "Mascote procurando comunidades";

  box.appendChild(title);
  box.appendChild(message);
  box.appendChild(backButton);
  box.appendChild(image);

  bookList.appendChild(box);
}

function showCommunities(communities, total) {
  bookList.innerHTML = "";

  //colocar pagina do gato com lupa para dar o aviso
  if (communities.length === 0) {
    resultsInfo.textContent = "";
    showEmptyState("Comunidade não encontrada", "Nenhuma comunidade pública bate com a sua busca.");
    return;
  }

  if (total > communities.length) {
    resultsInfo.textContent = "Mostrando " + communities.length + " de " + total + " comunidades";
  } else {
    resultsInfo.textContent = total + " comunidade(s) encontrada(s)";
  }

  for (var i = 0; i < communities.length; i++) {
    var community = communities[i];

    var card = document.createElement("div");
    card.className = "book-card";

    var info = document.createElement("div");
    info.className = "book-info";

    var title = document.createElement("h3");
    title.className = "book-title";
    title.textContent = community.name;
    // texto completo ao passar o mouse (o CSS corta com "...")
    title.title = community.name;

    var description = document.createElement("p");
    description.className = "book-synopsis";
    description.textContent = community.description || "Sem descrição.";
    description.title = description.textContent;

    var members = document.createElement("span");
    members.className = "book-genre";
    members.textContent = community.members_count + " membro(s)";

    var actions = document.createElement("div");
    actions.className = "book-actions";

    var joinLink = document.createElement("a");
    joinLink.className = "add-button";
    joinLink.href = community.url;
    joinLink.textContent = "Entrar na comunidade";

    actions.appendChild(joinLink);

    info.appendChild(title);
    info.appendChild(description);
    info.appendChild(members);
    info.appendChild(actions);

    card.appendChild(info);
    bookList.appendChild(card);
  }
}

function searchCommunities() {
  var term = searchInput.value.trim();
  var params = new URLSearchParams({ q: term });

  lastRequest++;
  var thisRequest = lastRequest;

  resultsInfo.textContent = "Buscando...";
  bookList.innerHTML = "";

  fetch(communitiesUrl + "?" + params.toString())
    .then(function (response) {
      if (!response.ok) {
        throw new Error("O servidor respondeu com status " + response.status);
      }
      return response.json();
    })
    .then(function (data) {
      if (thisRequest !== lastRequest) {
        return;
      }
      showCommunities(data.results, data.total);
    })
    .catch(function (error) {
      if (thisRequest !== lastRequest) {
        return;
      }
      console.log("Erro ao buscar comunidades:", error);
      resultsInfo.textContent = "Erro ao buscar as comunidades. Tente novamente em alguns minutos.";
    });
}

// Título acima da lista: muda conforme o que está sendo mostrado
// (sem busca = catálogo; com termo = resultados; só gênero = livros do gênero)
var resultsTitle = document.getElementById("resultsTitle");
var resultsIcon = document.getElementById("resultsIcon");

function updateResultsTitle() {
  var term = searchInput.value.trim();
  var genre = genreFilter.value;
  var isBooks = currentTab === "books";
  var text;

  if (term) {
    text = "Resultados para “" + term + "”";
  } else if (!isBooks) {
    text = "Comunidades públicas";
  } else if (genre) {
    text = "Livros de " + genreFilter.options[genreFilter.selectedIndex].text;
  } else {
    text = "Explore o catálogo";
  }

  resultsTitle.textContent = text;
  resultsIcon.className = "bx " + (term ? "bx-search" : (isBooks ? "bx-book-open" : "bx-group"));
}

function runSearch() {
  updateRecommendationsVisibility();
  updateResultsTitle();

  if (currentTab === "communities") {
    searchCommunities();
  } else {
    searchBooks();
  }
}

function setTab(tab) {
  currentTab = tab;

  if (tab === "communities") {
    tabCommunities.classList.add("active");
    tabBooks.classList.remove("active");
    genreFilter.classList.add("hidden");
    searchInput.placeholder = "Buscar comunidades...";
  } else {
    tabBooks.classList.add("active");
    tabCommunities.classList.remove("active");
    genreFilter.classList.remove("hidden");
    searchInput.placeholder = "Buscar livros...";
  }

  runSearch();
}

tabBooks.addEventListener("click", function () { setTab("books"); });
tabCommunities.addEventListener("click", function () { setTab("communities"); });

function searchBooks() {
  var term = searchInput.value.trim();
  var genre = genreFilter.value;

  var params = new URLSearchParams({ q: term, genre: genre });

  lastRequest++;
  var thisRequest = lastRequest;

  resultsInfo.textContent = "Buscando...";
  bookList.innerHTML = "";

  fetch(searchUrl + "?" + params.toString())
    .then(function (response) {
      if (!response.ok) {
        throw new Error("O servidor respondeu com status " + response.status);
      }
      return response.json();
    })
    .then(function (data) {
      if (thisRequest !== lastRequest) {
        return;
      }
      updateShelfFromResults(data.results);
      showBooks(data.results, data.total);
    })
    .catch(function (error) {
      if (thisRequest !== lastRequest) {
        return;
      }
      console.log("Erro ao buscar:", error);
      resultsInfo.textContent = "Erro ao buscar os livros. Tente novamente em alguns minutos.";
    });
}

searchButton.addEventListener("click", runSearch);


searchInput.addEventListener("keypress", function (event) {
  if (event.key === "Enter") {
    runSearch();
  }
});

genreFilter.addEventListener("change", runSearch);

document.addEventListener("keydown", function (event) {
  if (event.key === "Escape" && modalParts.overlay) {
    closeModal();
  }
});

loadRecommendations();
runSearch();