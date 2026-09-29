# Estação de Perícia Digital

Sistema da estação de perícia digital do projeto Perito Orienta 2026. Tudo roda num notebook: um dashboard mostra o celular ao vivo, a imagem extraída com seus metadados, a linha do tempo de localização num mapa e um terminal fake onde o perito digita os comandos. Os alunos enviam fotos pelo celular lendo um QR code.

## Como funciona

- **Flask** serve o login, o dashboard, a página de envio de fotos e uma API JSON.
- **ADB** lê o celular conectado por USB e copia as fotos da câmera.
- **Pillow** (com `pillow-heif`) valida as fotos, extrai EXIF e GPS e gera prévias. A foto original nunca é alterada.
- **Leaflet + OpenStreetMap** desenham a linha do tempo lida de `data/timeline.json`.
- **scrcpy** espelha o celular numa janela sem borda por cima da primeira coluna do dashboard.

## Requisitos

- Windows 10 ou 11
- Python 3.9 ou mais novo
- ADB e scrcpy no PATH (testado com scrcpy 3.3.4)
- Celular Android com depuração USB ativada.

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
| `CAMERA_TOKEN` | token da página de envio de fotos | `python -c "import secrets; print(secrets.token_urlsafe(16))"` |
| `TIMELINE_DATE` | dia da linha do tempo exibido no mapa (`AAAA-MM-DD`) | vazio mostra todos os dias |

O `.env` fica fora do git. Nunca publique esses valores.

## Como rodar

```powershell
.\.venv\Scripts\Activate.ps1
python run.py
```

Acesse `http://localhost:5000` e entre com o `ACCESS_CODE`. Depois de 5 códigos errados, o login fica bloqueado por 5 minutos.

A linha do tempo é lida só quando o servidor inicia. Se trocar o `data/timeline.json`, reinicie o servidor.

## Comandos do terminal

| Comando | O que faz |
|---|---|
| `help` | lista os comandos |
| `device` | mostra fabricante, modelo e versão do Android do celular |
| `photos` | lista as 10 fotos mais recentes da câmera do celular |
| `pull <file>` | copia uma foto do celular para `data/extracted/` e mostra o SHA-256 |
| `extracted` | lista as fotos já copiadas do celular |
| `uploads` | lista as fotos enviadas pelo QR code |
| `latest` | abre a última foto enviada |
| `open <file>` | abre uma imagem de `uploads/` ou `extracted/` no painel |
| `exif` | mostra o resumo dos metadados da imagem aberta |
| `hash` | calcula o SHA-256 do arquivo original da imagem aberta |
| `map route` | mostra só a linha do tempo completa no mapa |
| `map photo` | mostra só o local onde a foto aberta foi tirada |
| `clear` | limpa a tela do terminal |

As setas ↑ e ↓ repetem comandos anteriores. Os comandos que usam o ADB mostram um loader enquanto o celular responde. Nenhum comando executa shell de verdade: o terminal só aceita a lista acima.

## Pastas de dados

| Pasta | Conteúdo |
|---|---|
| `data/timeline.json` | linha do tempo exportada do Google Maps (formato `semanticSegments`) |
| `data/extracted/` | fotos originais copiadas do celular pelo `pull` |
| `data/uploads/` | fotos originais enviadas pelos alunos |
| `data/previews/` | cópias leves geradas só para exibir na tela |

Toda a pasta `data/` fica fora do git, porque guarda fotos e histórico de localização reais.

## Metadados das fotos

- A foto recebida é salva byte a byte, sem nenhuma alteração. As prévias são cópias separadas.
- Pelo navegador, o sistema do celular pode remover metadados antes do envio. No iPhone, dependendo de como a foto é escolhida, somem fabricante, modelo, data e GPS.
- As fotos HDR do iPhone chegam como JPEG com imagem extra embutida (o Pillow chama esse formato de `MPO`). Elas são aceitas e trazem os metadados completos.
- O original completo, com GPS, sempre vem pelo ADB (`photos`, `pull` e `open`).

## Testes

```powershell
python -m pytest
```

Os testes usam uma pasta temporária para os dados e um ADB falso, então não precisam de celular conectado.

## Estrutura

```
app/
├── __init__.py       create_app: configuração, pastas de dados, timeline e rotas
├── config.py         lê o .env
├── auth.py           login, limite de tentativas e token da câmera
├── utils.py          validação de nomes de arquivo e conversão de coordenadas
├── routes/           rotas HTTP (login, dashboard, câmera e API)
├── services/         ADB, imagens, metadados e linha do tempo
├── terminal/         comandos do terminal e mensagens exibidas
├── templates/        páginas HTML
└── static/           CSS, JavaScript e Leaflet local
scripts/
└── phone_window.py   abre o scrcpy posicionado e com cantos arredondados
tests/                testes com pytest
data/                 dados locais (fora do git)
```