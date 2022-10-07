#!/usr/bin/env python3
# Copyright 2022 pietro
# See LICENSE file for licensing details.


import logging
from typing import Optional

import ops.model
from ops.charm import CharmBase, RelationChangedEvent
from ops.main import main
from ops.model import ActiveStatus, _Secret, InvalidSecretIDError, BlockedStatus, WaitingStatus

logger = logging.getLogger(__name__)


class HolderCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.install, self._on_reset)
        self.framework.observe(self.on.do_secret_upgrade_action, self._on_do_secret_upgrade_action)
        self.framework.observe(self.on.secret_id_relation_changed, self._on_secret_provided)
        self.framework.observe(self.on.secret_id_relation_broken, self._on_reset)
        self.framework.observe(self.on.secret_changed, self._on_secret_change)
        self.framework.observe(self.on.update_status, self._on_update_status)

    def _has_secret(self):
        return len(self.model.relations.get('secret_id', ())) == 1

    def _obtain_secret(self) -> Optional[_Secret]:
        if not self._has_secret():
            return None
        relation = self.model.relations['secret_id'][0]
        secret_id = relation.data[relation.app]['secret-id']
        return self.model.get_secret(secret_id=secret_id, label='my-secret')

    @property
    def secret(self) -> _Secret:
        """only works AFTER self._obtain_secret has been called"""
        return self.model.get_secret(label='my-secret')

    def _on_reset(self, _):
        self.unit.status = WaitingStatus('waiting for secret_id relation')

    def _on_do_secret_upgrade_action(self, _):
        self._on_update_status(update=True)

    def _on_secret_change(self, event: RelationChangedEvent):
        try:
            secret = self._obtain_secret()
            if secret is None:
                self.unit.status = BlockedStatus(f'no secret relation could be found')
                return

        except ops.model.SecretsError:
            self.unit.status = BlockedStatus(f'relation-provided secret-id is invalid')
            return

        self._on_update_status()

    def _on_update_status(self, _=None, update: bool = False):
        secret = self._obtain_secret()
        if not secret:
            self.unit.status = WaitingStatus('waiting for secret_id relation')
            return

        username = secret.get('username', update=update)
        password = secret.get('password', update=update)

        username_peek = secret.get('username', peek=True)
        password_peek = secret.get('password', peek=True)

        if username_peek != username or password_peek != password:
            self.unit.status = ActiveStatus(f'{username}/{password} (new revision available!)')
        else:
            self.unit.status = ActiveStatus(f'{username}/{password}')


if __name__ == "__main__":
    main(HolderCharm)
