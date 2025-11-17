if __name__ == "__main__":
    a = None
    b = None
    c = None
    a = float(input())
    b = float(input())
    c = float(input())
    if a <= 0 or b <= 0 or c <= 0:
        print("Medidas inválidas")
    else:
        if a+b > c and a+c > b and b+c > a:
            if a == b and b == c:
                print("Triângulo equilátero válido")
            else:
                if a == b or a == c or b == c:
                    print("Triângulo isósceles válido")
                else:
                    print("Triângulo escaleno válido")
        else:
            print("Medidas inválidas")