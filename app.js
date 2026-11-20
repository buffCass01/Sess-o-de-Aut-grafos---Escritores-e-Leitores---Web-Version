"use strict";

const canvas = document.querySelector("#scene");
const ctx = canvas.getContext("2d");
const eventState = document.querySelector("#event-state");
const logList = document.querySelector("#event-log");
const logPanel = document.querySelector(".log-panel");
const autographButton = document.querySelector("#autograph");
const musicButton = document.querySelector("#toggle-music");
const readingTimeInput = document.querySelector("#reading-time");
const writingTimeInput = document.querySelector("#writing-time");
const readerLimitInput = document.querySelector("#reader-limit");

const scene = { width: 1260, height: 480 };
const maxVisibleFans = 5;
const terminalVisibleLines = 4;
const authors = [
  { name: "Gorender", label: "GORENDER", x: 675, appearance: 4, hairStyle: "balding", hairColor: "#514052" },
  {
    name: "Apolinário", label: "APOLINÁRIO", x: 755, appearance: 3,
    hairStyle: "quiff", hairColor: "#c0c5c8", skinColor: "#f1d8c0", shirtColor: "#4b965f", scale: 0.78,
  },
];
const terminalLines = [];
const queue = [];
const autographs = [];
const fanCharacters = new Map();
const readers = new Map();
const waitingReaders = [];
const activeReaders = new Map();
let nextFanId = 1;
let nextReaderId = 1;
let readerLimit = null;
let readerPriority = false;
let terminalScrollTop = 0;
let writerBusy = false;
let writerWaiting = false;
let writerActive = false;
let nextAuthorIndex = 0;
let signingAuthorIndex = 0;
let signingFan = null;
let audioContext = null;
let musicEnabled = true;
let musicTimer = null;
let musicIndex = 0;
let writingTimer = null;
let audioWarningShown = false;
let displayedAutographs = [];
let sceneState = {
  fan: "FÃ DA VEZ: AGUARDANDO AUTÓGRAFO",
  fanColor: "#f5c66a",
  reader: "LEITOR: LIVRE",
  readerColor: "#385d68",
  writer: "AUTORES: LIVRES",
  writerColor: "#9fe0a2",
};

const palettes = [
  { pele: "#f0b68f", cabelo: "#392b35", camisa: "#4c8f89", detalhe: "#e9c85d", calca: "#3e507b", sapato: "#4c332d" },
  { pele: "#d99b76", cabelo: "#472b62", camisa: "#ca668c", detalhe: "#f3d9a1", calca: "#633e72", sapato: "#382c43" },
  { pele: "#f4cba3", cabelo: "#d8873e", camisa: "#4187a1", detalhe: "#f2df6f", calca: "#466c75", sapato: "#48352c" },
  { pele: "#b8785c", cabelo: "#263d54", camisa: "#bd5967", detalhe: "#f2c8a4", calca: "#455074", sapato: "#332d43" },
  { pele: "#edc3a2", cabelo: "#246b78", camisa: "#d68b45", detalhe: "#f4de7a", calca: "#506c58", sapato: "#3b3546" },
];

const melody = [
  523.25, 659.25, 783.99, 659.25, 440, 523.25, 659.25, 783.99,
  349.23, 440, 523.25, 659.25, 392, 493.88, 587.33, 783.99,
  523.25, 659.25, 783.99, 659.25, 440, 523.25, 659.25, 783.99,
  349.23, 440, 523.25, 659.25, 392, 493.88, 587.33, 523.25,
];
const bassNotes = [130.81, 110, 87.31, 98];

function log(message, error = false) {
  const messageLines = message.match(/.{1,52}/g) || [""];
  messageLines.forEach((line, index) => {
    terminalLines.push({ text: `${index === 0 ? "> " : "  "}${line}`, error });
  });
  terminalScrollTop = Math.max(0, terminalLines.length - terminalVisibleLines);
  const entry = document.createElement("li");
  entry.textContent = message;
  if (error) entry.className = "error";
  logList.append(entry);
  logPanel.scrollTop = logPanel.scrollHeight;
}

function getTerminalMaxScroll() {
  return Math.max(0, terminalLines.length - terminalVisibleLines);
}

function syncTerminalScrollFromLogPanel() {
  const logMaxScroll = logPanel.scrollHeight - logPanel.clientHeight;
  const progress = logMaxScroll > 0 ? logPanel.scrollTop / logMaxScroll : 1;
  terminalScrollTop = Math.round(progress * getTerminalMaxScroll());
}

function syncLogPanelScrollFromTerminal() {
  const terminalMaxScroll = getTerminalMaxScroll();
  const progress = terminalMaxScroll > 0 ? terminalScrollTop / terminalMaxScroll : 1;
  logPanel.scrollTop = progress * Math.max(0, logPanel.scrollHeight - logPanel.clientHeight);
}

function setEventState(message) {
  eventState.textContent = message;
}

function setScenarioState(key, text, color) {
  sceneState[key] = text;
  sceneState[`${key}Color`] = color;
}

function clampedInput(input, minimum, maximum) {
  const parsed = Number.parseInt(input.value, 10);
  const value = Number.isFinite(parsed) ? Math.min(maximum, Math.max(minimum, parsed)) : minimum;
  input.value = String(value);
  return value;
}

function setupAudio() {
  if (audioContext) return true;
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  if (!AudioContextClass) {
    if (!audioWarningShown) {
      log("Áudio indisponível neste navegador.", true);
      audioWarningShown = true;
    }
    musicEnabled = false;
    updateMusicButton();
    return false;
  }
  try {
    audioContext = new AudioContextClass();
    if (audioContext.state === "suspended") audioContext.resume();
    if (musicEnabled) startMusic();
    return true;
  } catch (error) {
    if (!audioWarningShown) {
      log(`O áudio não pôde ser iniciado: ${error.message}`, true);
      audioWarningShown = true;
    }
    musicEnabled = false;
    updateMusicButton();
    return false;
  }
}

function playTone(frequency, duration, volume = 0.2, type = "sine", when = audioContext.currentTime) {
  if (!audioContext || frequency <= 0) return;
  const oscillator = audioContext.createOscillator();
  const gain = audioContext.createGain();
  oscillator.type = type;
  oscillator.frequency.setValueAtTime(frequency, when);
  gain.gain.setValueAtTime(0.0001, when);
  gain.gain.linearRampToValueAtTime(volume, when + 0.012);
  gain.gain.setValueAtTime(volume, Math.max(when + 0.012, when + duration - 0.025));
  gain.gain.linearRampToValueAtTime(0.0001, when + duration);
  oscillator.connect(gain);
  gain.connect(audioContext.destination);
  oscillator.start(when);
  oscillator.stop(when + duration + 0.01);
}

function sound(name) {
  if (!setupAudio()) return;
  const now = audioContext.currentTime;
  const sequences = {
    clique: [[880, 0.045], [660, 0.04]],
    chegada: [[587.33, 0.08], [783.99, 0.12]],
    passos: [[392, 0.055], [0, 0.035], [330, 0.055], [0, 0.035], [440, 0.07]],
    consulta: [[659.25, 0.07], [783.99, 0.12]],
  };
  if (name === "escrita") {
    if (writingTimer) return;
    let stroke = 0;
    const playStroke = () => {
      for (let index = 0; index < 6; index += 1) {
        playTone(390 + index * 28, 0.11, 0.05, "triangle", audioContext.currentTime + index * 0.18);
      }
      stroke += 1;
      if (stroke > 10000) stroke = 0;
    };
    playStroke();
    writingTimer = window.setInterval(playStroke, 1080);
    return;
  }
  let at = now;
  for (const [frequency, duration] of sequences[name] || []) {
    playTone(frequency, duration, 0.2, "sine", at);
    at += duration + 0.025;
  }
}

function startMusic() {
  if (!audioContext || musicTimer || !musicEnabled) return;
  const playNote = () => {
    if (!musicEnabled || !audioContext) return;
    const note = melody[musicIndex];
    const now = audioContext.currentTime;
    playTone(note, 0.18, 0.12, "sine", now);
    playTone(note * 2, 0.18, 0.025, "sine", now);
    if (musicIndex % 8 === 0) {
      playTone(bassNotes[Math.floor(musicIndex / 8)], 0.18, 0.05, "triangle", now);
    }
    musicIndex = (musicIndex + 1) % melody.length;
  };
  playNote();
  musicTimer = window.setInterval(playNote, 180);
}

function stopMusic() {
  if (musicTimer) window.clearInterval(musicTimer);
  musicTimer = null;
}

function updateMusicButton() {
  musicButton.textContent = `MÚSICA: ${musicEnabled ? "LIGADA" : "DESLIGADA"}`;
  musicButton.setAttribute("aria-pressed", String(musicEnabled));
}

function pixel(x, y, color) {
  ctx.fillStyle = color;
  ctx.fillRect(x * 4, y * 4, 4, 4);
}

function pixelRow(y, start, end, color) {
  for (let x = start; x <= end; x += 1) pixel(x, y, color);
}

function drawPerson(character, timestamp) {
  const {
    x, y, appearance, role = "fa", pose = "parado", walking = false,
    name, hairStyle, scale = 1,
  } = character;
  const frame = Math.floor(timestamp / 150) % 2;
  const palette = palettes[appearance % palettes.length];
  const { pele: paletteSkin, camisa: paletteShirt, detalhe, calca } = palette;
  const pele = character.skinColor || paletteSkin;
  const camisa = character.shirtColor || paletteShirt;
  const cabelo = character.hairColor || palette.cabelo;
  const hairstyle = hairStyle ?? appearance % 4;
  ctx.save();
  ctx.translate(Math.round(x + 34 * (1 - scale)), Math.round(y + 88 * (1 - scale)));
  ctx.scale(scale, scale);
  ctx.imageSmoothingEnabled = false;

  if (hairstyle === "balding") {
    for (const [row, start, end] of [[0, 6, 10], [1, 4, 12], [2, 3, 13], [3, 3, 13]]) {
      pixelRow(row, start, end, pele);
    }
    pixelRow(1, 4, 5, cabelo);
    pixelRow(1, 11, 12, cabelo);
    pixelRow(2, 3, 5, cabelo);
    pixelRow(2, 11, 13, cabelo);
    pixelRow(3, 3, 5, cabelo);
    pixelRow(3, 7, 9, cabelo);
    pixelRow(3, 11, 13, cabelo);
  } else {
    for (const [row, start, end] of [[0, 6, 10], [1, 4, 12], [2, 3, 13], [3, 3, 13]]) {
      pixelRow(row, start, end, cabelo);
    }
  }
  if (hairstyle === "quiff") {
    pixelRow(-1, 8, 9, cabelo);
    pixelRow(0, 7, 11, cabelo);
  } else if (hairstyle === 2) {
    pixelRow(3, 13, 15, cabelo);
    pixelRow(4, 14, 15, cabelo);
    pixelRow(5, 14, 15, cabelo);
  } else if (hairstyle === 3) {
    pixelRow(1, 2, 4, cabelo);
    pixelRow(1, 12, 14, cabelo);
    pixelRow(2, 1, 3, cabelo);
    pixelRow(2, 13, 15, cabelo);
  }

  for (let row = 4; row < 12; row += 1) pixelRow(row, 4, 12, pele);
  pixel(3, 7, pele);
  pixel(13, 7, pele);
  if (hairstyle === 1 || hairstyle === 3 || hairstyle === "balding") {
    for (let row = 4; row < 15; row += 1) {
      pixel(3, row, cabelo);
      pixel(13, row, cabelo);
    }
  } else {
    for (let row = 4; row < 9; row += 1) {
      pixel(3, row, cabelo);
      pixel(13, row, cabelo);
    }
  }
  if (hairstyle === 0) {
    pixelRow(4, 5, 7, cabelo);
    pixelRow(5, 9, 11, cabelo);
  } else if (hairstyle === 1) {
    pixelRow(4, 5, 11, cabelo);
  } else if (hairstyle === 2) {
    pixelRow(4, 5, 9, cabelo);
    pixelRow(5, 10, 12, cabelo);
  } else if (hairstyle === 3) {
    pixelRow(4, 4, 10, cabelo);
    pixel(11, 5, cabelo);
  } else if (hairstyle === "quiff") {
    pixelRow(4, 8, 10, cabelo);
  }
  for (const eye of [6, 10]) {
    pixel(eye, 6, cabelo);
    pixel(eye, 7, "#fff5df");
    pixel(eye, 8, "#24243d");
  }
  pixel(8, 9, "#c77e69");
  pixelRow(10, 7, 9, "#743d4b");
  pixel(5, 9, "#e99b86");
  pixel(11, 9, "#e99b86");
  if (hairstyle === 1) {
    for (const eye of [5, 7, 9, 11]) pixel(eye, 7, "#382b42");
    pixel(8, 7, "#382b42");
  } else if (hairstyle === 3) {
    pixel(5, 9, "#8c5749");
    pixel(11, 9, "#8c5749");
  }

  pixelRow(12, 7, 9, pele);
  pixelRow(13, 6, 10, camisa);
  for (let row = 14; row < 19; row += 1) pixelRow(row, 4, 12, camisa);
  const armOffset = walking ? frame : 0;
  for (let row = 14; row < 19; row += 1) {
    pixel(3, row + armOffset, pele);
    pixel(13, row - armOffset, pele);
  }
  pixel(4, 15, detalhe);
  pixel(12, 15, detalhe);
  pixelRow(16, 7, 9, detalhe);

  if (role === "autor") {
    pixelRow(19, 5, 11, calca);
    pixelRow(20, 6, 12, calca);
    pixelRow(21, 9, 13, palette.sapato);
    pixel(13, 15, pele);
    pixel(14, 15, pele);
    const penY = pose === "autografando" ? 16 + frame : 16;
    pixel(15, penY, "#332b42");
    pixel(14, penY, detalhe);
  } else if (pose === "lendo") {
    pixelRow(15, 13, 15, pele);
    pixelRow(16, 14, 15, "#584c7b");
    pixelRow(17, 14, 15, "#fff2c8");
    pixelRow(18, 14, 15, "#fff2c8");
    pixel(15, 17, "#ce6c78");
  } else {
    const leftLeg = walking ? -frame : 0;
    const rightLeg = walking ? frame : 0;
    for (const row of [19, 20, 21]) {
      pixel(6 + leftLeg, row, calca);
      pixel(7 + leftLeg, row, calca);
      pixel(10 + rightLeg, row, calca);
      pixel(11 + rightLeg, row, calca);
    }
    pixelRow(22, 5 + leftLeg, 7 + leftLeg, palette.sapato);
    pixelRow(22, 10 + rightLeg, 12 + rightLeg, palette.sapato);
  }

  ctx.restore();
  if (name) {
    ctx.save();
    ctx.translate(Math.round(x), Math.round(y));
    ctx.fillStyle = "#fff0c2";
    ctx.font = "bold 12px Consolas, monospace";
    ctx.textAlign = "center";
    ctx.textBaseline = "alphabetic";
    ctx.fillText(name, 34, 111);
    ctx.restore();
  }
}

function fillRect(x, y, width, height, color) {
  ctx.fillStyle = color;
  ctx.fillRect(x, y, width, height);
}

function drawText(text, x, y, color = "#f8e7a1", size = 12) {
  ctx.fillStyle = color;
  ctx.font = `bold ${size}px Consolas, monospace`;
  ctx.textBaseline = "top";
  ctx.fillText(text, x, y);
}

function drawBackground() {
  fillRect(0, 0, 1260, 480, "#282447");
  for (let x = 0; x < 1260; x += 40) {
    fillRect(x, 82, 20, 7, "#37345c");
    fillRect(x + 18, 184, 22, 7, "#37345c");
  }
  fillRect(0, 365, 1260, 115, "#583e50");
  for (let x = 0; x < 1260; x += 48) fillRect(x, 365, 2, 115, "#76505a");
  fillRect(0, 365, 1260, 4, "#e6a858");
  for (let x = 80; x < 1190; x += 48) {
    fillRect(x, 40, 8, 8, "#f8d875");
    fillRect(x + 8, 48, 8, 8, "#e98668");
  }
  drawText("LIVRARIA PIXEL - EVENTO DE LANCAMENTO", 405, 58, "#c7c5e8", 15);
  ctx.save();
  ctx.fillStyle = "#f5c66a";
  ctx.font = "bold 8px Consolas, monospace";
  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  ctx.fillText(
    "Lançamento: Estruturas de Dados para Primatas e Sistemas Básicos: Hardware e Software, para Burrinhos",
    630, 79,
  );
  ctx.restore();

  fillRect(270, 96, 352, 104, "#11111c");
  fillRect(278, 102, 336, 88, "#646875");
  fillRect(284, 108, 324, 76, "#101b1e");
  fillRect(284, 108, 324, 15, "#29434a");
  drawText("TV DA LIVRARIA | TERMINAL DE ACOES", 290, 111, "#b8e4dc", 8);
  terminalLines.slice(terminalScrollTop, terminalScrollTop + terminalVisibleLines).forEach((line, index) => {
    drawText(line.text, 290, 127 + index * 13, line.error ? "#ff8b82" : "#9fe0a2", 8);
  });
  const terminalMaxScroll = getTerminalMaxScroll();
  if (terminalMaxScroll > 0) {
    const trackY = 126;
    const trackHeight = 52;
    const thumbHeight = Math.max(8, trackHeight * terminalVisibleLines / terminalLines.length);
    const thumbY = trackY + (trackHeight - thumbHeight) * terminalScrollTop / terminalMaxScroll;
    fillRect(600, trackY, 3, trackHeight, "#35484a");
    fillRect(599, thumbY, 5, thumbHeight, "#9fe0a2");
  }
  fillRect(612, 137, 3, 3, "#e6a858");
  fillRect(430, 200, 32, 7, "#646875");
  fillRect(442, 207, 8, 12, "#646875");

  drawText("FILA DE FAS", 106, 175, "#a8d7e8");
  fillRect(90, 351, 455, 3, "#edbf61");
  for (const x of [180, 280, 380, 480]) {
    fillRect(x, 347, 5, 10, "#edbf61");
    fillRect(x + 5, 352, 5, 5, "#edbf61");
  }
  const outsideQueue = Math.max(0, queue.length - maxVisibleFans);
  drawText(`FILA: ${queue.length}${outsideQueue ? `  (+${outsideQueue} aguardando)` : ""}`, 105, 192, "#fff0c2", 10);
  drawText(sceneState.fan, 105, 211, sceneState.fanColor, 13);
  drawText("AUTORES", 700, 100, "#a8d7e8");
  fillRect(687, 205, 62, 84, "#76505a");
  fillRect(677, 201, 82, 10, "#e6a858");
  fillRect(695, 230, 10, 37, "#c78150");
  fillRect(737, 230, 10, 37, "#c78150");
  fillRect(633, 285, 193, 16, "#d18a4d");
  fillRect(646, 301, 14, 54, "#9a5d40");
  fillRect(797, 301, 14, 54, "#9a5d40");
  fillRect(614, 273, 52, 9, "#fff5d6");
  drawText("LIVRO DE AUTOGRAFOS", 605, 319, "#fff0c2", 11);
  drawText(sceneState.writer, 663, 371, sceneState.writerColor, 14);

  fillRect(890, 93, 330, 268, "#17172c");
  fillRect(898, 101, 314, 252, "#e4c78c");
  fillRect(905, 108, 300, 29, "#65466b");
  drawText("LISTA DE AUTOGRAFOS", 925, 114, "#fff0b0", 14);
  drawText("CONSULTA COMPARTILHADA", 919, 143, "#59485e", 11);
  let row = 0;
  const earlier = Math.max(0, displayedAutographs.length - 6);
  if (earlier) {
    drawText(`... ${earlier} autografos anteriores`, 921, 163, "#68586a", 11);
    row = 1;
  }
  for (const autograph of displayedAutographs.slice(-6)) {
    drawText(`OK  ${autograph.fan} - ${autograph.author}`, 921, 164 + row * 19, "#256044", 12);
    row += 1;
  }
  drawText(sceneState.reader, 918, 293, sceneState.readerColor, 13);
  fillRect(912, 308, 284, 2, "#b69a69");
  drawText(`TOTAL: ${displayedAutographs.length}`, 918, 315, "#385d68", 13);
  drawText(`LEITORES ATIVOS: ${activeReaders.size}`, 918, 335, "#385d68", 13);
}

function draw(timestamp) {
  ctx.clearRect(0, 0, scene.width, scene.height);
  drawBackground();
  for (const character of fanCharacters.values()) drawPerson(character, timestamp);

  authors.forEach((author, index) => {
    drawPerson({
      ...author, y: 164, role: "autor", name: author.label,
      pose: writerActive && signingAuthorIndex === index ? "autografando" : "parado",
    }, timestamp);
  });

  for (const reader of readers.values()) {
    const elapsed = timestamp - reader.startedAt;
    const travelDuration = 500;
    const total = Math.max(2000, reader.duration * 1000);
    const pauseEnd = total - travelDuration;
    let x;
    let pose = "andando";
    let walking = true;
    if (elapsed < travelDuration) {
      const progress = Math.max(0, elapsed / travelDuration);
      const eased = progress * progress * (3 - 2 * progress);
      x = 1070 + (817 - 1070) * eased;
    } else if (elapsed < pauseEnd) {
      x = 817;
      pose = "lendo";
      walking = false;
    } else {
      const progress = Math.min(1, Math.max(0, (elapsed - pauseEnd) / travelDuration));
      const eased = progress * progress * (3 - 2 * progress);
      x = 817 + (1070 - 817) * eased;
    }
    drawPerson({
      x, y: 238 + (reader.id % 2) * 18,
      appearance: reader.id + 2, role: "leitor", pose, walking,
    }, timestamp);
  }
  requestAnimationFrame(draw);
}

function animateCharacter(character, targetX, duration, onComplete) {
  const startX = character.x;
  const startTime = performance.now();
  character.walking = true;
  character.motion = { startX, targetX, startTime, duration, onComplete };
}

function updateCharacterMotions(timestamp) {
  for (const [id, character] of fanCharacters) {
    if (!character.motion) continue;
    const motion = character.motion;
    const progress = Math.min(1, (timestamp - motion.startTime) / motion.duration);
    const eased = progress * progress * (3 - 2 * progress);
    character.x = motion.startX + (motion.targetX - motion.startX) * eased;
    if (progress >= 1) {
      character.x = motion.targetX;
      character.motion = null;
      character.walking = false;
      if (motion.onComplete) motion.onComplete(id, character);
    }
  }
  requestAnimationFrame(updateCharacterMotions);
}

function syncQueue(animate = false, departedId = null) {
  const visible = queue.slice(0, maxVisibleFans);
  const visibleIds = new Set(visible.map((fan) => fan.id));
  for (const [id, character] of fanCharacters) {
    if (visibleIds.has(id) || id === signingFan) continue;
    if (id === departedId && animate) {
      character.pose = "andando";
      animateCharacter(character, 835, 520, () => fanCharacters.delete(id));
    } else {
      fanCharacters.delete(id);
    }
  }
  visible.forEach((fan, index) => {
    const targetX = 500 - index * 95;
    let character = fanCharacters.get(fan.id);
    if (!character) {
      character = {
        id: fan.id,
        name: fan.name,
        appearance: fan.appearance,
        x: animate ? 62 : targetX,
        y: 235,
        pose: "parado",
        walking: false,
      };
      fanCharacters.set(fan.id, character);
      if (animate) {
        character.pose = "andando";
        animateCharacter(character, targetX, 650);
      }
    } else if (fan.id !== signingFan) {
      if (animate && Math.abs(character.x - targetX) > 1) {
        character.pose = "andando";
        animateCharacter(character, targetX, 620);
      } else {
        character.x = targetX;
        character.walking = false;
        character.motion = null;
      }
    }
  });
}

function addFan(animate = true, shouldLog = true) {
  const fan = { id: nextFanId, name: `Fã ${nextFanId}`, appearance: nextFanId - 1 };
  nextFanId += 1;
  queue.push(fan);
  syncQueue(animate);
  if (shouldLog) sound("chegada");
  autographButton.disabled = queue.length === 0 || writerBusy;
  if (queue.length === 1 && !writerBusy) {
    setScenarioState("fan", `${fan.name.toUpperCase()}: AGUARDANDO PARA SER AUTOGRAFADO`, "#f5c66a");
  }
  if (shouldLog) log(`${fan.name} entrou no fim da fila.`);
  updateOverallState();
}

function applyReaderLimit() {
  readerLimit = clampedInput(readerLimitInput, 1, 3);
  readerPriority = false;
  log(`Limite aplicado: até ${readerLimit} leitor(es) simultâneo(s).`);
  processLockQueue();
}

function removeReaderLimit() {
  readerLimit = null;
  readerPriority = true;
  log("Limite removido: consultas sem limite, com prioridade para leitores.");
  processLockQueue();
}

function requestReader() {
  const reserved = activeReaders.size + waitingReaders.length;
  if (readerLimit !== null && reserved >= readerLimit) {
    log("Máximo de Leitores alcançado. Aguarde ao menos 1 leitor terminar a consulta.", true);
    return;
  }
  const id = nextReaderId;
  nextReaderId += 1;
  const duration = clampedInput(readingTimeInput, 2, 30);
  waitingReaders.push({ id, duration });
  log(`Leitor ${id} pediu para consultar a lista.`);
  setScenarioState("reader", `LEITOR ${id}: AGUARDANDO ACESSO`, "#f5c66a");
  setEventState(`LEITOR ${id}: AGUARDANDO ACESSO À LISTA`);
  processLockQueue();
}

function processLockQueue() {
  if (writerActive) return;
  if (readerPriority) {
    if (waitingReaders.length > 0) {
      while (waitingReaders.length > 0) startReader(waitingReaders.shift());
      return;
    }
    if (activeReaders.size > 0) return;
  }
  if (writerWaiting) {
    if (activeReaders.size === 0) startWriter();
    return;
  }
  while (
    waitingReaders.length > 0
    && (readerLimit === null || activeReaders.size < readerLimit)
  ) {
    startReader(waitingReaders.shift());
  }
}

function startReader(request) {
  const { id, duration } = request;
  const reader = { id, duration, startedAt: performance.now(), snapshot: [] };
  activeReaders.set(id, reader);
  readers.set(id, reader);
  sound("passos");
  sound("consulta");
  log(`Leitor ${id} está lendo a lista.`);
  setScenarioState("reader", `LEITOR ${id}: CONSULTANDO LISTA`, "#256044");
  if (waitingReaders.length) {
    setEventState(`LEITOR ${waitingReaders[0].id}: AGUARDANDO ACESSO À LISTA`);
  } else {
    setEventState(`LEITOR ${id}: CONSULTANDO A LISTA`);
  }
  window.setTimeout(() => {
    reader.snapshot = autographs.slice();
    activeReaders.delete(id);
    if (reader.snapshot.length >= displayedAutographs.length) {
      displayedAutographs = reader.snapshot;
    }
    if (waitingReaders.length) {
      setScenarioState("reader", `LEITOR ${waitingReaders[0].id}: AGUARDANDO ACESSO`, "#f5c66a");
    } else if (activeReaders.size) {
      setScenarioState("reader", `${activeReaders.size} LEITOR(ES): CONSULTANDO`, "#256044");
    } else {
      setScenarioState("reader", "LEITOR: CONSULTA CONCLUÍDA", "#385d68");
    }
    const content = reader.snapshot.length
      ? reader.snapshot.map(({ fan, author }) => `${author} autografou para ${fan}`).join(", ")
      : "a lista ainda está vazia";
    log(`Consulta concluída: ${content}.`);
    updateOverallState();
    processLockQueue();
  }, duration * 1000);
}

function autographNext() {
  if (writerBusy || queue.length === 0) return;
  const fan = queue[0];
  signingAuthorIndex = nextAuthorIndex;
  const author = authors[signingAuthorIndex];
  writerBusy = true;
  writerWaiting = true;
  autographButton.disabled = true;
  setScenarioState("fan", `${fan.name.toUpperCase()}: AGUARDANDO PARA SER AUTOGRAFADO`, "#f5c66a");
  setScenarioState("writer", `${author.label}: AGUARDANDO`, "#f5c66a");
  setEventState(`${author.name} aguarda para autografar para ${fan.name}.`);
  log(`${author.name} aguarda acesso exclusivo para atender ${fan.name}.`);
  processLockQueue();
}

function startWriter() {
  const fan = queue[0];
  if (!fan) {
    writerWaiting = false;
    writerBusy = false;
    return;
  }
  const author = authors[signingAuthorIndex];
  writerWaiting = false;
  writerActive = true;
  signingFan = fan.id;
  sound("escrita");
  const character = fanCharacters.get(fan.id);
  if (!character) {
    throw new Error("O próximo fã não está visível na fila.");
  }
  character.pose = "andando";
  animateCharacter(character, 590, 520, () => {
    character.pose = "recebendo";
    character.walking = false;
  });
  setScenarioState("fan", `${fan.name.toUpperCase()}: SENDO AUTOGRAFADO`, "#f17b61");
  setScenarioState("writer", `${author.label}: AUTOGRAFANDO`, "#f17b61");
  log(`${author.name} está autografando para ${fan.name}.`);
  if (waitingReaders.length) {
    setEventState(`LEITOR ${waitingReaders[0].id}: AGUARDANDO ACESSO À LISTA`);
  } else {
    setEventState(`${author.name} está autografando para ${fan.name}.`);
  }
  const duration = clampedInput(writingTimeInput, 2, 30);
  window.setTimeout(() => finishWriter(fan), duration * 1000);
}

function finishWriter(fan) {
  if (!queue.length || queue[0].id !== fan.id) {
    throw new Error("A ordem da fila mudou durante o autógrafo.");
  }
  if (writingTimer) window.clearInterval(writingTimer);
  writingTimer = null;
  const author = authors[signingAuthorIndex];
  queue.shift();
  autographs.push({ fan: fan.name, author: author.name });
  displayedAutographs = autographs.slice();
  writerActive = false;
  writerBusy = false;
  nextAuthorIndex = (signingAuthorIndex + 1) % authors.length;
  signingFan = null;
  setScenarioState("writer", "AUTORES: LIVRES", "#9fe0a2");
  syncQueue(true, fan.id);
  if (queue.length) {
    setScenarioState("fan", `${queue[0].name.toUpperCase()}: AGUARDANDO PARA SER AUTOGRAFADO`, "#f5c66a");
  } else {
    setScenarioState("fan", "FILA VAZIA: ADICIONE UM FÃ", "#c7c5e8");
  }
  log(`${author.name} autografou para ${fan.name}. Total: ${autographs.length}.`);
  autographButton.disabled = queue.length === 0;
  updateOverallState();
  processLockQueue();
}

function updateOverallState() {
  if (writerBusy) return;
  if (waitingReaders.length) {
    setEventState(`LEITOR ${waitingReaders[0].id}: AGUARDANDO ACESSO À LISTA`);
  } else if (activeReaders.size) {
    setEventState(`${activeReaders.size} leitor(es) consultando; ${autographs.length} autógrafo(s) na lista.`);
  } else if (queue.length) {
    setEventState(`${queue[0].name.toUpperCase()}: AGUARDANDO PARA SER AUTOGRAFADO`);
  } else {
    setEventState("Fila vazia. Adicione um fã para continuar.");
  }
}

function resizeCanvas() {
  const bounds = canvas.getBoundingClientRect();
  const ratio = window.devicePixelRatio || 1;
  canvas.width = Math.max(1, Math.round(bounds.width * ratio));
  canvas.height = Math.max(1, Math.round(bounds.height * ratio));
  ctx.setTransform(canvas.width / scene.width, 0, 0, canvas.height / scene.height, 0, 0);
}

function startReaderVisuals() {
  window.setInterval(() => {
    const now = performance.now();
    for (const [id, reader] of readers) {
      if (now - reader.startedAt >= Math.max(2000, reader.duration * 1000)) {
        readers.delete(id);
      }
    }
  }, 100);
}

document.querySelector("#add-fan").addEventListener("click", () => {
  sound("clique");
  addFan();
});
autographButton.addEventListener("click", () => {
  sound("clique");
  autographNext();
});
document.querySelector("#consult").addEventListener("click", () => {
  sound("clique");
  requestReader();
});
document.querySelector("#apply-limit").addEventListener("click", () => {
  sound("clique");
  applyReaderLimit();
});
document.querySelector("#remove-limit").addEventListener("click", () => {
  sound("clique");
  removeReaderLimit();
});
musicButton.addEventListener("click", () => {
  musicEnabled = !musicEnabled;
  if (musicEnabled) {
    if (setupAudio()) startMusic();
  } else {
    stopMusic();
  }
  updateMusicButton();
});

document.addEventListener("pointerdown", setupAudio, { once: true });
document.addEventListener("keydown", setupAudio, { once: true });
window.addEventListener("resize", resizeCanvas);
logPanel.addEventListener("scroll", syncTerminalScrollFromLogPanel);
canvas.addEventListener("wheel", (event) => {
  const bounds = canvas.getBoundingClientRect();
  const x = (event.clientX - bounds.left) * scene.width / bounds.width;
  const y = (event.clientY - bounds.top) * scene.height / bounds.height;
  if (x < 284 || x >= 608 || y < 123 || y >= 184) return;
  event.preventDefault();
  const maxScroll = getTerminalMaxScroll();
  terminalScrollTop = Math.max(0, Math.min(maxScroll, terminalScrollTop + Math.sign(event.deltaY)));
  syncLogPanelScrollFromTerminal();
}, { passive: false });

for (let index = 0; index < 4; index += 1) addFan(false, false);
log("Evento iniciado: quatro fãs aguardam o autógrafo.");
resizeCanvas();
requestAnimationFrame(draw);
requestAnimationFrame(updateCharacterMotions);
startReaderVisuals();
