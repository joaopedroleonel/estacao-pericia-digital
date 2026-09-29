export const summaryLabels = {
  model: "Modelo",
  takenAt: "Data",
  gps: "GPS",
  resolution: "Resolução",
  make: "Fabricante",
  altitude: "Altitude",
  software: "Software",
  fileSize: "Tamanho",
  sha256: "SHA-256",
};

export const tagGroups = {
  Image: "Imagem",
  Exif: "Exif",
  GPS: "GPS",
};

export const activityTypes = {
  IN_PASSENGER_VEHICLE: "De carro",
  IN_VEHICLE: "De carro",
  IN_BUS: "De ônibus",
  IN_TRAIN: "De trem",
  IN_SUBWAY: "De metrô",
  MOTORCYCLING: "De moto",
  CYCLING: "De bicicleta",
  WALKING: "A pé",
  RUNNING: "Correndo",
  FLYING: "De avião",
};

export const loadingMessages = {
  device: "conectando ao dispositivo...",
  photos: "lendo a galeria do dispositivo...",
  pull: "copiando arquivo do dispositivo...",
};

export const text = {
  notAvailable: "—",
  visit: "Visita",
  activityStart: "Início",
  activityEnd: "Fim",
  unknownActivity: "Deslocamento",
  requestFailed: "falha ao falar com o servidor",
  uploadSending: "Enviando…",
  uploadDone: "Foto enviada! Olhe para a tela",
};

export const uploadErrors = {
  invalid_image: "O arquivo não é uma imagem válida",
  too_large: "Foto grande demais",
  forbidden: "Link inválido. Escaneie o QR code novamente",
  missing_file: "Nenhuma foto selecionada",
  request_failed: "Não foi possível enviar. Tente de novo",
};

export function formatBinary(bytes) {
  return `<binário, ${bytes} bytes>`;
}
