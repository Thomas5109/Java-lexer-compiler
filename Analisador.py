import sys
import subprocess 
from antlr4 import *
import os 
from antlr4.error.ErrorListener import ErrorListener
from antlr4.tree.Trees import Trees

# 1. Importe o Lexer e o Parser gerados
from JavaSubsetLexer import JavaSubsetLexer
from JavaSubsetParser import JavaSubsetParser

# IMPORT DO NOVO ARQUIVO GERADO
from JavaSubsetVisitor import JavaSubsetVisitor

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

# ==========================================================
# --- NOVAS CLASSES PARA ANÁLISE SEMÂNTICA ---
# ==========================================================

# Classe 1: O Erro Semântico personalizado
class SemanticError(Exception):
    """Exceção para erros semânticos."""
    pass

# Classe 2: Representa uma variável na tabela
class Symbol:
    def __init__(self, name, type):
        self.name = name
        self.type = type
        # Você pode adicionar mais coisas aqui, como 'valor'

# Classe 3: A Tabela de Símbolos (com escopo)
class SymbolTable:
    """
    Implementa uma Tabela de Símbolos com escopo usando uma pilha de dicionários.
    """
    def __init__(self):
        # A pilha de escopos. O primeiro é o escopo global.
        self.scopes = [{}]

    def enter_scope(self):
        """Entra em um novo escopo (ex: ao entrar em um bloco '{')."""
        self.scopes.append({})

    def exit_scope(self):
        """Sai do escopo atual (ex: ao sair de um bloco '}')."""
        if len(self.scopes) > 1:
            self.scopes.pop()
        else:
            print("Aviso: Tentativa de sair do escopo global.")

    def add_symbol(self, symbol):
        """Adiciona um símbolo ao escopo ATUAL."""
        current_scope = self.scopes[-1]
        if symbol.name in current_scope:
            # Erro: Variável já declarada neste escopo 
            raise SemanticError(f"Variável '{symbol.name}' já foi declarada neste escopo.")
        current_scope[symbol.name] = symbol
        print(f"  [Semântica] Declarou '{symbol.name}' (Tipo: {symbol.type}) no escopo {len(self.scopes)-1}")

    def find_symbol(self, name):
        """Encontra um símbolo, procurando do escopo atual para o global."""
        # Procura de trás para frente (do escopo mais interno para o mais externo)
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None # Não encontrou

# Classe 4: O Visitante Semântico
class SemanticVisitor(JavaSubsetVisitor):
    """
    Visita a árvore sintática para construir a tabela de símbolos
    e verificar erros semânticos.
    """
    def __init__(self):
        self.table = SymbolTable()

    # --- GERENCIAMENTO DE ESCOPO ---

    def visitBloco_principal(self, ctx:JavaSubsetParser.Bloco_principalContext):
        # Entra no escopo principal (nível 1)
        self.table.enter_scope()
        resultado = self.visitChildren(ctx)
        self.table.exit_scope()
        return resultado

    def visitBloco_comando(self, ctx:JavaSubsetParser.Bloco_comandoContext):
        # Entra em um escopo aninhado (nível 2, 3, etc.)
        self.table.enter_scope()
        resultado = self.visitChildren(ctx)
        self.table.exit_scope()
        return resultado
    
    # --- VERIFICAÇÃO DE DECLARAÇÃO E USO ---

    def visitDeclaracao(self, ctx:JavaSubsetParser.DeclaracaoContext):
        var_type_declarado = ctx.tipo().getText()
        
        # Se houver uma expressão de inicialização (ex: int a = 10;)
        if ctx.expressao():
            tipo_expressao = self.visit(ctx.expressao()) # Isso vai chamar visitExpressao/Termo/Fator
            
            # --- VERIFICAÇÃO DE TIPO ---
            if var_type_declarado != tipo_expressao:
                # Permite 'float f = 10' (int cabe em float)
                if var_type_declarado == "float" and tipo_expressao == "int":
                    pass # Coerção permitida
                else:
                    raise SemanticError(f"[Linha {ctx.start.line}] Erro de Tipo: Não é possível atribuir um valor do tipo '{tipo_expressao}' a uma variável do tipo '{var_type_declarado}'.")

        # Adiciona os símbolos à tabela
        for id_node in ctx.ID():
            var_name = id_node.getText()
            symbol = Symbol(var_name, var_type_declarado)
            try:
                self.table.add_symbol(symbol)
            except SemanticError as e:
                raise SemanticError(f"[Linha {id_node.getSymbol().line}] {e}")
        
        return None # Já visitamos os filhos manualmente

    def visitAcesso_variavel(self, ctx:JavaSubsetParser.Acesso_variavelContext):
        var_name = ctx.ID().getText()
        symbol = self.table.find_symbol(var_name)
        if symbol is None:
            raise SemanticError(f"[Linha {ctx.ID().getSymbol().line}] Erro: Variável '{var_name}' não foi declarada.")
        
        # Checa se é um acesso de array (ex: meuArray[i])
        if ctx.ABRE_COLCHETES():
            if '[]' not in symbol.type:
                raise SemanticError(f"[Linha {ctx.ID().getSymbol().line}] Erro de Tipo: Tentativa de indexar variável '{var_name}' que não é um array.")
            
            # Checa o tipo do índice
            tipo_indice = self.visit(ctx.expressao(0)) # Pega o tipo da expressão no colchete
            if tipo_indice != "int":
                raise SemanticError(f"[Linha {ctx.ID().getSymbol().line}] Erro de Tipo: Índice de array deve ser 'int', mas foi '{tipo_indice}'.")
            
            return symbol.type.replace('[]', '') # Retorna o tipo base (ex: 'int' de 'int[]')
        else:
            # Checa se está usando um array sem colchetes
            if '[]' in symbol.type:
                raise SemanticError(f"[Linha {ctx.ID().getSymbol().line}] Erro de Tipo: Variável '{var_name}' é um array e deve ser acessada com um índice [].")
        
        return symbol.type # Retorna o tipo da variável

    def visitLer(self, ctx:JavaSubsetParser.LerContext):
        # A regra 'ler' também usa um ID que precisa ser checado
        var_name = ctx.ID().getText()
        if self.table.find_symbol(var_name) is None:
            raise SemanticError(f"[Linha {ctx.ID().getSymbol().line}] Erro: Variável '{var_name}' não foi declarada (usada no 'ler').")
        return self.visitChildren(ctx)

    def visitIncremento(self, ctx:JavaSubsetParser.IncrementoContext):
        # A regra 'incremento' (ex: i++) também usa um ID
        var_name = ctx.ID().getText()
        if self.table.find_symbol(var_name) is None:
            raise SemanticError(f"[Linha {ctx.ID().getSymbol().line}] Erro: Variável '{var_name}' não foi declarada (usada no incremento).")
        return self.visitChildren(ctx)
    
    def visitAtribuicao(self, ctx:JavaSubsetParser.AtribuicaoContext):
        # Visita o lado esquerdo (acesso_variavel) para obter seu tipo
        tipo_variavel = self.visit(ctx.acesso_variavel())
        
        # Visita o lado direito (expressao) para obter seu tipo
        tipo_expressao = self.visit(ctx.expressao())

        # --- VERIFICAÇÃO DE TIPO ---
        if tipo_variavel != tipo_expressao:
            # Permite 'float f = 10' (int cabe em float)
            if tipo_variavel == "float" and tipo_expressao == "int":
                pass # Coerção permitida
            else:
                raise SemanticError(f"[Linha {ctx.start.line}] Erro de Tipo: Não é possível atribuir um valor do tipo '{tipo_expressao}' a uma variável do tipo '{tipo_variavel}'.")
        
        return None # Já visitamos os filhos manualmente
    # (Cole dentro da classe SemanticVisitor)

    def visitFator(self, ctx:JavaSubsetParser.FatorContext):
        # Esta é a base: retorna o tipo de um item
        if ctx.acesso_variavel():
            # Visita o nó da variável (ex: 'x' ou 'meuArray[i]')
            # O próprio visitAcesso_variavel vai checar o escopo e retornar o tipo
            return self.visit(ctx.acesso_variavel())
        elif ctx.NUMERO_INTEIRO():
            return "int"
        elif ctx.NUMERO_REAL():
            return "float"
        elif ctx.STRING():
            return "String"
        elif ctx.expressao():
            # Visita a sub-expressão (ex: (1 + 2))
            return self.visit(ctx.expressao())
        elif ctx.criacao_array():
            # Visita o nó de criação (ex: new int[10])
            return self.visit(ctx.criacao_array())
        return "void" # Caso base

    def visitTermo(self, ctx:JavaSubsetParser.TermoContext):
        # Lida com * e /
        tipo_resultante = self.visit(ctx.fator(0))

        for i in range(1, len(ctx.fator())):
            tipo_direito = self.visit(ctx.fator(i))
            
            # Regras de tipo para * e /
            if tipo_resultante == "String" or tipo_direito == "String":
                raise SemanticError(f"[Linha {ctx.start.line}] Erro de Tipo: Operador '*' ou '/' não pode ser usado com 'String'.")
            elif tipo_resultante == "float" or tipo_direito == "float":
                tipo_resultante = "float" # int * float = float
            else:
                tipo_resultante = "int"
        
        return tipo_resultante

    def visitExpressao(self, ctx:JavaSubsetParser.ExpressaoContext):
        # Lida com + e -
        tipo_resultante = self.visit(ctx.termo(0))
        
        for i in range(1, len(ctx.termo())):
            tipo_direito = self.visit(ctx.termo(i))
            op = ctx.getChild(i*2 - 1).getText() # Pega o operador '+' ou '-'
            
            # Regras de tipo para + e -
            if op == '+':
                # Concatenação de String
                if tipo_resultante == "String" or tipo_direito == "String":
                    tipo_resultante = "String" 
                elif tipo_resultante == "float" or tipo_direito == "float":
                    tipo_resultante = "float"
                else:
                    tipo_resultante = "int"
            elif op == '-':
                if tipo_resultante == "String" or tipo_direito == "String":
                    raise SemanticError(f"[Linha {ctx.start.line}] Erro de Tipo: Operador '-' não pode ser usado com 'String'.")
                elif tipo_resultante == "float" or tipo_direito == "float":
                    tipo_resultante = "float"
                else:
                    tipo_resultante = "int"
        
        return tipo_resultante
    
    def visitCriacao_array(self, ctx:JavaSubsetParser.Criacao_arrayContext):
        # new INT [ expr ]
        tipo_base = ctx.getChild(1).getText() # 'int', 'float', ou 'String'
        
        # Checa o tipo da expressão do tamanho
        tipo_tamanho = self.visit(ctx.expressao())
        if tipo_tamanho != "int":
            raise SemanticError(f"[Linha {ctx.start.line}] Erro de Tipo: Tamanho do array deve ser 'int', mas foi '{tipo_tamanho}'.")
        
        return tipo_base + "[]" # Retorna o tipo do array, ex: "int[]"

# ==========================================================
# --- NOVA CLASSE PARA GERAÇÃO DE CÓDIGO PYTHON ---
# ==========================================================

class TradutorPythonVisitor(JavaSubsetVisitor):
    """
    Visita a árvore sintática e gera código Python funcional.
    """
    def __init__(self):
        self.python_code = []  # Armazena as linhas de código Python
        self.indent_level = 0

    def add_line(self, text):
        """Adiciona uma linha de código com a indentação correta."""
        indentation = "    " * self.indent_level
        self.python_code.append(f"{indentation}{text}")

    def indent(self):
        self.indent_level += 1

    def dedent(self):
        self.indent_level -= 1

    # --- Métodos que Reconstroem Expressões ---
    # Precisamos deles para traduzir '&&' para 'and' e '||' para 'or'

    def visitExpressao_logica(self, ctx:JavaSubsetParser.Expressao_logicaContext):
        # A expressão lógica é 'expressao (operador_logico expressao)*'
        py_expr = self.visit(ctx.expressao(0)) # Visita o primeiro lado
        
        for i in range(1, len(ctx.expressao())):
            op_java = ctx.operador_logico(i-1).getText()
            
            # Traduz os operadores lógicos
            if op_java == "&&":
                op_py = "and"
            elif op_java == "||":
                op_py = "or"
            else:
                op_py = op_java # Mantém '==', '!=', '<', '>', etc.
                
            rhs = self.visit(ctx.expressao(i)) # Visita o outro lado
            py_expr += f" {op_py} {rhs}"
            
        return py_expr

    # Para todas as outras expressões, a sintaxe é idêntica ao Python
    # Então, podemos simplesmente pegar o texto original.
    def visitExpressao(self, ctx:JavaSubsetParser.ExpressaoContext):
        return ctx.getText()

    def visitCriacao_array(self, ctx:JavaSubsetParser.Criacao_arrayContext):
        # JavaSubset: new int[10]
        # Python:     [None] * 10
        tamanho_expr = self.visit(ctx.expressao())
        return f"([None] * {tamanho_expr})"

    # --- Métodos que Geram Linhas de Código ---

    def visitBloco_principal(self, ctx:JavaSubsetParser.Bloco_principalContext):
        # Adiciona o 'if __name__ == "__main__":' (padrão Python)
        self.add_line('if __name__ == "__main__":')
        self.indent()
        self.visitChildren(ctx) # Visita os comandos dentro do main
        self.dedent()
        
        # Retorna a string de código completa
        return "\n".join(self.python_code)

    def visitDeclaracao(self, ctx:JavaSubsetParser.DeclaracaoContext):
        # JavaSubset: int x, y, z;  OU  int x = 10;
        # Python:     x = None; y = None; z = None;  OU  x = 10
        
        # Se for uma declaração com atribuição (ex: int x = 10)
        if ctx.expressao():
            expr_py = self.visit(ctx.expressao())
            var_name = ctx.ID(0).getText()
            self.add_line(f"{var_name} = {expr_py}")
        else:
            # Se for uma declaração simples (ex: int x, y;)
            for id_node in ctx.ID():
                # Inicializa como None (padrão Python)
                self.add_line(f"{id_node.getText()} = None")
        
        return None # Não precisa visitar filhos, já tratamos tudo

    def visitAtribuicao(self, ctx:JavaSubsetParser.AtribuicaoContext):
        # JavaSubset: x[i] = 10 + y;
        # Python:     x[i] = 10 + y
        lado_esquerdo = ctx.acesso_variavel().getText()
        lado_direito = self.visit(ctx.expressao())
        self.add_line(f"{lado_esquerdo} = {lado_direito}")
        return None

    def visitEscrever(self, ctx:JavaSubsetParser.EscreverContext):
        # JavaSubset: System.out.println(expr);  ou .print(expr);
        # Python:     print(expr)               ou print(expr, end="")
        expr_py = self.visit(ctx.expressao())
        
        if ctx.PRINTLN():
            self.add_line(f"print({expr_py})")
        elif ctx.PRINT():
            self.add_line(f'print({expr_py}, end="")')
            
        return None

    def visitLer(self, ctx:JavaSubsetParser.LerContext):
        # JavaSubset: x = sc.nextInt();
        # Python:     x = int(input())
        var_name = ctx.ID().getText()
        
        if ctx.NEXT_INT():
            tipo_py = "int"
        elif ctx.NEXT_FLOAT():
            tipo_py = "float"
        elif ctx.NEXT_LINE():
            tipo_py = "str" # (str(input()) é redundante, mas seguro)
        
        self.add_line(f'{var_name} = {tipo_py}(input())')
        return None

    def visitSe_entao(self, ctx:JavaSubsetParser.Se_entaoContext):
        # JavaSubset: if (cond) { ... } else { ... }
        # Python:     if cond: ... else: ...
        
        cond_py = self.visit(ctx.expressao_logica())
        self.add_line(f"if {cond_py}:")
        
        # Visita o bloco 'then'
        self.indent()
        self.visit(ctx.getChild(4)) # Visita o (comandos | bloco_comando)
        self.dedent()
        
        # Se houver um 'else'
        if ctx.ELSE():
            self.add_line("else:")
            self.indent()
            self.visit(ctx.getChild(6)) # Visita o (comandos | bloco_comando)
            self.dedent()
            
        return None

    def visitEnquanto(self, ctx:JavaSubsetParser.EnquantoContext):
        # JavaSubset: while (cond) { ... }
        # Python:     while cond: ...
        cond_py = self.visit(ctx.expressao_logica())
        self.add_line(f"while {cond_py}:")
        
        self.indent()
        self.visit(ctx.getChild(4)) # Visita o (comandos | bloco_comando)
        self.dedent()
        return None

    def visitPara(self, ctx:JavaSubsetParser.ParaContext):
        # Traduz o 'for' C-style para um 'while' Python
        # JavaSubset: for (init; cond; inc) { body }
        # Python:     init
        #             while cond:
        #                 body
        #                 inc
        
        # 1. Inicialização
        self.visit(ctx.getChild(2)) # (atribuicao | declaracao)
        
        # 2. Condição do While
        cond_py = self.visit(ctx.expressao_logica())
        self.add_line(f"while {cond_py}:")
        
        self.indent()
        # 3. Corpo
        self.visit(ctx.getChild(6)) # (comandos+ | bloco_comando)
        # 4. Incremento (no final do loop)
        self.visit(ctx.incremento())
        self.dedent()
        
        return None

    def visitIncremento(self, ctx:JavaSubsetParser.IncrementoContext):
        # JavaSubset: i++  ou  i = i + 1
        # Python:     i = i + 1
        var_name = ctx.ID().getText()
        if ctx.INCREMENTO():
            self.add_line(f"{var_name} = {var_name} + 1")
        elif ctx.DECREMENTO():
            self.add_line(f"{var_name} = {var_name} - 1")
        elif ctx.expressao():
            expr_py = self.visit(ctx.expressao())
            self.add_line(f"{var_name} = {expr_py}")
        
        return None

    def visitBloco_comando(self, ctx:JavaSubsetParser.Bloco_comandoContext):
        # Apenas visita os comandos dentro do bloco
        return self.visitChildren(ctx)
# ==========================================================
# --- FIM DAS NOVAS CLASSES ---
# ==========================================================

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
            
            sucesso_semantico = False  # Flag para controlar a geração da árvore
            # --- NOVO: INICIAR ANÁLISE SEMÂNTICA ---
            print("\nIniciando Análise Semântica...")
            try:
                semantic_visitor = SemanticVisitor()
                semantic_visitor.visit(tree)
                print("Análise Semântica CONCLUÍDA. Nenhum erro encontrado.")
                sucesso_semantico = True  # SUCESSO!
                # Se a semântica passou, continue para gerar a árvore
                
            except SemanticError as e:
                print("\n--- ERRO SEMÂNTICO ---")
                print(e)
                print("------------------------------------------------------")
                print("Análise Semântica FALHOU. Erros encontrados.")
            # --- FIM DA ANÁLISE SEMÂNTICA ---

            # Mostrar a estrutura textual da árvore
            if sucesso_semantico:
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
                
                # ===============================================
                # --- NOVO: GERAR CÓDIGO PYTHON ---
                # ===============================================
                print("\nIniciando Geração de Código Python...")
                try:
                    tradutor = TradutorPythonVisitor()
                    tradutor.visit(tree)
                    
                    # Define o nome do arquivo de saída
                    codigo_python = "\n".join(tradutor.python_code)
                    # Ex: "Exercicios\HelloWorld.JavaSubset" -> "Exercicios\HelloWorld.py"
                    arquivo_saida_py = arquivo_entrada.rsplit('.', 1)[0] + ".py"
                    
                    with open(arquivo_saida_py, "w", encoding="utf-8") as f:
                        f.write(codigo_python)
                    
                    print(f"Arquivo '{arquivo_saida_py}' gerado com sucesso!")
                    
                    # Imprime o código gerado no terminal
                    print("\n--- CÓDIGO PYTHON GERADO ---")
                    print(codigo_python)
                    print("------------------------------")
                
                except Exception as e:
                    print("\n--- ERRO NA TRADUÇÃO PARA PYTHON ---")
                    print(f"Ocorreu um erro: {e}")
                # ===============================================
                # --- FIM DA GERAÇÃO DE CÓDIGO ---
                # ===============================================
        else:
            print("Análise Sintática FALHOU. Erros encontrados.")

    except Exception as e:
        print(f"Ocorreu um erro geral durante a análise: {e}")


if __name__ == '__main__':
    main(sys.argv)
