"""Predeployed account tests"""

from test.settings import GATEWAY_URL

import pytest
import requests

from starkware.starknet.core.os.class_hash import compute_class_hash

from starknet_devnet.account import Account
from .util import (assert_equal, devnet_in_background)
from .support.assertions import assert_valid_schema

@pytest.mark.account_predeployed
def test_precomputed_contract_hash():
    """Test if the precomputed hash of the account contract is correct."""
    recalculated_hash = compute_class_hash(contract_class=Account.get_contract_class())
    assert_equal(recalculated_hash, Account.HASH)

@pytest.mark.account_predeployed
@devnet_in_background()
def test_predeployed_accounts_endpoint():
    '''Test if the endpoint return list of predeployed accounts'''
    response = requests.get(f"{GATEWAY_URL}/predeployed_accounts")
    assert response.status_code == 200
    assert_valid_schema(response.json(), 'predeployed_accounts.json')
