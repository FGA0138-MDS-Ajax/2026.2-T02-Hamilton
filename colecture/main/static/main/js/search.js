var searchInput = document.getElementById("searchInput");
var genreFilter = document.getElementById("genreFilter");
var searchButton = document.getElementById("searchButton");
var resultsInfo = document.getElementById("resultsInfo");
var bookList = document.getElementById("bookList");
var searchUrl = document.querySelector("main").dataset.searchUrl;


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

var modalParts = {};          // guarda os elementos da caixa
var modalOptionButtons = [];  // botoes Lendo / Lido / Quero ler
var currentBook = null;       // livro que esta aberto na caixa
var currentOnSave = null;     // funcao chamada depois de salvar
var selectedStatus = "";      // opcao marcada na caixa

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

// Fecha a caixa
function closeModal() {
  modalParts.overlay.classList.remove("open");
}

// Cria um botao de opcao dentro da caixa
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

// Monta a caixa inteira e coloca na pagina
function buildModal() {
  var overlay = document.createElement("div");
  overlay.className = "modal-overlay";

  var box = document.createElement("div");
  box.className = "modal-box";

  // topo: titulo + botao de fechar
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



// Cria a imagem da capa a partir do campo icon (URL) do livro
function createCover(book) {
  var cover = document.createElement("img");
  cover.className = "book-cover";
  cover.src = book.icon;
  cover.alt = "Capa de " + book.title;
  cover.loading = "lazy";

  // se a URL estiver quebrada, tira a imagem para nao mostrar um icone feio
  cover.addEventListener("error", function () {
    cover.remove();
  });

  return cover;
}

function showBooks(books, total) {
  bookList.innerHTML = "";

  if (books.length === 0) {
    resultsInfo.textContent = "Nenhum livro encontrado.";
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

    // imagem do livro: so aparece se o campo icon estiver preenchido
    if (book.icon) {
      card.appendChild(createCover(book));
    }

    // area de texto
    var info = document.createElement("div");
    info.className = "book-info";

    var title = document.createElement("h3");
    title.className = "book-title";
    title.textContent = book.title;

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

function searchBooks() {
  var term = searchInput.value.trim();
  var genre = genreFilter.value;

  var params = new URLSearchParams({ q: term, genre: genre });

  // evita que uma resposta antiga sobrescreva uma busca mais nova
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

searchButton.addEventListener("click", searchBooks);


searchInput.addEventListener("keypress", function (event) {
  if (event.key === "Enter") {
    searchBooks();
  }
});

genreFilter.addEventListener("change", searchBooks);

document.addEventListener("keydown", function (event) {
  if (event.key === "Escape" && modalParts.overlay) {
    closeModal();
  }
});

searchBooks();