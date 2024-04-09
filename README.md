# protoc-gen-mocks

> Status: Proof of concept with some known limitations.

A plugin for the Google protobuf compiler (protoc) that generates mocks for Python.

Each `.proto` file compiled will have a corresponding `_mock.py` file generated, which, for each protobuf message, contains a corresponing `make_{snake_case_of_message_name}` function, e.g. `message ExampleRequest` in `example.proto` will get a corresponding `make_example_request()` function in a `example_mock.py` file.

Each function supports keyword-only arguments which can be used to provide specific initial values.

Nested message definitions will result in nested `make_*` function definitions as well.

Where message definitions refer to other messages, it will be initialised using the relevant `make_*` function.

The intended use (at this stage) is to generate code, which can be altered as required with more sensible values where applicable.

## Usage 

`protoc-gen-mocks` is a plugin for the `protoc` compiler, which is enabled using the `--plugin` and `--mocks_out` options.

### Protoc
```
protoc --plugin="protoc-gen-mocks=$(which protoc-gen-mocks)" examples/*.proto --mocks_out=.  --proto_path=. --python_out=. --pyi_out=.
```

### grpcio-tools
```
python -m grpc_tools.protoc --plugin="protoc-gen-mocks=$(which protoc-gen-mocks)" examples/*.proto --mocks_out=.  --proto_path=. --python_out=. --pyi_out=.
```

