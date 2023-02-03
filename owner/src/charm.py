#!/usr/bin/env python3
# Copyright 2022 pietro
# See LICENSE file for licensing details.

import logging
from datetime import datetime

from ops.charm import CharmBase, RelationChangedEvent, SecretRotateEvent, SecretExpiredEvent, SecretRemoveEvent
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, WaitingStatus, SecretRotate, Secret

logger = logging.getLogger(__name__)


class OwnerCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.install, self._setup)
        self.framework.observe(self.on.secret_id_relation_created, self._push_secret)
        self.framework.observe(self.on.secret_id_relation_broken, self._remove_secret)
        self.framework.observe(self.on.do_secret_rotate_action, self._on_do_secret_rotate_action)

        self.framework.observe(self.on.secret_rotate, self._on_secret_rotate)
        self.framework.observe(self.on.secret_expired, self._on_secret_expired)
        self.framework.observe(self.on.secret_remove, self._on_secret_remove)

    def _on_secret_remove(self, event: SecretRemoveEvent):
        revision = event.secret.get_info().revision
        event.secret.remove_revision(revision)
        logger.debug(f'secret {event.secret.label!r} revision {revision}'
                     f'{event.secret} is no longer '
                     f'in use and has been pruned.')

    def _on_secret_rotate(self, _: SecretRotateEvent):
        self.unit.status = BlockedStatus(
            'secret needs to be rotated!'
            'run do-secret-rotate to publish a new revision.')

    def _on_secret_expired(self, _: SecretExpiredEvent):
        self.unit.status = BlockedStatus(
            'secret is expired!'
            'run do-secret-rotate to publish a new revision.')

    def _create_secret(self):
        secret = self.unit.add_secret(
            {'username': 'admin',
             'password': 'admin'},
            expire=datetime.fromisoformat(self.config['expire']),
            rotate=SecretRotate(self.config['rotate']),
            label='this-label'
        )
        return secret

    @property
    def secret(self) -> Secret:
        return self.model.get_secret(label='this-label')

    def _setup(self, _):
        self.unit.status = WaitingStatus('waiting for secret_id relation')

    @staticmethod
    def _create_new_secret_contents(secret: Secret):
        revision = secret.get_info().revision
        username = f"username-rev-{revision + 1}"
        password = f"password-rev-{revision + 1}"
        return {
            'username': username,
            'password': password
        }

    def _on_cleanup_old_revisions(self, _):
        self.secret.remove_all_revisions()

    def _on_do_secret_rotate_action(self, _):
        secret = self.secret
        revision_content = self._create_new_secret_contents(secret)
        secret.set_content(revision_content)
        secret.set_info(description='this new revision')

    def _remove_secret(self, event: RelationChangedEvent):
        secret = self.secret
        secret.revoke(event.relation)
        secret.remove_all_revisions()

    def _push_secret(self, event: RelationChangedEvent):
        secret = self._create_secret()

        if self.config['grant']:
            logger.debug('secret granted')
            secret.grant(event.relation)
        else:
            logger.warning('secret NOT granted')

        self.unit.status = ActiveStatus(f'published secret ID {secret.id}')
        relation = self.model.relations['secret_id'][0]
        relation.data[self.app]['secret-id'] = secret.id


if __name__ == "__main__":
    main(OwnerCharm)
