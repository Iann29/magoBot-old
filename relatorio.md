# Relatório Técnico: Problemas com Interação MEmu vs LDPlayer

## Descrição do Problema

Após a troca do emulador LDPlayer para o MEmu, mesmo mantendo o mesmo nome de janela ("FARMs") no novo emulador, as ações automatizadas (como kits e outras funcionalidades) não estão funcionando corretamente. Nenhuma das interações com a interface do jogo está sendo realizada com sucesso.

## Análise Técnica

### 1. Arquitetura do Sistema

O MagoBot utiliza uma arquitetura baseada em:
- Detecção de imagem (OpenCV) para reconhecer elementos do jogo
- PyGetWindow para manipulação da janela do emulador
- PyAutoGUI para realizar cliques e interações
- Offsets de coordenadas para ajustar a posição dos cliques

### 2. Causas Prováveis

#### Diferenças Estruturais entre Emuladores

1. **Geometria da Janela**: 
   - O código atual espera uma estrutura específica de janela com `window_height = 514` e `emulator_height = 480`
   - O cálculo `top_offset = window_height - emulator_height` (34 pixels no LDPlayer) provavelmente não é válido para o MEmu
   - Isso causa desalinhamento em todas as interações com a interface

2. **Hierarquia de Janelas e Implementação do Windows API**:
   - Diferentes emuladores implementam a interação com o Windows API de formas distintas
   - O MEmu pode ter uma estrutura interna de janelas diferente, mesmo mantendo o título "FARMs"

3. **Região de Captura de Tela**:
   - A função `capture_screen()` usa coordenadas relativas à posição da janela:
```python
screenshot = pyautogui.screenshot(region=(
    window.left,
    window.top + self.top_offset,
    self.emulator_width,
    self.emulator_height
))
```
   - Se o MEmu tem uma estrutura de janela diferente, estas coordenadas resultarão em capturas imprecisas

#### Problemas de Reconhecimento de Templates

- Devido ao desalinhamento da captura, os templates não são reconhecidos corretamente
- As regiões de interesse (ROIs) definidas para os templates estão capturando áreas incorretas da tela

### 3. Propagação dos Erros

O problema inicial com o `top_offset` se propaga por todo o sistema:
1. Captura de tela ocorre em região incorreta
2. Templates não são encontrados ou são encontrados em posições erradas
3. Cliques são realizados em coordenadas incorretas
4. Detecção de estado falha, levando a comportamentos inesperados nas funções de automação

## Soluções Propostas

### Solução Imediata

1. **Recalibração do Top Offset**:
   - Medir manualmente a diferença entre a altura total da janela e a área útil no MEmu
   - Atualizar o `window_height` ou criar um offset específico para o MEmu

2. **Implementação de Configuração por Emulador**:
   - Modificar o arquivo `emulator_config.json` para incluir offsets específicos por emulador
   - Exemplo de estrutura:
```json
{
  "window_name": "FARMs",
  "emulators": {
    "ldplayer": {
      "window_height": 514,
      "emulator_height": 480
    },
    "memu": {
      "window_height": [VALOR_CORRETO],
      "emulator_height": 480
    }
  }
}
```

### Solução Completa

1. **Sistema de Detecção Automática de Bordas**:
   - Implementar um sistema que detecte automaticamente os limites da área útil do emulador
   - Usar pontos de referência visuais conhecidos para calibrar a área de interação

2. **Refatoração do Sistema de Interação**:
   - Abstrair o sistema de interação com a janela para lidar com diferentes emuladores
   - Criar perfis de emuladores com configurações específicas

3. **Testes Extensivos**:
   - Criar testes automatizados para verificar a captura de tela e interação
   - Validar o sistema em múltiplos emuladores para garantir compatibilidade

## Próximos Passos

1. Medir manualmente a altura da barra de título e bordas no MEmu
2. Atualizar o `top_offset` para o valor correto
3. Testar o sistema com as novas configurações
4. Implementar um sistema mais robusto de configuração por emulador

---

**Autor:** Cascade  
**Data:** 09/04/2025
