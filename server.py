from flask import Flask, request, jsonify, abort
from starkware.starknet.services.api.contract_definition import ContractDefinition
from starkware.starknet.testing.starknet import Starknet
from starkware.starknet.testing.contract import StarknetContract
from starkware.starknet.services.api.gateway.transaction import InvokeFunction, Transaction
from starkware.starknet.compiler.compile import get_selector_from_name
from starkware.starkware_utils.error_handling import StarkErrorCode
from util import TxStatus, parse_args

app = Flask(__name__)
address2contract = {}
transactions = []

class StarknetWrapper:
    def __init__(self):
        self.starknet = None

    async def get_starknet(self):
        if not self.starknet:
            self.starknet = await Starknet.empty()
        return self.starknet

starknet_wrapper = StarknetWrapper()

@app.route("/is_alive", methods=["GET"])
@app.route("/gateway/is_alive", methods=["GET"])
@app.route("/feeder_gateway/is_alive", methods=["GET"])
def is_alive():
    return "Alive!!!"

async def deploy(contract_definition: ContractDefinition, contract_address: str):
    starknet = await starknet_wrapper.get_starknet()
    contract = await starknet.deploy(contract_def=contract_definition, contract_address=contract_address)
    address2contract[contract.contract_address] = contract
    return {}

def attempt_hex(x):
    try:
        return hex(x)
    except:
        pass
    return x

async def call_or_invoke(choice, contract_address: str, entry_point_selector: int, calldata: list):
    if (contract_address not in address2contract):
        abort(400, f"No contract at the provided address ({hex(contract_address)})")

    contract: StarknetContract = address2contract[contract_address]
    for method_name in contract._abi_function_mapping:
        selector = get_selector_from_name(method_name)
        if selector == entry_point_selector:
            method = getattr(contract, method_name)
            break
    else:
        abort(400, f"Illegal method selector: {entry_point_selector}")

    prepared = method(*calldata)
    called = getattr(prepared, choice)
    result = await called()

    return { "result": [attempt_hex(r) for r in result] }

def is_transaction_id_legal(transaction_id: int) -> bool:
    return 0 <= transaction_id < len(transactions)

@app.route("/gateway/add_transaction", methods=["POST"])
async def add_transaction():
    raw_data = request.get_data()
    transaction = Transaction.loads(raw_data)

    tx_type = transaction.tx_type.name
    result_dict = {}
    if tx_type == "DEPLOY":
        result_dict = await deploy(
            transaction.contract_definition,
            transaction.contract_address
        )
    elif tx_type == "INVOKE_FUNCTION":
        result_dict = await call_or_invoke("invoke",
            contract_address=transaction.contract_address,
            entry_point_selector=transaction.entry_point_selector,
            calldata=transaction.calldata
        )
    else:
        abort(400, f"Invalid tx_type: {tx_type}")

    new_id = len(transactions)
    transaction = {
        "block_id": new_id,
        "block_number": new_id,
        "status": TxStatus.PENDING.name,
        "transaction": {
            "contract_address": hex(transaction.contract_address),
            "type": tx_type
        },
        "transaction_id": new_id,
        "transaction_index": 0 # always the first (and only) tx in the block
    }
    transactions.append(transaction)

    return jsonify({
        "code": StarkErrorCode.TRANSACTION_RECEIVED.name,
        "tx_id": new_id,
        **result_dict
    })

@app.route("/feeder_gateway/get_contract_addresses", methods=["GET"])
def get_contract_addresses():
    return "No can do", 400

@app.route("/feeder_gateway/call_contract", methods=["POST"])
async def call_contract():
    raw_data = request.get_data()
    call_specifications = InvokeFunction.loads(raw_data)
    result_dict = await call_or_invoke("call",
        contract_address=call_specifications.contract_address,
        entry_point_selector=call_specifications.entry_point_selector,
        calldata=call_specifications.calldata
    )
    return jsonify(result_dict)

@app.route("/feeder_gateway/get_block", methods=["GET"])
def get_block():
    block_id = request.args.get("blockId", type=int)
    print(block_id)
    return "Not implemented", 501

@app.route("/feeder_gateway/get_code", methods=["GET"])
def get_code():
    block_id = request.args.get("blockId", type=int)
    print(block_id)

    contract_address = request.args.get("contractAddress", type=int)
    print(contract_address)
    return "Not implemented", 501

@app.route("/feeder_gateway/get_storage_at", methods=["GET"])
def get_storage_at():
    contract_address = request.args.get("contractAddress", type=int)
    print(contract_address)

    key = request.args.get("key")
    print(key)

    block_id = request.args.get("blockId", type=int)
    print(block_id)
    return "Not implemented", 501

@app.route("/feeder_gateway/get_transaction_status", methods=["GET"])
def get_transaction_status():
    transaction_id = request.args.get("transactionId", type=int)
    tx_status = (
        TxStatus.PENDING.name
        if is_transaction_id_legal(transaction_id)
        else TxStatus.NOT_RECEIVED.name
    )
    return jsonify({
        "tx_status": tx_status
    })

@app.route("/feeder_gateway/get_transaction", methods=["GET"])
def get_transaction():
    transaction_id = request.args.get("transactionId", type=int)
    if 0 <= transaction_id < len(transactions):
        return jsonify(transactions[transaction_id])
    else:
        return jsonify({
            "status": TxStatus.NOT_RECEIVED.name,
            "transaction_id": transaction_id
        })

if __name__ == "__main__":
    args = parse_args()
    app.run(**vars(args))
