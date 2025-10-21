# Java-lexer-compiler
Compilador que reproduz o a linguagem Java

    grammar Thomas;
    
    program
        : bloco_classe+
        ;
        
    bloco_classe
        : 'public' 'class' ID '{' bloco_main+ '}' ;
    
    bloco_main
        : 'public' 'static' 'void' 'main' '(' 'String[]' 'args' ')'
        '{' comando+ '}'
        ;
    
    //COMANDO GERAL PARA AS FUNÇÕES
    comando
        : declaracao
        | atribuicao
        ;
    
    //---DECLARAÇÃO---//
    declaracao
        : de_variavel
        | de_inteiro
        | de_real
        | de_string
        ;
    
    de_variavel
        : tipagem ID (',' ID)* ';' ;
    
    de_inteiro
        : 'int' ID (',' ID)* '=' NUMERO_INT ';' ;
        
    de_real
        : 'float' ID (',' ID)* '=' NUMERO_REAL ';' ;
    
    de_string
        : 'String' ID (',' ID)* '=' STRING ';' ;
    
    tipagem
        : 'int'
        | 'float'
        | 'String'
        ;
    
    //---ATRIBUIÇÃO---//
    atribuicao
        : ID '=' valor ';' ;
    
    
    //---VALOR E EXPRESSÕES---//
    valor
        : NUMERO_INT
        | NUMERO_REAL
        | STRING
        ;
    
    expressao 
        : termo (('+'|'-') termo)*
        ;
        
    termo
        : fator (('*'|'/') fator)*
        ;
        
    fator
        : ID
        | valor
        | '('expressao')'
        ;
    
    // --- REGRAS LÉXICAS (TOKENS) ---
    
    ID          : [a-zA-Z] [a-zA-Z0-9]* ;
    NUMERO_INT  : [0-9]+ ;
    NUMERO_REAL : [0-9]+ '.' [0-9]+ ;
    STRING      : '"' .*? '"' ;
    WS          : [ \t\r\n]+ -> skip ; 
