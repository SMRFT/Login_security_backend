import base64, os

CRYPT_ALGORITHM_VALUE = "bit_map"

permissions = []
perms_hash  = ""

pmv = os.environ.get('PERMISSIONS_MASTER_VERSION', '')
pmfn = f'auth/permissions_master_{pmv}.lst' if pmv else 'auth/permissions_master.lst'
if not os.path.exists(pmfn):
    pmv = ''
    pmfn = 'auth/permissions_master.lst'

with open(pmfn, 'r') as f:
    permissions = [line.strip() for line in f.readlines()]
perms_hash = str(hash(''.join(permissions)))


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
    print("base64BitMap", base64BitMap)
    return CRYPT_ALGORITHM_VALUE, base64BitMap
 
    

def decrypt(base64BitMap: str) -> list[str]:
    # decode base64 to bytes
    bitMap = base64.b64decode(base64BitMap.encode('utf-8'))
    print("bitMap", bitMap)
    actions = []
    
    # reverse the bitmap to get actions
    for i in range(len(bitMap)*8):
        bytePosition = i // 8
        bitPosition = i % 8
        if bitMap[bytePosition] & (1 << (7 - bitPosition)):
            actions.append(permissions[i])

    return actions

def hash() -> str:
    return perms_hash

def ver() -> str:
    return pmv
