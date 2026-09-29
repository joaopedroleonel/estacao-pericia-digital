UNKNOWN_COMMAND = "comando não encontrado: {name}. Digite help para ver a lista."

INVALID_SYNTAX = "comando inválido: confira as aspas."

USAGE = "uso: {usage}"

DESCRIPTIONS = {
    "help": "lista os comandos",
    "device": "mostra o modelo e a versão do Android do celular",
    "photos": "lista as últimas fotos da câmera do celular",
    "pull": "copia uma foto do celular e calcula o SHA-256",
    "extracted": "lista as fotos já copiadas do celular",
    "uploads": "lista as fotos enviadas pelo QR code",
    "latest": "abre a última foto enviada",
    "open": "abre uma imagem no painel",
    "exif": "mostra o resumo dos metadados",
    "hash": "calcula o SHA-256 da imagem aberta",
    "map route": "mostra o trajeto completo no mapa",
    "map photo": "voa até o local onde a foto foi tirada",
    "clear": "limpa a tela",
}

DEVICE_INFO = "{manufacturer} {model} · Android {androidVersion}"

NO_DEVICE_PHOTOS = "nenhuma foto encontrada na câmera do celular"

INVALID_FILENAME = "nome de arquivo inválido: {name}"

PULLED = "{name} copiado para extraídas ({size})"

OPEN_HINT = "use open {name} para ver a imagem"

NO_EXTRACTED = "nenhuma foto copiada do celular ainda. Use pull <file>"

NO_UPLOADS = "nenhuma foto recebida ainda"

CLOUD_SYNCED = "{count} foto(s) nova(s) baixada(s) da nuvem"

CLOUD_SYNC_FAILED = "não foi possível sincronizar com a nuvem"

IMAGE_NOT_FOUND = "imagem não encontrada: {name}"

IMAGE_UNREADABLE = "não foi possível ler a imagem"

IMAGE_LOADED_WITH_GPS = "imagem carregada · GPS encontrado"

IMAGE_LOADED_WITHOUT_GPS = "imagem carregada · sem GPS"

NO_IMAGE_OPEN = "nenhuma imagem aberta. Use open <file> ou latest"

NO_GPS = "a imagem aberta não tem GPS"

TIMELINE_EMPTY = "linha do tempo indisponível"

MAP_ROUTE = "mostrando o trajeto completo"

MAP_PHOTO = "local da foto: {lat}, {lng}"

ADB_ERRORS = {
    "no_device": "nenhum celular conectado. Confira o cabo USB",
    "unauthorized": "celular não autorizado. Aceite a depuração USB na tela do celular",
    "timeout": "o celular demorou demais para responder",
    "adb_not_found": "ADB não encontrado no computador",
    "file_not_found": "arquivo não encontrado no celular",
    "command_failed": "falha ao executar o comando no celular",
}

SUMMARY_LABELS = {
    "make": "Fabricante",
    "model": "Modelo",
    "takenAt": "Data",
    "gps": "GPS",
    "altitude": "Altitude",
    "resolution": "Resolução",
    "software": "Software",
    "fileSize": "Tamanho",
    "sha256": "SHA-256",
}

NOT_AVAILABLE = "—"

DATE_FORMAT = "%d/%m/%Y %H:%M"
