var searchInput = document.getElementById("searchInput");
var genreFilter = document.getElementById("genreFilter");
var searchButton = document.getElementById("searchButton");
var resultsInfo = document.getElementById("resultsInfo");
var bookList = document.getElementById("bookList");
// Procura pelo atributo (e não pela tag <main>): o sidebar.html já envolve a página em um <main>.
var searchUrl = document.querySelector("[data-search-url]").dataset.searchUrl;
var communitiesUrl = document.querySelector("[data-communities-url]").dataset.communitiesUrl;
var tabBooks = document.getElementById("tabBooks");
var tabCommunities = document.getElementById("tabCommunities");
var currentTab = "books";
var emptyImg = document.querySelector("[data-empty-img]").dataset.emptyImg;


var statusOptions = [
  { value: "reading", label: "Lendo" },
  { value: "read", label: "Lido" },
  { value: "want-to-read", label: "Quero ler" }
];


var shelfStorageKey = "colectureShelf";


function getShelf() {
  var saved = localStorage.getItem(shelfStorageKey);
  if (saved) {
    return JSON.parse(saved);
  }
  return {};
}


function saveShelf(shelf) {
  localStorage.setItem(shelfStorageKey, JSON.stringify(shelf));
}


function setStatus(bookId, status) {
  var shelf = getShelf();

  if (status === "") {
    delete shelf[bookId];
  } else {
    shelf[bookId] = status;
  }

  saveShelf(shelf);


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

  
  saveButton.addEventListener("click", function () {
    setStatus(currentBook.id, selectedStatus);
    currentOnSave();
    closeModal();
  });

  
  removeButton.addEventListener("click", function () {
    setStatus(currentBook.id, "");
    currentOnSave();
    closeModal();
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
    resultsInfo.textContent = total + " livro(s) encontrado(s)";
  }

  for (var i = 0; i < books.length; i++) {
    var book = books[i];

    var card = document.createElement("div");
    card.className = "book-card";
    var bookUrl = "/books/" + book.id + "/";

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
  
    title.appendChild(titleLink);

    var author = document.createElement("p");
    author.className = "book-author";
    author.textContent = book.year ? book.author + " (" + book.year + ")" : book.author;

    var details = [];
    if (book.publisher) {
      details.push(book.publisher);
    }
    if (book.pages) {
      details.push(book.pages + " páginas");
    }
    details.push("ISBN " + book.isbn);

    var synopsis = document.createElement("p");
    synopsis.className = "book-synopsis";
    synopsis.textContent = details.join(" · ");

    info.appendChild(title);
    info.appendChild(author);
    info.appendChild(synopsis);

    if (book.genre) {
      var genre = document.createElement("span");
      genre.className = "book-genre";
      genre.textContent = book.genre;
      info.appendChild(genre);
    }

    info.appendChild(createActions(book));

    card.appendChild(info);
    bookList.appendChild(card);
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

    var description = document.createElement("p");
    description.className = "book-synopsis";
    description.textContent = community.description || "Sem descrição.";

    var members = document.createElement("span");
    members.className = "book-genre";
    members.textContent = community.members_count + " membro(s)";

    var actions = document.createElement("div");
    actions.className = "book-actions";

    var joinLink = document.createElement("a");
    joinLink.className = "add-button";
    joinLink.href = "/communities/" + community.id + "/";
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

function runSearch() {
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

runSearch();