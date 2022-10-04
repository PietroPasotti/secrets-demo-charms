#!/usr/bin/env python3
# Copyright 2022 pietro
# See LICENSE file for licensing details.


import logging
from typing import Optional

from ops.charm import CharmBase, RelationChangedEvent
from ops.main import main
from ops.model import ActiveStatus, Secret, InvalidSecretIDError, BlockedStatus, WaitingStatus

logger = logging.getLogger(__name__)


class HolderCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.install, self._on_reset)
        self.framework.observe(self.on.do_secret_upgrade_action, self._on_do_secret_upgrade_action)
        self.framework.observe(self.on.secret_id_relation_changed, self._on_secret_change)
        self.framework.observe(self.on.secret_id_relation_broken, self._on_reset)
        self.framework.observe(self.on.secret_changed, self._on_secret_change)
        self.framework.observe(self.on.update_status, self._on_update_status)

    def _get_secret(self) -> Optional[Secret]:
        try:
            return self.model.get_secret('my-label')
        except InvalidSecretIDError as e:
            logger.error(e)
            return

    def _on_reset(self, _):
        self.unit.status = WaitingStatus('waiting for secret_id relation')

    def _on_do_secret_upgrade_action(self, _):
        self._on_update_status(update=True)

    def _on_secret_change(self, event: RelationChangedEvent):
        secret = self._get_secret()
        if not secret:
            try:
                sec_id = event.relation.data[event.app]['secret-id']
            except KeyError:
                self.unit.status = BlockedStatus('secret-id not provided by relation')
                return

            try:
                secret = self.model.get_secret(sec_id)
            except InvalidSecretIDError:
                self.unit.status = BlockedStatus(f'relation-provided secret-id {sec_id} is invalid')
                return

            secret.set_label('my-label')
            self._on_update_status()

    def _on_update_status(self, _=None, update: bool = False):
        secret = self._get_secret()
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
