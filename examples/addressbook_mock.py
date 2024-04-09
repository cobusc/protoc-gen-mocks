from google.protobuf import Message
from typing import Optional
from examples import addressbook_pb2 as pb

from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.timestamp_mock import *  # TODO

def make_person(
    *,  # Keyword arguments only
    name: Optional[str] = None,
    id: Optional[int] = None,
    email: Optional[str] = None,
    phones: Optional[list[pb.Person.PhoneNumber]] = None,
    last_updated: Optional[Timestamp] = None,

) -> pb.Person:
    
    def make_phone_number(
        *,  # Keyword arguments only
        number: Optional[str] = None,
        type: Optional[PhoneType] = None,
    
    ) -> pb.Person.PhoneNumber:
        nested_mock = pb.Person.PhoneNumber(
            number=number or "some_string",
            type=type or choice([v.name for v in PhoneType]),
    
        )
        assert nested_mock.IsInitialized()
        return nested_mock
    
    mock = pb.Person(
        name=name or "some_string",
        id=id or 79750,
        email=email or "some_string",
        phones=phones or [make_phone_number()],
        last_updated=last_updated or make_timestamp(),

# field.name='name' field.type=9 field.type_name=''# field.name='id' field.type=5 field.type_name=''# field.name='email' field.type=9 field.type_name=''# field.name='phones' field.type=11 field.type_name='.tutorial.Person.PhoneNumber'# field.name='last_updated' field.type=11 field.type_name='.google.protobuf.Timestamp'
    )
    assert mock.IsInitialized()
    return mock
    

def make_address_book(
    *,  # Keyword arguments only
    people: Optional[list[pb.Person]] = None,

) -> pb.AddressBook:

    mock = pb.AddressBook(
        people=people or [make_person()],

# field.name='people' field.type=11 field.type_name='.tutorial.Person'
    )
    assert mock.IsInitialized()
    return mock
    