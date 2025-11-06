import sys
import subprocess 
from antlr4 import *
import os 
from antlr4.error.ErrorListener import ErrorListener
from antlr4.tree.Trees import Trees

# 1. Importe o Lexer e o Parser gerados
from JavaSubsetLexer import JavaSubsetLexer
from JavaSubsetParser import JavaSubsetParser


# --- ERRO LÉXICO PERSONALIZADO ---
class MeuErrorListenerLexico(ErrorListener):
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        print(f"ERRO LÉXICO [Linha {line}, Coluna {column}]: {msg}")


# --- ERRO SINTÁTICO PERSONALIZADO ---
class MeuErrorListenerSintatico(ErrorListener):
    def __init__(self):
        super(MeuErrorListenerSintatico, self).__init__()
        self.sucesso = True

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.sucesso = False
        print(f"\n--- ERRO SINTÁTICO ---")
        print(f"  [Linha {line}, Coluna {column}]")
        print(f"  Mensagem: {msg}")
        if offendingSymbol:
            print(f"  Token problemático: '{offendingSymbol.text}'")


def gerar_dot(tree, parser):
    """Gera a árvore sintática em formato DOT (Graphviz)."""
    def escape(text):
        return text.replace('"', '\\"')
    output = ["digraph G {"]

    def visitar(no, pai_id=None, contador=[0]):
        meu_id = contador[0]
        contador[0] += 1

        label = escape(Trees.getNodeText(no, parser.ruleNames))
        output.append(f'  node{meu_id} [label="{label}"];')

        if pai_id is not None:
            output.append(f'  node{pai_id} -> node{meu_id};')

        for i in range(no.getChildCount()):
            visitar(no.getChild(i), meu_id)

    visitar(tree)
    output.append("}")
    return "\n".join(output)


def main(argv):
    if len(argv) < 2:
        print("Uso: python AnalisadorSintatico.py <arquivo_java>")
        return

    arquivo_entrada = argv[1]
    print(f"Iniciando análise sintática completa de: {arquivo_entrada}")
    
    input_stream = FileStream(arquivo_entrada, encoding='utf-8')

    # 2. Crie o Lexer
    lexer = JavaSubsetLexer(input_stream)

    # Substituir o método padrão de notificação de erro
    def custom_notifyListeners(self, e):
        text = self._input.getText(self._tokenStartCharIndex, self._input.index)
        print(f"ERRO LÉXICO [Linha {self.line}, Coluna {self.column}]: símbolo inesperado '{text.strip()}'")

    lexer.notifyListeners = custom_notifyListeners.__get__(lexer, JavaSubsetLexer)

    lexer.removeErrorListeners()
    lexer.addErrorListener(MeuErrorListenerLexico())
   
    # 3. Crie o fluxo de tokens a partir do Lexer
    stream = CommonTokenStream(lexer)
    stream.fill()  # Lê todos os tokens

    # --- MOSTRAR TOKENS GERADOS ---
    print("\n--- TOKENS GERADOS ---")
    for token in stream.tokens:
        if token.type == Token.EOF:
            token_name = "EOF"
        elif 0 <= token.type < len(JavaSubsetLexer.symbolicNames):
            token_name = JavaSubsetLexer.symbolicNames[token.type]
        else:
            token_name = f"Desconhecido({token.type})"

        print(f"<Tipo: {token_name}, Lexema: '{token.text}', Linha: {token.line}, Coluna: {token.column}>")
        # 4. Crie o Parser a partir do fluxo de tokens
    parser = JavaSubsetParser(stream)

    # 5. Configurar nosso ErrorListener personalizado
    parser.removeErrorListeners()
    error_listener = MeuErrorListenerSintatico()
    parser.addErrorListener(error_listener)

    try:
        # 6. Ponto de entrada: regra principal "programa"
        tree = parser.programa()
        
        print("\n------------------------------------------------------")
        if error_listener.sucesso:
            print("Análise Sintática CONCLUÍDA. A sintaxe está CORRETA.")
            
            # Mostrar a estrutura textual da árvore
            print("\n--- ÁRVORE SINTÁTICA (formato textual) ---")
            print(Trees.toStringTree(tree, None, parser))

            # Gera o arquivo DOT
            dot_output = gerar_dot(tree, parser)
            with open("arvore.dot", "w", encoding="utf-8") as f:
                f.write(dot_output)
            print("\nArquivo 'arvore.dot' gerado com sucesso! Visualize com Graphviz.")
            print("Gerando 'arvore.png' automaticamente...")
            try:
                comando = ["dot", "-Tpng", "arvore.dot", "-o", "arvore.png"]
                subprocess.run(comando, check=True)
                print("Arquivo 'arvore.png' criado com sucesso!")

                # --- NOVO: ABRIR O ARQUIVO (POP-UP) ---
                print("Abrindo 'arvore.png' no visualizador padrão...")
                os.startfile("arvore.png")  # <-- ADICIONE ESTA LINHA
                # --- FIM DA LINHA ADICIONADA ---
            
            except FileNotFoundError:
                print("--- ERRO AO GERAR PNG ---")
                print("O comando 'dot' não foi encontrado. Verifique se o Graphviz está instalado e no PATH do sistema.")                
            except subprocess.CalledProcessError as e:
                print(f"--- ERRO AO GERAR PNG ---")
                print(f"O comando 'dot' falhou com o erro: {e}")
            # --- FIM DO NOVO CÓDIGO ---
        else:
            print("Análise Sintática FALHOU. Erros encontrados.")

    except Exception as e:
        print(f"Ocorreu um erro geral durante a análise: {e}")


if __name__ == '__main__':
    main(sys.argv)
