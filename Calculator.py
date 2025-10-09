print("Enter 1st Variables")
a=input()
a=float(a)
print("Enter 2nd Variables")
b=input()
b=float(b)
print("Select which operation to perform")
print("Enter 1 for addition, Enter 2 for subtraction, Enter 3 for multiplication, Enter 4 for division, Enter 5 for average, Enter 6 for mod, Enter 7 for max, Enter 8 for min")
selection=input()
selection=float(selection)

if selection==1:
    def add(a,b):
        return a+b
    print("Sum of 2 Variables is", add(a,b))

elif selection==2:
    def Sub(a,b):
        return a-b
    print("Subtraction of 2 Variables is", Sub(a,b))

elif selection==3:
    def Mul(a,b):
        return a*b
    print("Multiplication of 2 Variables is", Mul(a,b))

elif selection==4:
    def Div(a,b):
        return a/b
    print("Division of 2 Variables is", Div(a,b))

elif selection==5:
    def Avg(a,b):
        return (a+b)/2
    print("Average of 2 Variables is", Avg(a,b))

elif selection==6:
    def Mod(a,b):
        return a%b
    print("Modulus of 2 Variables is", Mod(a,b))

elif selection==7:
    def Max(a,b):
        if b>a:
            return b
        elif a>b:
            return a
        else:
            return "None, Both are equal"
    print("Maximum of 2 Variables is", Max(a,b))

elif selection==8:
    def Min(a,b):
        if b<a:
            return b
        elif a<b:
            return a
        else:
            return "None, Both are equal"
    print("Minimum of 2 Variables is", Min(a,b))