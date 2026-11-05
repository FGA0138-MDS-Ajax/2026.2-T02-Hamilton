
var dados = JSON.parse(document.getElementById("dados-forum").textContent);

var storageKey = "colectureForum-" + dados.id;

var forumTitle = document.getElementById("forumTitle");
var forumBadge = document.getElementById("forumBadge");
var forumDescription = document.getElementById("forumDescription");
var descToggle = document.getElementById("descToggle");

var forumMenu = document.getElementById("forumMenu");
var menuButton = document.getElementById("menuButton");
var menuList = document.getElementById("menuList");
var menuPin = document.getElementById("menuPin");
var menuLock = document.getElementById("menuLock");
var menuDelete = document.getElementById("menuDelete");

var pinnedBox = document.getElementById("pinnedBox");
var pinnedContent = document.getElementById("pinnedContent");
var pinnedRemove = document.getElementById("pinnedRemove");
var pickBanner = document.getElementById("pickBanner");
var pickCancel = document.getElementById("pickCancel");

var messagesBox = document.getElementById("messages");
var lockedNotice = document.getElementById("lockedNotice");
var composer = document.getElementById("composer");
var messageInput = document.getElementById("messageInput");

var confirmOverlay = document.getElementById("confirmOverlay");
var confirmCancel = document.getElementById("confirmCancel");
var confirmDelete = document.getElementById("confirmDelete");

var forumBox = document.getElementById("forum");

// Estado da página
var state = {
  locked: dados.locked === true,
  pinnedId: dados.pinned_id || null,
  messages: dados.messages || []
};
var picking = false; 



function loadState() {
  var saved = null;
  try { saved = localStorage.getItem(storageKey); } catch (e) {}
  if (saved) {
    state = JSON.parse(saved);
  }
}

function saveState() {
  try { localStorage.setItem(storageKey, JSON.stringify(state)); } catch (e) {}
}



function renderHeader() {
  if (dados.community_url) {
    document.getElementById("forumBack").href = dados.community_url;
    forumBox.dataset.redirectUrl = dados.community_url;
  }

  forumTitle.textContent = dados.title;
  forumTitle.title = dados.title;
  forumDescription.textContent = dados.description || "";

  if (dados.kind === "meta") {
    forumBadge.textContent = "Meta: " + dados.meta_name;
  } else {
    forumBadge.textContent = "Fórum geral";
  }

  if (!dados.description) {
    forumDescription.classList.add("hidden");
  }

  updateDescToggle();
}

function updateDescToggle() {
  var overflowing = forumDescription.scrollHeight > forumDescription.clientHeight + 1;
  var expanded = forumDescription.classList.contains("expanded");

  if (dados.description && (overflowing || expanded)) {
    descToggle.classList.remove("hidden");
  } else {
    descToggle.classList.add("hidden");
  }
}

window.addEventListener("resize", updateDescToggle);



function renderDetails() {
  document.getElementById("sideAbout").textContent = dados.description || "Este fórum ainda não tem descrição.";

  document.getElementById("detailKind").textContent = dados.kind === "meta" ? "Meta: " + dados.meta_name : "Fórum geral";
  document.getElementById("detailCreator").textContent = dados.created_by || "-";
  document.getElementById("detailCount").textContent = state.messages.length;
  document.getElementById("detailStatus").textContent = state.locked ? "Trancado" : "Aberto";

  // Cadeado aberto ou fechado
  document.getElementById("iconUnlocked").classList.toggle("hidden", state.locked);
  document.getElementById("iconLocked").classList.toggle("hidden", !state.locked);
}

descToggle.addEventListener("click", function () {
  var expanded = forumDescription.classList.toggle("expanded");
  descToggle.textContent = expanded ? "ver menos" : "ver mais";
});



function closeMenu() {
  menuList.classList.remove("open");
  menuButton.setAttribute("aria-expanded", "false");
}

menuButton.addEventListener("click", function (event) {
  event.stopPropagation();
  var open = menuList.classList.toggle("open");
  menuButton.setAttribute("aria-expanded", String(open));
});

document.addEventListener("click", function (event) {
  if (!forumMenu.contains(event.target)) {
    closeMenu();
  }
});

menuPin.addEventListener("click", function () {
  closeMenu();
  picking = true;
  pickBanner.classList.remove("hidden");
  renderMessages();
});

pickCancel.addEventListener("click", stopPicking);

function stopPicking() {
  picking = false;
  pickBanner.classList.add("hidden");
  renderMessages();
}

pinnedRemove.addEventListener("click", function () {
  state.pinnedId = null;
  saveState();
  renderAll();
});

menuLock.addEventListener("click", function () {
  closeMenu();
  state.locked = !state.locked;
  saveState();
  // BACKEND: avisar o servidor que o chat foi trancado/destrancado
  renderAll();
});

menuDelete.addEventListener("click", function () {
  closeMenu();
  confirmOverlay.classList.add("open");
});

function closeConfirm() {
  confirmOverlay.classList.remove("open");
}

confirmCancel.addEventListener("click", closeConfirm);

confirmOverlay.addEventListener("click", function (event) {
  if (event.target === confirmOverlay) {
    closeConfirm();
  }
});

confirmDelete.addEventListener("click", function () {
  // BACKEND: fetch(deleteUrl, { method: "POST", ... }).then(function () { ...redireciona... })
  try { localStorage.removeItem(storageKey); } catch (e) {}
  window.location.href = forumBox.dataset.redirectUrl;
});

document.addEventListener("keydown", function (event) {
  if (event.key === "Escape") {
    closeConfirm();
    closeMenu();
    cancelReply();
    if (picking) {
      stopPicking();
    }
  }
});



function findMessage(id) {
  for (var i = 0; i < state.messages.length; i++) {
    if (state.messages[i].id === id) {
      return state.messages[i];
    }
  }
  return null;
}

function renderPinned() {
  var message = state.pinnedId ? findMessage(state.pinnedId) : null;

  if (!message) {
    pinnedBox.classList.add("hidden");
    return;
  }

  pinnedContent.textContent = message.author + ": " + message.text;
  pinnedBox.classList.remove("hidden");

  if (dados.is_moderator) {
    pinnedRemove.classList.remove("hidden");
  } else {
    pinnedRemove.classList.add("hidden");
  }
}


function createMessage(message) {
  var item = document.createElement("div");
  item.className = "message";
  item.dataset.id = message.id;

  if (message.mine) {
    item.classList.add("mine");
  }
  if (message.id === state.pinnedId) {
    item.classList.add("pinned-message");
  }
  if (picking) {
    item.classList.add("pickable");
    item.addEventListener("click", function () {
      state.pinnedId = message.id;
      saveState();
      // BACKEND: avisar o servidor qual mensagem foi fixada
      picking = false;
      pickBanner.classList.add("hidden");
      renderAll();
    });
  }

  var author = document.createElement("span");
  author.className = "message-author";
  author.textContent = message.author;

  var text = document.createElement("div");
  text.className = "message-text";
  text.textContent = message.text;

  var footer = document.createElement("div");
  footer.className = "message-footer";

  if (message.id === state.pinnedId) {
    var tag = document.createElement("span");
    tag.className = "message-pin-tag";
    tag.textContent = "Fixada";
    footer.appendChild(tag);
  }

  if (!picking && !state.locked) {
    var replyButton = document.createElement("button");
    replyButton.type = "button";
    replyButton.className = "message-reply-btn";
    replyButton.textContent = "Responder";
    replyButton.addEventListener("click", function () {
      startReply(message);
    });
    footer.appendChild(replyButton);
  }

  var time = document.createElement("span");
  time.textContent = message.time;
  footer.appendChild(time);

  if (!message.mine) {
    item.appendChild(author);
  }

  if (message.reply_to) {
    item.appendChild(createQuote(message.reply_to));
  }

  item.appendChild(text);
  item.appendChild(footer);

  return item;
}

function renderMessages() {
  messagesBox.innerHTML = "";

  if (state.messages.length === 0) {
    var empty = document.createElement("p");
    empty.className = "messages-empty";
    empty.textContent = "Nenhuma mensagem ainda. Comece a conversa!";
    messagesBox.appendChild(empty);
    return;
  }

  for (var i = 0; i < state.messages.length; i++) {
    messagesBox.appendChild(createMessage(state.messages[i]));
  }

  messagesBox.scrollTop = messagesBox.scrollHeight;
}



function renderLock() {
  if (state.locked) {
    cancelReply();
    lockedNotice.classList.remove("hidden");
    composer.classList.add("hidden");
    menuLock.textContent = "Destrancar chat";
  } else {
    lockedNotice.classList.add("hidden");
    composer.classList.remove("hidden");
    menuLock.textContent = "Trancar chat";
  }
}



var replyBar = document.getElementById("replyBar");
var replyBarAuthor = document.getElementById("replyBarAuthor");
var replyBarContent = document.getElementById("replyBarContent");
var replyBarClose = document.getElementById("replyBarClose");

var replyingTo = null; 
function startReply(message) {
  replyingTo = {
    id: message.id,
    author: message.author,
    text: message.text.slice(0, 200)
  };

  replyBarAuthor.textContent = replyingTo.author;
  replyBarContent.textContent = replyingTo.text;
  replyBar.classList.remove("hidden");
  messageInput.focus();
}

function cancelReply() {
  replyingTo = null;
  replyBar.classList.add("hidden");
}

replyBarClose.addEventListener("click", cancelReply);

function createQuote(reply) {
  var quote = document.createElement("div");
  quote.className = "reply-quote";

  var quoteAuthor = document.createElement("span");
  quoteAuthor.className = "reply-quote-author";
  quoteAuthor.textContent = reply.author;

  var quoteText = document.createElement("div");
  quoteText.className = "reply-quote-text";
  quoteText.textContent = reply.text;

  quote.appendChild(quoteAuthor);
  quote.appendChild(quoteText);

  quote.addEventListener("click", function () {
    goToMessage(reply.id);
  });

  return quote;
}

function goToMessage(id) {
  var original = messagesBox.querySelector('[data-id="' + id + '"]');

  if (!original) {
    return;
  }

  original.scrollIntoView({ behavior: "smooth", block: "center" });
  original.classList.add("highlight");

  setTimeout(function () {
    original.classList.remove("highlight");
  }, 1500);
}



function getTime() {
  var now = new Date();
  var hours = String(now.getHours()).padStart(2, "0");
  var minutes = String(now.getMinutes()).padStart(2, "0");
  return hours + ":" + minutes;
}

function sendMessage() {
  var text = messageInput.value.trim();

  if (text === "" || state.locked) {
    return;
  }

  // BACKEND: fetch(sendUrl, { method: "POST", body: ... }).then(...) e usar a resposta do servidor
  state.messages.push({
    id: Date.now(),
    author: dados.current_user || "Você",
    text: text,
    time: getTime(),
    mine: true,
    reply_to: replyingTo
  });

  cancelReply();
  saveState();
  messageInput.value = "";
  resizeInput();
  renderMessages();
  renderDetails();
}

composer.addEventListener("submit", function (event) {
  event.preventDefault();
  sendMessage();
});

messageInput.addEventListener("keydown", function (event) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
});

function resizeInput() {
  messageInput.style.height = "auto";
  messageInput.style.height = messageInput.scrollHeight + "px";
}

messageInput.addEventListener("input", resizeInput);



function renderAll() {
  renderPinned();
  renderMessages();
  renderLock();
  renderDetails();
}

if (dados.is_moderator) {
  forumMenu.classList.remove("hidden");
}

loadState();
renderHeader();
renderAll();