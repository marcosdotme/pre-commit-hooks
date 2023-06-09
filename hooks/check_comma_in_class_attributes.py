from __future__ import annotations

import argparse
import ast
from pathlib import Path
from typing import List
from typing import Sequence


ERROR_MESSAGE_TEMPLATE = """File "{file}", line {line_number} in <class {class_name}>
    {line_of_code}
{pointer}
SyntaxError: Found comma in class attribute
"""


class AttributeVisitor(ast.NodeVisitor):
    def __init__(self):
        self.class_infos = []
        self.has_comma_in_class_attributes = False

    def visit_ClassDef(self, node):
        self.class_name = node.name
        self.generic_visit(node)

    def visit_Assign(self, node):
        if self.class_name is not None and isinstance(node.targets[0], ast.Attribute):
            attribute_name = node.targets[0].attr
            line_number = node.lineno

            if isinstance(node.value, ast.Tuple) and len(node.value.elts) == 1:
                self.has_comma_in_class_attributes = True
                self.class_infos.append((self.class_name, attribute_name, line_number))

        self.generic_visit(node)


def has_comma_in_class_attributes(filenames: List[str]) -> bool:
    for filename in filenames:
        with open(filename, mode='r') as file:
            code = file.read()
            code_lines = code.split('\n')
            code_lines = list(map(str.strip, code_lines))

        tree = ast.parse(code)
        visitor = AttributeVisitor()
        visitor.visit(tree)

        if visitor.has_comma_in_class_attributes:
            for class_name, attribute_name, line_number in visitor.class_infos:
                line_of_code = code_lines[line_number-1]

                comma_position = (line_of_code.find(',')) + 4 # 4 is the number of tab length used in ERROR_MESSAGE_TEMPLATE
                pointer = ' '*comma_position + '^'

                print(
                    ERROR_MESSAGE_TEMPLATE.format(
                        file=Path(filename).absolute(),
                        class_name=class_name,
                        line_number=line_number,
                        line_of_code=line_of_code,
                        attribute_name=attribute_name,
                        pointer=pointer
                    )
                )
            return True

        return False

def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*')
    args = parser.parse_args(argv)

    retval = 0
    if has_comma_in_class_attributes(filenames=args.filenames):
        retval = 1

    return retval


if __name__ == '__main__':
    raise SystemExit(main())
