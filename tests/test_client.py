# Copyright 2021-2022 Zenauth Ltd.
# SPDX-License-Identifier: Apache-2.0

import pytest

from cerbos.sdk.client import CerbosClient, PrincipalContext
from cerbos.sdk.model import *


class TestCerbosClient:
    def test_is_healthy(self, cerbos_client: CerbosClient):
        have = cerbos_client.is_healthy()
        assert have == True

    def test_is_allowed(self, cerbos_client: CerbosClient):
        p = Principal(
            "john",
            roles={"employee"},
            policy_version="20210210",
            attr={"department": "marketing", "geography": "GB", "team": "design"},
        )
        r = Resource(
            "XX125",
            "leave_request",
            policy_version="20210210",
            attr={
                "id": "XX125",
                "department": "marketing",
                "geography": "GB",
                "team": "design",
                "owner": "john",
            },
        )

        have = cerbos_client.is_allowed("view:public", p, r)
        assert have == True

    def test_principal_context_is_allowed(self, principal_ctx: PrincipalContext):
        r = Resource(
            "XX125",
            "leave_request",
            policy_version="20210210",
            attr={
                "id": "XX125",
                "department": "marketing",
                "geography": "GB",
                "team": "design",
                "owner": "john",
            },
        )

        have = principal_ctx.is_allowed("view:public", r)
        assert have == True

    def test_check_resources(self, cerbos_client: CerbosClient):
        p = Principal(
            "john",
            roles={"employee"},
            policy_version="20210210",
            attr={"department": "marketing", "geography": "GB", "team": "design"},
        )

        resources = [
            ResourceAction(
                resource=Resource(
                    "XX125",
                    "leave_request",
                    policy_version="20210210",
                    attr={
                        "id": "XX125",
                        "department": "marketing",
                        "geography": "GB",
                        "team": "design",
                        "owner": "john",
                    },
                ),
                actions={"view:public", "approve"},
            ),
            ResourceAction(
                resource=Resource(
                    "XX225",
                    "leave_request",
                    policy_version="20210210",
                    attr={
                        "id": "XX225",
                        "department": "marketing",
                        "geography": "GB",
                        "team": "design",
                        "owner": "alice",
                        "status": "PENDING_APPROVAL",
                    },
                ),
                actions={"view:private", "approve"},
            ),
        ]

        have = cerbos_client.check_resources(p, ResourceList(resources))
        assert have.failed() == False

        xx125 = have.get_resource(
            "XX125", predicate=lambda r: r.policy_version == "20210210"
        )
        assert xx125 is not None
        assert xx125.is_allowed("view:public") == True
        assert xx125.is_allowed("approve") == False

        xx225 = have.get_resource("XX225")
        assert xx225 is not None
        assert xx225.is_allowed("view:public") == False
        assert xx225.is_allowed("approve") == False

        zz225 = have.get_resource("ZZ225")
        assert zz225 is None

    def test_check_resources_empty_resources(self, cerbos_client: CerbosClient):
        p = Principal(
            "john",
            roles={"employee"},
            policy_version="20210210",
            attr={"department": "marketing", "geography": "GB", "team": "design"},
        )

        have = cerbos_client.check_resources(p, ResourceList())
        assert have.failed() == True
        assert have.status_msg.code == 3

        with pytest.raises(CerbosRequestException):
            have.raise_if_failed()


@pytest.fixture
def principal_ctx(cerbos_client):
    p = Principal(
        "john",
        roles={"employee"},
        policy_version="20210210",
        attr={"department": "marketing", "geography": "GB", "team": "design"},
    )

    return cerbos_client.with_principal(p)