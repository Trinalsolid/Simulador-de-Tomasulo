def parse_mips(line: str) -> dict:
    line = line.strip()
    
    if not line or line.startswith('#'):

        return None

    particao = line.split()
    
    if len(particao) < 4:
        return None
    
    op = particao[0].upper()

    if op in ['ADD', 'SUB', 'MUL', 'DIV']:
        return {
            'op': op,
            'dest': particao[1],
            'reg1': particao[2],
            'reg2': particao[3],
            'estado': 'espera'
        }

    if op in ['LW', 'SW']:
        return {
            'op': op,
            'dest': particao[1],
            'reg1': particao[3],
            'reg2': 'R0',
            'offset': particao[2],
            'estado': 'espera'
        }

    if op in ['BEQ', 'BNE']:
        return {
            'op': op,
            'reg1': particao[1],
            'reg2': particao[2],
            'offset': int(particao[3]),
            'dest': 'R0',
            'estado': 'espera'
        }
    
    return None
