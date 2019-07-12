# -*- coding: utf-8 -*-
"""Keychain functions for zazu."""
__author__ = 'Nicholas Wiles'
__copyright__ = 'Copyright 2019'

import zazu.imports
zazu.imports.lazy_import(locals(), [
    'click',
    'keyring',
    'zazu',
    'zazu.config',
    'zazu.util'
])


class CredentialInterface(object):
    """Class that allows loading and saving of credentials from the keychain."""

    def __init__(self, name, url, attribute_list=None, secret_attribute_list=None, validator_callback=None):
        """Constructor.

        Args:
            name: the service name that these credentials are used for.
            url: the URL of the service.
            attribute_list: A list of attributes that will be stored in the keychain and are ok to show in clear text.
            secret_attribute_list: A list of attributes that should never be shown in clear text.

        """
        self._name = name
        self._url = url
        self._attributes = {}
        self._attribute_list = []
        if attribute_list is not None:
            self._attributes.update({a: None for a in attribute_list})
            self._attribute_list += attribute_list
        if secret_attribute_list is not None:
            self._attributes.update({a: None for a in secret_attribute_list})
            self._attribute_list += secret_attribute_list
        self._secret_attributes = secret_attribute_list
        self._validator_callback = validator_callback

    def name(self):
        """Gets the service type name for these credentials."""
        return self._name

    def url(self):
        """Gets the URL for these credentials."""
        return self._url

    def attributes(self):
        """Gets attribute names."""
        return self._attribute_list

    def __getitem__(self, item):
        return self._attributes[item]

    def __setitem__(self, item, value):
        self._attributes[item] = value

    def delete(self):
        """Deletes attributes from the keychain regardless of whether of not they exist."""
        for attribute in self._attribute_list:
            try:
                keyring.delete_password(self._url, attribute)
            except keyring.errors.PasswordDeleteError:
                pass

    def set_interactive(self):
        """Sets attributes interactively."""
        for attribute in self._attribute_list:
            item = click.prompt('Enter {} {} for {}'.format(self._name, attribute, self._url),
                                type=str, hide_input=(attribute in self._secret_attributes))
            if item is not None:
                self._attributes[attribute] = item

    def offer_to_save(self):
        if click.confirm('Do you want to save these credentials?', default=True):
            self.save()
            click.echo('Saved.')

    def load(self):
        """Loads attributes from the keychain and returns True if all were found."""
        for attribute in self._attribute_list:
            self._attributes[attribute] = keyring.get_password(self._url, attribute)
        return None not in self._attributes.values()

    def save(self):
        """Saves attributes to the keychain."""
        for name in self._attribute_list:
            keyring.set_password(self._url, name, self._attributes[name])

    def validate(self):
        """Returns True if all attributes have values and the validator_callback returns True (if on exists)."""
        return (None not in self._attributes.values() and
                (self._validator_callback is None or self._validator_callback(self)))


def escape_colons(s):
    return s.replace(':', '\\:')


def complete_entry(ctx, args, incomplete):
    creds = zazu.config.Config().credentials()
    return [(escape_colons(k), creds[k].name()) for k in sorted(creds.keys()) if k.startswith(incomplete)]


@click.command()
@zazu.config.pass_config
@click.pass_context
@click.option('-l', '--list', is_flag=True, help='list expected entries, whether they are set, and if they are valid')
@click.option('--set', is_flag=True, help='set or update an entry in the keychain')
@click.option('--unset', is_flag=True, help='remove an entry from the keychain')
@click.argument('entry_name', required=False, type=str, autocompletion=complete_entry)
def keychain(ctx, config, list, set, unset, entry_name):
    """Manage zazu credentials saved in the system keychain."""
    if not any([list, set, unset, entry_name]):
        print(ctx.get_help())
        ctx.exit(-1)
    if (set + unset + list) > 1:
        raise click.UsageError('--add, --unset, --list are mutually exclusive')
    if entry_name is None and (set or unset):
        raise click.UsageError('ENTRY_NAME is required')
    if entry_name is not None:
        if list:
            raise click.UsageError('ENTRY_NAME is not allowed with --list')
        if not (set or unset):
            raise click.UsageError('ENTRY_NAME requires --set or --unset')

    credentials = config.credentials()

    if list:
        statuses = [click.style('MISSING ', fg='red', bold=True),
                    click.style('REJECTED', fg='red', bold=True),
                    click.style('   OK   ', fg='green', bold=True)]
        for key, entry in sorted(credentials.items()):
            idx = 0 if not entry.load() else 1 if not entry.validate() else 2
            click.echo(zazu.util.format_checklist_item(idx, '{} ({})'.format(key, entry.name()), statuses))
        return

    try:
        entry = credentials[entry_name]
    except KeyError:
        raise click.ClickException('Keychain entry {} not known.'.format(entry_name))

    if set:
        entry.set_interactive()
        if entry.validate():
            entry.save()
        else:
            raise click.ClickException('{} rejected these credentials'.format(entry.url()))

    if unset:
        entry.delete()
