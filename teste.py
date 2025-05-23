chip_id_byte = b'$\n\xc4\x00\x01\x10'


def chipid_byte_to_hex():
    return ''.join(
        [':{:02x}'.format(b) for b in chip_id_byte]).upper().lstrip(':')


print(chipid_byte_to_hex())
