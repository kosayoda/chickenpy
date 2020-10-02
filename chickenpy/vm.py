import enum
import logging
import typing as t

log = logging.getLogger("chickenpy.VM")


@enum.unique
class OPCODE(enum.IntEnum):
    EXIT = 0
    CHICKEN = 1
    ADD = 2
    SUB = 3
    MUL = 4
    CMP = 5
    LOAD = 6
    STORE = 7
    JMP = 8
    CHAR = 9

    def __str__(self):
        return f"OP.{self.name} ({self.value})"


Token = t.Union[OPCODE, int, str]


class Machine:
    """
    Virtual machine for the Chicken programming language.
    Full specification can be found here: https://esolangs.org/wiki/Chicken
    """
    def __init__(self, code: t.List[str], stdin: str = ""):
        self.stack = []

        # First segment
        self.stack.append(self.stack)
        self.stack.append(stdin)

        # Second segment
        self.stack.extend(code)
        self.stack.append(OPCODE.EXIT)

        self.instruction_pointer = 2  # Instructions start at second segment

        # Everything after this index is data from program execution
        self._data_start = len(self.stack)

    @property
    def data_stack(self) -> t.List[Token]:
        return self.stack[self._data_start:]

    @property
    def next_token(self) -> Token:
        opcode = self.stack[self.instruction_pointer]
        self.instruction_pointer += 1
        return opcode

    def pop(self) -> Token:
        """Removes and returns the token at the top of the stack."""
        return self.stack.pop()

    def push(self, value: Token):
        """Pushes a token to the top of the stack."""
        self.stack.append(value)

    def peek(self) -> Token:
        """Returns the token at the top of the stack."""
        return self.stack[-1]

    def dispatch(self, op: Token):
        """
        Executes the current opcode.
        See: https://esolangs.org/wiki/Chicken#Instructions
        """
        log.debug(f"Evaluating {str(op)}")

        if op is OPCODE.CHICKEN:
            log.debug("Pushing 'chicken' to stack")
            self.push("chicken")

        elif op is OPCODE.ADD:
            operand_2, operand_1 = self.pop(), self.pop()
            # Javascript casts to string and concatenates if either operand are strings
            try:
                result = operand_1 + operand_2
            except TypeError:
                result = f"{operand_1}{operand_2}"
            log.debug(f"{operand_1!r} + {operand_2!r} = {result!r}")
            self.push(result)

        elif op is OPCODE.SUB:
            operand_2, operand_1 = self.pop(), self.pop()
            # Javascript implicitly casts to int
            result = int(operand_1) - int(operand_2)
            log.debug(f"{operand_1!r} - {operand_2!r} = {result!r}")
            self.push(result)

        elif op is OPCODE.MUL:
            operand_2, operand_1 = self.pop(), self.pop()
            # Javascript implicitly casts to int
            result = int(operand_2) * int(operand_1)
            log.debug(f"{operand_1!r} * {operand_2!r} = {result!r}")
            self.push(result)

        elif op is OPCODE.CMP:
            operand_2, operand_1 = self.pop(), self.pop()
            result = operand_2 == operand_1
            log.debug(f"{operand_1!r} {'==' if result else '!='!r} {operand_2!r}")
            self.push(result)

        elif op is OPCODE.LOAD:
            load_from = self.next_token
            source = self.stack[load_from]
            load_index = self.pop()
            log.debug(
                f"Loading index {load_index!r} from {'stack' if load_from == 0 else 'user input'!r}"
            )
            # Accessing a string with an invalid index returns `undefined` in JS.
            # We return an empty string to ensure the 99 chickens example doesn't crash,
            # as it relies in UB.
            try:
                load = source[load_index]
            except IndexError:
                load = ""
            log.debug(f"Loading {load!r} to top of stack")
            self.push(load)

        elif op is OPCODE.STORE:
            address = self.pop()
            load = self.pop()
            log.debug(f"Storing {load!r} to {address!r}")
            self.stack[address] = load

        elif op is OPCODE.JMP:
            rel_offset = self.pop()
            if self.pop():
                log.debug(f"Jumping pointer by {rel_offset!r}")
                self.instruction_pointer += rel_offset
            else:
                log.debug("Jump skipped")

        elif op is OPCODE.CHAR:
            token = self.pop()
            char = chr(token)
            log.debug(f"Pushing {token!r} as {char!r}")
            self.push(char)

        else:
            token = op - 10
            log.debug(f"Pushing {token!r} as literal")
            self.push(token)

    def run(self) -> Token:
        """Executes the current code until completion or error."""
        while self.instruction_pointer <= len(self.stack):
            if self.stack[self.instruction_pointer] is OPCODE.EXIT:
                break

            self.dispatch(self.next_token)
            log.debug(f"Stack: {self.data_stack!r}")

        return self.peek()
