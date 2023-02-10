#!/usr/bin/env python3
# Copyright 2022 pietro
# See LICENSE file for licensing details.

import logging
import random

from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, WaitingStatus, Relation

logger = logging.getLogger(__name__)


class OwnerCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.install, self._on_reset)
        self.framework.observe(self.on.secret_id_relation_broken, self._on_reset)
        self.framework.observe(self.on.secret_id_relation_created, self._push_secret)
        self.framework.observe(self.on.do_secret_rotate_action, self._on_do_secret_rotate_action)

    @property
    def secret_relation(self) -> Relation:
        return self.model.get_relation('secret_id')

    def _on_reset(self, _):
        self.unit.status = WaitingStatus('waiting for secret_id relation')

    @staticmethod
    def _create_new_secret_contents(revision: int):
        username = f"username"
        password = "".join(map(str, (random.randrange(9, 9999) for _ in range(5))))
        return {
            'username': username,
            'password': password
        }

    def _on_do_secret_rotate_action(self, _):
        self._push_secret(None)

    def _push_secret(self, _):
        content = self._create_new_secret_contents(0)
        self.secret_relation.data[self.app]['username'] = content['username']
        self.secret_relation.data[self.app]['password'] = content['password']
        self.unit.status = ActiveStatus('secret published')


if __name__ == "__main__":
    main(OwnerCharm)
