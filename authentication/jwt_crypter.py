import base64

CRYPT_ALGORITHM_VALUE = "bit_map"

permissions = []
# read file permisions.txt and create a list of permissions
with open('auth/permissions_master.lst', 'r') as f:
    permissions = [line.strip() for line in f.readlines()]

def crypt(actions: list[str] = []) -> tuple[str, str]:
    bitMap = bytes(128)
    for action in actions:
        if action not in permissions:
            continue
        
        position = permissions.index(action)
        #Get the byte at the position
        bytePosition = position // 8
        bitPosition = position % 8

        #set bit position to 1
        currentByte = bitMap[bytePosition]
        bitMap = bitMap[:bytePosition] + bytes([currentByte | (1 << (7 - bitPosition))]) + bitMap[bytePosition+1:]  
 
    # base64 encode the bitmap
    base64BitMap = base64.b64encode(bitMap).decode('utf-8')
    return CRYPT_ALGORITHM_VALUE, base64BitMap
 
    

def decrypt(base64BitMap: str) -> list[str]:
    # decode base64 to bytes
    bitMap = base64.b64decode(base64BitMap.encode('utf-8'))
    actions = []
    
    # reverse the bitmap to get actions
    for i in range(len(bitMap)*8):
        bytePosition = i // 8
        bitPosition = i % 8
        if bitMap[bytePosition] & (1 << (7 - bitPosition)):
            actions.append(permissions[i])

    return actions


