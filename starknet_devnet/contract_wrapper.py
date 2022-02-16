"""
Contains code for wrapping StarknetContract instances.
"""

from dataclasses import dataclass
from typing import List, Tuple

from starkware.cairo.lang.compiler.ast.cairo_types import (
    CairoType,
    TypeFelt,
    TypePointer
)
from starkware.cairo.lang.compiler.parser import parse_type
from starkware.cairo.lang.compiler.type_system import mark_type_resolved
from starkware.starknet.public.abi import get_selector_from_name
from starkware.starknet.services.api.contract_definition import ContractDefinition
from starkware.starknet.testing import contract
from starkware.starknet.testing.contract import StarknetContract
from starkware.starknet.testing.objects import StarknetTransactionExecutionInfo

from starknet_devnet.adapt import adapt_calldata, adapt_output
from starknet_devnet.util import Choice, StarknetDevnetException

def extract_types(abi):
    """
    Extracts the types (structs) used in the contract whose ABI is provided.
    """

    structs = [entry for entry in abi if entry["type"] == "struct"]
    type_dict = { struct["name"]: struct for struct in structs }
    return type_dict

def patched_parse_arguments(arguments_abi: dict) -> Tuple[List[str], List[CairoType]]:
    """
    Given the input or output field of a StarkNet contract function ABI,
    computes the arguments that the python proxy function should accept.
    In particular, an array input that has two inputs in the
    original ABI (foo_len: felt, foo: felt*) will be converted to a single argument foo.

    Returns the argument names and their Cairo types in two separate lists.
    """
    print("DEBUG received arguments_abi", arguments_abi)
    arg_names: List[str] = []
    arg_types: List[CairoType] = []
    for arg_entry in arguments_abi:
        name = arg_entry["name"]
        arg_type = mark_type_resolved(parse_type(code=arg_entry["type"]))
        if isinstance(arg_type, TypePointer):
            size_arg_actual_name = arg_names.pop()
            actual_type = arg_types.pop()
            # Make sure the last argument was {name}_len, and remove it.
            len_arg_name = f"{name}_len"
            patched_size_arg_name = f"{name}_size"
            assert (
                size_arg_actual_name in [len_arg_name, patched_size_arg_name]
            ), f"Array size argument {len_arg_name} must appear right before {name}."

            assert isinstance(actual_type, TypeFelt), (
                f"Array size entry {len_arg_name} expected to be type felt. Got: "
                f"{actual_type.format()}."
            )

        arg_names.append(name)
        arg_types.append(arg_type)

    print("DEBUG returning arg_names", arg_names)
    print("DEBUG returning arg_types", arg_types)
    return arg_names, arg_types

contract.parse_arguments = patched_parse_arguments

@dataclass
class ContractWrapper:
    """
    Wraps a StarknetContract, storing its types and code for later use.
    """
    # pylint: disable=redefined-outer-name
    def __init__(self, contract: StarknetContract, contract_definition: ContractDefinition):
        self.contract: StarknetContract = contract
        self.code: dict = {
            "abi": contract_definition.abi,
            "bytecode": [hex(el) for el in contract_definition.program.data]
        }

        self.types: dict = extract_types(contract_definition.abi)

    async def call_or_invoke(self, choice: Choice, entry_point_selector: int, calldata: List[int], signature: List[int]):
        """
        Depending on `choice`, performs the call or invoke of the function
        identified with `entry_point_selector`, potentially passing in `calldata` and `signature`.
        """
        function_mapping = self.contract._abi_function_mapping # pylint: disable=protected-access
        for method_name in function_mapping:
            selector = get_selector_from_name(method_name)
            if selector == entry_point_selector:
                try:
                    method = getattr(self.contract, method_name)
                except NotImplementedError as nie:
                    raise StarknetDevnetException from nie
                function_abi = function_mapping[method_name]
                break
        else:
            raise StarknetDevnetException(message=f"Illegal method selector: {entry_point_selector}.")

        adapted_calldata = adapt_calldata(calldata, function_abi["inputs"], self.types)

        prepared = method(*adapted_calldata)
        called = getattr(prepared, choice.value)
        execution_info: StarknetTransactionExecutionInfo = await called(signature=signature)
        return adapt_output(execution_info.result), execution_info
