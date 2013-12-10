#!/usr/bin/python
#
# Copyright (c) 2014 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Pretty print (and check) a set of group/user accounts"""

from __future__ import print_function

import collections
import glob
import os
import sys


# Objects to hold group/user accounts.
Group = collections.namedtuple('Group', ['group', 'password', 'gid', 'users'])
User = collections.namedtuple('User', ['user', 'password', 'uid', 'gid',
                                       'gecos', 'home', 'shell'])


def _ParseAccount(content, obj, defaults):
  """Parse the raw data in |content| and return a new |obj|"""
  d = defaults.copy()

  for line in content.splitlines():
    if not line or line.startswith('#'):
      continue

    key, val = line.split(':')
    if key not in obj._fields:
      raise ValueError('unknown key: %s' % key)
    d[key] = val

  missing_keys = set(obj._fields) - set(d.keys())
  if missing_keys:
    raise ValueError('missing keys: %s' % ' '.join(missing_keys))

  return obj(**d)


def ParseGroup(content):
  """Parse |content| as a Group object"""
  defaults = {
      'password': '!',
      'users': '',
  }
  return _ParseAccount(content, Group, defaults)


def ParseUser(content):
  """Parse |content| as a User object"""
  defaults = {
      'gecos': '',
      'home': '/dev/null',
      'password': '!',
      'shell': '/bin/false',
  }
  return _ParseAccount(content, User, defaults)


def AlignWidths(arr):
  """Calculate a set of widths for alignment

  Args:
    arr: An array of collections.namedtuple objects

  Returns:
    A dict whose fields have the max length
  """
  d = {}
  for f in arr[0]._fields:
    d[f] = 0

  for a in arr:
    for f in a._fields:
      d[f] = max(d[f], len(getattr(a, f)))

  return d


def DisplayAccounts(accts, order):
  """Display |accts| as a table using |order| for field ordering

  Args:
    accts: An array of collections.namedtuple objects
    order: The order in which to display the members
  """
  obj = type(accts[0])
  header_obj = obj(**dict([(k, (v if v else k).upper()) for k, v in order]))
  keys = [k for k, _ in order]
  sorter = lambda x: int(getattr(x, keys[0]))

  widths = AlignWidths([header_obj] + accts)
  def p(obj):
    for k in keys:
      print('%-*s ' % (widths[k], getattr(obj, k)), end='')
    print()

  for a in [header_obj] + sorted(accts, key=sorter):
    p(a)


def main(args):
  if not args:
    accounts_dir = os.path.dirname(os.path.realpath(__file__))
    args = (glob.glob(os.path.join(accounts_dir, 'group', '*')) +
            glob.glob(os.path.join(accounts_dir, 'user', '*')))

  groups = []
  users = []
  for f in args:
    try:
      content = open(f).read()
      if 'group:' in content:
        groups.append(ParseGroup(content))
      else:
        users.append(ParseUser(content))
    except ValueError as e:
      print('error: %s: %s' % (f, e))
      return os.EX_DATAERR

  if groups:
    order = (
        ('gid', ''),
        ('group', ''),
        ('password', 'pass'),
        ('users', ''),
    )
    DisplayAccounts(groups, order)

  if users:
    if groups:
      print()
    order = (
        ('uid', ''),
        ('gid', ''),
        ('user', ''),
        ('shell', ''),
        ('home', ''),
        ('password', 'pass'),
        ('gecos', ''),
    )
    DisplayAccounts(users, order)


if __name__ == '__main__':
  exit(main(sys.argv[1:]))
