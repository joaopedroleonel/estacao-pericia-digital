# Estação de Perícia Digital

Sistema da estação de perícia digital do projeto Perito Orienta 2026. Quase tudo roda num notebook: um dashboard mostra o celular ao vivo, a imagem extraída com seus metadados, a linha do tempo de localização num mapa e um terminal fake onde o perito digita os comandos. Os alunos enviam fotos lendo um QR code que abre uma página publicada em um microserviço separado, e as fotos ficam guardadas na nuvem até o dashboard baixá-las.

## Como funciona

- **Flask (notebook)** serve o login, o dashboard e uma API JSON.
- **ADB** lê o celular conectado por USB e copia as fotos da câmera.
- **Pillow** (com `pillow-heif`) extrai EXIF e GPS e gera prévias. A foto original nunca é alterada.
- **Leaflet + OpenStreetMap** desenham a linha do tempo lida de `data/timeline.json`.
- **scrcpy** espelha o celular numa janela sem borda por cima da primeira coluna do dashboard.
- **Microserviço de envio (Vercel)** publica a página "Inserir foto", valida a imagem e a guarda no **Supabase Storage**.

## Requisitos

- Windows 10 ou 11
- Python 3.9 ou mais novo
- ADB e scrcpy no PATH (testado com scrcpy 3.3.4)
- Celular Android com depuração USB ativada.
- Conta gratuita no Supabase e no Vercel para o envio de fotos.

## Instalação

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Preencha o `.env`:

| Variável | O que é | Como gerar |
|---|---|---|
| `SECRET_KEY` | chave da sessão do Flask | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ACCESS_CODE` | código de 4 dígitos do login | escolha um número |
| `TIMELINE_DATE` | dia da linha do tempo exibido no mapa (`AAAA-MM-DD`) | vazio mostra todos os dias |
| `SUPABASE_URL` | endereço do projeto no Supabase | Project Settings, API |
| `SUPABASE_SECRET_KEY` | chave secreta do Supabase (`sb_secret_...` ou a antiga `service_role`) | Project Settings, API Keys |
| `SUPABASE_BUCKET` | nome do bucket das fotos | padrão `uploads` |

Sem `SUPABASE_URL` e `SUPABASE_SECRET_KEY`, o dashboard funciona normalmente, só não sincroniza com a nuvem.

O `.env` fica fora do git. Nunca publique esses valores.

## Como rodar

```powershell
.\.venv\Scripts\Activate.ps1
python run.py
```

Acesse `http://localhost:5000` e entre com o `ACCESS_CODE`. Depois de 5 códigos errados, o login fica bloqueado por 5 minutos.

A linha do tempo é lida só quando o servidor inicia. Se trocar o `data/timeline.json`, reinicie o servidor.

## Envio de fotos (microserviço)

A página de envio fica na pasta `upload_service/`, que é publicada separadamente no Vercel. O fluxo de cada foto:

1. A página pede à API uma URL de envio. A API confere o token do QR code e pede ao Supabase uma URL assinada, válida para um único arquivo em `pending/`.
2. O navegador envia a foto **direto para o Supabase**, com os bytes originais. A foto não passa pelo Vercel, então o limite de 4,5 MB do Vercel não se aplica.
3. A página avisa a API que terminou. A API baixa o arquivo, valida com o Pillow (JPEG, JPEG HDR do iPhone, PNG, WEBP e HEIC) e move para a raiz do bucket como `upload_AAAAMMDD_HHMMSS_xxxx.<ext>`. Se não for uma imagem válida, apaga e mostra o erro ao aluno.
4. No dashboard, `uploads` e `latest` baixam as fotos da raiz do bucket para `data/uploads/` e apagam da nuvem.

A chave secreta do Supabase fica só no Vercel e no `.env` do notebook. O navegador recebe apenas a URL assinada, que não lê, não lista e não apaga nada.

### Configurar o Supabase

1. Crie um projeto em [supabase.com](https://supabase.com).
2. Em Storage, crie um bucket **privado** chamado `uploads`, com limite de 25 MB por arquivo.
3. Em Project Settings, copie a URL do projeto e a chave secreta.

### Rodar o microserviço localmente

```powershell
cd upload_service
pip install -r requirements-dev.txt
copy .env.example .env
flask --app api/index.py run --port 5100
```

Preencha o `upload_service/.env`:

| Variável | O que é |
|---|---|
| `CAMERA_TOKEN` | token do QR code: `python -c "import secrets; print(secrets.token_urlsafe(16))"` |
| `SUPABASE_URL` | mesmo valor do notebook |
| `SUPABASE_SECRET_KEY` | mesmo valor do notebook |
| `SUPABASE_BUCKET` | padrão `uploads` |

A página fica em `http://localhost:5100/camera?token=SEU_CAMERA_TOKEN`.

### Publicar no Vercel

1. Importe o repositório no Vercel e defina **Root Directory** como `upload_service`.
2. Cadastre as mesmas variáveis do `upload_service/.env` em Settings, Environment Variables.
3. Faça o deploy. O `vercel.json` já direciona todas as rotas para o Flask em `api/index.py`.

Gere o QR code com a URL:

```
https://SEU-PROJETO.vercel.app/camera?token=SEU_CAMERA_TOKEN
```

Quem tiver o QR code consegue enviar fotos. Troque o `CAMERA_TOKEN` depois de cada evento.

## Comandos do terminal

| Comando | O que faz |
|---|---|
| `help` | lista os comandos |
| `device` | mostra fabricante, modelo e versão do Android do celular |
| `photos` | lista as 10 fotos mais recentes da câmera do celular |
| `pull <file>` | copia uma foto do celular para `data/extracted/` e mostra o SHA-256 |
| `extracted` | lista as fotos já copiadas do celular |
| `uploads` | baixa da nuvem as fotos novas enviadas pelo QR code, apaga da nuvem e lista todas |
| `latest` | baixa as fotos novas da nuvem e abre a última enviada |
| `open <file>` | abre uma imagem de `uploads/` ou `extracted/` no painel |
| `exif` | mostra o resumo dos metadados da imagem aberta |
| `hash` | calcula o SHA-256 do arquivo original da imagem aberta |
| `map route` | mostra só a linha do tempo completa no mapa |
| `map photo` | mostra só o local onde a foto aberta foi tirada |
| `clear` | limpa a tela do terminal |

As setas ↑ e ↓ repetem comandos anteriores. Os comandos que usam o ADB ou a nuvem mostram um loader enquanto esperam a resposta. Se a nuvem estiver fora do ar, `uploads` e `latest` avisam e continuam com as fotos locais. Nenhum comando executa shell de verdade: o terminal só aceita a lista acima.

## Pastas de dados

| Pasta | Conteúdo |
|---|---|
| `data/timeline.json` | linha do tempo exportada do Google Maps (formato `semanticSegments`) |
| `data/extracted/` | fotos originais copiadas do celular pelo `pull` |
| `data/uploads/` | fotos originais enviadas pelos alunos e baixadas da nuvem |
| `data/previews/` | cópias leves geradas só para exibir na tela |

Toda a pasta `data/` fica fora do git, porque guarda fotos e histórico de localização reais.

## Metadados das fotos

- A foto enviada é guardada e baixada byte a byte, sem nenhuma alteração. O SHA-256 no notebook é o mesmo do arquivo que saiu do celular. As prévias são cópias separadas.
- Pelo navegador, o sistema do celular pode remover metadados antes do envio. No iPhone, dependendo de como a foto é escolhida, somem fabricante, modelo, data e GPS.
- As fotos HDR do iPhone chegam como JPEG com imagem extra embutida (o Pillow chama esse formato de `MPO`). Elas são aceitas e trazem os metadados completos.
- O original completo, com GPS, sempre vem pelo ADB (`photos`, `pull` e `open`).

## Testes

```powershell
python -m pytest
cd upload_service
python -m pytest
```

Os testes usam pastas temporárias, um ADB falso e um Supabase falso, então não precisam de celular nem de internet.

## Estrutura

```
app/                  dashboard do notebook
├── __init__.py       create_app: configuração, pastas de dados, timeline, nuvem e rotas
├── config.py         lê o .env
├── auth.py           login e limite de tentativas
├── utils.py          validação de nomes de arquivo e conversão de coordenadas
├── routes/           rotas HTTP (login, dashboard e API)
├── services/         ADB, imagens, metadados, linha do tempo e sincronização com o Supabase
├── terminal/         comandos do terminal e mensagens exibidas
├── templates/        páginas HTML
└── static/           CSS, JavaScript e Leaflet local
upload_service/       microserviço de envio de fotos (Vercel)
├── api/index.py      ponto de entrada do Vercel
├── uploader/         rotas, validação da imagem, cliente do Supabase e página "Inserir foto"
├── tests/            testes com pytest
└── vercel.json       configuração do deploy
scripts/
└── phone_window.py   abre o scrcpy posicionado e com cantos arredondados
tests/                testes do dashboard com pytest
data/                 dados locais (fora do git)
```
