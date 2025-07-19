
def alphaIn(str):

    for ch in str:
        if ('a' <= ch <= 'z') or ('A' <= ch <= 'Z'):
            return True

    return False

def convertStringToList(string):

    account_list = []
    length = len(string)
    j = 0

    for i in range(length):
        if string[i] == ',':
            if string[i] == ',' and i + 1 < length and string[i + 1] == ' ':
                account_list.append(string[j:i])
                j = i + 2
            else:
                account_list.append(string[j:i])
                j = i + 1
            # print(string[j])

    account_list.append(string[j:])

    if not alphaIn(account_list[-1]):
        account_list.pop()

    return account_list

inp_str = "Product Enablement, Product Enablement - Test, Product Enablement Europe, Product Enablement - feat"

account_list = convertStringToList(inp_str)

print(account_list)