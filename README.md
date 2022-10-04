# Secrets demo charms

This repo contains two charms meant to demo the juju3.x Secrets feature.

Usage:

```bash
cd holder
charmcraft pack
juju deploy ./<holder>.charm holder

cd ../owner
charmcraft pack
juju deploy ./<owner>.charm owner

juju relate owner holder
``` 

You can mock the owner's secret management to some extent by, before `relate`, configuring:
 
 - `grant`: whether the secret is to be granted to the holder on creation or not
 - `expire`: expiration date (iso format)
 - `rotate`: rotation policy. one of `['never', 'hourly', 'daily', 'weekly', 'monthly', 'quarterly', 'yearly']`

Every time you relate owner-holder, owner will create a new Secret giving it these settings. So in order to apply them (after some change), you'll need to remove the relation and re-apply it.

The owner also has an action:

    `juju run owner/0 do-secret-rotate`

that will cause the owner to publish a new revision of the secret, generating a new secret-instance-unique username/password pair. 

You should be able to observe that the holder charm knows that a new revision is available (secret-changed). Its status will change to say: `new revision available`.
At that point you should be able to run on the holder:

    `juju run holder/0 do-secret-upgrade

this will cause the holder to fetch the newest secret revision (and update to it).

The owner will now receive a secret-remove event informing it that an outdated revision can be removed.


# Testing with bleeding-edge locally-installed ops

If you are using this bundle to test a bleeding-edge ops release (not released yet), you might want to use the following command to inject and keep in sync your local ops source to the live units:

```bash
 ljhack sync ~/canonical/operator/ops owner/0 --remote-root  /var/lib/juju/agents/unit-owner-0/charm/venv/ops
 ljhack sync ~/canonical/operator/ops holder/0 --remote-root  /var/lib/juju/agents/unit-holder-0/charm/venv/ops 
 ```
