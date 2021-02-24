# Python bytecode 2.7 (decompiled from Python 2.7)
# Embedded file name: C:\Python\compiler\pjorion.py
# Compiled at: 2016-09-16 12:58:32
from dispack.disassemble_2 import *
from struct import pack
from random import randint, choice
from types import CodeType

class Analizator(object):

    def __init__(self, co=None):
        self.JUMP_ONLY = (110, 113, 119)
        self.JUMP_AND_NEXT = (93, 120, 121, 122, 143, 111, 112, 114, 115)
        self.CAMO_OPCODE = [ op for op in xrange(HAVE_ARGUMENT, 256) if opname[op][0] != '<' ]
        self.FAKE_OPCODES = [ opname.index(op) for op in opname if op[0] == '<' ]
        self.new_id = 0
        self.Codes = {}
        self.Order = []
        if co is not None:
            self.ParseCO(co)
        return

    def Clear(self):
        self.new_id = 0
        self.Codes.clear()
        self.Order = []

    def ParseCO(self, co):
        self.Clear()
        _, ext_labels = findlabels(co.co_code)
        n = len(co.co_code)
        i = self.new_id = extended_arg = 0
        free = None
        while i < n:
            try:
                self.Codes[self.new_id] = {}
                self.Codes[self.new_id]['hex'] = co.co_code[i]
                op = ord(self.Codes[self.new_id]['hex'])
                self.Codes[self.new_id]['op'] = op
                self.Codes[self.new_id]['fake'] = False
                if op <= OPCODE_MAX:
                    self.Codes[self.new_id]['name'] = opname[op]
                    if '<' == self.Codes[self.new_id]['name'][0]:
                        self.Codes[self.new_id]['fake'] = True
                else:
                    self.Codes[self.new_id]['fake'] = True
                    self.Codes[self.new_id]['name'] = '<' + repr(op) + '>'
                self.Codes[self.new_id]['nexts'] = []
                self.Codes[self.new_id]['labels'] = []
                if self.new_id > 0:
                    if self.new_id in self.Codes[self.new_id - 1]['nexts'] and self.new_id - 1 not in self.Codes[self.new_id]['labels']:
                        self.Codes[self.new_id]['labels'].append(self.new_id - 1)
                elif -1 not in self.Codes[self.new_id]['labels']:
                    self.Codes[self.new_id]['labels'].append(-1)
                if i in ext_labels:
                    for v in ext_labels[i]:
                        if v not in self.Codes[self.new_id]['labels']:
                            self.Codes[self.new_id]['labels'].append(v)

                i += 1
                if not self.Codes[self.new_id]['fake']:
                    if op not in hasjrel and op not in hasjabs:
                        num = -1 if i == n else self.new_id + 1
                        if num not in self.Codes[self.new_id]['nexts']:
                            self.Codes[self.new_id]['nexts'].append(num)
                    if op >= HAVE_ARGUMENT and i + 1 < n:
                        self.Codes[self.new_id]['hex'] += co.co_code[i] + co.co_code[i + 1]
                        try:
                            oparg = ord(co.co_code[i]) + ord(co.co_code[i + 1]) * 256 + extended_arg
                        except:
                            self.Codes[self.new_id]['fake'] = True
                            continue

                        extended_arg = 0
                        i = i + 2
                        if op == EXTENDED_ARG:
                            extended_arg = oparg * 65536L
                        if op in hasconst:
                            self.Codes[self.new_id]['fake'] = not (oparg >= 0 and oparg < len(co.co_consts))
                        elif op in hasname:
                            self.Codes[self.new_id]['fake'] = not (oparg >= 0 and oparg < len(co.co_names))
                        elif op in hasjrel:
                            if op in self.JUMP_AND_NEXT:
                                num = self.new_id + 1 if i < n else -1
                                if num not in self.Codes[self.new_id]['nexts']:
                                    self.Codes[self.new_id]['nexts'].append(num)
                            self.Codes[self.new_id]['fake'] = not (i + oparg >= 0 and i + oparg < n)
                        elif op in hasjabs:
                            if op in self.JUMP_AND_NEXT:
                                num = self.new_id + 1 if i < n else -1
                                if num not in self.Codes[self.new_id]['nexts']:
                                    self.Codes[self.new_id]['nexts'].append(num)
                            self.Codes[self.new_id]['fake'] = not (oparg >= 0 and oparg < n)
                        elif op in haslocal:
                            self.Codes[self.new_id]['fake'] = not (oparg >= 0 and oparg < len(co.co_varnames))
                        elif op in hascompare:
                            self.Codes[self.new_id]['fake'] = not (oparg >= 0 and oparg < len(cmp_op))
                        elif op in hasfree:
                            if free is None:
                                free = co.co_cellvars + co.co_freevars
                            self.Codes[self.new_id]['fake'] = not (oparg >= 0 and oparg < len(free))
            finally:
                self.Order.append(self.new_id)
                self.new_id += 1

        CodeinHex = self.CreateCodeinHexDict()
        for i in ext_labels:
            current_id = CodeinHex[i]
            for v in ext_labels[i]:
                if current_id not in self.Codes[v]['nexts']:
                    self.Codes[v]['nexts'].append(current_id)

        pos = 0
        while pos < len(self.Order):
            code_id = self.Order[pos]
            if not self.Codes[code_id]['fake'] and self.Codes[code_id]['op'] == 145:
                self.DelCodeId(code_id)
            pos += 1

        return

    def BuildCoCode(self, add_ext=True):
        co_code = ''
        if add_ext:
            self.AddExtForJumpInstruction()
        prev_id = -1
        hexPos = self.CreateHexPosCodeDict()
        for code_id in self.Order:
            if self.Codes[code_id]['op'] in hasjrel:
                if not self.Codes[code_id]['fake']:
                    begin_code = self.GetNextCodeId(code_id)
                    end_code = self.Codes[code_id]['nexts'][-1]
                    hex_jrel = pack('<I', hexPos[end_code] - hexPos[begin_code])
                    if prev_id != -1 and not self.Codes[prev_id]['fake'] and self.Codes[prev_id]['op'] == 145:
                        self.Codes[prev_id]['hex'] = pack('<H', 145)[0] + hex_jrel[2:4]
                    self.Codes[code_id]['hex'] = pack('<H', self.Codes[code_id]['op'])[0] + hex_jrel[:2]
            elif self.Codes[code_id]['op'] in hasjabs:
                if not self.Codes[code_id]['fake']:
                    next_code = self.Codes[code_id]['nexts'][-1]
                    hex_jmp = pack('<I', hexPos[next_code])
                    if prev_id != -1 and not self.Codes[prev_id]['fake'] and self.Codes[prev_id]['op'] == 145:
                        self.Codes[prev_id]['hex'] = pack('<H', 145)[0] + hex_jmp[2:4]
                    self.Codes[code_id]['hex'] = pack('<H', self.Codes[code_id]['op'])[0] + hex_jmp[:2]
            if self.Codes[code_id]['op'] != 145 or self.Codes[code_id]['fake']:
                if prev_id != -1 and not self.Codes[prev_id]['fake'] and self.Codes[prev_id]['op'] == 145:
                    co_code += self.Codes[prev_id]['hex']
                co_code += self.Codes[code_id]['hex']
            elif prev_id != -1 and not self.Codes[prev_id]['fake'] and self.Codes[prev_id]['op'] == 145:
                co_code += self.Codes[prev_id]['hex']
            prev_id = code_id

        return co_code

    def AddExtForJumpInstruction(self, all_jump=False):
        pos = 0
        hexPos = self.CreateHexPosCodeDict()
        ext_list = []
        while pos < len(self.Order):
            code_id = self.Order[pos]
            if self.Codes[code_id]['op'] in self.JUMP_ONLY + self.JUMP_AND_NEXT and not self.Codes[code_id]['fake']:
                prev_id = self.GetPreviousCodeId(code_id)
                if prev_id == -1 or self.Codes[prev_id]['fake'] or self.Codes[prev_id]['op'] != 145:
                    if self.Codes[code_id]['op'] in hasjrel:
                        begin_code = self.GetNextCodeId(code_id)
                        end_code = self.Codes[code_id]['nexts'][-1]
                        if all_jump or hexPos[end_code] - hexPos[begin_code] > 50000:
                            ext_list.append(pos)
                            pos += 1
                    elif self.Codes[code_id]['op'] in hasjabs:
                        next_code = self.Codes[code_id]['nexts'][-1]
                        if all_jump or hexPos[next_code] > 50000:
                            ext_list.append(pos)
                            pos += 1
            pos += 1

        for pos in ext_list[::-1]:
            self.InsCodeInOrder(pos, 145, '\x00\x00', False, True)

    def CZBBuildCoCode(self, data):
        self.InsCodeInOrder(0, 1, '', False, False)
        self.InsCodeInOrder(0, 1, '', False, False)
        jmp_code_id = self.InsCodeInOrder(0, 1, '', False, False)
        self.InsCamoFakeOpcode(0)
        code_id = self.InsFakeOpcode(0)
        self.Codes[code_id]['hex'] += data
        code_id = self.InsCodeInOrder(0, 121, '\x00\x00', False, True, jmp_code_id)
        self.Codes[jmp_code_id]['labels'] = [code_id]
        self.AddExtForJumpInstruction(True)
        return self.BuildCoCode(False)

    def DelCodeId(self, code_id):
        if code_id in self.Codes:
            pos = tuple(self.Order).index(code_id)
            next_inst = self.Order[pos + 1] if pos < len(self.Order) - 1 else -1
            for code in self.Codes[code_id]['labels']:
                if code > -1:
                    nexts = self.Codes[code]['nexts']
                    nexts[nexts.index(code_id)] = next_inst
                    self.Codes[code]['nexts'] = nexts

            if next_inst > -1:
                labels = []
                for code in self.Codes[code_id]['labels']:
                    if code not in self.Codes[next_inst]['labels']:
                        labels.append(code)

                self.Codes[next_inst]['labels'] = labels + self.Codes[next_inst]['labels']
            for code in self.Codes[code_id]['nexts']:
                if code > -1:
                    if code_id in self.Codes[code]['labels']:
                        self.Codes[code]['labels'].remove(code_id)

            del self.Codes[code_id]
            self.Order.remove(code_id)

    def InsFakeOpcode(self, pos):
        op = self.FAKE_OPCODES[randint(0, len(self.FAKE_OPCODES) - 1)]
        return self.InsCodeInOrder(pos, op, '', True, False)

    def InsCamoFakeOpcode(self, pos):
        op = self.CAMO_OPCODE[randint(0, len(self.CAMO_OPCODE) - 1)]
        return self.InsCodeInOrder(pos, op, '', True, False)

    def InsJumpAbsolute(self, pos, label, fake=False, updatejumplinks=True):
        op = 113
        set_code = self.Order[-1] if label >= len(self.Order) else self.Order[label]
        return self.InsCodeInOrder(pos, op, '\x00\x00', fake, updatejumplinks, set_code)

    def InsCodeInOrder(self, pos, op, arghex, fake, updatejumplinks, tag=None):
        code_record = {'op': op,
         'name': opname[op],
         'hex': pack('<H', op)[0] + arghex,
         'fake': fake,
         'labels': [],
         'nexts': []}
        if pos == 0:
            code_record['labels'] = [-1]
            next_code = self.Order[0]
            if -1 in self.Codes[next_code]['labels']:
                self.Codes[next_code]['labels'].remove(-1)
        elif pos >= len(self.Order):
            prev_code = self.Order[-1]
            if -1 in self.Codes[prev_code]['nexts']:
                self.Codes[prev_code]['nexts'].remove(-1)
                if self.new_id not in self.Codes[prev_code]['nexts']:
                    self.Codes[prev_code]['nexts'] = [self.new_id] + self.Codes[prev_code]['nexts']
                code_record['labels'] = [prev_code]
        else:
            prev_code = self.Order[pos - 1]
            next_code = self.Order[pos]
            labels = tuple([ x for x in self.Codes[next_code]['labels'] ])
            for code in labels:
                need_move = False
                if labels.index(code) == 0:
                    if next_code in self.Codes[prev_code]['nexts'] and self.Codes[prev_code]['op'] not in self.JUMP_ONLY:
                        need_move = True
                    else:
                        need_move = updatejumplinks
                else:
                    need_move = updatejumplinks
                if need_move:
                    self.Codes[next_code]['labels'].remove(code)
                    self.Codes[code]['nexts'][self.Codes[code]['nexts'].index(next_code)] = self.new_id
                    code_record['labels'].append(code)

        if op not in self.JUMP_ONLY or fake:
            if pos >= len(self.Order):
                code_record['nexts'] = [-1]
            else:
                next_code = self.Order[pos]
                if self.new_id not in self.Codes[next_code]['labels']:
                    self.Codes[next_code]['labels'] = [self.new_id] + self.Codes[next_code]['labels']
                code_record['nexts'] = [next_code]
        if op in hasjrel and not fake:
            if pos >= len(self.Order):
                if -1 not in code_record['nexts']:
                    code_record['nexts'] = [-1]
            else:
                if self.new_id not in self.Codes[tag]['labels']:
                    self.Codes[tag]['labels'].append(self.new_id)
                if tag not in code_record['nexts']:
                    code_record['nexts'].append(tag)
        if op in hasjabs and not fake:
            if self.new_id not in self.Codes[tag]['labels']:
                self.Codes[tag]['labels'].append(self.new_id)
            if tag not in code_record['nexts']:
                code_record['nexts'].append(tag)
        self.Codes[self.new_id] = code_record.copy()
        self.Order.insert(pos, self.new_id)
        code_id = self.new_id
        self.new_id += 1
        return code_id

    def RepJumpForwardOnAbsolute(self, pos):
        code_id = self.Order[pos]
        if self.Codes[code_id]['op'] == 110:
            op = 113
            self.Codes[code_id]['op'] = op
            self.Codes[code_id]['name'] = opname[op]
            return True
        return False

    def RepAllJumpForwardOnAbsolute(self, rep_rand=False, rep_fake=False):
        for pos in xrange(0, len(self.Order)):
            code_id = self.Order[pos]
            if self.Codes[code_id]['op'] == 110 and (not self.Codes[code_id]['fake'] or rep_fake):
                if not rep_rand or randint(0, 1) == 1:
                    self.RepJumpForwardOnAbsolute(pos)

    def RepJumpAbsoluteOnForward(self, pos):
        code_id = self.Order[pos]
        if self.Codes[code_id]['op'] == 113:
            if tuple(self.Order).index(self.Codes[code_id]['nexts'][0]) > pos:
                op = 110
                self.Codes[code_id]['op'] = op
                self.Codes[code_id]['name'] = opname[op]
                return True
        return False

    def RepAllJumpAbsoluteOnForward(self, rep_rand=False, rep_fake=False):
        count = 0
        for pos in xrange(0, len(self.Order)):
            code_id = self.Order[pos]
            if self.Codes[code_id]['op'] == 113 and (not self.Codes[code_id]['fake'] or rep_fake):
                if not rep_rand or count == 0 or randint(0, 1) == 1:
                    if self.RepJumpAbsoluteOnForward(pos):
                        count += 1

        return count

    def RepJumpAbsoluteOnException(self, pos):
        code_id = self.Order[pos]
        if self.Codes[code_id]['op'] == 113:
            nexts_code_id = self.Codes[code_id]['nexts'][0]
            jmp_pos = tuple(self.Order).index(nexts_code_id)
            if jmp_pos > pos:
                self.Codes[nexts_code_id]['labels'] = [ x for x in self.Codes[nexts_code_id]['labels'] if x != code_id ]
                prev_pos = jmp_pos - 1
                prev_code_id = self.Order[prev_pos]
                if not self.Codes[prev_code_id]['fake'] and self.Codes[prev_code_id]['op'] not in self.JUMP_ONLY and nexts_code_id in self.Codes[prev_code_id]['nexts']:
                    self.InsJumpAbsolute(jmp_pos, jmp_pos)
                    jmp_pos += 1
                self.InsCodeInOrder(jmp_pos, 1, '', False, False)
                self.InsCodeInOrder(jmp_pos, 1, '', False, False)
                jmp_code_id = self.InsCodeInOrder(jmp_pos, 1, '', False, False)
                next_pos = pos + 1
                next_code_id = self.Order[next_pos]
                if next_pos >= len(self.Order) or self.Codes[next_code_id]['op'] not in self.FAKE_OPCODES:
                    next_code_id = self.InsFakeOpcode(next_pos)
                    self.InsCamoFakeOpcode(next_pos + 1)
                if code_id not in self.Codes[next_code_id]['labels']:
                    self.Codes[next_code_id]['labels'].insert(0, code_id)
                op = 121
                self.Codes[code_id]['op'] = op
                self.Codes[code_id]['name'] = opname[op]
                self.Codes[code_id]['nexts'] = [next_code_id, jmp_code_id]
                self.Codes[jmp_code_id]['labels'] = [code_id]
                return True
        return False

    def ConvJumpRelToAbsolute(self, pos):
        block = []
        code_id = self.Order[pos]
        if self.Codes[code_id]['op'] in hasjrel and self.Codes[code_id]['op'] != 110:
            if len(self.Codes[code_id]['nexts']) == 2:
                jump_code1 = self.InsJumpAbsolute(pos + 1, pos + 1)
                link_id = self.Codes[code_id]['nexts'][1]
                self.Codes[link_id]['labels'].remove(code_id)
                link_pos = tuple(self.Order).index(link_id)
                jump_code2 = self.InsJumpAbsolute(pos + 2, link_pos, False, False)
                self.Codes[code_id]['nexts'][1] = jump_code2
                self.Codes[jump_code2]['labels'] = [code_id]
                block = [code_id, jump_code1, jump_code2]
        return block

    def ConvAllJumpRelToAbsolute(self):
        blocks = []
        codes_list = [ x for x in self.Order ]
        for pos in xrange(0, len(codes_list)):
            code_id = codes_list[pos]
            if self.Codes[code_id]['op'] in hasjrel and self.Codes[code_id]['op'] != 110:
                ins_pos = tuple(self.Order).index(code_id)
                block = self.ConvJumpRelToAbsolute(ins_pos)
                if block:
                    blocks.append(block)

        return blocks

    def Obfuscate(self, jumprel_blocks, insert_camo_jumprel=True, insert_unused_bytecode=True, insert_exception_jump=False):
        jumprel_codes = []
        jumprel_first_codes = frozenset([ block[0] for block in jumprel_blocks ])
        for block in jumprel_blocks:
            jumprel_codes += block

        jumprel_codes = frozenset(jumprel_codes)
        order_blocks = []
        order_length = len(self.Order)
        getBlockSize = lambda length: randint(max(1, length // length), max(1, length // 300))
        block_size = getBlockSize(order_length)
        new_block = []
        new_jumprel_block = []
        for code in self.Order:
            if code in jumprel_codes:
                if new_block:
                    if block_size - len(new_block) < 3:
                        order_blocks.append(new_block)
                    else:
                        new_jumprel_block = [ x for x in new_block ]
                    new_block = []
                    block_size = getBlockSize(order_length)
                if code in jumprel_first_codes:
                    if new_jumprel_block and new_jumprel_block[-1] in jumprel_codes and block_size - len(new_jumprel_block) < 3:
                        order_blocks.append(new_jumprel_block)
                        new_jumprel_block = []
                new_jumprel_block.append(code)
            if new_jumprel_block:
                if len(jumprel_codes) < block_size:
                    new_block = [ x for x in new_jumprel_block ]
                else:
                    order_blocks.append(new_jumprel_block)
                new_jumprel_block = []
            if len(new_block) < block_size:
                new_block.append(code)
            order_blocks.append(new_block)
            block_size = getBlockSize(order_length)
            new_block = [code]

        if new_jumprel_block:
            order_blocks.append(new_jumprel_block)
        if new_block:
            order_blocks.append(new_block)
        i = 0
        for block in order_blocks:
            if i > 0:
                pos = tuple(self.Order).index(block[0])
                jump_id = self.InsJumpAbsolute(pos, pos)
                order_blocks[i - 1].append(jump_id)
            i += 1

        jump_id = self.InsJumpAbsolute(0, 0)
        order_blocks = [[jump_id]] + order_blocks
        self.Order = order_blocks[0]
        order_blocks.remove(order_blocks[0])
        while len(order_blocks) > 0:
            block = choice(order_blocks)
            order_blocks.remove(block)
            self.Order += block

        if insert_exception_jump:
            self.RepJumpAbsoluteOnException(tuple(self.Order).index(jump_id))
        getBlockSize = lambda length: randint(1, 1 if length < 20 else (3 if length < 100 else (5 if length < 1000 else (8 if length < 10000 else 10))))
        not_jabs_codes_list = [ code for code in self.Order if self.Codes[code]['op'] != 113 ]
        codes_list = [ x for x in self.Order ]
        codes_count = len(codes_list)
        if insert_camo_jumprel or insert_unused_bytecode:
            i = 1
            while i < codes_count:
                if self.Codes[codes_list[i - 1]]['op'] == 113:
                    ins_pos = tuple(self.Order).index(codes_list[i])
                    if insert_unused_bytecode:
                        block_size = getBlockSize(codes_count)
                        fake_jump_index = randint(1, block_size) if block_size > 4 else 5
                        for x in xrange(1, block_size + 1):
                            j = randint(0, 100)
                            if j >= 95 or x == fake_jump_index:
                                self.InsJumpAbsolute(ins_pos, tuple(self.Order).index(choice(self.Order)), True, False)
                            elif j >= 60:
                                self.InsFakeOpcode(ins_pos)
                            else:
                                code_id = choice(not_jabs_codes_list)
                                self.InsCodeInOrder(ins_pos, self.Codes[code_id]['op'], self.Codes[code_id]['hex'][1:], True, False)
                            ins_pos += 1

                    if insert_camo_jumprel:
                        self.InsCamoFakeOpcode(ins_pos)
                i += 1

    def GetCodeIdinHex(self, pos):
        code_id = -1
        i = 0
        for code in self.Order:
            offset = len(self.Codes[code]['hex'])
            if i <= pos and pos <= i + offset - 1:
                code_id = code
                break
            i += offset

        return code_id

    def CreateCodeinHexDict(self):
        i = 0
        CodeinHex = {}
        for code in self.Order:
            CodeinHex[i] = code
            i += len(self.Codes[code]['hex'])

        return CodeinHex

    def GetHexPosCodeId(self, code_id):
        i = 0
        find = False
        for code in self.Order:
            if code_id == code:
                find = True
                break
            i += len(self.Codes[code]['hex'])

        if not find:
            i = -1
        return i

    def CreateHexPosCodeDict(self):
        i = 0
        hexPos = {}
        for code_id in self.Order:
            hexPos[code_id] = i
            i += len(self.Codes[code_id]['hex'])

        return hexPos

    def HexCountAtToCodeId(self, at_code_id, to_code_id):
        count = 0
        if at_code_id > -1 and to_code_id > -1:
            Order = tuple(self.Order)
            i = Order.index(at_code_id)
            j = Order.index(to_code_id)
            while i < j:
                count += len(self.Codes[self.Order[i]]['hex'])
                i += 1

        return count

    def GetNextCodeId(self, code_id):
        pos = tuple(self.Order).index(code_id)
        return self.Order[pos + 1] if pos < len(self.Order) - 1 else -1

    def GetPreviousCodeId(self, code_id):
        pos = tuple(self.Order).index(code_id)
        return self.Order[pos - 1] if pos > 0 else -1


class CharsCrypter(object):

    def __init__(self, prefix='', num_length=0):
        self.prefix = prefix
        self.num_length = num_length
        self.keys = {}
        self.main_keys_pos = []
        self.var_names = ['PJO0000',
         'PJO0001',
         'PJO0002',
         'PJO0003',
         'PJO0004',
         'PJO0005',
         'PJO0006',
         'PJO0007',
         'PJO0008',
         'PJO0009',
         'PJO0010',
         'PJO0011',
         'PJO0012',
         'PJO0013',
         'PJO0014',
         'PJO0015',
         'PJO0016',
         'PJO0017',
         'PJO0018',
         'PJO0019',
         'PJO0020',
         'PJO0021',
         'PJO0022',
         'PJO0023',
         'PJO0024',
         'PJO0025',
         'PJO0026',
         'PJO0027',
         'PJO0028',
         'PJO0029',
         'PJO0030',
         'PJO0031',
         'PJO0032',
         'PJO0033',
         'PJO0034',
         'PJO0035',
         'PJO0036',
         'PJO0037',
         'PJO0038',
         'PJO0039',
         'PJO0040',
         'PJO0041',
         'PJO0042',
         'PJO0043',
         'PJO0044',
         'PJO0045',
         'PJO0046',
         'PJO0047',
         'PJO0048',
         'PJO0049',
         'PJO0050',
         'PJO0051',
         'PJO0052',
         'PJO0053',
         'PJO0054',
         'PJO0055',
         'PJO0056',
         'PJO0057',
         'PJO0058',
         'PJO0059',
         'PJO0100',
         'PJO0101',
         'PJO0102',
         'PJO0103',
         'PJO0104',
         'PJO0105',
         'PJO0106',
         'PJO0107',
         'PJO0108',
         'PJO0109',
         'PJO0110',
         'PJO0111',
         'PJO0112',
         'PJO0113',
         'PJO0114',
         'PJO0115',
         'PJO0116',
         'PJO0117',
         'PJO0118',
         'PJO0119',
         'PJO0120',
         'PJO0121',
         'PJO0122',
         'PJO0123',
         'PJO0124',
         'PJO0125',
         'PJO0126',
         'PJO0127',
         'PJO0128',
         'PJO0129',
         'PJO0130',
         'PJO0131',
         'PJO0132',
         'PJO0133',
         'PJO0134',
         'PJO0135',
         'PJO0136',
         'PJO0137',
         'PJO0138',
         'PJO0139',
         'PJO0140',
         'PJO0141',
         'PJO0142',
         'PJO0143',
         'PJO0144',
         'PJO0145',
         'PJO0146',
         'PJO0147',
         'PJO0148',
         'PJO0149',
         'PJO0150',
         'PJO0151',
         'PJO0152',
         'PJO0153',
         'PJO0154',
         'PJO0155',
         'PJO0156',
         'PJO0157',
         'PJO0158',
         'PJO0159',
         'PJO0160',
         'PJO0161',
         'PJO0162',
         'PJO0163',
         'PJO0164',
         'PJO0165',
         'PJO0166',
         'PJO0167',
         'PJO0168',
         'PJO0169',
         'PJO0170',
         'PJO0171',
         'PJO0172',
         'PJO0173',
         'PJO0174',
         'PJO0175',
         'PJO0176',
         'PJO0177',
         'PJO0178',
         'PJO0179',
         'PJO0180',
         'PJO0181',
         'PJO0182',
         'PJO0183',
         'PJO0184',
         'PJO0185',
         'PJO0186',
         'PJO0187',
         'PJO0188',
         'PJO0189',
         'PJO0190',
         'PJO0191',
         'PJO0192',
         'PJO0193',
         'PJO0194',
         'PJO0195',
         'PJO0196',
         'PJO0197',
         'PJO0198',
         'PJO0199',
         'PJO0200',
         'PJO0201',
         'PJO0202',
         'PJO0203',
         'PJO0204',
         'PJO0205',
         'PJO0206',
         'PJO0207',
         'PJO0208',
         'PJO0209',
         'PJO0210',
         'PJO0211',
         'PJO0212',
         'PJO0213',
         'PJO0214',
         'PJO0215',
         'PJO0216',
         'PJO0217',
         'PJO0218',
         'PJO0219']

    def GK(self, new_pos=0, isMain=False):
        self.keys[new_pos] = randint(0, 255)
        if isMain and new_pos not in self.main_keys_pos:
            self.main_keys_pos.append(new_pos)
        return str(self.keys[new_pos])

    def XK(self, new_pos, mul_pos, isMain=False):
        gen_num = self.GK(new_pos)
        self.keys[new_pos] = self.keys[new_pos] ^ self.keys[mul_pos]
        if isMain and new_pos not in self.main_keys_pos:
            self.main_keys_pos.append(new_pos)
        return gen_num + ' ^ ' + self.prefix + str(mul_pos).rjust(self.num_length, '0')

    def XRK(self, new_pos, isMain=False):
        gen_num = self.GK(new_pos)
        base_num = choice(self.main_keys_pos) if self.main_keys_pos else 0
        self.keys[new_pos] = self.keys[new_pos] ^ self.keys[base_num]
        if isMain and new_pos not in self.main_keys_pos:
            self.main_keys_pos.append(new_pos)
        return gen_num + ' ^ ' + self.prefix + str(base_num).rjust(self.num_length, '0')

    def XC(self, char, mul_pos):
        return str(ord(char) ^ self.keys[mul_pos]) + ' ^ ' + self.prefix + str(mul_pos).rjust(self.num_length, '0')

    def XRC(self, char):
        mul_pos = choice(self.main_keys_pos) if len(self.main_keys_pos) > 0 else 0
        return str(ord(char) ^ self.keys[mul_pos]) + ' ^ ' + self.prefix + str(mul_pos).rjust(self.num_length, '0')

    def Clear(self):
        self.keys.clear()
        self.main_keys_pos = []

    def CodeReplace(self, codeobject):
        obf_numbers = list(xrange(0, 32))
        obf_names = []
        for name in self.var_names:
            if codeobject.find(name) > -1:
                new_name = ''
                while True:
                    while len(new_name) < len(name):
                        new_name += chr(choice(obf_numbers))

                    if new_name in obf_names:
                        new_name = ''
                    obf_names.append(new_name)
                    break

                codeobject = codeobject.replace(name, new_name)

        return codeobject

    def ObjReplace(self, object):
        from marshal import dumps, loads
        codeobject = dumps(object)
        return loads(self.CodeReplace(codeobject))


def obfuscate(filename, temp_filename=None):
    Error = False
    Error_Msg = ''
    Revision = '<pjorion_obfuscated>'

    def CompileMarshalCode(filename, filename_tag='', temp_filename=None):
        global Error_Msg
        global Error
        from os import path
        codeobject = None
        try:
            if temp_filename != None:
                if path.exists(temp_filename):
                    try:
                        f = open(temp_filename, 'U')
                        codestring = f.read()
                        f.close()
                        try:
                            codeobject = compile(codestring, filename_tag, 'exec')
                        except Exception as E:
                            Error = True
                            Error_Msg = 'Error: check the syntax of the source code!' + str(E).replace('\n', ' ')

                    except Exception as E:
                        Error = True
                        Error_Msg = "Error: file '%s' could not read!" % temp_filename

                else:
                    Error = True
                    Error_Msg = "Error: file '%s' not found! " % temp_filename
            elif path.exists(filename):
                try:
                    f = open(filename, 'U')
                    codestring = f.read()
                    f.close()
                    try:
                        codeobject = compile(codestring, filename_tag, 'exec')
                    except Exception as E:
                        Error = True
                        Error_Msg = 'Error: check the syntax of the source file!' + str(E).replace('\n', ' ')

                except Exception as E:
                    Error = True
                    Error_Msg = 'Error: could not read source file! ' + str(E).replace('\n', ' ')

        finally:
            return codeobject

    def SaveMarshalCode(object, filename):
        global Error_Msg
        global Error
        from time import time
        from imp import get_magic
        from marshal import dumps
        timestamp = long(time())
        try:
            codeobject = dumps(object)
            try:
                fc = open(filename, 'wb')
                fc.write('\x00\x00\x00\x00')
                fc.write(chr(timestamp & 255))
                fc.write(chr(timestamp >> 8 & 255))
                fc.write(chr(timestamp >> 16 & 255))
                fc.write(chr(timestamp >> 24 & 255))
                fc.write(codeobject)
                fc.flush()
                fc.seek(0, 0)
                fc.write(get_magic())
                fc.close()
            except Exception as E:
                Error = True
                Error_Msg = 'Error: could not write new file! ' + str(E).replace('\n', ' ')

        except Exception as E:
            Error = True
            Error_Msg = 'Error: out marshal-code is not valid! ' + str(E).replace('\n', ' ')

    def Obfuscator(obj, code, level=0):
        new_co_consts = []
        for const in code.co_consts:
            if type(const) is CodeType:
                new_const = obj(obj, const, level + 1)
            else:
                new_const = const
            new_co_consts.append(new_const)

        Crypter = Analizator(code)
        Crypter.RepAllJumpForwardOnAbsolute()
        if level == 0:
            Crypter.Obfuscate(Crypter.ConvAllJumpRelToAbsolute(), True, True, True)
        else:
            Crypter.Obfuscate(Crypter.ConvAllJumpRelToAbsolute())
        Crypter.RepAllJumpAbsoluteOnForward(True)
        return type(code)(code.co_argcount, code.co_nlocals, code.co_stacksize, code.co_flags, Crypter.BuildCoCode(), tuple(new_co_consts), code.co_names, code.co_varnames, code.co_filename, code.co_name, 1, '', code.co_freevars, code.co_cellvars)

    from os import path, rename, remove
    _, filename_tag = path.split(filename)
    filename_tag, _ = path.splitext(filename_tag)
    ByteCode = CompileMarshalCode(filename, filename_tag, temp_filename)
    if ByteCode is not None:
        try:
            ObfuscateCode = Obfuscator(Obfuscator, ByteCode)
            ObfuscateCode = type(ObfuscateCode)(ObfuscateCode.co_argcount, ObfuscateCode.co_nlocals, ObfuscateCode.co_stacksize, ObfuscateCode.co_flags, ObfuscateCode.co_code, ObfuscateCode.co_consts, ObfuscateCode.co_names, ObfuscateCode.co_varnames, ObfuscateCode.co_filename, Revision, 1, '', ObfuscateCode.co_freevars, ObfuscateCode.co_cellvars)
            filename = path.splitext(filename)[0] + '.pyc'
            if path.isfile(filename):
                remove(filename)
            SaveMarshalCode(ObfuscateCode, filename)
        except Exception as E:
            Error = True
            Error_Msg = 'Error: obfuscating will not be completed! ' + str(E).replace('\n', ' ')

    elif not Error:
        Error = True
        Error_Msg = 'Error: file not consist compilation python-code!'
    if Error:
        print Error_Msg
    return


def protect(filename, lock_attr_review, exec_in_wot, use_exe_injector, create_backup):
    from random import randint, choice
    Error = False
    Error_Msg = ''
    Revision = '<pjorion_protected>'
    CC = CharsCrypter('PJO', 4)

    def SaveMarshalCode(object, filename):
        global Error_Msg
        global Error
        from time import time
        from imp import get_magic
        from marshal import dumps
        timestamp = long(time())
        try:
            codeobject = dumps(object)
            try:
                fc = open(filename, 'wb')
                fc.write('\x00\x00\x00\x00')
                fc.write(chr(timestamp & 255))
                fc.write(chr(timestamp >> 8 & 255))
                fc.write(chr(timestamp >> 16 & 255))
                fc.write(chr(timestamp >> 24 & 255))
                fc.write(codeobject)
                fc.flush()
                fc.seek(0, 0)
                fc.write(get_magic())
                fc.close()
            except Exception as E:
                Error = True
                Error_Msg = 'Error: could not write new file! ' + str(E).replace('\n', ' ')

        except Exception as E:
            Error = True
            Error_Msg = 'Error: out marshal-code is not valid! ' + str(E).replace('\n', ' ')

    def CreateRandomString(length=10, shortrange=True):
        symbols = list(xrange(0, 32)) if shortrange else list(xrange(0, 255))
        key = ''
        while len(key) < length:
            key += chr(choice(symbols))

        return key

    from __builtin__ import compile
    from new import function
    LoaderMainFunction = 'def LoaderMainFunction():\t\t\t' + '\n' + '\tdef PJO0000(PJO0001):\t\t\t' + '\n' + '\t\tPJO0003 = ' + CC.GK(3) + '\n' + '\t\tPJO0004 = ' + CC.XK(4, 3, True) + '\n' + '\t\tPJO0005 = ' + CC.XK(5, 3, True) + '\n' + '\t\tPJO0006 = ' + CC.XK(6, 3, True) + '\n' + '\t\tPJO0010 = chr\t ' + '\n' + '\t\tPJO0016 = eval\t' + '\n' + '\t\tPJO0023 = map\t ' + '\n' + '\t\tPJO0002 = PJO0016(PJO0010(' + CC.XRC('g') + ')+PJO0010(' + CC.XRC('e') + ')+PJO0010(' + CC.XRC('t') + ')+PJO0010(' + CC.XRC('a') + ')+PJO0010(' + CC.XRC('t') + ')+PJO0010(' + CC.XRC('t') + ')+PJO0010(' + CC.XRC('r') + '))   ' + '\n' + '\t\tPJO0024 = PJO0010(' + CC.XRC('j') + ')+PJO0010(' + CC.XRC('o') + ')+PJO0010(' + CC.XRC('i') + ')+PJO0010(' + CC.XRC('n') + ')   ' + '\n' + '\t\tPJO0011 = PJO0016(PJO0002("",PJO0024)(PJO0023(PJO0010,[' + CC.XRC('t') + ',' + CC.XRC('y') + ',' + CC.XRC('p') + ',' + CC.XRC('e') + '])))   ' + '\n' + '\t\tPJO0019 = PJO0016(PJO0002("",PJO0024)(PJO0023(PJO0010,[' + CC.XRC('_') + ',' + CC.XRC('_') + ',' + CC.XRC('i') + ',' + CC.XRC('m') + ',' + CC.XRC('p') + ',' + CC.XRC('o') + ',' + CC.XRC('r') + ',' + CC.XRC('t') + ',' + CC.XRC('_') + ',' + CC.XRC('_') + '])))   ' + '\n' + '\t\tPJO0021 = PJO0019(PJO0002("",PJO0024)(PJO0023(PJO0010,[' + CC.XRC('t') + ',' + CC.XRC('y') + ',' + CC.XRC('p') + ',' + CC.XRC('e') + ',' + CC.XRC('s') + '])))\t\t\t\t  ' + '\n' + '\t\tPJO0022 = PJO0002("",PJO0024)(PJO0023(PJO0010,[' + CC.XRC('B') + ',' + CC.XRC('u') + ',' + CC.XRC('i') + ',' + CC.XRC('l') + ',' + CC.XRC('t') + ',' + CC.XRC('i') + ',' + CC.XRC('n') + ',' + CC.XRC('F') + ',' + CC.XRC('u') + ',' + CC.XRC('n') + ',' + CC.XRC('c') + ',' + CC.XRC('t') + ',' + CC.XRC('i') + ',' + CC.XRC('o') + ',' + CC.XRC('n') + ',' + CC.XRC('T') + ',' + CC.XRC('y') + ',' + CC.XRC('p') + ',' + CC.XRC('e') + ']))   ' + '\n' + '\t\tPJO0026 = PJO0002("",PJO0024)(PJO0023(PJO0010,[' + CC.XRC('b') + ',' + CC.XRC('u') + ',' + CC.XRC('i') + ',' + CC.XRC('l') + ',' + CC.XRC('t') + ',' + CC.XRC('i') + ',' + CC.XRC('n') + ',' + CC.XRC('_') + ',' + CC.XRC('f') + ',' + CC.XRC('u') + ',' + CC.XRC('n') + ',' + CC.XRC('c') + ',' + CC.XRC('t') + ',' + CC.XRC('i') + ',' + CC.XRC('o') + ',' + CC.XRC('n') + ',' + CC.XRC('_') + ',' + CC.XRC('o') + ',' + CC.XRC('r') + ',' + CC.XRC('_') + ',' + CC.XRC('m') + ',' + CC.XRC('e') + ',' + CC.XRC('t') + ',' + CC.XRC('h') + ',' + CC.XRC('o') + ',' + CC.XRC('d') + ']))' + '\n' + '\t\tif PJO0026 in ((PJO0010(' + CC.XRC('%') + ')+PJO0010(' + CC.XRC('s') + ')) % PJO0002(PJO0021, PJO0022)):   ' + '\n' + '\t\t\tif PJO0011(PJO0002) == PJO0011(PJO0010) == PJO0011(PJO0016) == PJO0011(PJO0023) == PJO0011(PJO0019) == PJO0002(PJO0021, PJO0022):\t ' + '\n'
    Checking_Rotators = ['PJO0002("",PJO0024)(PJO0023(PJO0010,[' + CC.XRC('_') + ',' + CC.XRC('_') + ',' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('d') + ',' + CC.XRC('e') + ',' + CC.XRC('_') + ',' + CC.XRC('_') + ']))',
     'PJO0002("",PJO0024)(PJO0023(PJO0010,[' + CC.XRC('f') + ',' + CC.XRC('u') + ',' + CC.XRC('n') + ',' + CC.XRC('c') + ',' + CC.XRC('_') + ',' + CC.XRC('c') + ',' + CC.XRC('l') + ',' + CC.XRC('o') + ',' + CC.XRC('s') + ',' + CC.XRC('u') + ',' + CC.XRC('r') + ',' + CC.XRC('e') + ']))',
     'PJO0002("",PJO0024)(PJO0023(PJO0010,[' + CC.XRC('f') + ',' + CC.XRC('u') + ',' + CC.XRC('n') + ',' + CC.XRC('c') + ',' + CC.XRC('_') + ',' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('d') + ',' + CC.XRC('e') + ']))',
     'PJO0002("",PJO0024)(PJO0023(PJO0010,[' + CC.XRC('f') + ',' + CC.XRC('u') + ',' + CC.XRC('n') + ',' + CC.XRC('c') + ',' + CC.XRC('_') + ',' + CC.XRC('d') + ',' + CC.XRC('e') + ',' + CC.XRC('f') + ',' + CC.XRC('a') + ',' + CC.XRC('u') + ',' + CC.XRC('l') + ',' + CC.XRC('t') + ',' + CC.XRC('s') + ']))',
     'PJO0002("",PJO0024)(PJO0023(PJO0010,[' + CC.XRC('f') + ',' + CC.XRC('u') + ',' + CC.XRC('n') + ',' + CC.XRC('c') + ',' + CC.XRC('_') + ',' + CC.XRC('d') + ',' + CC.XRC('i') + ',' + CC.XRC('c') + ',' + CC.XRC('t') + ']))',
     'PJO0002("",PJO0024)(PJO0023(PJO0010,[' + CC.XRC('f') + ',' + CC.XRC('u') + ',' + CC.XRC('n') + ',' + CC.XRC('c') + ',' + CC.XRC('_') + ',' + CC.XRC('d') + ',' + CC.XRC('o') + ',' + CC.XRC('c') + ']))',
     'PJO0002("",PJO0024)(PJO0023(PJO0010,[' + CC.XRC('f') + ',' + CC.XRC('u') + ',' + CC.XRC('n') + ',' + CC.XRC('c') + ',' + CC.XRC('_') + ',' + CC.XRC('g') + ',' + CC.XRC('l') + ',' + CC.XRC('o') + ',' + CC.XRC('b') + ',' + CC.XRC('a') + ',' + CC.XRC('l') + ',' + CC.XRC('s') + ']))',
     'PJO0002("",PJO0024)(PJO0023(PJO0010,[' + CC.XRC('f') + ',' + CC.XRC('u') + ',' + CC.XRC('n') + ',' + CC.XRC('c') + ',' + CC.XRC('_') + ',' + CC.XRC('n') + ',' + CC.XRC('a') + ',' + CC.XRC('m') + ',' + CC.XRC('e') + ']))']
    Checking_Rotators_Position = []
    while len(Checking_Rotators_Position) < 6:
        Checking_Rotators_Position.append(randint(0, len(Checking_Rotators) - 1))

    LoaderMainFunction += '\t\t\t\ttry:\t\t\t\t\t\t\t   ' + '\n' + '\t\t\t\t\tPJO0002(PJO0002,' + Checking_Rotators[Checking_Rotators_Position[0]] + ')\t   ' + '\n' + '\t\t\t\texcept:\t\t\t\t\t\t\t' + '\n' + '\t\t\t\t\ttry:\t\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\tPJO0002(PJO0010,' + Checking_Rotators[Checking_Rotators_Position[1]] + ')\t ' + '\n' + '\t\t\t\t\texcept:\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\ttry:\t\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\t\tPJO0002(PJO0016,' + Checking_Rotators[Checking_Rotators_Position[2]] + ')\t ' + '\n' + '\t\t\t\t\t\texcept:\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\t\ttry:\t\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\t\t\tPJO0002(PJO0023,' + Checking_Rotators[Checking_Rotators_Position[3]] + ')\t ' + '\n' + '\t\t\t\t\t\t\texcept:\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\t\t\ttry:\t\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\t\t\t\tPJO0002(PJO0011,' + Checking_Rotators[Checking_Rotators_Position[4]] + ')\t ' + '\n' + '\t\t\t\t\t\t\t\texcept:\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\t\t\t\tPJO0012 = PJO0016(PJO0010(' + CC.XRC('l') + ')+PJO0010(' + CC.XRC('e') + ')+PJO0010(' + CC.XRC('n') + '))   ' + '\n' + '\t\t\t\t\t\t\t\t\tPJO0013 = PJO0016(PJO0010(' + CC.XRC('s') + ')+PJO0010(' + CC.XRC('t') + ')+PJO0010(' + CC.XRC('r') + '))   ' + '\n' + '\t\t\t\t\t\t\t\t\tPJO0014 = PJO0016(PJO0002("",PJO0024)(PJO0023(PJO0010,[' + CC.XRC('g') + ',' + CC.XRC('l') + ',' + CC.XRC('o') + ',' + CC.XRC('b') + ',' + CC.XRC('a') + ',' + CC.XRC('l') + ',' + CC.XRC('s') + '])))   ' + '\n' + '\t\t\t\t\t\t\t\t\tPJO0007 = PJO0002("",PJO0024)(PJO0023(PJO0010,[' + CC.XRC('f') + ',' + CC.XRC('u') + ',' + CC.XRC('n') + ',' + CC.XRC('c') + ',' + CC.XRC('_') + ',' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('d') + ',' + CC.XRC('e') + ']))\t' + '\n' + '\t\t\t\t\t\t\t\t\tPJO0008 = PJO0002("",PJO0024)(PJO0023(PJO0010,[' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('_') + ',' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('n') + ',' + CC.XRC('s') + ',' + CC.XRC('t') + ',' + CC.XRC('s') + ']))\t' + '\n' + '\t\t\t\t\t\t\t\t\tPJO0009 = PJO0002("",PJO0024)(PJO0023(PJO0010,[' + CC.XRC('f') + ',' + CC.XRC('u') + ',' + CC.XRC('n') + ',' + CC.XRC('c') + ',' + CC.XRC('_') + ',' + CC.XRC('g') + ',' + CC.XRC('l') + ',' + CC.XRC('o') + ',' + CC.XRC('b') + ',' + CC.XRC('a') + ',' + CC.XRC('l') + ',' + CC.XRC('s') + ']))\t ' + '\n'
    LoaderMainFunction += '\t\t\t\t\t\t\t\t\tPJO0015 = PJO0016(PJO0002("",PJO0024)(PJO0023(PJO0010,[' + CC.XRC('N') + ',' + CC.XRC('o') + ',' + CC.XRC('n') + ',' + CC.XRC('e') + '])))   ' + '\n' + '\t\t\t\t\t\t\t\t\texec PJO0011(PJO0001)(PJO0002(PJO0002(PJO0001, PJO0007), PJO0008)[-PJO0012(PJO0013(PJO0012(PJO0013(PJO0012(PJO0002(PJO0002(PJO0001, PJO0007), PJO0008)))))+PJO0013(PJO0012(PJO0013(PJO0012(PJO0002(PJO0002(PJO0001, PJO0007), PJO0008))))))],\\' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t   PJO0002(PJO0001, PJO0009))\\' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t (PJO0011(PJO0001)(PJO0002(PJO0002(PJO0001, PJO0007), PJO0008)[-PJO0012(PJO0013(PJO0012(PJO0013(PJO0012(PJO0002(PJO0002(PJO0001, PJO0007), PJO0008)))))+PJO0013(PJO0012(PJO0013(PJO0012(PJO0002(PJO0002(PJO0001, PJO0007), PJO0008))))))],\\' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t   PJO0002(PJO0001, PJO0009)),\\' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t  PJO0002(PJO0002(PJO0001, PJO0007), PJO0008)[-PJO0012(PJO0013(PJO0012(PJO0013(PJO0012(PJO0002(PJO0002(PJO0001, PJO0007), PJO0008))))))],\\' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t  PJO0015) in PJO0014() ' + '\n' if not exec_in_wot else '\t\t\t\t\t\t\t\t\tPJO0017 = PJO0002("",PJO0024)(PJO0023(PJO0010,[' + CC.XRC('B') + ',' + CC.XRC('i') + ',' + CC.XRC('g') + ',' + CC.XRC('W') + ',' + CC.XRC('o') + ',' + CC.XRC('r') + ',' + CC.XRC('l') + ',' + CC.XRC('d') + ']))   ' + '\n' + '\t\t\t\t\t\t\t\t\tPJO0018 = PJO0002("",PJO0024)(PJO0023(PJO0010,[' + CC.XRC('p') + ',' + CC.XRC('l') + ',' + CC.XRC('a') + ',' + CC.XRC('y') + ',' + CC.XRC('e') + ',' + CC.XRC('r') + ']))   ' + '\n' + '\t\t\t\t\t\t\t\t\tPJO0020 = PJO0019(PJO0017)\t\t\t\t  ' + '\n' + '\t\t\t\t\t\t\t\t\tPJO0025 = PJO0002("",PJO0024)(PJO0023(PJO0010,[' + CC.XRC('M') + ',' + CC.XRC('o') + ',' + CC.XRC('d') + ',' + CC.XRC('u') + ',' + CC.XRC('l') + ',' + CC.XRC('e') + ',' + CC.XRC('T') + ',' + CC.XRC('y') + ',' + CC.XRC('p') + ',' + CC.XRC('e') + ']))   ' + '\n' + '\t\t\t\t\t\t\t\t\tPJO0026 = PJO0002("",PJO0024)(PJO0023(PJO0010,[' + CC.XRC('m') + ',' + CC.XRC('o') + ',' + CC.XRC('d') + ',' + CC.XRC('u') + ',' + CC.XRC('l') + ',' + CC.XRC('e') + ']))   ' + '\n' + '\t\t\t\t\t\t\t\t\tif PJO0026 in ((PJO0010(' + CC.XRC('%') + ')+PJO0010(' + CC.XRC('s') + ')) % PJO0002(PJO0021, PJO0025)):   ' + '\n' + '\t\t\t\t\t\t\t\t\t\tif PJO0011(PJO0020) == PJO0002(PJO0021, PJO0025):\t ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\tif PJO0011(PJO0002(PJO0020, PJO0018)) == PJO0002(PJO0021, PJO0022):\t ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\ttry:\t\t\t\t\t\t\t\t\t\t\t' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0002(PJO0002(PJO0020, PJO0018),' + Checking_Rotators[Checking_Rotators_Position[5]] + ')  ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\texcept:\t\t\t\t\t\t\t\t\t\t ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\texec PJO0011(PJO0001)(PJO0002(PJO0002(PJO0001, PJO0007), PJO0008)[-PJO0012(PJO0013(PJO0012(PJO0013(PJO0012(PJO0002(PJO0002(PJO0001, PJO0007), PJO0008)))))+PJO0013(PJO0012(PJO0013(PJO0012(PJO0002(PJO0002(PJO0001, PJO0007), PJO0008))))))],\\' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t  PJO0002(PJO0001, PJO0009))\\' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t (PJO0011(PJO0001)(PJO0002(PJO0002(PJO0001, PJO0007), PJO0008)[-PJO0012(PJO0013(PJO0012(PJO0013(PJO0012(PJO0002(PJO0002(PJO0001, PJO0007), PJO0008)))))+PJO0013(PJO0012(PJO0013(PJO0012(PJO0002(PJO0002(PJO0001, PJO0007), PJO0008))))))],\\' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t   PJO0002(PJO0001, PJO0009)),\\' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t  PJO0002(PJO0002(PJO0001, PJO0007), PJO0008)[-PJO0012(PJO0013(PJO0012(PJO0013(PJO0012(PJO0002(PJO0002(PJO0001, PJO0007), PJO0008))))))],\\' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t  PJO0002(PJO0020, PJO0018)()) in PJO0014() ' + '\n'
    LoaderMainFunction += '\ttry:\t\t\t\t\t\t\t   ' + '\n' + '\t\tPJO0000(PJO0000)\t\t\t   ' + '\n' + '\tfinally:\t\t\t\t\t\t   ' + '\n' + '\t\tdel PJO0000\t\t\t\t\t'
    LoaderMainFunction = compile(LoaderMainFunction, '', 'exec')
    LoaderMainFunction = function(LoaderMainFunction.co_consts[0], globals())
    Key_Rotators = [['key = key[len(key)//len(key):]+key[:len(key)//len(key)]', 'PJO0122 = PJO0122[PJO0148(PJO0122)//PJO0148(PJO0122):]+PJO0122[:PJO0148(PJO0122)//PJO0148(PJO0122)]'],
     ['key = key[-len(key)//len(key):]+key[:-len(key)//len(key)]', 'PJO0122 = PJO0122[-PJO0148(PJO0122)//PJO0148(PJO0122):]+PJO0122[:-PJO0148(PJO0122)//PJO0148(PJO0122)]'],
     ['key = key[::-len(key)//len(key)]', 'PJO0122 = PJO0122[::-PJO0148(PJO0122)//PJO0148(PJO0122)]'],
     ['key = key[len(key)%len(key)::len(str(-len(key)//len(key)))]+key[len(key)//len(key)::len(str(-len(key)//len(key)))]', 'PJO0122 = PJO0122[PJO0148(PJO0122)-PJO0148(PJO0122)::PJO0148(PJO0187(-PJO0148(PJO0122)//PJO0148(PJO0122)))]+PJO0122[PJO0148(PJO0122)//PJO0148(PJO0122)::PJO0148(PJO0187(-PJO0148(PJO0122)//PJO0148(PJO0122)))]'],
     ['key = key[len(key)//len(key)::len(str(-len(key)//len(key)))]+key[len(key)%len(key)::len(str(-len(key)//len(key)))]', 'PJO0122 = PJO0122[PJO0148(PJO0122)//PJO0148(PJO0122)::PJO0148(PJO0187(-PJO0148(PJO0122)//PJO0148(PJO0122)))]+PJO0122[PJO0148(PJO0122)-PJO0148(PJO0122)::PJO0148(PJO0187(-PJO0148(PJO0122)//PJO0148(PJO0122)))]'],
     ['key = key[len(key)%len(key)::len(str(-len(key)//len(key)))][::-len(key)//len(key)]+key[len(key)//len(key)::len(str(-len(key)//len(key)))]', 'PJO0122 = PJO0122[PJO0148(PJO0122)-PJO0148(PJO0122)::PJO0148(PJO0187(-PJO0148(PJO0122)//PJO0148(PJO0122)))][::-PJO0148(PJO0122)//PJO0148(PJO0122)]+PJO0122[PJO0148(PJO0122)//PJO0148(PJO0122)::PJO0148(PJO0187(-PJO0148(PJO0122)//PJO0148(PJO0122)))]'],
     ['key = key[len(key)%len(key)::len(str(-len(key)//len(key)))]+key[len(key)//len(key)::len(str(-len(key)//len(key)))][::-len(key)//len(key)]', 'PJO0122 = PJO0122[PJO0148(PJO0122)-PJO0148(PJO0122)::PJO0148(PJO0187(-PJO0148(PJO0122)//PJO0148(PJO0122)))]+PJO0122[PJO0148(PJO0122)//PJO0148(PJO0122)::PJO0148(PJO0187(-PJO0148(PJO0122)//PJO0148(PJO0122)))][::-PJO0148(PJO0122)//PJO0148(PJO0122)]'],
     ['key = key[len(key)//len(key)::len(str(-len(key)//len(key)))][::-len(key)//len(key)]+key[len(key)%len(key)::len(str(-len(key)//len(key)))]', 'PJO0122 = PJO0122[PJO0148(PJO0122)//PJO0148(PJO0122)::PJO0148(PJO0187(-PJO0148(PJO0122)//PJO0148(PJO0122)))][::-PJO0148(PJO0122)//PJO0148(PJO0122)]+PJO0122[PJO0148(PJO0122)-PJO0148(PJO0122)::PJO0148(PJO0187(-PJO0148(PJO0122)//PJO0148(PJO0122)))]'],
     ['key = key[len(key)//len(key)::len(str(-len(key)//len(key)))]+key[len(key)%len(key)::len(str(-len(key)//len(key)))][::-len(key)//len(key)]', 'PJO0122 = PJO0122[PJO0148(PJO0122)//PJO0148(PJO0122)::PJO0148(PJO0187(-PJO0148(PJO0122)//PJO0148(PJO0122)))]+PJO0122[PJO0148(PJO0122)-PJO0148(PJO0122)::PJO0148(PJO0187(-PJO0148(PJO0122)//PJO0148(PJO0122)))][::-PJO0148(PJO0122)//PJO0148(PJO0122)]']]
    Rotators_Position = []
    while len(Rotators_Position) < 12:
        Rotators_Position.append(randint(0, len(Key_Rotators) - 1))

    Obfuscator = 'def Obfuscator(obj, code, key):\t\t\t\t\t\t' + '\n' + '\tfrom types import CodeType, StringType, TupleType, IntType  ' + '\n' + '\tfrom itertools import izip, cycle\t\t\t\t  ' + '\n'
    Standart_List = ['\tnew_co_code="".join(map(chr,[x^y for (x,y) in izip(map(ord,code.co_code), cycle(map(ord,key)))])) ' + '\n' + '\t' + Key_Rotators[Rotators_Position[0]][0] + '\n',
     '\tnew_co_consts = []\t\t\t\t\t\t\t\t\t ' + '\n' + '\tfor const in code.co_consts:\t\t\t\t\t\t  ' + '\n' + '\t\tif type(const) is TupleType:\t\t\t\t\t\t ' + '\n' + '\t\t\tnew_const = []\t\t\t\t\t\t\t\t\t  ' + '\n' + '\t\t\tfor item in const:\t\t\t\t\t\t\t\t\t' + '\n' + '\t\t\t\tif type(item) is IntType:\t\t\t\t\t\t' + '\n' + '\t\t\t\t\tnew_item = item ^ ord(key[0])\t\t\t\t\t ' + '\n' + '\t\t\t\t\t' + Key_Rotators[Rotators_Position[1]][0] + '\n' + '\t\t\t\telif type(item) is StringType:\t\t\t\t\t\t' + '\n' + '\t\t\t\t\tnew_item="".join(map(chr,[x^y for (x,y) in izip(map(ord,item), cycle(map(ord,key)))])) ' + '\n' + '\t\t\t\t\t' + Key_Rotators[Rotators_Position[2]][0] + '\n' + '\t\t\t\telse:\t\t\t\t\t\t\t\t\t\t\t   ' + '\n' + '\t\t\t\t\tnew_item = item\t\t\t\t\t\t\t' + '\n' + '\t\t\t\tnew_const.append(new_item)\t\t\t\t\t\t' + '\n' + '\t\t\tnew_const = tuple(new_const)\t\t\t\t\t\t' + '\n' + '\t\telif type(const) is CodeType:\t\t\t\t\t\t\t ' + '\n' + '\t\t\tnew_const = obj(obj, const, key)\t\t\t\t   ' + '\n' + '\t\telif type(const) is IntType:\t\t\t\t\t\t' + '\n' + '\t\t\tnew_const = const ^ ord(key[-1])\t\t\t\t\t ' + '\n' + '\t\t\t' + Key_Rotators[Rotators_Position[3]][0] + '\n' + '\t\telif type(const) is StringType:\t\t\t\t\t\t' + '\n' + '\t\t\tnew_const="".join(map(chr,[x^y for (x,y) in izip(map(ord,const), cycle(map(ord,key)))])) ' + '\n' + '\t\t\t' + Key_Rotators[Rotators_Position[4]][0] + '\n' + '\t\telse:\t\t\t\t\t\t\t\t\t\t\t\t   ' + '\n' + '\t\t\tnew_const = const\t\t\t\t\t\t\t\t\t' + '\n' + '\t\tnew_co_consts.append(new_const)\t\t\t\t\t\t  ' + '\n',
     '\tnew_co_names = []\t\t\t\t\t\t\t\t\t\t\t' + '\n' + '\tfor name in code.co_names:\t\t\t\t\t\t\t\t   ' + '\n' + '\t\tif type(name) is StringType:\t\t\t\t\t\t\t ' + '\n' + '\t\t\tnew_name="".join(map(chr,[x^y for (x,y) in izip(map(ord,name), cycle(map(ord,key)))])) ' + '\n' + '\t\t\t' + Key_Rotators[Rotators_Position[5]][0] + '\n' + '\t\telse:\t\t\t\t\t\t\t\t\t\t\t\t\t ' + '\n' + '\t\t\tnew_name = name\t\t\t\t\t\t\t\t\t   ' + '\n' + '\t\tnew_co_names.append(new_name)\t\t\t\t\t\t\t ' + '\n',
     '\tnew_co_varnames = []\t\t\t\t\t\t\t\t\t\t  ' + '\n' + '\tfor varname in code.co_varnames:\t\t\t\t\t\t\t  ' + '\n' + '\t\tif type(varname) is StringType:\t\t\t\t\t\t   ' + '\n' + '\t\t\tnew_varname="".join(map(chr,[x^y for (x,y) in izip(map(ord,varname), cycle(map(ord,key)))])) ' + '\n' + '\t\t\t' + Key_Rotators[Rotators_Position[6]][0] + '\n' + '\t\telse:\t\t\t\t\t\t\t\t\t\t\t\t\t\t' + '\n' + '\t\t\tnew_varname = varname\t\t\t\t\t\t\t\t\t' + '\n' + '\t\tnew_co_varnames.append(new_varname)\t\t\t\t\t\t ' + '\n',
     '\tnew_co_filename="".join(map(chr,[x^y for (x,y) in izip(map(ord,code.co_filename), cycle(map(ord,key)))])) ' + '\n' + '\t' + Key_Rotators[Rotators_Position[7]][0] + '\n',
     '\tnew_co_name="".join(map(chr,[x^y for (x,y) in izip(map(ord,code.co_name), cycle(map(ord,key)))])) ' + '\n' + '\t' + Key_Rotators[Rotators_Position[8]][0] + '\n',
     '\tnew_co_lnotab="".join(map(chr,[x^y for (x,y) in izip(map(ord,code.co_lnotab), cycle(map(ord,key)))])) ' + '\n' + '\t' + Key_Rotators[Rotators_Position[9]][0] + '\n',
     '\tnew_co_freevars = []\t\t\t\t\t\t\t\t\t\t\t ' + '\n' + '\tfor freevar in code.co_freevars:\t\t\t\t\t\t\t\t' + '\n' + '\t\tif type(freevar) is StringType:\t\t\t\t\t\t\t ' + '\n' + '\t\t\tnew_freevar="".join(map(chr,[x^y for (x,y) in izip(map(ord,freevar), cycle(map(ord,key)))])) ' + '\n' + '\t\t\t' + Key_Rotators[Rotators_Position[10]][0] + '\n' + '\t\telse:\t\t\t\t\t\t\t\t\t\t\t\t\t\t' + '\n' + '\t\t\tnew_freevar = freevar\t\t\t\t\t\t\t\t\t' + '\n' + '\t\tnew_co_freevars.append(new_freevar)\t\t\t\t\t\t   ' + '\n',
     '\tnew_co_cellvars = []\t\t\t\t\t\t\t\t\t\t\t' + '\n' + '\tfor cellvar in code.co_cellvars:\t\t\t\t\t\t\t   ' + '\n' + '\t\tif type(cellvar) is StringType:\t\t\t\t\t\t\t  ' + '\n' + '\t\t\tnew_cellvar="".join(map(chr,[x^y for (x,y) in izip(map(ord,cellvar), cycle(map(ord,key)))])) ' + '\n' + '\t\t\t' + Key_Rotators[Rotators_Position[11]][0] + '\n' + '\t\telse:\t\t\t\t\t\t\t\t\t\t\t\t\t\t' + '\n' + '\t\t\tnew_cellvar = cellvar\t\t\t\t\t\t\t\t\t ' + '\n' + '\t\tnew_co_cellvars.append(new_cellvar)\t\t\t\t\t\t ' + '\n']
    Blocks_Positions = []
    Interation_List = [ x for x in Standart_List ]
    while Interation_List:
        Block = choice(Interation_List)
        Obfuscator += Block
        Blocks_Positions.append(Standart_List.index(Block))
        Interation_List.remove(Block)

    Obfuscator += '\treturn type(code)(code.co_argcount, \\' + '\n' + '\t\t\t\t\t  code.co_nlocals, \\' + '\n' + '\t\t\t\t\t  code.co_stacksize, \\' + '\n' + '\t\t\t\t\t  code.co_flags, \\' + '\n' + '\t\t\t\t\t  new_co_code, \\' + '\n' + '\t\t\t\t\t  tuple(new_co_consts), \\' + '\n' + '\t\t\t\t\t  tuple(new_co_names), \\' + '\n' + '\t\t\t\t\t  tuple(new_co_varnames), \\' + '\n' + '\t\t\t\t\t  new_co_filename, \\' + '\n' + '\t\t\t\t\t  new_co_name, \\' + '\n' + '\t\t\t\t\t  code.co_firstlineno, \\' + '\n' + '\t\t\t\t\t  new_co_lnotab, \\' + '\n' + '\t\t\t\t\t  tuple(new_co_freevars), \\' + '\n' + '\t\t\t\t\t  tuple(new_co_cellvars))'
    Obfuscator = compile(Obfuscator, '', 'exec')
    Obfuscator = function(Obfuscator.co_consts[0], globals())
    CC.Clear()
    LoaderCryptFunction = 'def LoaderCryptFunction(PJO0110, PJO0111, PJO0122): #its obj, code, key\t ' + '\n' + '\tPJO0100 = ' + CC.GK(100) + '\n' + '\tPJO0101 = ' + CC.XK(101, 100, True) + '\n' + '\tPJO0102 = ' + CC.XK(102, 100, True) + '\n' + '\tPJO0103 = ' + CC.XK(103, 100, True) + '\n' + '\tPJO0104 = ' + CC.XK(104, 100, True) + '\n' + '\tPJO0105 = ' + CC.XK(105, 100, True) + '\n' + '\tPJO0106 = ' + CC.XK(106, 100, True) + '\n' + '\tPJO0107 = ' + CC.XK(107, 100, True) + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t   ' + '\n' + '\tPJO0146 = chr\t\t\t\t\t\t\t\t  ' + '\n' + '\tPJO0186 = eval\t\t\t\t\t\t\t\t ' + '\n' + '\tPJO0188 = map\t\t\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t   ' + '\n' + '\tPJO0113 = PJO0186(PJO0146(' + CC.XRC('g') + ')+PJO0146(' + CC.XRC('e') + ')+PJO0146(' + CC.XRC('t') + ')+PJO0146(' + CC.XRC('a') + ')+PJO0146(' + CC.XRC('t') + ')+PJO0146(' + CC.XRC('t') + ')+PJO0146(' + CC.XRC('r') + '))  ' + '\n' + '\tPJO0189 = PJO0146(' + CC.XRC('j') + ')+PJO0146(' + CC.XRC('o') + ')+PJO0146(' + CC.XRC('i') + ')+PJO0146(' + CC.XRC('n') + ')   ' + '\n' + '\tPJO0112 = PJO0186(PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('_') + ',' + CC.XRC('_') + ',' + CC.XRC('i') + ',' + CC.XRC('m') + ',' + CC.XRC('p') + ',' + CC.XRC('o') + ',' + CC.XRC('r') + ',' + CC.XRC('t') + ',' + CC.XRC('_') + ',' + CC.XRC('_') + '])))  ' + '\n' + '\tPJO0144 = PJO0186(PJO0146(' + CC.XRC('o') + ')+PJO0146(' + CC.XRC('r') + ')+PJO0146(' + CC.XRC('d') + '))  ' + '\n' + '\tPJO0145 = PJO0186(PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('t') + ',' + CC.XRC('y') + ',' + CC.XRC('p') + ',' + CC.XRC('e') + '])))  ' + '\n' + '\tPJO0173 = PJO0186(PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('h') + ',' + CC.XRC('a') + ',' + CC.XRC('s') + ',' + CC.XRC('h') + '])))  ' + '\n' + '\tPJO0178 = PJO0186(PJO0146(' + CC.XRC('a') + ')+PJO0146(' + CC.XRC('b') + ')+PJO0146(' + CC.XRC('s') + '))  ' + '\n' + '\tPJO0179 = PJO0186(PJO0146(' + CC.XRC('h') + ')+PJO0146(' + CC.XRC('e') + ')+PJO0146(' + CC.XRC('x') + '))  ' + '\n' + '\tPJO0114 = PJO0112(PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('t') + ',' + CC.XRC('y') + ',' + CC.XRC('p') + ',' + CC.XRC('e') + ',' + CC.XRC('s') + '])))  ' + '\n'
    Checking_Rotators = ['PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('_') + ',' + CC.XRC('_') + ',' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('d') + ',' + CC.XRC('e') + ',' + CC.XRC('_') + ',' + CC.XRC('_') + ']))',
     'PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('f') + ',' + CC.XRC('u') + ',' + CC.XRC('n') + ',' + CC.XRC('c') + ',' + CC.XRC('_') + ',' + CC.XRC('c') + ',' + CC.XRC('l') + ',' + CC.XRC('o') + ',' + CC.XRC('s') + ',' + CC.XRC('u') + ',' + CC.XRC('r') + ',' + CC.XRC('e') + ']))',
     'PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('f') + ',' + CC.XRC('u') + ',' + CC.XRC('n') + ',' + CC.XRC('c') + ',' + CC.XRC('_') + ',' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('d') + ',' + CC.XRC('e') + ']))',
     'PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('f') + ',' + CC.XRC('u') + ',' + CC.XRC('n') + ',' + CC.XRC('c') + ',' + CC.XRC('_') + ',' + CC.XRC('d') + ',' + CC.XRC('e') + ',' + CC.XRC('f') + ',' + CC.XRC('a') + ',' + CC.XRC('u') + ',' + CC.XRC('l') + ',' + CC.XRC('t') + ',' + CC.XRC('s') + ']))',
     'PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('f') + ',' + CC.XRC('u') + ',' + CC.XRC('n') + ',' + CC.XRC('c') + ',' + CC.XRC('_') + ',' + CC.XRC('d') + ',' + CC.XRC('i') + ',' + CC.XRC('c') + ',' + CC.XRC('t') + ']))',
     'PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('f') + ',' + CC.XRC('u') + ',' + CC.XRC('n') + ',' + CC.XRC('c') + ',' + CC.XRC('_') + ',' + CC.XRC('d') + ',' + CC.XRC('o') + ',' + CC.XRC('c') + ']))',
     'PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('f') + ',' + CC.XRC('u') + ',' + CC.XRC('n') + ',' + CC.XRC('c') + ',' + CC.XRC('_') + ',' + CC.XRC('g') + ',' + CC.XRC('l') + ',' + CC.XRC('o') + ',' + CC.XRC('b') + ',' + CC.XRC('a') + ',' + CC.XRC('l') + ',' + CC.XRC('s') + ']))',
     'PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('f') + ',' + CC.XRC('u') + ',' + CC.XRC('n') + ',' + CC.XRC('c') + ',' + CC.XRC('_') + ',' + CC.XRC('n') + ',' + CC.XRC('a') + ',' + CC.XRC('m') + ',' + CC.XRC('e') + ']))']
    Checking_Rotators_Position = []
    while len(Checking_Rotators_Position) < 9:
        Checking_Rotators_Position.append(randint(0, len(Checking_Rotators) - 1))

    LoaderCryptFunction += '\tPJO0184 = PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('B') + ',' + CC.XRC('u') + ',' + CC.XRC('i') + ',' + CC.XRC('l') + ',' + CC.XRC('t') + ',' + CC.XRC('i') + ',' + CC.XRC('n') + ',' + CC.XRC('F') + ',' + CC.XRC('u') + ',' + CC.XRC('n') + ',' + CC.XRC('c') + ',' + CC.XRC('t') + ',' + CC.XRC('i') + ',' + CC.XRC('o') + ',' + CC.XRC('n') + ',' + CC.XRC('T') + ',' + CC.XRC('y') + ',' + CC.XRC('p') + ',' + CC.XRC('e') + ']))   ' + '\n' + '\tPJO0185 = PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('b') + ',' + CC.XRC('u') + ',' + CC.XRC('i') + ',' + CC.XRC('l') + ',' + CC.XRC('t') + ',' + CC.XRC('i') + ',' + CC.XRC('n') + ',' + CC.XRC('_') + ',' + CC.XRC('f') + ',' + CC.XRC('u') + ',' + CC.XRC('n') + ',' + CC.XRC('c') + ',' + CC.XRC('t') + ',' + CC.XRC('i') + ',' + CC.XRC('o') + ',' + CC.XRC('n') + ',' + CC.XRC('_') + ',' + CC.XRC('o') + ',' + CC.XRC('r') + ',' + CC.XRC('_') + ',' + CC.XRC('m') + ',' + CC.XRC('e') + ',' + CC.XRC('t') + ',' + CC.XRC('h') + ',' + CC.XRC('o') + ',' + CC.XRC('d') + ']))' + '\n' + '\tif PJO0185 in ((PJO0146(' + CC.XRC('%') + ')+PJO0146(' + CC.XRC('s') + ')) % PJO0113(PJO0114, PJO0184)):   ' + '\n' + '\t\tif PJO0145(PJO0113) == PJO0145(PJO0146) == PJO0145(PJO0186) == PJO0145(PJO0188) == PJO0145(PJO0144) == PJO0145(PJO0173) == PJO0145(PJO0178) == PJO0145(PJO0179) == PJO0145(PJO0112) == PJO0113(PJO0114, PJO0184):\t ' + '\n' + '\t\t\ttry:\t\t\t\t\t\t\t   ' + '\n' + '\t\t\t\tPJO0113(PJO0113,' + Checking_Rotators[Checking_Rotators_Position[0]] + ')\t   ' + '\n' + '\t\t\texcept:\t\t\t\t\t\t\t' + '\n' + '\t\t\t\ttry:\t\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\tPJO0113(PJO0146,' + Checking_Rotators[Checking_Rotators_Position[1]] + ')\t ' + '\n' + '\t\t\t\texcept:\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\ttry:\t\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\tPJO0113(PJO0186,' + Checking_Rotators[Checking_Rotators_Position[2]] + ')\t ' + '\n' + '\t\t\t\t\texcept:\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\ttry:\t\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\t\tPJO0113(PJO0188,' + Checking_Rotators[Checking_Rotators_Position[3]] + ')\t ' + '\n' + '\t\t\t\t\t\texcept:\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\t\ttry:\t\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\t\t\tPJO0113(PJO0144,' + Checking_Rotators[Checking_Rotators_Position[4]] + ')\t ' + '\n' + '\t\t\t\t\t\t\texcept:\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\t\t\ttry:\t\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\t\t\t\tPJO0113(PJO0173,' + Checking_Rotators[Checking_Rotators_Position[5]] + ')\t ' + '\n' + '\t\t\t\t\t\t\t\texcept:\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\t\t\t\ttry:\t\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\t\t\t\t\tPJO0113(PJO0178,' + Checking_Rotators[Checking_Rotators_Position[6]] + ')\t ' + '\n' + '\t\t\t\t\t\t\t\t\texcept:\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\t\t\t\t\ttry:\t\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\tPJO0113(PJO0179,' + Checking_Rotators[Checking_Rotators_Position[7]] + ')\t ' + '\n' + '\t\t\t\t\t\t\t\t\t\texcept:\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\ttry:\t\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tPJO0113(PJO0145,' + Checking_Rotators[Checking_Rotators_Position[8]] + ')\t ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\texcept:\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tPJO0115 = PJO0113(PJO0114, PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('C') + ',' + CC.XRC('o') + ',' + CC.XRC('d') + ',' + CC.XRC('e') + ',' + CC.XRC('T') + ',' + CC.XRC('y') + ',' + CC.XRC('p') + ',' + CC.XRC('e') + '])))  ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tPJO0116 = PJO0113(PJO0114, PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('S') + ',' + CC.XRC('t') + ',' + CC.XRC('r') + ',' + CC.XRC('i') + ',' + CC.XRC('n') + ',' + CC.XRC('g') + ',' + CC.XRC('T') + ',' + CC.XRC('y') + ',' + CC.XRC('p') + ',' + CC.XRC('e') + '])))  ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tPJO0181 = PJO0113(PJO0114, PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('T') + ',' + CC.XRC('u') + ',' + CC.XRC('p') + ',' + CC.XRC('l') + ',' + CC.XRC('e') + ',' + CC.XRC('T') + ',' + CC.XRC('y') + ',' + CC.XRC('p') + ',' + CC.XRC('e') + '])))  ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tPJO0190 = PJO0113(PJO0114, PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('I') + ',' + CC.XRC('n') + ',' + CC.XRC('t') + ',' + CC.XRC('T') + ',' + CC.XRC('y') + ',' + CC.XRC('p') + ',' + CC.XRC('e') + '])))  ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tPJO0117 = PJO0112(PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('i') + ',' + CC.XRC('t') + ',' + CC.XRC('e') + ',' + CC.XRC('r') + ',' + CC.XRC('t') + ',' + CC.XRC('o') + ',' + CC.XRC('o') + ',' + CC.XRC('l') + ',' + CC.XRC('s') + '])))   ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tPJO0118 = PJO0113(PJO0117, PJO0146(' + CC.XRC('i') + ')+PJO0146(' + CC.XRC('z') + ')+PJO0146(' + CC.XRC('i') + ')+PJO0146(' + CC.XRC('p') + '))\t ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tPJO0119 = PJO0113(PJO0117, PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('c') + ',' + CC.XRC('y') + ',' + CC.XRC('c') + ',' + CC.XRC('l') + ',' + CC.XRC('e') + '])))   ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tPJO0148 = PJO0186(PJO0146(' + CC.XRC('l') + ')+PJO0146(' + CC.XRC('e') + ')+PJO0146(' + CC.XRC('n') + '))  ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tPJO0170 = PJO0112(PJO0146(' + CC.XRC('s') + ')+PJO0146(' + CC.XRC('y') + ')+PJO0146(' + CC.XRC('s') + '))   ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tPJO0171 = PJO0113(PJO0170, PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('_') + ',' + CC.XRC('g') + ',' + CC.XRC('e') + ',' + CC.XRC('t') + ',' + CC.XRC('f') + ',' + CC.XRC('r') + ',' + CC.XRC('a') + ',' + CC.XRC('m') + ',' + CC.XRC('e') + '])))   ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tif PJO0122 == PJO0186(PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('N') + ',' + CC.XRC('o') + ',' + CC.XRC('n') + ',' + CC.XRC('e') + ']))):\t\t  ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0120 = PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('f') + ',' + CC.XRC('u') + ',' + CC.XRC('n') + ',' + CC.XRC('c') + ',' + CC.XRC('_') + ',' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('d') + ',' + CC.XRC('e') + ']))   ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0121 = PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('_') + ',' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('n') + ',' + CC.XRC('s') + ',' + CC.XRC('t') + ',' + CC.XRC('s') + ']))\t' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0122 = ""\t\t\t' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\twhile PJO0148(PJO0122) < 10:\t\t' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0122 = PJO0146(PJO0113(PJO0113(PJO0110, PJO0120), PJO0121)[-(PJO0148(PJO0122)+1)]) + PJO0122\t   ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0174 = PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('f') + ',' + CC.XRC('_') + ',' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('d') + ',' + CC.XRC('e') + ']))\t' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0175 = PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('_') + ',' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('d') + ',' + CC.XRC('e') + ']))  ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0191 = PJO0186(PJO0146(' + CC.XRC('d') + ')+PJO0146(' + CC.XRC('i') + ')+PJO0146(' + CC.XRC('r') + '))  ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0192 = PJO0112(PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('m') + ',' + CC.XRC('a') + ',' + CC.XRC('r') + ',' + CC.XRC('s') + ',' + CC.XRC('h') + ',' + CC.XRC('a') + ',' + CC.XRC('l') + '])))   ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0193 = PJO0113(PJO0192, PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('l') + ',' + CC.XRC('o') + ',' + CC.XRC('a') + ',' + CC.XRC('d') + ',' + CC.XRC('s') + '])))   ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0172 = 0\t\t\t\t\t\t\t   ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\ttry:\t\t\t\t\t\t\t\t\t   ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\twhile PJO0172<4:\t\t\t\t\t\t ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0180 = PJO0113(PJO0113(PJO0171(PJO0172), PJO0174), PJO0175)\t\t\t\t ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0180 = PJO0180[7:(PJO0148(PJO0191(PJO0193))>>1)] if PJO0172 == 3 else PJO0180\t\t\t ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0122 = PJO0113("",PJO0189)(PJO0188(PJO0146,[PJO0124^PJO0125 for (PJO0124,PJO0125) in PJO0118(PJO0188(PJO0144,PJO0122), PJO0119(PJO0188(PJO0144,PJO0179(PJO0178(PJO0173(PJO0180)))[2:])))])) ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0172 += 1\t\t\t\t\t\t\t ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\texcept:\t\t\t\t\t\t\t\t\t   ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\tpass\t\t\t\t\t\t\t\t\t   ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tPJO0130 = PJO0113(PJO0111, PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('_') + ',' + CC.XRC('a') + ',' + CC.XRC('r') + ',' + CC.XRC('g') + ',' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('u') + ',' + CC.XRC('n') + ',' + CC.XRC('t') + '])))   ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tPJO0131 = PJO0113(PJO0111, PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('_') + ',' + CC.XRC('n') + ',' + CC.XRC('l') + ',' + CC.XRC('o') + ',' + CC.XRC('c') + ',' + CC.XRC('a') + ',' + CC.XRC('l') + ',' + CC.XRC('s') + '])))\t\t\t  ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tPJO0132 = PJO0113(PJO0111, PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('_') + ',' + CC.XRC('s') + ',' + CC.XRC('t') + ',' + CC.XRC('a') + ',' + CC.XRC('c') + ',' + CC.XRC('k') + ',' + CC.XRC('s') + ',' + CC.XRC('i') + ',' + CC.XRC('z') + ',' + CC.XRC('e') + '])))\t  ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tPJO0133 = PJO0113(PJO0111, PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('_') + ',' + CC.XRC('f') + ',' + CC.XRC('l') + ',' + CC.XRC('a') + ',' + CC.XRC('g') + ',' + CC.XRC('s') + '])))\t\t ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tPJO0134 = PJO0113(PJO0111, PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('_') + ',' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('d') + ',' + CC.XRC('e') + '])))\t\t\t' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tPJO0135 = PJO0113(PJO0111, PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('_') + ',' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('n') + ',' + CC.XRC('s') + ',' + CC.XRC('t') + ',' + CC.XRC('s') + '])))\t ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tPJO0136 = PJO0113(PJO0111, PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('_') + ',' + CC.XRC('n') + ',' + CC.XRC('a') + ',' + CC.XRC('m') + ',' + CC.XRC('e') + ',' + CC.XRC('s') + '])))   ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tPJO0137 = PJO0113(PJO0111, PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('_') + ',' + CC.XRC('v') + ',' + CC.XRC('a') + ',' + CC.XRC('r') + ',' + CC.XRC('n') + ',' + CC.XRC('a') + ',' + CC.XRC('m') + ',' + CC.XRC('e') + ',' + CC.XRC('s') + '])))\t' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tPJO0138 = PJO0113(PJO0111, PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('_') + ',' + CC.XRC('f') + ',' + CC.XRC('i') + ',' + CC.XRC('l') + ',' + CC.XRC('e') + ',' + CC.XRC('n') + ',' + CC.XRC('a') + ',' + CC.XRC('m') + ',' + CC.XRC('e') + '])))\t' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tPJO0139 = PJO0113(PJO0111, PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('_') + ',' + CC.XRC('n') + ',' + CC.XRC('a') + ',' + CC.XRC('m') + ',' + CC.XRC('e') + '])))   ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tPJO0140 = PJO0113(PJO0111, PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('_') + ',' + CC.XRC('f') + ',' + CC.XRC('i') + ',' + CC.XRC('r') + ',' + CC.XRC('s') + ',' + CC.XRC('t') + ',' + CC.XRC('l') + ',' + CC.XRC('i') + ',' + CC.XRC('n') + ',' + CC.XRC('e') + ',' + CC.XRC('n') + ',' + CC.XRC('o') + '])))   ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tPJO0141 = PJO0113(PJO0111, PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('_') + ',' + CC.XRC('l') + ',' + CC.XRC('n') + ',' + CC.XRC('o') + ',' + CC.XRC('t') + ',' + CC.XRC('a') + ',' + CC.XRC('b') + '])))\t' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tPJO0142 = PJO0113(PJO0111, PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('_') + ',' + CC.XRC('f') + ',' + CC.XRC('r') + ',' + CC.XRC('e') + ',' + CC.XRC('e') + ',' + CC.XRC('v') + ',' + CC.XRC('a') + ',' + CC.XRC('r') + ',' + CC.XRC('s') + '])))\t' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tPJO0143 = PJO0113(PJO0111, PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('_') + ',' + CC.XRC('c') + ',' + CC.XRC('e') + ',' + CC.XRC('l') + ',' + CC.XRC('l') + ',' + CC.XRC('v') + ',' + CC.XRC('a') + ',' + CC.XRC('r') + ',' + CC.XRC('s') + '])))   ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tPJO0147 = PJO0186(PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('t') + ',' + CC.XRC('u') + ',' + CC.XRC('p') + ',' + CC.XRC('l') + ',' + CC.XRC('e') + '])))  ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tPJO0149 = PJO0113("",PJO0189)(PJO0188(PJO0146,[' + CC.XRC('a') + ',' + CC.XRC('p') + ',' + CC.XRC('p') + ',' + CC.XRC('e') + ',' + CC.XRC('n') + ',' + CC.XRC('d') + ']))\t' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tPJO0187 = PJO0186(PJO0146(' + CC.XRC('s') + ')+PJO0146(' + CC.XRC('t') + ')+PJO0146(' + CC.XRC('r') + '))  ' + '\n'
    Standart_List = ['\t\t\t\t\t\t\t\t\t\t\t\tPJO0123 = PJO0113("",PJO0189)(PJO0188(PJO0146,[PJO0124^PJO0125 for (PJO0124,PJO0125) in PJO0118(PJO0188(PJO0144,PJO0134), PJO0119(PJO0188(PJO0144,PJO0122)))])) ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t' + Key_Rotators[Rotators_Position[0]][1] + '\n',
     '\t\t\t\t\t\t\t\t\t\t\t\tPJO0150 = []\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tfor PJO0151 in PJO0135:\t\t\t\t\t\t\t\t\t\t\t\t   ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\tif PJO0145(PJO0151) is PJO0181:\t\t\t\t\t\t ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0152 = []\t\t\t\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\tfor PJO0182 in PJO0151:\t\t\t\t\t\t\t\t\t' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tif PJO0145(PJO0182) is PJO0190:\t\t\t\t\t\t' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0183 = PJO0182 ^ ord(PJO0122[0])\t\t\t\t\t ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t' + Key_Rotators[Rotators_Position[1]][1] + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\telif PJO0145(PJO0182) is PJO0116:\t\t\t\t\t\t' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0183 = PJO0113("",PJO0189)(PJO0188(PJO0146,[PJO0124^PJO0125 for (PJO0124,PJO0125) in PJO0118(PJO0188(PJO0144,PJO0182), PJO0119(PJO0188(PJO0144,PJO0122)))])) ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t' + Key_Rotators[Rotators_Position[2]][1] + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\telse:\t\t\t\t\t\t\t\t\t\t\t   ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0183 = PJO0182\t\t\t\t\t\t\t' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0113(PJO0152, PJO0149)(PJO0183)\t\t\t\t\t\t' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0152 = PJO0147(PJO0152)\t\t\t\t\t\t\t ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\telif PJO0145(PJO0151) is PJO0115:\t\t\t\t\t\t\t\t\t\t' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0152 = PJO0110(PJO0110, PJO0151, PJO0122)\t\t\t\t\t\t\t   ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\telif PJO0145(PJO0151) is PJO0190:\t\t\t\t\t\t\t\t' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0152 = PJO0151 ^ ord(PJO0122[-1])\t\t\t\t\t\t ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t' + Key_Rotators[Rotators_Position[3]][1] + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\telif PJO0145(PJO0151) is PJO0116:\t\t\t\t\t\t\t\t\t   ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0152 = PJO0113("",PJO0189)(PJO0188(PJO0146,[PJO0124^PJO0125 for (PJO0124,PJO0125) in PJO0118(PJO0188(PJO0144,PJO0151), PJO0119(PJO0188(PJO0144,PJO0122)))])) ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t' + Key_Rotators[Rotators_Position[4]][1] + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\telse:\t\t\t\t\t\t\t\t\t\t\t ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0152 = PJO0151\t\t\t\t\t\t\t ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0113(PJO0150, PJO0149)(PJO0152)\t\t\t\t  ' + '\n',
     '\t\t\t\t\t\t\t\t\t\t\t\tPJO0153 = []\t\t\t\t\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tfor PJO0154 in PJO0136:\t\t\t\t\t\t\t   ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\tif PJO0145(PJO0154) is PJO0116:\t\t\t\t\t' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0155 = PJO0113("",PJO0189)(PJO0188(PJO0146,[PJO0124^PJO0125 for (PJO0124,PJO0125) in PJO0118(PJO0188(PJO0144,PJO0154), PJO0119(PJO0188(PJO0144,PJO0122)))])) ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t' + Key_Rotators[Rotators_Position[5]][1] + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\telse:\t\t\t\t\t\t\t\t\t\t\t   ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0155 = PJO0154\t\t\t\t\t\t\t\t ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0113(PJO0153, PJO0149)(PJO0155)\t\t\t\t\t' + '\n',
     '\t\t\t\t\t\t\t\t\t\t\t\tPJO0156 = []\t\t\t\t\t\t\t\t\t\t\t ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tfor PJO0157 in PJO0137:\t\t\t\t\t\t\t\t   ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\tif PJO0145(PJO0157) is PJO0116:\t\t\t\t\t   ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0158 = PJO0113("",PJO0189)(PJO0188(PJO0146,[PJO0124^PJO0125 for (PJO0124,PJO0125) in PJO0118(PJO0188(PJO0144,PJO0157), PJO0119(PJO0188(PJO0144,PJO0122)))])) ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t' + Key_Rotators[Rotators_Position[6]][1] + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\telse:\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0158 = PJO0157\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0113(PJO0156, PJO0149)(PJO0158)\t\t\t\t\t\t\t\t\t\t\t\t' + '\n',
     '\t\t\t\t\t\t\t\t\t\t\t\tPJO0159 = PJO0113("",PJO0189)(PJO0188(PJO0146,[PJO0124^PJO0125 for (PJO0124,PJO0125) in PJO0118(PJO0188(PJO0144,PJO0138), PJO0119(PJO0188(PJO0144,PJO0122)))])) ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t' + Key_Rotators[Rotators_Position[7]][1] + '\n',
     '\t\t\t\t\t\t\t\t\t\t\t\tPJO0160 = PJO0113("",PJO0189)(PJO0188(PJO0146,[PJO0124^PJO0125 for (PJO0124,PJO0125) in PJO0118(PJO0188(PJO0144,PJO0139), PJO0119(PJO0188(PJO0144,PJO0122)))])) ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t' + Key_Rotators[Rotators_Position[8]][1] + '\n',
     '\t\t\t\t\t\t\t\t\t\t\t\tPJO0161 = PJO0113("",PJO0189)(PJO0188(PJO0146,[PJO0124^PJO0125 for (PJO0124,PJO0125) in PJO0118(PJO0188(PJO0144,PJO0141), PJO0119(PJO0188(PJO0144,PJO0122)))])) ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t' + Key_Rotators[Rotators_Position[9]][1] + '\n',
     '\t\t\t\t\t\t\t\t\t\t\t\tPJO0162 = []\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t   ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tfor PJO0163 in PJO0142:\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\tif PJO0145(PJO0163) is PJO0116:\t\t\t\t\t\t\t\t\t\t\t\t\t' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0164 = PJO0113("",PJO0189)(PJO0188(PJO0146,[PJO0124^PJO0125 for (PJO0124,PJO0125) in PJO0118(PJO0188(PJO0144,PJO0163), PJO0119(PJO0188(PJO0144,PJO0122)))])) ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t' + Key_Rotators[Rotators_Position[10]][1] + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\telse:\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t   ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0164 = PJO0163\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0113(PJO0162, PJO0149)(PJO0164)\t\t\t\t\t\t\t\t\t\t\t\t   ' + '\n',
     '\t\t\t\t\t\t\t\t\t\t\t\tPJO0165 = []\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\tfor PJO0166 in PJO0143:\t\t\t\t\t\t\t\t\t\t\t\t\t\t' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\tif PJO0145(PJO0166) is PJO0116:\t\t\t\t\t\t\t\t\t\t\t ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0167 = PJO0113("",PJO0189)(PJO0188(PJO0146,[PJO0124^PJO0125 for (PJO0124,PJO0125) in PJO0118(PJO0188(PJO0144,PJO0166), PJO0119(PJO0188(PJO0144,PJO0122)))])) ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t' + Key_Rotators[Rotators_Position[11]][1] + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\telse:\t\t\t\t\t\t\t\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0167 = PJO0166\t\t\t\t\t\t\t\t\t   ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0113(PJO0165, PJO0149)(PJO0167)\t\t\t\t\t\t ' + '\n']
    for pos in Blocks_Positions:
        LoaderCryptFunction += Standart_List[pos]

    LoaderCryptFunction += '\t\t\t\t\t\t\t\t\t\t\t\treturn PJO0145(PJO0111)(PJO0130, \\' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0131, \\' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0132, \\' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0133, \\' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0123, \\' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0147(PJO0150), \\' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0147(PJO0153), \\' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0147(PJO0156), \\' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0159, \\' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0160, \\' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0140, \\' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0161, \\' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0147(PJO0162), \\' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\tPJO0147(PJO0165))' + '\n' + '\treturn PJO0111'
    LoaderCryptFunction = compile(LoaderCryptFunction, '', 'exec')
    LoaderCryptFunction = function(LoaderCryptFunction.co_consts[0], globals())
    CC.Clear()
    if lock_attr_review:
        Wrapper = 'def PJO0000():\t' + '\n' + '\tpass\t\t  ' + '\n' + 'def PJO0001(PJO0002):\t\t\t\t\t\t\t\t' + '\n' + '\tPJO0003 = ' + CC.GK(3) + '\n' + '\tPJO0004 = ' + CC.XK(4, 3, True) + '\n' + '\tPJO0005 = ' + CC.XK(5, 3, True) + '\n' + '\tPJO0006 = ' + CC.XK(6, 3, True) + '\n' + '\tPJO0007 = ' + CC.XK(7, 3, True) + '\n' + '\tPJO0008 = ' + CC.XK(8, 3, True) + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t   ' + '\n' + '\tPJO0009 = chr\t\t\t\t\t\t\t\t  ' + '\n' + '\tPJO0010 = eval\t\t\t\t\t\t\t\t ' + '\n' + '\tPJO0011 = map\t\t\t\t\t\t\t\t  ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t   ' + '\n' + '\tPJO0012 = PJO0010(PJO0009(' + CC.XRC('g') + ')+PJO0009(' + CC.XRC('e') + ')+PJO0009(' + CC.XRC('t') + ')+PJO0009(' + CC.XRC('a') + ')+PJO0009(' + CC.XRC('t') + ')+PJO0009(' + CC.XRC('t') + ')+PJO0009(' + CC.XRC('r') + '))  ' + '\n' + '\tPJO0013 = PJO0009(' + CC.XRC('j') + ')+PJO0009(' + CC.XRC('o') + ')+PJO0009(' + CC.XRC('i') + ')+PJO0009(' + CC.XRC('n') + ')   ' + '\n' + '\tPJO0014 = PJO0010(PJO0012("",PJO0013)(PJO0011(PJO0009,[' + CC.XRC('_') + ',' + CC.XRC('_') + ',' + CC.XRC('i') + ',' + CC.XRC('m') + ',' + CC.XRC('p') + ',' + CC.XRC('o') + ',' + CC.XRC('r') + ',' + CC.XRC('t') + ',' + CC.XRC('_') + ',' + CC.XRC('_') + '])))  ' + '\n' + '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t   ' + '\n' + '\tPJO0015 = PJO0014(PJO0009(' + CC.XRC('s') + ')+PJO0009(' + CC.XRC('y') + ')+PJO0009(' + CC.XRC('s') + '))\t\t\t\t\t\t ' + '\n' + '\tPJO0016 = PJO0014(PJO0009(' + CC.XRC('i') + ')+PJO0009(' + CC.XRC('m') + ')+PJO0009(' + CC.XRC('p') + '))\t\t\t\t\t\t ' + '\n' + '\tPJO0012(PJO0016, PJO0012("",PJO0013)(PJO0011(PJO0009,[' + CC.XRC('a') + ',' + CC.XRC('c') + ',' + CC.XRC('q') + ',' + CC.XRC('u') + ',' + CC.XRC('i') + ',' + CC.XRC('r') + ',' + CC.XRC('e') + ',' + CC.XRC('_') + ',' + CC.XRC('l') + ',' + CC.XRC('o') + ',' + CC.XRC('c') + ',' + CC.XRC('k') + '])))() ' + '\n' + '\ttry:\t\t\t\t\t\t\t\t\t\t  ' + '\n' + '\t\tPJO0017 = PJO0010(PJO0009(' + CC.XRC('h') + ')+PJO0009(' + CC.XRC('a') + ')+PJO0009(' + CC.XRC('s') + ')+PJO0009(' + CC.XRC('a') + ')+PJO0009(' + CC.XRC('t') + ')+PJO0009(' + CC.XRC('t') + ')+PJO0009(' + CC.XRC('r') + '))  ' + '\n' + '\t\tPJO0018 = PJO0012("",PJO0013)(PJO0011(PJO0009,[' + CC.XRC('_') + ',' + CC.XRC('_') + ',' + CC.XRC('d') + ',' + CC.XRC('a') + ',' + CC.XRC('t') + ',' + CC.XRC('a') + ',' + CC.XRC('_') + ',' + CC.XRC('c') + ',' + CC.XRC('a') + ',' + CC.XRC('c') + ',' + CC.XRC('h') + ',' + CC.XRC('e') + ',' + CC.XRC('_') + ',' + CC.XRC('_') + ']))  ' + '\n' + '\t\tPJO0028 = PJO0010(PJO0009(' + CC.XRC('s') + ')+PJO0009(' + CC.XRC('e') + ')+PJO0009(' + CC.XRC('t') + ')+PJO0009(' + CC.XRC('a') + ')+PJO0009(' + CC.XRC('t') + ')+PJO0009(' + CC.XRC('t') + ')+PJO0009(' + CC.XRC('r') + '))  ' + '\n' + '\t\tif not PJO0017(PJO0015, PJO0018):\t\t\t\t\t\t\t\t\t   ' + '\n' + '\t\t\tPJO0028(PJO0015, PJO0018, {})\t\t\t\t\t\t\t\t\t\t\t\t  ' + '\n' + '\t\tPJO0027 = PJO0012("",PJO0013)(PJO0011(PJO0009,[' + CC.XRC('_') + ',' + CC.XRC('_') + ',' + CC.XRC('c') + ',' + CC.XRC('o') + ',' + CC.XRC('d') + ',' + CC.XRC('e') + ',' + CC.XRC('_') + ',' + CC.XRC('_') + ']))  ' + '\n' + '\t\tPJO0019 = PJO0012(PJO0012(PJO0002,PJO0027), PJO0012("",PJO0013)(PJO0011(PJO0009,[' + CC.XRC('_') + ',' + CC.XRC('_') + ',' + CC.XRC('h') + ',' + CC.XRC('a') + ',' + CC.XRC('s') + ',' + CC.XRC('h') + ',' + CC.XRC('_') + ',' + CC.XRC('_') + '])))() ' + '\n' + '\t\tif not PJO0019 in PJO0012(PJO0015, PJO0018):\t\t\t\t\t\t\t\t\t  ' + '\n' + '\t\t\tPJO0012(PJO0015, PJO0018)[PJO0019] = PJO0012(PJO0016, PJO0012("",PJO0013)(PJO0011(PJO0009,[' + CC.XRC('n') + ',' + CC.XRC('e') + ',' + CC.XRC('w') + ',' + CC.XRC('_') + ',' + CC.XRC('m') + ',' + CC.XRC('o') + ',' + CC.XRC('d') + ',' + CC.XRC('u') + ',' + CC.XRC('l') + ',' + CC.XRC('e') + '])))("") ' + '\n' + '\t\t\ttry:\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t ' + '\n' + '\t\t\t\tPJO0020 = PJO0012("",PJO0013)(PJO0011(PJO0009,[' + CC.XRC('_') + ',' + CC.XRC('_') + ',' + CC.XRC('b') + ',' + CC.XRC('u') + ',' + CC.XRC('i') + ',' + CC.XRC('l') + ',' + CC.XRC('t') + ',' + CC.XRC('i') + ',' + CC.XRC('n') + ',' + CC.XRC('s') + ',' + CC.XRC('_') + ',' + CC.XRC('_') + '])) ' + '\n' + '\t\t\t\tPJO0028(PJO0012(PJO0015, PJO0018)[PJO0019], PJO0020, PJO0010(PJO0020))\t\t   ' + '\n' + '\t\t\t\tPJO0021 = PJO0012("",PJO0013)(PJO0011(PJO0009,[' + CC.XRC('_') + ',' + CC.XRC('_') + ',' + CC.XRC('d') + ',' + CC.XRC('o') + ',' + CC.XRC('c') + ',' + CC.XRC('_') + ',' + CC.XRC('_') + '])) ' + '\n' + '\t\t\t\tPJO0028(PJO0012(PJO0015, PJO0018)[PJO0019], PJO0021, PJO0010(PJO0021))\t\t\t\t' + '\n' + '\t\t\t\tPJO0022 = PJO0012("",PJO0013)(PJO0011(PJO0009,[' + CC.XRC('_') + ',' + CC.XRC('_') + ',' + CC.XRC('f') + ',' + CC.XRC('i') + ',' + CC.XRC('l') + ',' + CC.XRC('e') + ',' + CC.XRC('_') + ',' + CC.XRC('_') + '])) ' + '\n' + '\t\t\t\tPJO0028(PJO0012(PJO0015, PJO0018)[PJO0019], PJO0022, PJO0010(PJO0022))\t\t\t\t' + '\n' + '\t\t\t\tPJO0023 = PJO0012("",PJO0013)(PJO0011(PJO0009,[' + CC.XRC('_') + ',' + CC.XRC('_') + ',' + CC.XRC('n') + ',' + CC.XRC('a') + ',' + CC.XRC('m') + ',' + CC.XRC('e') + ',' + CC.XRC('_') + ',' + CC.XRC('_') + '])) ' + '\n' + '\t\t\t\tPJO0028(PJO0012(PJO0015, PJO0018)[PJO0019], PJO0023, PJO0010(PJO0023))\t\t\t\t' + '\n' + '\t\t\t\tPJO0024 = PJO0012("",PJO0013)(PJO0011(PJO0009,[' + CC.XRC('_') + ',' + CC.XRC('_') + ',' + CC.XRC('p') + ',' + CC.XRC('a') + ',' + CC.XRC('c') + ',' + CC.XRC('k') + ',' + CC.XRC('a') + ',' + CC.XRC('g') + ',' + CC.XRC('e') + ',' + CC.XRC('_') + ',' + CC.XRC('_') + '])) ' + '\n' + '\t\t\t\tPJO0028(PJO0012(PJO0015, PJO0018)[PJO0019], PJO0024, PJO0010(PJO0024))\t\t\t ' + '\n' + '\t\t\t\tPJO0025 = PJO0012("",PJO0013)(PJO0011(PJO0009,[' + CC.XRC('_') + ',' + CC.XRC('_') + ',' + CC.XRC('d') + ',' + CC.XRC('i') + ',' + CC.XRC('c') + ',' + CC.XRC('t') + ',' + CC.XRC('_') + ',' + CC.XRC('_') + '])) ' + '\n' + '\t\t\t\texec PJO0012(PJO0002,PJO0027) in PJO0012(PJO0012(PJO0015, PJO0018)[PJO0019], PJO0025)\t\t\t\t  ' + '\n' + '\t\t\texcept Exception as PJO0026:\t\t\t\t\t\t\t\t\t\t\t   ' + '\n' + '\t\t\t\tdel PJO0012(PJO0015, PJO0018)[PJO0019]\t\t\t\t\t\t\t\t\t' + '\n' + '\t\t\t\tprint "Error in module \'%s\': %s" % (PJO0010(PJO0023), PJO0026)\t\t\t   ' + '\n' + '\tfinally:\t\t\t\t\t\t\t\t\t ' + '\n' + '\t\tPJO0012(PJO0016, PJO0012("",PJO0013)(PJO0011(PJO0009,[' + CC.XRC('r') + ',' + CC.XRC('e') + ',' + CC.XRC('l') + ',' + CC.XRC('e') + ',' + CC.XRC('a') + ',' + CC.XRC('s') + ',' + CC.XRC('e') + ',' + CC.XRC('_') + ',' + CC.XRC('l') + ',' + CC.XRC('o') + ',' + CC.XRC('c') + ',' + CC.XRC('k') + '])))() ' + '\n' + 'try:\t\t\t\t\t\t\t\t\t\t\t ' + '\n' + '\tPJO0001(PJO0000)\t\t\t\t\t\t\t  ' + '\n' + 'finally:\t\t\t\t\t\t\t\t\t\t ' + '\n' + '\tdel PJO0000, PJO0001'
        Wrapper = CC.ObjReplace(compile(Wrapper, '', 'exec'))
    ZipBoxLoader = 'import __builtin__, sys, zlib, marshal  ' + '\n' + 'reload(__builtin__)\t\t\t\t\t ' + '\n' + 'exec marshal.loads("".join([chr(int((bin(ord(x))[2:].rjust(8, "0"))[::-1],2)) for x in zlib.decompress(sys._getframe().f_code.co_code[(len(dir(marshal.loads))>>1):])])) in globals()'
    ZipBoxLoader = compile(ZipBoxLoader, '', 'exec')
    from dispack.dispyc import get_bytecode_file
    from os import path, rename, remove
    from itertools import izip, cycle
    _, filename_tag = path.split(filename)
    filename_tag, _ = path.splitext(filename_tag)
    if not use_exe_injector:
        ByteCode = get_bytecode_file(filename)
    else:
        try:
            if path.exists(filename + '.temp'):
                with open(filename + '.temp', 'rb') as f:
                    CODE = f.read()
                remove(filename + '.temp')
                new_crypt_co_consts = [ (CODE[:10] if const == '%CODE1%' else (CODE[10:] if const == '%CODE2%' else const)) for const in GLOBAL_PYINJECTOR.co_consts[0].co_consts ]
                for s in GLOBAL_RANDOM_KEY[::-1]:
                    new_crypt_co_consts.append(ord(s))

                new_co_consts = [ const for const in GLOBAL_PYINJECTOR.co_consts ]
                new_co_consts[0] = type(GLOBAL_PYINJECTOR.co_consts[0])(GLOBAL_PYINJECTOR.co_consts[0].co_argcount, GLOBAL_PYINJECTOR.co_consts[0].co_nlocals, GLOBAL_PYINJECTOR.co_consts[0].co_stacksize, GLOBAL_PYINJECTOR.co_consts[0].co_flags, GLOBAL_PYINJECTOR.co_consts[0].co_code, tuple(new_crypt_co_consts), GLOBAL_PYINJECTOR.co_consts[0].co_names, GLOBAL_PYINJECTOR.co_consts[0].co_varnames, filename_tag, GLOBAL_PYINJECTOR.co_consts[0].co_name, 1, '', GLOBAL_PYINJECTOR.co_consts[0].co_freevars, GLOBAL_PYINJECTOR.co_consts[0].co_cellvars)
                ByteCode = type(GLOBAL_PYINJECTOR)(GLOBAL_PYINJECTOR.co_argcount, GLOBAL_PYINJECTOR.co_nlocals, GLOBAL_PYINJECTOR.co_stacksize, GLOBAL_PYINJECTOR.co_flags, GLOBAL_PYINJECTOR.co_code, tuple(new_co_consts), GLOBAL_PYINJECTOR.co_names, GLOBAL_PYINJECTOR.co_varnames, filename_tag, GLOBAL_PYINJECTOR.co_name, 1, '', GLOBAL_PYINJECTOR.co_freevars, GLOBAL_PYINJECTOR.co_cellvars)
            else:
                Error = True
                Error_Msg = "Error: file '%s' not found! " % (filename + '.temp')
        except Exception as E:
            Error = True
            Error_Msg = 'Error: injector will not be installed! ' + str(E).replace('\n', ' ')

    if not Error:
        if ByteCode is not None:
            Crypter = Analizator()
            try:
                if lock_attr_review:
                    new_co_consts = [ const for const in Wrapper.co_consts ]
                    new_co_consts[0] = type(Wrapper.co_consts[0])(ByteCode.co_argcount, ByteCode.co_nlocals, ByteCode.co_stacksize, ByteCode.co_flags, ByteCode.co_code, ByteCode.co_consts, ByteCode.co_names, ByteCode.co_varnames, ByteCode.co_filename, Wrapper.co_consts[0].co_name, ByteCode.co_firstlineno, ByteCode.co_lnotab, ByteCode.co_freevars, ByteCode.co_cellvars)
                    Crypter.ParseCO(Wrapper.co_consts[1])
                    Crypter.RepAllJumpForwardOnAbsolute()
                    Crypter.Obfuscate(Crypter.ConvAllJumpRelToAbsolute(), True, True, True)
                    Crypter.RepAllJumpAbsoluteOnForward(True)
                    new_co_consts[1] = type(Wrapper.co_consts[1])(Wrapper.co_consts[1].co_argcount, Wrapper.co_consts[1].co_nlocals, Wrapper.co_consts[1].co_stacksize, Wrapper.co_consts[1].co_flags, Crypter.BuildCoCode(), Wrapper.co_consts[1].co_consts, Wrapper.co_consts[1].co_names, Wrapper.co_consts[1].co_varnames, filename_tag, Wrapper.co_consts[1].co_name, 1, '', Wrapper.co_consts[1].co_freevars, Wrapper.co_consts[1].co_cellvars)
                    Crypter.ParseCO(Wrapper)
                    Crypter.RepAllJumpForwardOnAbsolute()
                    Crypter.Obfuscate(Crypter.ConvAllJumpRelToAbsolute(), True, True, True)
                    Crypter.RepAllJumpAbsoluteOnForward(True)
                    ByteCode = type(Wrapper)(Wrapper.co_argcount, Wrapper.co_nlocals, Wrapper.co_stacksize, Wrapper.co_flags, Crypter.BuildCoCode(), tuple(new_co_consts), Wrapper.co_names, Wrapper.co_varnames, filename_tag, Wrapper.co_name, 1, '', Wrapper.co_freevars, Wrapper.co_cellvars)
            except Exception as E:
                Error = True
                Error_Msg = 'Error: wrapping will not be completed! ' + str(E).replace('\n', ' ')
            else:
                try:
                    new_co_consts = [ const for const in LoaderMainFunction.__code__.co_consts[1].co_consts ]
                    OpenCryptKey = CreateRandomString(10)
                    new_crypt_co_consts = [ x for x in LoaderCryptFunction.__code__.co_consts ]
                    for s in OpenCryptKey:
                        new_crypt_co_consts.append(ord(s))

                    Crypter.ParseCO(LoaderCryptFunction.__code__)
                    Crypter.RepAllJumpForwardOnAbsolute()
                    Crypter.Obfuscate(Crypter.ConvAllJumpRelToAbsolute(), True, True, True)
                    Crypter.RepAllJumpAbsoluteOnForward(True)
                    new_co_consts.append(type(LoaderCryptFunction.__code__)(LoaderCryptFunction.__code__.co_argcount, LoaderCryptFunction.__code__.co_nlocals, LoaderCryptFunction.__code__.co_stacksize, LoaderCryptFunction.__code__.co_flags, Crypter.BuildCoCode(), tuple(new_crypt_co_consts), LoaderCryptFunction.__code__.co_names, LoaderCryptFunction.__code__.co_varnames, filename_tag, CreateRandomString(randint(3, 12)), 1, '', LoaderCryptFunction.__code__.co_freevars, LoaderCryptFunction.__code__.co_cellvars))
                    LittleCryptKey = ''.join(map(chr, [ x ^ y for x, y in izip(map(ord, OpenCryptKey), cycle(map(ord, hex(abs(hash(new_co_consts[-1].co_code)))[2:]))) ]))
                    Crypter.ParseCO(LoaderMainFunction.__code__.co_consts[1])
                    Crypter.RepAllJumpForwardOnAbsolute()
                    Crypter.Obfuscate(Crypter.ConvAllJumpRelToAbsolute(), True, True, True)
                    Crypter.RepAllJumpAbsoluteOnForward(True)
                    new_co_code = Crypter.BuildCoCode()
                    MiddleCryptKey = ''.join(map(chr, [ x ^ y for x, y in izip(map(ord, LittleCryptKey), cycle(map(ord, hex(abs(hash(new_co_code)))[2:]))) ]))
                    Crypter.ParseCO(LoaderMainFunction.__code__)
                    Crypter.RepAllJumpForwardOnAbsolute()
                    Crypter.Obfuscate(Crypter.ConvAllJumpRelToAbsolute(), True, True, True)
                    Crypter.RepAllJumpAbsoluteOnForward(True)
                    new_main_co_code = Crypter.BuildCoCode()
                    LongCryptKey = ''.join(map(chr, [ x ^ y for x, y in izip(map(ord, MiddleCryptKey), cycle(map(ord, hex(abs(hash(new_main_co_code)))[2:]))) ]))
                    from marshal import loads
                    CZBLabel = CreateRandomString((len(dir(loads)) >> 1) - 7, False)
                    BigCryptKey = ''.join(map(chr, [ x ^ y for x, y in izip(map(ord, LongCryptKey), cycle(map(ord, hex(abs(hash(CZBLabel)))[2:]))) ]))
                    new_co_consts.append(Obfuscator(Obfuscator, ByteCode, BigCryptKey))
                    LoaderSubFunction = type(LoaderMainFunction.__code__.co_consts[1])(LoaderMainFunction.__code__.co_consts[1].co_argcount, LoaderMainFunction.__code__.co_consts[1].co_nlocals, LoaderMainFunction.__code__.co_consts[1].co_stacksize, LoaderMainFunction.__code__.co_consts[1].co_flags, new_co_code, tuple(new_co_consts), LoaderMainFunction.__code__.co_consts[1].co_names, LoaderMainFunction.__code__.co_consts[1].co_varnames, filename_tag, LoaderMainFunction.__code__.co_consts[1].co_name, 1, '', LoaderMainFunction.__code__.co_consts[1].co_freevars, LoaderMainFunction.__code__.co_consts[1].co_cellvars)
                    new_co_consts = [ x for x in LoaderMainFunction.__code__.co_consts ]
                    new_co_consts[1] = LoaderSubFunction
                    ProtectCode = type(LoaderMainFunction.__code__)(LoaderMainFunction.__code__.co_argcount, LoaderMainFunction.__code__.co_nlocals, LoaderMainFunction.__code__.co_stacksize, LoaderMainFunction.__code__.co_flags, new_main_co_code, tuple(new_co_consts), LoaderMainFunction.__code__.co_names, LoaderMainFunction.__code__.co_varnames, filename_tag, Revision, 1, '', LoaderMainFunction.__code__.co_freevars, LoaderMainFunction.__code__.co_cellvars)
                    from marshal import dumps
                    from zlib import compress
                    Crypter.ParseCO(ZipBoxLoader)
                    ZipBoxCode = Crypter.CZBBuildCoCode(CZBLabel + compress(''.join([ chr(int(bin(ord(x))[2:].rjust(8, '0')[::-1], 2)) for x in dumps(CC.ObjReplace(ProtectCode)) ]), 9))
                    ZipBoxCode = type(ZipBoxLoader)(ZipBoxLoader.co_argcount, ZipBoxLoader.co_nlocals, ZipBoxLoader.co_stacksize, ZipBoxLoader.co_flags, ZipBoxCode, ZipBoxLoader.co_consts, ZipBoxLoader.co_names, ZipBoxLoader.co_varnames, filename_tag, Revision, 1, '', ZipBoxLoader.co_freevars, ZipBoxLoader.co_cellvars)
                    if create_backup:
                        back_filename = filename + '.backup'
                        if path.isfile(back_filename):
                            remove(back_filename)
                        rename(filename, back_filename)
                    SaveMarshalCode(ZipBoxCode, filename)
                except Exception as E:
                    Error = True
                    Error_Msg = 'Error: crypting will not be completed! ' + str(E).replace('\n', ' ')

            del Crypter
        else:
            Error = True
            Error_Msg = 'Error: marshal-code in the file is not valid!'
    del CC
    if Error:
        print Error_Msg
    return