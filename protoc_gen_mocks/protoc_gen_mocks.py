#!/usr/bin/env python
"""
https://googleapis.dev/python/protobuf/latest/google/protobuf/descriptor.html
https://googleapis.dev/python/protobuf/latest/google/protobuf/descriptor_pb2.html
"""
import builtins
import logging
import random
import sys
from keyword import iskeyword  # Needed at some point to deal with Python keywords used in proto definitions
from typing import Optional, Any, Callable

from google.protobuf.compiler import plugin_pb2 as plugin
from google.protobuf.descriptor import MakeDescriptor
from google.protobuf.descriptor_pb2 import FileDescriptorProto, DescriptorProto, FieldDescriptorProto, \
    EnumDescriptorProto, SourceCodeInfo
from google.protobuf.json_format import MessageToDict, MessageToJson

LOGGER = logging.getLogger(__name__)
# logging.basicConfig(
#     level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# )


# Mock map
MOCK_MAP: dict[str, Callable[[], str]] = {
    "float": lambda: str(random.random() * 1000),
    "int": lambda: str(random.randint(1, 100000)),
    "bool": lambda: str(random.choice([True, False])),
    "str": lambda: '"some_string"',
    "bytes": lambda: '"some_bytes"',
}


# Primitive types. Messages, Enums and Groups are handled separately.
TYPE_MAP: dict[FieldDescriptorProto.Type.ValueType, str] = {
    FieldDescriptorProto.TYPE_DOUBLE: "float",
    FieldDescriptorProto.TYPE_FLOAT: "float",
    FieldDescriptorProto.TYPE_INT64: "int",
    FieldDescriptorProto.TYPE_UINT64: "int",
    FieldDescriptorProto.TYPE_FIXED64: "int",
    FieldDescriptorProto.TYPE_SFIXED64: "int",
    FieldDescriptorProto.TYPE_SINT64: "int",
    FieldDescriptorProto.TYPE_INT32: "int",
    FieldDescriptorProto.TYPE_UINT32: "int",
    FieldDescriptorProto.TYPE_FIXED32: "int",
    FieldDescriptorProto.TYPE_SFIXED32: "int",
    FieldDescriptorProto.TYPE_SINT32: "int",
    FieldDescriptorProto.TYPE_BOOL: "bool",
    FieldDescriptorProto.TYPE_STRING: "str",
    FieldDescriptorProto.TYPE_BYTES: "bytes",
}


SOURCE_CODE_INFO: Optional[SourceCodeInfo] = None


def is_well_known_type(field: FieldDescriptorProto) -> bool:
    return field.type_name.startswith(".google.protobuf.")


def get_field_type(field: FieldDescriptorProto) -> str:
    if field.type == FieldDescriptorProto.TYPE_ENUM:
        return field.type_name.split(".")[-1]

    if field.type in [
        FieldDescriptorProto.TYPE_MESSAGE,
        FieldDescriptorProto.TYPE_GROUP,
    ]:
        # Nested protobufs have a type like "foo.bar.SomeMessage.NestedMessage"
        field_type = ".".join(filter(lambda x: x and not x[0].islower(), field.type_name.split(".")))

        if not is_well_known_type(field):
            field_type = f"pb.{field_type}"

        return field_type

    return TYPE_MAP[field.type]


def get_make_for_field_type_message(field: FieldDescriptorProto) -> str:
    if field.type == FieldDescriptorProto.TYPE_MESSAGE:
        message_type = field.type_name.split(".")[-1]
        return f"make_{camel_to_snake(message_type)}"

    raise RuntimeError(f"Field {field} is not a Message or Group")


def generate_field_value_mock(field: FieldDescriptorProto):
    field_type = get_field_type(field)
    if field.label == FieldDescriptorProto.LABEL_REPEATED:
        if field.type == FieldDescriptorProto.TYPE_MESSAGE:
            return f"{field.name} or [{get_make_for_field_type_message(field)}()],"

        if field.type == FieldDescriptorProto.TYPE_ENUM:
            return f"{field.name} or [choice([v.name for v in {field_type}])],"

        return f"{field.name} or [{MOCK_MAP[field_type]()}],"
    else:
        response: str
        if field.type == FieldDescriptorProto.TYPE_MESSAGE:
            response = f"{field.name} or {get_make_for_field_type_message(field)}(),"
        elif field.type == FieldDescriptorProto.TYPE_ENUM:
            response = f"{field.name} or choice([v.name for v in {field_type}]),"
        else:
            response = f"{field.name} or {MOCK_MAP[field_type]()},"

        if field.label == FieldDescriptorProto.LABEL_REQUIRED:
            response += "  # required"

        return response


def generate_field_mock(field: FieldDescriptorProto, padding: int = 0) -> str:
    return f"{' '*padding}{field.name}={generate_field_value_mock(field)}\n"


def generate_field_parameter(field: FieldDescriptorProto, padding: int = 0) -> str:
    # All parameters are always marked as optional
    response = f"{field.name}: Optional["

    is_list = field.label == FieldDescriptorProto.LABEL_REPEATED

    if is_list:
        response += "list["

    try:
        response += get_field_type(field)
    except KeyError:
        LOGGER.exception(f"Unknown type {FieldDescriptorProto.Type.Name(field.type)}")

    if is_list:
        response += "]"

    response += "] = None"

    return " " * padding + response + ",\n"


def generate_class_parameter(field: FieldDescriptorProto, padding: int = 0) -> str:
    is_optional = field.label == FieldDescriptorProto.LABEL_OPTIONAL

    is_list = field.label == FieldDescriptorProto.LABEL_REPEATED

    response = f"{field.name}: "

    if is_optional:
        response += "Optional["

    if is_list:
        response += "list["

    try:
        response += get_field_type(field)
    except KeyError:
        LOGGER.exception(f"Unknown type {FieldDescriptorProto.Type.Name(field.type)}")

    if is_list:
        response += "]"

    if is_optional:
        response += "]"

    return " " * padding + response + "\n"


def camel_to_snake(message) -> str:
    xform = lambda c: f"_{c.lower()}" if c.isupper() else c
    return "".join(xform(c) for c in message).strip("_")  # Strip leading "_"


# def generate_class_attribute_assignment(field: FieldDescriptorProto, padding: int = 0) -> str:
#     return f"{padding * ' '}self.{field.name} = {field.name}\n"
#
def generate_nested_message_mock(message: DescriptorProto, parent_message: str, padding: int = 0) -> str:
    code = f"""
def make_{camel_to_snake(message.name)}(
    *,  # Keyword arguments only
{"".join(generate_field_parameter(field, padding=padding) for field in message.field)}
) -> pb.{parent_message}.{message.name}:
    nested_mock = pb.{parent_message}.{message.name}(
{''.join(generate_field_mock(field, padding=padding+4) for field in message.field)}
    )
    assert nested_mock.IsInitialized()
    return nested_mock
"""
    return "\n".join(f"{padding * ' '}{line}" for line in code.split("\n"))


def generate_message_mock(message: DescriptorProto) -> str:
    nested_type_mocks = ""
    if message.nested_type:
        nested_type_mocks = "".join(generate_nested_message_mock(nested_type, message.name, padding=4) for nested_type in message.nested_type)

    arguments = "# No arguments"
    if message.field:
        arguments = "*,  # Keyword arguments only\n" + "".join(generate_field_parameter(field, padding=4) for field in message.field)

    return f"""def make_{camel_to_snake(message.name)}(
    {arguments}
) -> pb.{message.name}:
{nested_type_mocks}
    mock = pb.{message.name}(
{''.join(generate_field_mock(field, padding=8) for field in message.field)}
    )
    assert mock.IsInitialized()
    return mock
    """


def generate_dependency_import_statement(dependency: str) -> str:
    """Converts a dependency into an import statement.

    If dependency is "google/protobuf/timestamp.proto" then this function
    will return "from google.protobuf.timestamp_pb2 import Timestamp".
    """
    parts = dependency.split("/")
    filename = parts[-1]
    file_without_extension = filename.split(".")[0]
    return f"from {'.'.join(parts[0:-1])}.{file_without_extension}_pb2 import {file_without_extension.title()}" \
           f"\nfrom {'.'.join(parts[0:-1])}.{file_without_extension}_mock import *  # TODO"


def generate_file_import_statement(filepath: str) -> str:
    """Creates the import statement for the protobufs for this file.

    If filepath is "google/protobuf/timestamp.proto" then this function
    will return "from google.protobuf import timestamp_pb2 as pb".
    """
    parts = filepath.split("/")
    filename = parts[-1]
    file_without_extension = filename.split(".")[0]
    return f"from {'.'.join(parts[0:-1])} import {file_without_extension}_pb2 as pb"


def generate_enum_type(enum_type: EnumDescriptorProto) -> str:
    response = f"class {enum_type.name}(Enum):\n"
    response += "\n".join(f"    {v.name}: {v.number}" for v in enum_type.value)
    response += "\n\n"
    return response


def process_file(
    proto_file: FileDescriptorProto, response: plugin.CodeGeneratorResponse
) -> None:
    LOGGER.info(f"Processing proto_file: {proto_file.name}")

    LOGGER.debug("Input:\n%s", MessageToDict(proto_file))

    # Create dict of options
    options = str(proto_file.options).strip().replace("\n", ", ").replace('"', "")
    options_dict = dict(item.split(": ") for item in options.split(", ") if options)

    SOURCE_CODE_INFO = proto_file.source_code_info

    data = ""
    if proto_file.enum_type:
        data += "from enum import Enum\n"
        data += "from random import choice\n"

    data += "from google.protobuf import Message\n"
    data += "from typing import Optional\n"


    data += generate_file_import_statement(proto_file.name) + "\n\n"

    if proto_file.dependency:
        data += "\nn".join(generate_dependency_import_statement(dependency) for dependency in proto_file.dependency) + "\n\n"

    if proto_file.enum_type:
        data += "\n\n".join(generate_enum_type(enum) for enum in proto_file.enum_type) + "\n"

    if proto_file.message_type:
        data += "\n\n".join(
            generate_message_mock(message)
            for message in proto_file.message_type
        )

    file = response.file.add()
    file.name = proto_file.name.removesuffix(".proto") + "_mock.py"
    LOGGER.info(f"Creating new file: {file.name}")
    file.content = data


def process(
    request: plugin.CodeGeneratorRequest, response: plugin.CodeGeneratorResponse
) -> None:
    for proto_file in request.proto_file:
        process_file(proto_file, response)


def main() -> None:
    # Load the request from stdin
    request = plugin.CodeGeneratorRequest.FromString(sys.stdin.buffer.read())


    LOGGER.debug("Request:\n%s\n", MessageToJson(request, indent=2))

    # Create a response
    response = plugin.CodeGeneratorResponse()

    process(request, response)

    # logger.debug("Response:\n%s\n", MessageToJson(response, indent=2))

    # Serialize response and write to stdout
    sys.stdout.buffer.write(response.SerializeToString())


if __name__ == "__main__":
    main()
