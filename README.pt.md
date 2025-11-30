<div align="center">
  <h1>GrabText</h1>
  <p>
    <img src="https://img.shields.io/badge/version-1.3.3-blue" alt="Version">
    <img src="https://img.shields.io/badge/Platform-Linux-lightgrey" alt="Platform">
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
    <img src="https://img.shields.io/badge/status-ativo-success" alt="Status">
    <a href="README.md"><img src="https://img.shields.io/badge/Language-English%20%F0%9F%87%AC%F0%9F%87%A7-blue" alt="English"></a>
  </p>
    <p>
    Capture e copie texto de qualquer imagem ou vídeo na sua tela. Uma ferramenta de OCR simples e poderosa para sistemas baseadas em Linux. Com interface gráfica e linha de comando.
  </p>
</div>

---

## Sobre o Projeto

<div align="center">
  <img src="preview.gif" width="70%" alt="Preview">
</div>

**GrabText** é uma ferramenta de produtividade que agiliza o processo de captura de texto de qualquer lugar da tela. Seja de uma imagem, um vídeo, um documento protegido ou uma página web, basta selecionar a área desejada para que o texto seja reconhecido e copiado para sua área de transferência instantaneamente.

Utiliza o **Tesseract** para o reconhecimento de caracteres e o **Flameshot** para uma seleção de tela intuitiva.

---

## Funcionalidades

### Funcionalidades Principais
*   **OCR Multilíngue:** Suporte robusto para reconhecimento de texto em inglês (`en`) e português (`pt`).
*   **Captura de Tela Intuitiva:** Utilize a interface do Flameshot para selecionar facilmente a área desejada da tela.
*   **Cópia Instantânea:** O texto reconhecido é automaticamente copiado para a área de transferência.
*   **Configuração Flexível:** Alterne o idioma do OCR usando arquivo de configuração ou comandos CLI.
*   **Registro de Atividades:** Geração de logs detalhados para facilitar a depuração.
*   **Comportamento Padrão:** Executar `grabtext` sem argumentos captura área da tela automaticamente.

### Funcionalidades da Linha de Comando
*   **Captura de Tela:** Captura intuitiva de texto de áreas da tela
*   **Processamento de Imagens:** Processe imagens individuais ou diretórios inteiros
*   **Monitoramento de Diretórios:** Observe pastas por novas imagens para processar
*   **Múltiplos Formatos de Saída:** Suporte para saídas em texto, JSON e CSV
*   **Exportação de Dados Estruturados:** Formatos JSON e CSV ricos com metadados e confiança OCR
*   **Gerenciamento Avançado de Logs:** Filtre, exporte e analise arquivos de log
*   **Status do Sistema:** Verifique dependências e configuração
*   **Processamento em Lote:** Manipule múltiplas imagens eficientemente com estruturas de dados unificadas

## Comandos CLI

A CLI do GrabText está organizada em comandos principais e comandos de utilidade para melhor usabilidade:

### Comandos Principais

```bash
# Captura de Tela (Comportamento Padrão)
grabtext                           # Capturar área da tela e extrair texto (padrão)
grabtext grab                      # Mesmo que acima, comando explícito
grabtext grab -l en                # Usar OCR em inglês
grabtext grab -o saida.txt         # Salvar saída em arquivo
grabtext grab --no-clipboard       # Não copiar para área de transferência
grabtext grab --dry-run            # Mostrar o que seria feito

# Processar Arquivos Existentes
grabtext process imagem.png        # Processar imagem única
grabtext process ./imagens -r      # Processar diretório recursivamente
grabtext process ./imagens -f json # Saída em formato JSON
grabtext process ./imagens --batch # Processar múltiplas imagens

# Monitorar Diretórios
grabtext monitor ./imagens         # Monitorar diretório por novas imagens
grabtext monitor ./imagens -r      # Monitorar recursivamente
grabtext monitor ./imagens -f csv  # Saída em formato CSV
```

### Comandos de Utilidade

```bash
# Informações do Sistema
grabtext status                    # Mostrar status do sistema e dependências
grabtext config                    # Mostrar configuração atual
grabtext version                   # Exibir informações de versão
grabtext help                      # Mostrar ajuda geral

# Gerenciamento de Idioma
grabtext get-lang                  # Mostrar idioma atual
grabtext set-lang en               # Definir idioma para inglês
grabtext set-lang pt               # Definir idioma para português

# Gerenciamento de Logs
grabtext logs --tail 10            # Mostrar últimas 10 entradas do log
grabtext logs --since 2023-10-01   # Mostrar logs desde 1º de outubro
grabtext logs --errors             # Mostrar apenas erros
grabtext logs --export logs.txt    # Exportar logs para arquivo
grabtext logs --clear              # Limpar arquivo de log

# Opções de Depuração
grabtext --debug                   # Ativar modo de depuração com saída detalhada
grabtext --verbose                 # Mostrar informações detalhadas de progresso
grabtext --dry-run                 # Mostrar o que seria feito sem executar
```

---

## Formatos de Exportação

O GrabText suporta três formatos de saída, cada um otimizado para diferentes casos de uso:

### Formato Texto (Padrão)
Saída de texto simples - apenas o conteúdo do texto extraído.

### Formato JSON
Dados estruturados ricos com metadados abrangentes e informações OCR:

```bash
# Saída JSON de imagem única
grabtext process imagem.png -f json

# Saída JSON de processamento em lote
grabtext process ./imagens -f json -o resultados.json
```

**Estrutura JSON:**
```json
{
  "metadata": {
    "filename": "documento.png",
    "filepath": "/caminho/para/documento.png",
    "file_size_bytes": 245760,
    "file_modified": "2025-10-11T16:30:00.000000",
    "image_width": 1920,
    "image_height": 1080,
    "image_format": "PNG",
    "image_mode": "RGB"
  },
  "ocr": {
    "text": "Conteúdo do texto extraído...",
    "word_count": 25,
    "char_count": 150,
    "avg_confidence": 87.5,
    "language_used": "por",
    "has_text": true,
    "processing_timestamp": "2025-10-11T16:35:00.000000"
  },
  "processing_info": {
    "grabtext_version": "1.3.2",
    "processed_at": "2025-10-11T16:35:00.000000"
  }
}
```

**Estrutura JSON em Lote:**
```json
{
  "batch_info": {
    "total_files": 5,
    "processed_at": "2025-10-11T16:35:00.000000",
    "directory": "/caminho/para/imagens",
    "recursive": false,
    "grabtext_version": "1.3.2",
    "successfully_processed": 5
  },
  "results": [
    { /* Dados individuais do arquivo como acima */ }
  ]
}
```

### Formato CSV
Dados tabulares perfeitos para aplicações de planilha e análise de dados:

```bash
# Saída CSV de imagem única
grabtext process imagem.png -f csv

# Saída CSV de processamento em lote
grabtext process ./imagens -f csv -o resultados.csv
```

**Colunas CSV:**
- `filename`: Nome do arquivo de imagem
- `filepath`: Caminho completo para a imagem
- `file_size_bytes`: Tamanho do arquivo em bytes
- `file_modified`: Timestamp da última modificação
- `image_width`: Largura da imagem em pixels
- `image_height`: Altura da imagem em pixels
- `image_format`: Formato da imagem (PNG, JPEG, etc.)
- `image_mode`: Modo de cor (RGB, RGBA, etc.)
- `text`: Conteúdo do texto extraído
- `word_count`: Número de palavras detectadas
- `char_count`: Número de caracteres detectados
- `avg_confidence`: Confiança média do OCR (0-100)
- `language_used`: Idioma do OCR usado
- `has_text`: Se texto foi detectado (true/false)
- `processing_timestamp`: Quando o processamento ocorreu

### Casos de Uso

**Formato JSON é ideal para:**
- Integrações de API e aplicações web
- Análise de dados com linguagens de programação
- Pipelines de processamento automatizado
- Trilhas de auditoria detalhadas

**Formato CSV é ideal para:**
- Análise em planilhas (Excel, LibreOffice Calc)
- Importações de banco de dados
- Ferramentas de análise estatística
- Revisão e comparação rápida de dados

---

## Variáveis de Ambiente

As seguintes variáveis de ambiente podem ser usadas para configurar o GrabText:

*   `GRABTEXT_LANG`: Define o idioma padrão do OCR (`en` ou `pt`)
*   `GRABTEXT_LOG`: Define localização personalizada do arquivo de log (padrão: `~/.local/share/grabtext/grabtext.log`)
*   `GRABTEXT_NO_NOTIFY`: Desativa notificações do desktop quando definido como `1`

---

## Compatibilidade

Este projeto foi desenvolvido e testado para funcionar nos principais ambientes de desktop Linux. A automação de atalhos é mais eficaz nos seguintes ambientes:

*   **Ambientes com Suporte Ideal:** GNOME, XFCE
*   **Ambientes com Suporte Guiado:** KDE Plasma
*   **Distribuições Suportadas:** Qualquer distribuição baseada em `apt` (Debian, Ubuntu), `pacman` (Arch Linux), `dnf` (Fedora), ou `zypper` (openSUSE).

---

## Instalação

1.  **Clone este repositório:**
    ```bash
    git clone https://github.com/rouri404/grab-text.git
    cd grab-text
    ```

2.  **Torne o script de instalação executável:**
    ```bash
    chmod +x install.sh
    ```

3.  **Execute o instalador:**
    ```bash
    ./install.sh
    ```
    O script irá pedir sua senha para instalar os pacotes de sistema (se ainda não estiverem instalados) e irá configurar o restante do ambiente.

---

## Como Usar

1.  Pressione a tecla `INSERT`.
2.  A interface de captura aparecerá. Selecione a área da tela com o texto desejado.
3.  Pressione `Enter` ou clique no ícone de `✓` (Confirmar).
4.  O texto extraído estará na sua área de transferência, pronto para ser colado com `Ctrl+V`.

### Forçando o Idioma do OCR

Você pode forçar o idioma do OCR (entre inglês `en` e português `pt`) usando a variável de ambiente `GRABTEXT_LANG`.

*   **Para uma única execução:**
    ```bash
    GRABTEXT_LANG=en ./launch.sh
    ```
    ou
    ```bash
    GRABTEXT_LANG=pt ./launch.sh
    ```

*   **Para definir permanentemente (ex: no .bashrc ou .zshrc):**
    Adicione a linha abaixo ao final do seu arquivo de configuração de shell (ex: `~/.bashrc`):
    ```bash
    export GRABTEXT_LANG=en
    ```
    Após editar o arquivo, execute `source ~/.bashrc` (ou o arquivo correspondente) para aplicar a mudança imediatamente.

---

## Solução de Problemas

Problemas comuns e soluções:

<details>
  <summary><strong>OCR não funciona corretamente</strong></summary>
  
  *   Certifique-se que a imagem tem bom contraste e não está borrada.
  *   Tente mudar o idioma do OCR com a flag `-l`.
  *   Verifique se o Tesseract está instalado corretamente.
</details>

<details>
  <summary><strong>Comando não encontrado</strong></summary>
  
  *   Verifique se `~/.local/bin` está no seu PATH.
  *   Tente executar `source ~/.bashrc` ou reiniciar seu terminal.
  *   Execute novamente o script de instalação.
</details>

<details>
  <summary><strong>Captura GUI não funciona</strong></summary>
  
  *   Verifique se o Flameshot está instalado e em execução.
  *   Certifique-se de estar em um ambiente gráfico.
  *   Tente reiniciar o serviço do Flameshot.
</details>

<details>
  <summary><strong>Logs não aparecem</strong></summary>
  
  *   Verifique o arquivo de log em `~/.local/share/grabtext/grabtext.log`.
  *   Certifique-se de ter permissões de escrita no diretório de log.
  *   Tente usar `grabtext logs --errors` para ver mensagens de erro.
</details>

<details>
  <summary><strong>O atalho não foi criado automaticamente. Como configuro manualmente?</strong></summary>
  
  Se a automação falhou ou foi pulada, você pode configurar o atalho manualmente em poucos passos. O comando que você precisará usar é o caminho absoluto para o script `launch.sh`, que o instalador criou para você.
  
  **Exemplo do Comando:** `/home/$USER/GrabText/launch.sh grab`

  Siga o guia correspondente ao seu ambiente de trabalho:

  #### Para GNOME (Ubuntu, Fedora)
  1.  Abra **Configurações** > **Teclado** > **Atalhos de Teclado**.
  2.  Role até **Atalhos Personalizados** e clique no `+`.
  3.  Preencha os campos:
      * **Nome:** `GrabText`
      * **Comando:** Insira o caminho completo para o arquivo `launch.sh`, seguido por `grab`. Por exemplo, `/home/$USER/GrabText/launch.sh grab`.
      * **Atalho:** Pressione a tecla `INSERT`.
  4.  Clique em "Adicionar".

  #### Para KDE Plasma
  1.  Abra **Configurações do Sistema** > **Atalhos** > **Atalhos Personalizados**.
  2.  Vá em `Editar` > `Novo` > `Atalho Global` > `Comando/URL`.
  3.  Preencha os campos:
      * **Nome:** `GrabText`
      * Aba **Gatilho**: Pressione a tecla `INSERT`.
      * Aba **Ação**: No campo "Comando/URL", insira o caminho completo para o `launch.sh`, seguido por `grab`. Por exemplo, `/home/$USER/GrabText/launch.sh grab`.
  4.  Clique em "Aplicar".

  #### Para XFCE
  1.  Vá para **Configurações** > **Teclado** > **Atalhos de aplicativos**.
  2.  Clique em **"Add"**.
  3.  No campo "Comando", insira o caminho completo para o `launch.sh`, seguido por `grab`. Por exemplo, `/home/$USER/GrabText/launch.sh grab`.
  4.  Quando o sistema pedir a tecla, pressione `INSERT`.
</details>

<details>
  <summary><strong>O OCR não extrai nenhum texto ou o resultado sai incorreto.</strong></summary>
  
  A qualidade do OCR depende 99% da qualidade da imagem. Lembre-se das boas práticas:
  *   **Alto Contraste:** Texto escuro sobre fundo claro e sólido funciona melhor.
  *   **Fontes Padrão:** Fontes muito artísticas ou pequenas são difíceis de ler.
  *   **Boa Resolução:** Se o texto na tela estiver pequeno, use o zoom (`Ctrl` + `+`) na aplicação antes de capturar a tela.
</details>

<details>
  <summary><strong>Como posso personalizar a aparência da interface de captura?</strong></summary>
  
  A aparência da interface é controlada pelo Flameshot. Para personalizar cores, botões e opacidade, execute o seguinte comando no terminal:
  ```bash
  flameshot config
  ```
  O `install.sh` já aplica uma configuração inicial minimalista, mas você pode ajustá-la como preferir através desse painel. Se a aparência não mudar após a edição, tente fechar completamente o Flameshot com `killall flameshot` e acionar o atalho novamente.
</details>

<details>
  <summary><strong>Onde posso encontrar logs para depuração?</strong></summary>
  
  O GrabText agora gera um arquivo de log chamado `grabtext.log` no diretório do projeto. Este log é sempre em inglês e possui um formato limpo e estruturado, o que facilita a identificação e depuração de quaisquer problemas que possam surgir durante a execução da ferramenta. Você pode consultá-lo para obter informações detalhadas sobre o processo de OCR e outras operações.
</details>

<details>
  <summary><strong>Exportação JSON/CSV não está funcionando corretamente</strong></summary>
  
  *   Certifique-se de ter permissões de escrita no diretório de saída.
  *   Verifique se o caminho do arquivo de saída é válido e acessível.
  *   Para lotes grandes, o processo pode demorar - verifique os logs para acompanhar o progresso.
  *   Verifique se as imagens contêm texto legível para resultados OCR significativos.
  *   Use `grabtext --debug` para ver informações detalhadas de processamento.
</details>

<details>
  <summary><strong>Arquivo CSV parece corrompido ou tem problemas de formatação</strong></summary>
  
  *   Arquivos CSV usam escape adequado para conteúdo de texto com vírgulas ou aspas.
  *   Abra o arquivo CSV com um editor de texto primeiro para verificar a estrutura.
  *   Importe no Excel/LibreOffice Calc usando "Texto para Colunas" se necessário.
  *   Verifique se o conteúdo do texto não contém caracteres problemáticos.
  *   Para arquivos CSV grandes, use um leitor CSV adequado em vez de abrir diretamente no Excel.
  *   Se o texto contém quebras de linha, certifique-se de que seu leitor CSV lida com células multilinhas corretamente.
</details>

<details>
  <summary><strong>Baixa confiança OCR ou reconhecimento de texto ruim</strong></summary>
  
  *   **Qualidade da Imagem**: Certifique-se de alto contraste entre texto e fundo.
  *   **Resolução**: Use imagens de maior resolução ou aplique zoom antes de capturar.
  *   **Configurações de Idioma**: Tente alternar entre idiomas `pt` e `en`.
  *   **Pré-processamento de Imagem**: Considere recortar para focar apenas nas áreas de texto.
  *   **Tipo de Fonte**: Fontes padrão funcionam melhor que texto decorativo ou manuscrito.
  *   **Verificar Confiança**: Use saída JSON para ver pontuações de confiança e identificar imagens problemáticas.
</details>

<details>
  <summary><strong>Processamento em lote está lento ou travando</strong></summary>
  
  *   **Imagens Grandes**: Reduza a resolução das imagens antes de processar arquivos grandes.
  *   **Uso de Memória**: Feche outras aplicações para liberar RAM.
  *   **Monitoramento de Progresso**: Use `grabtext logs --tail 10` para monitorar o progresso.
  *   **Interromper com Segurança**: Use Ctrl+C para parar o processamento graciosamente.
  *   **Resultados Parciais**: Verifique se arquivos de saída foram criados com resultados parciais.
  *   **Recursos do Sistema**: Monitore uso de CPU e memória durante o processamento.
</details>

<details>
  <summary><strong>Erros de permissão ao salvar arquivos</strong></summary>
  
  *   **Permissões de Diretório**: Certifique-se de acesso de escrita ao diretório de saída.
  *   **Permissões de Arquivo**: Verifique se o arquivo de saída está bloqueado por outra aplicação.
  *   **Espaço em Disco**: Verifique se há espaço suficiente disponível.
  *   **Comprimento do Caminho**: Evite caminhos de arquivo extremamente longos.
  *   **Caracteres Especiais**: Evite caracteres especiais em nomes de arquivo de saída.
  *   **Diretório Raiz**: Não tente escrever em diretórios protegidos do sistema.
</details>

<details>
  <summary><strong>Problemas de memória com processamento em lote grande</strong></summary>
  
  *   **Processar em Lotes Menores**: Divida diretórios grandes em grupos menores.
  *   **Monitorar Recursos do Sistema**: Use `htop` ou `top` para monitorar uso de memória.
  *   **Fechar Outras Aplicações**: Libere RAM antes de processar lotes grandes.
  *   **Usar Processamento Recursivo**: Processe subdiretórios separadamente em vez de todos de uma vez.
  *   **Verificar Memória Disponível**: Certifique-se de pelo menos 2GB de RAM livre para operações de lote grandes.
</details>

<details>
  <summary><strong>Saída JSON/CSV contém dados vazios ou incompletos</strong></summary>
  
  *   **Suporte a Formato de Imagem**: Certifique-se de que as imagens estão em formatos suportados (PNG, JPG, JPEG).
  *   **Corrupção de Arquivo**: Verifique se os arquivos de imagem não estão corrompidos.
  *   **Imagens Vazias**: Verifique se as imagens realmente contêm texto legível.
  *   **Idioma OCR**: Tente configurações de idioma diferentes para melhor reconhecimento.
  *   **Orientação da Imagem**: Gire imagens se o texto estiver de lado ou de cabeça para baixo.
  *   **Modo Debug**: Use `grabtext --debug` para ver informações detalhadas de processamento.
</details>

<details>
  <summary><strong>Comando monitor não está detectando novos arquivos</strong></summary>
  
  *   **Eventos do Sistema de Arquivos**: Alguns sistemas de arquivos podem não suportar monitoramento de arquivos.
  *   **Permissões**: Certifique-se de acesso de leitura ao diretório monitorado.
  *   **Extensões de Arquivo**: Apenas arquivos com extensões .png, .jpg, .jpeg são monitorados.
  *   **Unidades de Rede**: O monitoramento de arquivos pode não funcionar em diretórios montados em rede.
  *   **Monitoramento Recursivo**: Use a flag `-r` para monitoramento de subdiretórios.
  *   **Teste Manual**: Teste primeiro com o comando `grabtext process`.
</details>

<details>
  <summary><strong>Alternância de idioma não está funcionando corretamente</strong></summary>
  
  *   **Dados do Tesseract**: Certifique-se de que os pacotes de dados de idioma estão instalados:
    - `tesseract-ocr-eng` e `tesseract-ocr-por` para inglês e português
  *   **Arquivo de Configuração**: Verifique `~/.local/share/grabtext/.grabtext_config` para configuração de idioma.
  *   **Variável de Ambiente**: Verifique se `GRABTEXT_LANG` está definida corretamente.
  *   **Sobrescrever Linha de Comando**: Use `-l pt` ou `-l en` para sobrescrever o idioma padrão.
  *   **Instalação do Tesseract**: Reinstale o Tesseract se a alternância de idioma falhar.
</details>

<details>
  <summary><strong>Problemas de desempenho e dicas de otimização</strong></summary>
  
  *   **Tamanho do Lote**: Processe imagens em lotes de 50-100 para desempenho ótimo.
  *   **Compressão de Imagem**: Comprima imagens grandes antes do processamento para reduzir uso de memória.
  *   **Armazenamento SSD**: Use armazenamento SSD para operações I/O mais rápidas durante processamento em lote.
  *   **Núcleos de CPU**: O GrabText pode se beneficiar de múltiplos núcleos de CPU para processamento paralelo.
  *   **Armazenamento de Rede**: Evite processar imagens de diretórios montados em rede.
  *   **Arquivos Temporários**: Certifique-se de espaço suficiente no diretório /tmp para operações temporárias.
</details>

<details>
  <summary><strong>Integração com outras ferramentas e automação</strong></summary>
  
  *   **Scripts Shell**: Use GrabText em scripts shell para processamento automatizado de documentos.
  *   **Trabalhos Cron**: Agende processamento em lote regular com cron para fluxos de trabalho automatizados.
  *   **Integração de API**: Analise saída JSON para integração com serviços web ou bancos de dados.
  *   **Integração Excel**: Importe arquivos CSV diretamente no Excel para análise adicional.
  *   **Importação de Banco de Dados**: Use saída CSV para importações em massa de banco de dados.
  *   **Automação de Fluxo de Trabalho**: Combine com outras ferramentas OCR para tipos de documento especializados.
</details>

<details>
  <summary><strong>Depuração avançada e diagnósticos</strong></summary>
  
  *   **Logging Detalhado**: Use `grabtext --verbose` para informações detalhadas de operação.
  *   **Modo Debug**: Habilite `grabtext --debug` para ver detalhes internos de processamento.
  *   **Análise de Log**: Use `grabtext logs --filter ERROR` para encontrar padrões de erro específicos.
  *   **Monitoramento do Sistema**: Monitore recursos do sistema durante operações de lote grandes.
  *   **Teste do Tesseract**: Teste o Tesseract diretamente com `tesseract imagem.png output -l por`.
  *   **Verificação de Dependências**: Use `grabtext status` para verificar se todas as dependências estão funcionando.
</details>

Para mais ajuda, execute `grabtext help` ou verifique a ajuda específica do comando com `grabtext <comando> --help`. Ao reportar problemas, você pode usar `grabtext --debug` para obter uma saída mais detalhada que ajudará a diagnosticar o problema.

---

### Instalação Manual e Pré-requisitos

Caso o script `install.sh` encontre algum erro, você pode instalar as dependências manualmente com os seguintes comandos:

#### Para Arch Linux e derivados (Manjaro, EndeavourOS)
```bash
sudo pacman -S flameshot tesseract tesseract-data-por tesseract-data-eng xclip python-pip libnotify
```

#### Para Debian, Ubuntu e derivados (Mint, Pop!_OS)
```bash
sudo apt install flameshot tesseract-ocr tesseract-ocr-por tesseract-ocr-eng xclip python3-pip libnotify-bin
```

#### Para Fedora
```bash
sudo dnf install flameshot tesseract tesseract-langpack-por langpacks-eng xclip python3-pip libnotify
```

#### Para openSUSE
```bash
sudo zypper install flameshot tesseract-ocr tesseract-ocr-data-por tesseract-ocr-eng xclip python3-pip libnotify-tools
```
Após a instalação manual, continue no passo 2 da seção de **Instalação** acima.

---

## Desinstalação

Para remover o GrabText e seus componentes:

1.  Navegue até a pasta do projeto.
2.  Torne o desinstalador executável:
    ```bash
    chmod +x uninstall.sh
    ```
3.  Execute o script e siga as instruções:
    ```bash
    ./uninstall.sh
    ```
