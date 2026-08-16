# 🎵 Music 10 - Studio de Áudio & Mídia

Aplicação web interativa, moderna e responsiva construída em **Python** e **Streamlit**, projetada para download de vídeos e músicas do YouTube/YouTube Music em MP3, compressão de áudio e imagens, e organização profissional de tags ID3 e renomeação de arquivos em lote.

---

## 🚀 Como Executar

### 1. Pré-requisitos
Certifique-se de estar no diretório do projeto com o Python 3.10+ instalado:
```bash
cd C:\Users\Usuario\Documents\Doc_Py\Codigos\app_music_dez
```

### 2. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 3. Iniciar a Aplicação
```bash
streamlit run main_app.py
```

---

## 🎛️ Módulos do Sistema

### 🏠 **Dashboard Principal (`main_app.py`)**
- Visão geral da plataforma com atalhos para os 2 módulos integrados.
- Status em tempo real do motor de conversão **FFmpeg**.
- **Modo Escuro Studio Fixo:** Design moderno, responsivo e limpo para desktop e smartphones.
- **Faixa Ativa na Memória (`st.session_state`)**: Permite transitar dados entre módulos com 1 clique.

### 🎵 **Módulo 1: YouTube para MP3 & Tags ID3 (`pages/1_🎵_YouTube_para_MP3.py`)**
- **Extração YouTube & YouTube Music:** Bypass de verificação de bot via clientes mobile e normalização de URLs (removendo parâmetros de tracking `&si=...`).
- **Seletor de Bitrate:** 320 kbps (Alta Fidelidade), 192 kbps (Padrão), 128 kbps (Econômico).
- **Player Integrado e Download Direto.**
- **Organizador de Tags ID3 Integrado na Mesma Tela:**
  - Busca automática na **iTunes Search API** (oficial e gratuita da Apple).
  - Aplicação com 1 clique de Título, Artista, Álbum, Ano, Gênero e Capas HD (600x600/1200x1200px).
  - Formulário para edição manual e upload de capa personalizada.
  - Gravação permanente de metadados e imagem com **Mutagen** e download do MP3 padronizado (`Artista - Título.mp3`).
  - Suporte a upload de arquivo `.mp3` local para editar tags diretamente.

### 🗜️ **Módulo 2: Compressor & Organizador de Mídia (`pages/2_🗜️_Compressor_Audio_Imagens.py`)**
- **Aba 1: Compressor de Áudio:** Otimização de `.mp3`, `.wav`, `.m4a`, `.ogg` por taxa de bits (64 a 320 kbps) e conversão para Mono, com comparativo de MB e % economizada.
- **Aba 2: Compressor de Imagens:** Upload em lote (`.jpg`, `.png`, `.webp`), controle de qualidade e escala, com download individual ou pacote `.zip` completo.
- **Aba 3: Renomeador e Organizador de Arquivos em Lote:**
  - **Modo 1 (Sequencial):** Padronização ordenada com dígitos alinhados (ex: `001_img_nova.jpg`, `002_img_nova.jpg`).
  - **Modo 2 (Find & Replace / Deletar):** Localização e exclusão ou substituição de termos específicos (ex: retirar `_nova` para virar `001_img.jpg`).
  - Tabela de prévia antes vs depois em tempo real e botão de **Download do Pacote ZIP Completo**.

---

## 📂 Estrutura de Pastas

```text
app_music_dez/
├── .streamlit/
│   └── config.toml                  # Tema Studio Dark nativo, limite de upload de 250MB
├── assets/
│   └── style.css                    # CSS responsivo Dark Studio
├── pages/
│   ├── 1_🎵_YouTube_para_MP3.py     # Módulo 1: YouTube para MP3 + Tags ID3 & Capas
│   └── 2_🗜️_Compressor_Audio_Imagens.py # Módulo 2: Compressor de Áudio, Imagens e Renomeador em Lote
├── tests/
│   └── test_modules.py              # Suite completa de validação automatizada
├── utils/
│   ├── __init__.py                  # Auto-carregamento e setup de FFmpeg
│   ├── ffmpeg_config.py             # Detecção e configuração do executável FFmpeg
│   ├── state_manager.py             # Compartilhamento global de estado (st.session_state)
│   ├── theme_manager.py             # Injeção limpa de CSS do Modo Escuro
│   ├── youtube_extractor.py         # Módulo yt-dlp com normalização e bypass de bot
│   ├── audio_processor.py           # Processamento e compressão de áudio com pydub
│   ├── image_processor.py           # Otimização de imagens e empacotador ZIP com Pillow
│   ├── file_renamer.py              # Renomeador sequencial e find-replace em lote
│   └── tag_manager.py               # iTunes Search API + Mutagen ID3 (TIT2, TPE1, APIC)
├── app.py                           # Ponto de entrada secundário
├── main_app.py                      # Ponto de entrada principal do Streamlit
├── requirements.txt                 # Dependências do projeto
└── README.md                        # Documentação completa
```
