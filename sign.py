from binascii import hexlify, unhexlify
from Crypto.Hash import SHA256, RIPEMD160
import math

SIGHASH_ALL = 1
SIGHASH_NONE = 2
SIGHASH_SINGLE = 3
BASE58_ALPHABET = b'123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def hash160(s):
    """Computes the RIPEMD-160 hash of the SHA-256 hash of the input."""
    sha256_hash = SHA256.new(s).digest()
    return RIPEMD160.new(sha256_hash).digest()


def double_sha256(s):
    """Computes the double SHA-256 hash."""
    return SHA256.new(SHA256.new(s).digest()).digest()


def encode_base58(s):
    """Encodes bytes into base58 format."""
    count = 0
    for c in s:
        if c == 0:
            count += 1
        else:
            break
    prefix = b'1' * count
    num = int.from_bytes(s, 'big')
    result = bytearray()
    while num > 0:
        num, mod = divmod(num, 58)
        result.insert(0, BASE58_ALPHABET[mod])
    
    return prefix + bytes(result)


def encode_base58_checksum(s):
    """Encodes bytes into base58 format with a checksum."""
    return encode_base58(s + double_sha256(s)[:4]).decode('ascii')


def decode_base58(s, num_bytes=25, strip_leading_zeros=False):
    """Decodes a base58 encoded string into bytes."""
    num = 0
    for c in s.encode('ascii'):
        num *= 58
        num += BASE58_ALPHABET.index(c)
    combined = num.to_bytes(num_bytes, byteorder='big')
    
    if strip_leading_zeros:
        while combined[0] == 0:
            combined = combined[1:]
    
    checksum = combined[-4:]
    
    if double_sha256(combined[:-4])[:4] != checksum:
        raise ValueError('bad address: {} {}'.format(
            checksum, double_sha256(combined)[:4]))
    
    return combined[:-4]


def p2pkh_script(h160):
    """Creates a Pay-to-Public-Key-Hash (P2PKH) script."""
    return b'\x76\xa9\x14' + h160 + b'\x88\xac'


def p2sh_script(h160):
    """Creates a Pay-to-Script-Hash (P2SH) script."""
    return b'\xa9\x14' + h160 + b'\x87'


def read_varint(s):
    """Reads a variable-length integer from a stream."""
    i = s.read(1)[0]
    
    if i == 0xfd:
        return little_endian_to_int(s.read(2))
    elif i == 0xfe:
        return little_endian_to_int(s.read(4))
    elif i == 0xff:
        return little_endian_to_int(s.read(8))
    
    return i


def encode_varint(i):
    """Encodes an integer as a variable-length integer."""
    if i < 0xfd:
        return bytes([i])
    elif i < 0x10000:
        return b'\xfd' + int_to_little_endian(i, 2)
    elif i < 0x100000000:
        return b'\xfe' + int_to_little_endian(i, 4)
    elif i < 0x10000000000000000:
        return b'\xff' + int_to_little_endian(i, 8)
    
    raise ValueError('integer too large: {}'.format(i))


def flip_endian(h):
    """Flips the endianness of a hex string."""
    b = unhexlify(h)
    b_rev = b[::-1]
    
    return hexlify(b_rev).decode('ascii')


def little_endian_to_int(b):
    """Converts little-endian byte sequence to an integer."""
    return int.from_bytes(b, 'little')


def int_to_little_endian(n, length):
    """Returns the little-endian byte sequence of an integer."""
    return n.to_bytes(length, 'little')


def h160_to_p2pkh_address(h160, prefix=b'\x00'):
    """Generates a P2PKH address from a hash160 value."""
    return encode_base58_checksum(prefix + h160)


def h160_to_p2sh_address(h160, prefix=b'\x05'):
    """Generates a P2SH address from a hash160 value."""
    return encode_base58_checksum(prefix + h160)


def merkle_parent(hash1, hash2):
    """Calculates the Merkle parent of two hashes using double SHA-256."""
    return double_sha256(hash1 + hash2)


def merkle_parent_level(hash_list):
    """Computes the parent level of a list of hashes."""
    if len(hash_list) == 1:
        raise RuntimeError('Cannot take a parent level with only 1 item')
    
    if len(hash_list) % 2 == 1:
        hash_list.append(hash_list[-1])
    
    parent_level = []
    
    for i in range(0, len(hash_list), 2):
        parent = merkle_parent(hash_list[i], hash_list[i+1])
        parent_level.append(parent)
    
    return parent_level


def merkle_root(hash_list):
    """Calculates the Merkle root from a list of hashes."""
    current_level = hash_list
    
    while len(current_level) > 1:
        current_level = merkle_parent_level(current_level)
    
    return current_level[0]


def merkle_path(index, total):
    """Returns the path to the Merkle root for a given index and total number of nodes."""
    path = []
    
    num_levels = math.ceil(math.log(total, 2))
    
    for _ in range(num_levels):
        path.append(index)
        index //= 2
    
    return path