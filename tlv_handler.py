from binascii import hexlify, unhexlify

def parse_tlv(data):
    tlvs = []
    i = 0
    while i < len(data):
        tag = data[i]
        i += 1
        if (tag & 0x1F) == 0x1F:
            tag_bytes = [tag]
            while True:
                if i >= len(data):
                    break
                b = data[i]
                i += 1
                tag_bytes.append(b)
                if (b & 0x80) == 0:
                    break
            tag = int.from_bytes(bytes(tag_bytes), 'big')

        if i >= len(data):
            break

        length = data[i]
        i += 1
        if length & 0x80:
            num_len_bytes = length & 0x7F
            length = int.from_bytes(data[i:i+num_len_bytes], 'big')
            i += num_len_bytes

        value = data[i:i+length]
        i += length

        children = parse_tlv(value) if (tag & 0x20) == 0x20 else None

        tlvs.append({'tag': tag, 'length': length, 'value': value, 'children': children})
    return tlvs

def build_tlv(tlvs):
    result = bytearray()
    for tlv in tlvs:
        tag = tlv['tag']
        if tag <= 0xFF:
            tag_bytes = tag.to_bytes(1, 'big')
        else:
            tag_bytes_list = []
            temp_tag = tag
            while temp_tag > 0:
                tag_bytes_list.insert(0, temp_tag & 0xFF)
                temp_tag >>= 8
            tag_bytes = bytes(tag_bytes_list)

        value = build_tlv(tlv['children']) if tlv['children'] else tlv['value']
        length = len(value)
        if length < 0x80:
            length_bytes = length.to_bytes(1, 'big')
        else:
            length_len = (length.bit_length() + 7) // 8
            length_bytes = bytes([0x80 | length_len]) + length.to_bytes(length_len, 'big')

        result.extend(tag_bytes)
        result.extend(length_bytes)
        result.extend(value)
    return bytes(result)

def find_tlv(tlvs, tag):
    for tlv in tlvs:
        if tlv['tag'] == tag:
            return tlv
        if tlv['children']:
            found = find_tlv(tlv['children'], tag)
            if found:
                return found
    return None

def replace_tlv_value(tlvs, tag_hex, new_value_hex):
    tag = int(tag_hex, 16)
    new_value = unhexlify(new_value_hex)
    tlv = find_tlv(tlvs, tag)
    if tlv:
        tlv['value'] = new_value
        tlv['length'] = len(new_value)
        tlv['children'] = None
    return tlvs