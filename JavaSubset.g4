grammar JavaSubset;

programa
    : bloco_classe+
    ;

bloco_classe
    : PUBLIC CLASS ID ABRE_CHAVE bloco_principal+ FECHA_CHAVE
    ;

bloco_principal
    : PUBLIC STATIC VOID PRINCIPAL ABRE_PARENTESE STR ABRE_COLCHETES FECHA_COLCHETES ARGS FECHA_PARENTESE
      ABRE_CHAVE comandos+ FECHA_CHAVE
    ;

comandos
    : declaracao
    | atribuicao
    | lista_comandos
    ;

declaracao
    : tipo ID (VIRGULA ID)* (IGUAL expressao)? PONTO_E_VIRGULA
    ;
tipo
    : (INT | FLOAT | STR) (ABRE_COLCHETES FECHA_COLCHETES)* // Agora permite 'int', 'int[]', 'int[][]', etc.
    ;

// NOVA REGRA para acesso a variável (normal ou array)
acesso_variavel
    : ID (ABRE_COLCHETES expressao FECHA_COLCHETES)* // Permite ID, ID[expr], ID[expr][expr], etc.
    ;

atribuicao
    : acesso_variavel IGUAL expressao PONTO_E_VIRGULA // Agora permite 'x = 10' e 'x[i] = 10'
    ;

// ----------------------------------------------------------
// COMANDOS PRINCIPAIS
// ----------------------------------------------------------

lista_comandos
    : escrever
    | ler
    | se_entao
    | enquanto
    | para
    | bloco_comando
    ;

bloco_comando
    : ABRE_CHAVE comandos* FECHA_CHAVE
    ;

// comando de escrita
escrever
    : SYSTEM_OUT PONTO (PRINT | PRINTLN) ABRE_PARENTESE expressao FECHA_PARENTESE PONTO_E_VIRGULA
    ;

// comando de leitura
ler
    : ID IGUAL SCANNER_ID PONTO (NEXT_INT | NEXT_FLOAT | NEXT_LINE) ABRE_PARENTESE FECHA_PARENTESE PONTO_E_VIRGULA
    ;

// estrutura condicional if-else
se_entao
    : IF ABRE_PARENTESE expressao_logica FECHA_PARENTESE (comandos | bloco_comando)
      (ELSE (comandos | bloco_comando))?
    ;

// laço while
enquanto
    : WHILE ABRE_PARENTESE expressao_logica FECHA_PARENTESE (comandos | bloco_comando)
    ;

// laço for
para
    : FOR ABRE_PARENTESE (atribuicao | declaracao) expressao_logica PONTO_E_VIRGULA incremento FECHA_PARENTESE
      (comandos+ | bloco_comando)
    ;

incremento
    : ID (INCREMENTO | DECREMENTO)
    | ID IGUAL expressao
    ;

// ----------------------------------------------------------
// EXPRESSÕES
// ----------------------------------------------------------

expressao_logica
    : expressao (operador_logico expressao)*
    ;

operador_logico
    : IGUAL_IGUAL
    | DIFERENTE
    | MENOR
    | MAIOR
    | MENOR_IGUAL
    | MAIOR_IGUAL
    | E_LOGICO
    | OU_LOGICO
    ;

expressao
    : termo ((SOMA | SUBTRACAO) termo)*
    ;

termo
    : fator ((MULTIPLICACAO | DIVISAO) fator)*
    ;

fator
    : acesso_variavel // Agora permite ler 'x' e 'x[i]'    
    | NUMERO_INTEIRO
    | NUMERO_REAL
    | STRING
    | ABRE_PARENTESE expressao FECHA_PARENTESE
    | criacao_array // Permite 'new int[10]'
    ;

criacao_array
    : NEW (INT | FLOAT | STR) ABRE_COLCHETES expressao FECHA_COLCHETES
    ;
// ==========================================================
// TOKENS LÉXICOS (REGRAS DE LÉXICO)
// ==========================================================

// Palavras-chave e estrutura
PUBLIC         : 'public';
CLASS          : 'class';
STATIC         : 'static';
VOID           : 'void';
INT            : 'int';
FLOAT          : 'float';
STR            : 'String';
PRINCIPAL      : 'main';
ARGS           : 'args';
NEW            : 'new';

// Estruturas de controle
FOR            : 'for';
IF             : 'if';
ELSE           : 'else';
WHILE          : 'while';

// Entrada e saída
SYSTEM_OUT     : 'System.out';
PRINT          : 'print';
PRINTLN        : 'println';
SCANNER_ID     : 'sc';
NEXT_INT       : 'nextInt';
NEXT_FLOAT     : 'nextFloat';
NEXT_LINE      : 'nextLine';

// Símbolos e operadores
PONTO          : '.';
ABRE_PARENTESE : '(';
FECHA_PARENTESE: ')';
ABRE_COLCHETES : '[';
FECHA_COLCHETES: ']';
ABRE_CHAVE     : '{';
FECHA_CHAVE    : '}';
PONTO_E_VIRGULA: ';';
VIRGULA        : ',';
SOMA           : '+';
SUBTRACAO      : '-';
MULTIPLICACAO  : '*';
DIVISAO        : '/';
IGUAL          : '=';
IGUAL_IGUAL    : '==';
DIFERENTE      : '!=';
MENOR          : '<';
MAIOR          : '>';
MENOR_IGUAL    : '<=';
MAIOR_IGUAL    : '>=';
E_LOGICO       : '&&';
OU_LOGICO      : '||';
INCREMENTO     : '++';
DECREMENTO     : '--';

// Literais e identificadores
ID              : [a-zA-Z_] [a-zA-Z0-9_]* ;
NUMERO_INTEIRO  : [0-9]+ ;
NUMERO_REAL     : [0-9]+ '.' [0-9]+ ;
STRING          : '"' ( ~["\r\n] | '""' )* '"' ;
ESPACO : [ \t\r\n\u00A0\u2000-\u200B\u202F\u205F\u3000]+ -> skip ;
COMENTARIO      : '//' .*? '\n' -> skip ;
