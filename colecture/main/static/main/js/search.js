
var searchInput = document.getElementById("searchInput");
var genreFilter = document.getElementById("genreFilter");
var searchButton = document.getElementById("searchButton");
var resultsInfo = document.getElementById("resultsInfo");
var bookList = document.getElementById("bookList");


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



function showBooks(books) {
  bookList.innerHTML = "";

  if (books.length === 0) {
    resultsInfo.textContent = "Nenhum livro encontrado.";
    return;
  }

  resultsInfo.textContent = books.length + " livro(s) encontrado(s)";

  for (var i = 0; i < books.length; i++) {
    var book = books[i];

    var card = document.createElement("div");
    card.className = "book-card";

    var cover = document.createElement("img");
    cover.className = "book-cover";
    cover.alt = "Capa de " + book.title;
    if (book.cover !== "") {
      cover.src = book.cover;
    }

    // area de texto
    var info = document.createElement("div");
    info.className = "book-info";

    var title = document.createElement("h3");
    title.className = "book-title";
    title.textContent = book.title;

    var author = document.createElement("p");
    author.className = "book-author";
    author.textContent = book.author + " (" + book.year + ")";

    var synopsis = document.createElement("p");
    synopsis.className = "book-synopsis";
    synopsis.textContent = book.synopsis;

    var genre = document.createElement("span");
    genre.className = "book-genre";
    genre.textContent = book.genre;

    info.appendChild(title);
    info.appendChild(author);
    info.appendChild(synopsis);
    info.appendChild(genre);
    info.appendChild(createActions(book));

    card.appendChild(cover);
    card.appendChild(info);
    bookList.appendChild(card);
  }
}
//API
function convertBook(item) {
  var cover = "";
  if (item.cover_i) {
    cover = "https://covers.openlibrary.org/b/id/" + item.cover_i + "-M.jpg";
  }

  var synopsis = "Sem descrição.";
  if (item.first_sentence) {
    if (Array.isArray(item.first_sentence)) {
      synopsis = item.first_sentence[0];
    } else {
      synopsis = item.first_sentence;
    }
  }

  var title = item.title || "Sem título";
  var author = item.author_name ? item.author_name.join(", ") : "Autor desconhecido";

  return {
    id: item.key || (title + "-" + author),
    title: title,
    author: author,
    genre: item.subject ? item.subject[0] : "Sem gênero",
    year: item.first_publish_year || "?",
    synopsis: synopsis,
    cover: cover
  };
}

function searchBooks() {
  var term = searchInput.value.trim();
  var genre = genreFilter.value;

  if (term === "") {
    resultsInfo.textContent = "Digite um título ou autor para buscar.";
    bookList.innerHTML = "";
    return;
  }

  var query = term;
  if (genre !== "") {
    query = query + ' subject:"' + genre + '"';
  }

  var url = "https://openlibrary.org/search.json?q=" + encodeURIComponent(query) +
    "&limit=20&fields=key,title,author_name,first_publish_year,subject,cover_i,first_sentence";

  resultsInfo.textContent = "Buscando...";
  bookList.innerHTML = "";

  fetch(url)
    .then(function (response) {
      if (!response.ok) {
        throw new Error("A API respondeu com status " + response.status);
      }
      return response.json();
    })
    .then(function (data) {
      var items = data.docs || [];
      var books = [];

      for (var i = 0; i < items.length; i++) {
        books.push(convertBook(items[i]));
      }

      showBooks(books);
    })
    .catch(function (error) {
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

genreFilter.addEventListener("change", function () {
  if (searchInput.value.trim() !== "") {
    searchBooks();
  }
});

document.addEventListener("keydown", function (event) {
  if (event.key === "Escape" && modalParts.overlay) {
    closeModal();
  }
});
