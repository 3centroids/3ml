from dataclasses import dataclass, field
from typing import List, Dict


# AST Node definitions
@dataclass
class Node:
    children: List["Node"] = field(default_factory=list, init=False)


@dataclass
class Document(Node):
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class Section(Node):
    level: int
    title: str


@dataclass
class Paragraph(Node):
    text: str


@dataclass
class ListBlock(Node):
    items: List[str] = field(default_factory=list)


@dataclass
class Definition(Node):
    title: str


@dataclass
class Theorem(Node):
    title: str


# Parser Exceptions
class ParseError(Exception):
    pass


# Command handling
def _handle_command(line: str, lineno: int, stack: List[Node]):
    parts = line.split(maxsplit=1)
    cmd = parts[0][1:]
    arg = parts[1] if len(parts) > 1 else ""

    current = stack[-1]

    # Explicit #end
    if cmd == "end":
        if len(stack) == 1:
            raise ParseError(f"Line {lineno}: unexpected #end")
        if isinstance(stack[-1], Section):
            raise ParseError(f"Line {lineno}: sections do not use #end")
        stack.pop()
        return

    # Sections (#s1, #s2, ...)
    if cmd.startswith("s") and cmd[1:].isdigit():
        level = int(cmd[1:])
        # pop previous sections of same or higher level
        while len(stack) > 1 and isinstance(stack[-1], Section) and stack[-1].level >= level:
            stack.pop()
        node = Section(level, arg)
        stack[-1].children.append(node)
        stack.append(node)
        return

    # Block openers
    if cmd == "list":
        node = ListBlock()
        stack[-1].children.append(node)
        stack.append(node)
        return

    if cmd == "def":
        node = Definition(arg)
        stack[-1].children.append(node)
        stack.append(node)
        return

    if cmd == "thm":
        node = Theorem(arg)
        stack[-1].children.append(node)
        stack.append(node)
        return

    # Metadata
    if isinstance(current, Document):
        current.metadata[cmd] = arg
        return

    raise ParseError(f"Line {lineno}: unknown command #{cmd}")



# Text handling
def _handle_text(line: str, lineno: int, stack: List[Node]):
    if not line.strip():
        return  # skip empty lines

    current = stack[-1]

    if isinstance(current, ListBlock):
        if not line.startswith("- "):
            raise ParseError(f"Line {lineno}: list items must start with '- '")
        current.items.append(line[2:])
    else:
        current.children.append(Paragraph(line))



# Block parser
def parse_blocks(source: str) -> Document:
    lines = source.splitlines()
    doc = Document()
    stack: List[Node] = [doc]

    for lineno, line in enumerate(lines, 1):
        line = line.rstrip()
        if line.startswith("#"):
            _handle_command(line, lineno, stack)
        else:
            _handle_text(line, lineno, stack)

    # At EOF: check for unclosed explicit blocks
    for node in stack[1:]:  # skip Document
        if isinstance(node, (Definition, Theorem, ListBlock)):
            raise ParseError("Unclosed block at end of file")
    # Sections left on stack are implicitly closed -> OK

    return doc



# Example usage
if __name__ == "__main__":
    source = """#title Number Theory Basics
#author Author

#s1 Introduction

Some text to illustrate 3ML's capabilities.

#list
- fundamental theory of arithmetic
- congruences
#end

#def Prime number
A _prime number_ is a natural number greater than 1 that is not a product
of two smaller natural numbers.
#end
"""

    ast = parse_blocks(source)
    print(ast)
