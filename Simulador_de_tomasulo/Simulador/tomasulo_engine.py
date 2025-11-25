import copy

#quantidade de reigstradores
QuantRegs = 32 

class TomasuloEngine:

    def __init__(self):

        #historico do steap-back
        self.historico = []
        
        self.LATENCIAS = {

            'ADD': 2, 'SUB': 2,
            'MUL': 4, 'DIV': 10,
            'LW': 3, 'SW': 2,
            'BEQ': 1, 'BNE': 1
        }

        # RS de 5 valores : 3 ADD/SUB, 2 MULT/DIV
        self.rs = [
            {'name': 'Add1', 'busy': False, 'op': None, 'vj': 0, 'vk': 0, 'qj': None, 'qk': None, 'dest': None, 'cycles': 0, 'rob_index': None, 'pc_when_issued': None},
            {'name': 'Add2', 'busy': False, 'op': None, 'vj': 0, 'vk': 0, 'qj': None, 'qk': None, 'dest': None, 'cycles': 0, 'rob_index': None, 'pc_when_issued': None},
            {'name': 'Add3', 'busy': False, 'op': None, 'vj': 0, 'vk': 0, 'qj': None, 'qk': None, 'dest': None, 'cycles': 0, 'rob_index': None, 'pc_when_issued': None},
            {'name': 'Mult1', 'busy': False, 'op': None, 'vj': 0, 'vk': 0, 'qj': None, 'qk': None, 'dest': None, 'cycles': 0, 'rob_index': None, 'pc_when_issued': None},
            {'name': 'Mult2', 'busy': False, 'op': None, 'vj': 0, 'vk': 0, 'qj': None, 'qk': None, 'dest': None, 'cycles': 0, 'rob_index': None, 'pc_when_issued': None},
        ]
        
        # buffer de rerordenamento
        self.rob = [
            {'busy': False, 'instruction': None, 'estado': 'espera', 'value': None, 'dest': None, 'should_branch': False, 'target_pc': None}
            for _ in range(8)
        ]

        #inicio e fim do ROB
        self.rob_head = 0  
        self.rob_tail = 0  
        

        self.registers = [0] * QuantRegs
        self.reg_status = [None] * QuantRegs
        
        # Estado da simulação
        self.cycle = 0
        self.instructions = []
        self.pc = 0
        self.instructions_committed = 0
        self.ciclos_bolha = 0
        self.flush_count = 0
        self.log_messages = []

    def criar_estado(self):
        return {
            'cycle': self.cycle,'pc': self.pc,'rs': copy.deepcopy(self.rs),'rob': copy.deepcopy(self.rob),'rob_head': self.rob_head,'rob_tail': self.rob_tail,'registers': list(self.registers),      
            'reg_status': list(self.reg_status),    'instructions_committed': self.instructions_committed,'ciclos_bolha': self.ciclos_bolha,'flush_count': self.flush_count,'log_messages': list(self.log_messages) 
        }

    def restaurar_estado(self, snap):

        self.cycle = snap['cycle']
        self.pc = snap['pc']
        self.rs = copy.deepcopy(snap['rs'])
        self.rob = copy.deepcopy(snap['rob'])
        self.rob_head = snap['rob_head']
        self.rob_tail = snap['rob_tail']
        self.registers = list(snap['registers'])
        self.reg_status = list(snap['reg_status'])
        self.instructions_committed = snap['instructions_committed']
        self.ciclos_bolha = snap['ciclos_bolha']
        self.flush_count = snap['flush_count']
        self.log_messages = list(snap['log_messages'])

    #setp foward das intruções
    def step(self):

        self.historico.append(self.criar_estado())
        self.commit()
        self.escrever_resultado()
        self.executar()
        self.despacho_de_instrucao()
        

        self.cycle += 1

    #stepback das instruções
    def step_back(self):

        if not self.historico:

            return
        
        last_state = self.historico.pop()
        self.restaurar_estado(last_state)
        self.log_messages.append(f"--- STEP BACK executado. Voltando para Ciclo {self.cycle} ---")
    
    #reset dos valores dos registradores e do simulador como um todo
    def reset(self):

        current_instructions = self.instructions
        self.__init__()
        self.instructions = current_instructions
        self.registers[2] = 5   
        self.registers[3] = 10  
        self.registers[5] = 2   
        self.registers[6] = 3   
    
    #carregamento doa arquivo de instruções pro mips .ASM
    def carregar_arquivo(self, instructions):

        self.reset()
        self.instructions = [inst for inst in instructions if inst is not None]
    
    def despacho_de_instrucao(self):
        if self.pc >= len(self.instructions):
            return

        instruction = self.instructions[self.pc]
        op = instruction['op']

        rs_ranges = {
            'ADD': range(0, 3), 'SUB': range(0, 3),
            'MUL': range(3, 5), 'DIV': range(3, 5),
            'LW': range(0, 3), 'SW': range(0, 3),
            'BEQ': range(0, 3), 'BNE': range(0, 3)
        }

        def rs_livres(indices):
            for i in indices:
                if not self.rs[i]['busy']:
                    return i
            return None

        rs_index = rs_livres(rs_ranges.get(op, []))

        if rs_index is None or self.rob[self.rob_tail]['busy']:
            self.ciclos_bolha += 1
            return

        rs = self.rs[rs_index]
        rs.update({
            'busy': True,
            'op': op,
            'cycles': self.LATENCIAS.get(op, 1),
            'rob_index': self.rob_tail,
            'pc_when_issued': self.pc
        })

        def resolucao_operandos(reg_name):
            reg_num = int(instruction[reg_name][1:]) if instruction[reg_name] else 0
            if self.reg_status[reg_num] is None:
                return self.registers[reg_num], None
            return None, self.reg_status[reg_num]

        rs['vj'], rs['qj'] = resolucao_operandos('reg1')
        rs['vk'], rs['qk'] = resolucao_operandos('reg2')

        dest_reg = int(instruction['dest'][1:]) if instruction['dest'] else 0
        rob_entry = self.rob[self.rob_tail]
        rob_entry.update({
            'busy': True,
            'instruction': instruction,
            'estado': 'executing',
            'dest': dest_reg,
            'value': None,
            'should_branch': False,
            'target_pc': None
        })

        if op not in ['BEQ', 'BNE', 'SW']:
            self.reg_status[dest_reg] = self.rob_tail

        self.pc += 1
        self.rob_tail = (self.rob_tail + 1) % len(self.rob)
        self.log_messages.append(f"{op} Despachado em PC={self.pc-1}")

    def executar(self):
        for rs in self.rs:
            if not rs['busy']:
                continue
            
            if rs['qj'] is None and rs['qk'] is None:
                if rs['cycles'] > 0:
                    rs['cycles'] -= 1
    
    def escrever_resultado(self):
        def compute_result(op, vj, vk):
            operations = {
                'ADD': lambda: vj + vk,
                'SUB': lambda: vj - vk,
                'MUL': lambda: vj * vk,
                'DIV': lambda: vj // vk if vk != 0 else 0,
                'LW':  lambda: vj + vk,
                'SW':  lambda: vj + vk
            }
            return operations.get(op, lambda: 0)()

        def handle_branch(rs, rob_entry, condition):
            instruction = rob_entry['instruction']
            pc_when_issued = rs['pc_when_issued']
            target_pc = pc_when_issued + 1 + instruction['offset']
            rob_entry['should_branch'] = condition
            rob_entry['target_pc'] = target_pc
            self.log_messages.append(
                f"{rs['op']} resolvido: {rs['vj']} {('==' if rs['op']=='BEQ' else '!=')} {rs['vk']}? {condition}, ir para PC={target_pc}"
            )

        for rs in self.rs:
            if not rs['busy'] or rs['cycles'] > 0 or rs['qj'] is not None or rs['qk'] is not None:
                continue

            op, vj, vk, rob_index = rs['op'], rs['vj'], rs['vk'], rs['rob_index']
            rob_entry = self.rob[rob_index]

            if op in ['BEQ', 'BNE']:
                condition = (vj == vk) if op == 'BEQ' else (vj != vk)
                handle_branch(rs, rob_entry, condition)
                result = 0
            else:
                result = compute_result(op, vj, vk)

            rob_entry['value'] = result
            rob_entry['estado'] = 'ready'

            for espera_rs in self.rs:
                if espera_rs['busy']:
                    if espera_rs['qj'] == rob_index:
                        espera_rs['vj'], espera_rs['qj'] = result, None
                    if espera_rs['qk'] == rob_index:
                        espera_rs['vk'], espera_rs['qk'] = result, None

            rs.update({'busy': False, 'op': None, 'vj': 0, 'vk': 0,
                    'qj': None, 'qk': None, 'dest': None, 'cycles': 0})


    def commit(self):

        rob_entry = self.rob[self.rob_head]
        
        if not rob_entry['busy'] or rob_entry['estado'] != 'ready':
            return
        
        instruction = rob_entry['instruction']
        op = instruction['op'] if instruction else None
        
        if op in ['BEQ', 'BNE']:
            predicted_taken = False 
            actual_should_branch = rob_entry['should_branch']
            
            if actual_should_branch != predicted_taken:
                target_pc = rob_entry['target_pc']
                self.log_messages.append(f"FLUSH! predicao errada de branch, pulando para PC={target_pc}")
                self.missprediction_flush(target_pc)
                self.flush_count += 1
                return
            
            self.limpar_entrada_rob(rob_entry)
            self.rob_head = (self.rob_head + 1) % 8
            self.instructions_committed += 1
            self.log_messages.append(f"{op} Commitado")
            return
        
        dest_reg = rob_entry['dest']
        if dest_reg is not None and dest_reg < QuantRegs:
            self.registers[dest_reg] = rob_entry['value']
            if self.reg_status[dest_reg] == self.rob_head:
                self.reg_status[dest_reg] = None
        
        self.limpar_entrada_rob(rob_entry)
        
        self.rob_head = (self.rob_head + 1) % 8
        self.instructions_committed += 1
        self.log_messages.append(f"{op} Commitado")


    def limpar_entrada_rob(self, entry):

        entry['busy'] = False
        entry['instruction'] = None
        entry['estado'] = 'espera'
        entry['value'] = None
        entry['dest'] = None
        entry['should_branch'] = False
        entry['target_pc'] = None


    def missprediction_flush(self, correct_pc):

        instrucoes_descartadas = 0

        for rs in self.rs:

            if rs['busy']:
                instrucoes_descartadas += 1
            rs['busy'] = False
            rs['op'] = None
            rs['vj'] = 0
            rs['vk'] = 0
            rs['qj'] = None
            rs['qk'] = None
            rs['dest'] = None
            rs['cycles'] = 0

        for i in range(8):
            if self.rob[i]['busy']:
                instrucoes_descartadas += 1
            self.limpar_entrada_rob(self.rob[i])
            
        self.rob_head = 0
        self.rob_tail = 0
        
        for i in range(QuantRegs):
            self.reg_status[i] = None
        
        self.pc = correct_pc 
        self.ciclos_bolha += instrucoes_descartadas
        self.log_messages.append(

            f"PC redirecionado para {correct_pc} (Pipeline Flush, {instrucoes_descartadas} instruções descartadas)"
        )

    
    def completo(self):

        pc_done = self.pc >= len(self.instructions)
        rob_empty = not self.rob[self.rob_head]['busy']
        
        return pc_done and rob_empty
    
    def get_metricas(self):

        ipc = self.instructions_committed / self.cycle if self.cycle > 0 else 0

        return {
            'cycles': self.cycle,'instructions': self.instructions_committed,
            'ipc': ipc,'bubbles': self.ciclos_bolha,
            'flushes': self.flush_count
        }
