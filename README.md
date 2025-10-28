# Java-lexer-compiler
Compilador que reproduz o a linguagem Java

    grammar JavaSubset;
    
    // --- ESTRUTURA DO PROGRAMA ---
    
    programa
        : bloco_classe+
        ;
        
    bloco_classe
        : 'public' 'class' ID '{' bloco_main+ '}'
        ;
    
    bloco_main
        : 'public' 'static' 'void' 'main' '(' 'String[]' 'args' ')'
          '{' (comandos)+ '}' 
        ;
    
    //COMANDO GERAL PARA AS FUNÇÕES
    comandos
        : declaracao
        | atribuicao
        | lista_comandos
        ;
    
    // --- DECLARAÇÃO DE VARIÁVEIS ---
    declaracao
        : de_variavel
        | de_inteiro
        | de_real
        | de_string
        ;
    
    de_variavel
        : tipagem ID (',' ID)* ';'  // Ex: int x, y
        ;
    
    de_inteiro
        : 'int' ID (',' ID)* '=' expressao ';'     // Ex: int x = 10 + y
        ;
    
    de_real
        : 'float' ID (',' ID)* '=' expressao ';'   // Ex: float f = x / 2.0
        ;
    
    de_string    
        : 'String' ID (',' ID)* '=' expressao ';' // Ex: String s = "Ola";
        ;
    
    tipagem
        : 'int'
        | 'float'
        | 'String'
        ;
    
    atribuicao
        : ID '=' expressao ';' // Ex: x = y * (z + 2)
        ;
    
    // --- COMANDOS PRINCIPAIS ---
    lista_comandos
        : escrever
        | ler
        | se_entao
        | enquanto
        | bloco_comando
        ;
    
    // bloco de comandos (usado no IF, ELSE, WHILE)
    bloco_comando
        : '{' (comandos)* '}'
        ;
    
    // comando de escrita do Java
    escrever
        : 'System.out' '.' ('print' | 'println') '(' expressao ')' ';'
        ;
    
    // objeto 'sc' do tipo Scanner.
    // Ex: x = sc.nextInt(); ou f = sc.nextFloat();
    ler
        : ID '=' 'sc' '.' ('nextInt' | 'nextFloat' | 'nextLine') '(' ')' ';'
        ;
    
      // Regra para 'if' e 'else' opcional
    se_entao
        : 'if' '(' expressao_logica ')' (comandos | bloco_comando)
          ('else' (comandos | bloco_comando))?
        ;
    
    enquanto
        : 'while' '(' expressao_logica ')' (comandos | bloco_comando)
        ;
    
    expressao_logica
        : expressao (operador_logico expressao)*
        ;
    
    operador_logico
        : '=='
        | '!='
        | '<'
        | '>'
        | '<='
        | '>='
        | '&&'
        | '||'
        ;
    
    expressao 
        : termo (('+'|'-') termo)*
        ;
        
    termo
        : fator (('*'|'/') fator)*
        ;
        
    fator
        : ID
        | NUMERO_INT
        | NUMERO_REAL
        | STRING
        | '(' expressao ')'
        ;
    
    // --- REGRAS LÉXICAS (TOKENS) ---
    
    ID          : [a-zA-Z_] [a-zA-Z0-9_]* ;
    NUMERO_INT  : [0-9]+ ;
    NUMERO_REAL : [0-9]+ '.' [0-9]+ ;
    STRING      : '"' ( ~["\r\n] | '""' )* '"' ;
    WS          : [ \t\r\n]+ -> skip ; 
    COMENTARIO  : '//' .*? '\n' -> skip ; 
