"""Read-only TiinyOS token-format check. Never prints or saves token values."""
import os
import pathlib
import struct
import sys

try:
    import cramjam
except ImportError:
    sys.exit('Missing dependency. Run: python -m pip install --only-binary=:all: cramjam')


def varint(data, pos):
    value = 0
    for shift in range(0, 70, 7):
        if pos >= len(data):
            raise ValueError('Truncated varint')
        byte = data[pos]
        pos += 1
        value |= (byte & 127) << shift
        if byte < 128:
            return value, pos
    raise ValueError('Oversized varint')


def entries(data):
    if len(data) < 4:
        raise ValueError('Short block')
    count = struct.unpack_from('<I', data, len(data) - 4)[0]
    end = len(data) - 4 - 4 * count
    if end < 0:
        raise ValueError('Invalid restart array')
    pos, previous = 0, b''
    while pos < end:
        shared, pos = varint(data, pos)
        length, pos = varint(data, pos)
        size, pos = varint(data, pos)
        if shared > len(previous) or pos + length + size > end:
            raise ValueError('Invalid block entry')
        key = previous[:shared] + data[pos:pos + length]
        pos += length
        value = data[pos:pos + size]
        pos += size
        previous = key
        yield key, value


def block(data, handle):
    offset, pos = varint(handle, 0)
    size, _ = varint(handle, pos)
    if offset + size + 5 > len(data):
        raise ValueError('Block outside file')
    raw = data[offset:offset + size]
    kind = data[offset + size]
    if kind == 1:
        return bytes(cramjam.snappy.decompress_raw(raw))
    if kind != 0:
        raise ValueError('Unsupported block compression')
    return raw


def main():
    folder = pathlib.Path(os.environ['APPDATA']) / 'TiinyOS/Local Storage/leveldb'
    if len(sys.argv) > 1:
        folder = pathlib.Path(sys.argv[1])
    print('Database:', folder)
    print('Mode: local files only; no network requests; no token output.')
    if not folder.is_dir():
        sys.exit('Database directory not found.')
    candidates, warnings = [], []

    def remember(key, value, sequence):
        if key.endswith(b'\x01tiiny_auth_key'):
            candidates.append((sequence, value))

    files = sorted(set(folder.glob('*.ldb')) | set(folder.glob('*.sst')) | set(folder.glob('*.log')))
    if not files:
        sys.exit('No database table or write-ahead log files found.')
    snapshots = []
    for file in files:
        try:
            snapshots.append((file.name, file.read_bytes()))
        except OSError:
            warnings.append(file.name)
    for name, data in snapshots:
        try:
            if name.endswith(('.ldb', '.sst')):
                if len(data) < 48 or data[-8:] != struct.pack('<Q', 0xdb4775248b80fb57):
                    raise ValueError('Unrecognized table footer')
                footer = data[-48:]
                _, pos = varint(footer, 0)
                _, pos = varint(footer, pos)
                for _, handle in entries(block(data, footer[pos:])):
                    for key, value in entries(block(data, handle)):
                        if len(key) < 8:
                            raise ValueError('Short internal key')
                        tag = struct.unpack('<Q', key[-8:])[0]
                        remember(key[:-8], value if tag & 255 else b'', tag >> 8)
            else:
                pos, fragments = 0, b''
                while pos + 7 <= len(data):
                    left = 32768 - pos % 32768
                    if left < 7:
                        pos += left
                        continue
                    _, size, kind = struct.unpack_from('<IHB', data, pos)
                    if kind == 0:
                        pos += left
                        continue
                    if size > left - 7 or pos + 7 + size > len(data):
                        raise ValueError('Truncated log record')
                    chunk = data[pos + 7:pos + 7 + size]
                    pos += 7 + size
                    if kind in (1, 2):
                        fragments = chunk
                    elif kind in (3, 4):
                        fragments += chunk
                    else:
                        raise ValueError('Unknown log record type')
                    if kind not in (1, 4):
                        continue
                    if len(fragments) < 12:
                        raise ValueError('Short write batch')
                    sequence, count = struct.unpack_from('<QI', fragments, 0)
                    p = 12
                    for i in range(count):
                        kind = fragments[p]
                        p += 1
                        size, p = varint(fragments, p)
                        if p + size > len(fragments):
                            raise ValueError('Truncated log key')
                        key = fragments[p:p + size]
                        p += size
                        value = b''
                        if kind == 1:
                            size, p = varint(fragments, p)
                            if p + size > len(fragments):
                                raise ValueError('Truncated log value')
                            value = fragments[p:p + size]
                            p += size
                        elif kind != 0:
                            raise ValueError('Unknown write batch operation')
                        remember(key, value, sequence + i)
        except Exception:
            warnings.append(name)
    print('Files read into memory:', len(snapshots))
    if warnings:
        print('INCONCLUSIVE: unreadable or unrecognized files:', ', '.join(sorted(set(warnings))))
        print('No token validity conclusion made. Close TiinyOS completely and retry.')
        return 2
    if not candidates:
        print('NOT FOUND: no matching tiiny_auth_key entry in the scanned files.')
        return 1
    latest_sequence = max(seq for seq, _ in candidates)
    latest_values = {value for seq, value in candidates if seq == latest_sequence}
    if len(latest_values) != 1:
        print('INCONCLUSIVE: conflicting entries at the latest sequence.')
        return 2
    value = latest_values.pop()
    if not value:
        print('NOT AVAILABLE: latest matching entry is empty or deleted.')
        return 1
    try:
        if value[:1] not in (b'\x00', b'\x01'):
            raise ValueError('Unrecognized string encoding')
        token = value[1:].decode('utf-16-le' if value[:1] == b'\x00' else 'utf-8')
        if not token.strip():
            raise ValueError('Empty token')
    except (ValueError, UnicodeError):
        print('INCONCLUSIVE: matching entry found, but its encoding differs from expectations.')
        return 2
    print('SUCCESS: a nonempty Tiiny management-token candidate was found and decoded.')
    print('Token value intentionally hidden; not written to a file.')
    print('Device acceptance has NOT been tested. Device unchanged.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
