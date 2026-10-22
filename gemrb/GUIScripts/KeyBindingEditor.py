# SPDX-FileCopyrightText: 2026 Contributors to the GemRB project <https://gemrb.org>
# SPDX-License-Identifier: GPL-2.0-or-later
"""Staged action bindings and atomic profile persistence; no input dispatch."""
import os
from pathlib import Path
import tempfile


class BindingConflict(ValueError):
	pass


def normalize_key(value):
	value = value.lower()
	if value and (len(value) != 1 or value not in "abcdefghijklmnopqrstuvwxyz,./;'[]\\"):
		raise ValueError("Use one plain letter or , . / ; ' [ ] \\. Fixed and modified shortcuts are unchanged.")
	return value


def atomic_write(path, data):
	"""Replace only the nominated profile file; failed writes retain its bytes."""
	path = Path(path)
	with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".gemrb-keymap-", delete=False) as temp:
		name = temp.name
		try:
			temp.write(data)
			temp.flush()
			os.fsync(temp.fileno())
		except BaseException:
			temp.close()
			os.unlink(name)
			raise
	try:
		os.replace(name, path)
	finally:
		if os.path.exists(name): os.unlink(name)


class Draft:
	def __init__(self, rows):
		self.original = {row["name"]: row["key"] for row in rows}
		self.defaults = {row["name"]: row["default"] for row in rows}
		self.working = dict(self.original)

	def assign(self, action, key, replace=False):
		if action not in self.working: raise ValueError("Unknown action")
		key = normalize_key(key)
		conflicts = [name for name, current in self.working.items() if name != action and key and current == key]
		if conflicts and not replace:
			raise BindingConflict("%s is assigned to %s. Replace explicitly or choose another key." % (key.upper(), conflicts[0].replace("_", " ")))
		for name in conflicts: self.working[name] = ""
		self.working[action] = key

	def reset(self):
		self.working = dict(self.defaults)

	def apply(self, api, profile, rebind):
		current = {row["name"]: row["key"] for row in api.GetKeyBindings()}
		if current != self.original: raise ValueError("Bindings changed while this editor was open; reopen before applying.")
		api.SetKeyBindings(self.working, True)
		profile = Path(profile)
		if not profile.is_dir(): raise ValueError("Save profile directory unavailable")
		path = profile / "gemrb-keymap.ini"
		old = path.read_bytes() if path.exists() else None
		data = "; GemRB profile bindings v1; original game keymap is unchanged.\n[Bindings]\n"
		data += "".join("%s=%s\n" % (name, key) for name, key in sorted(self.working.items()))
		atomic_write(path, data.encode("ascii"))
		try:
			api.SetKeyBindings(self.working)
			rebind(self.working)
		except Exception:
			# Restore both routes and persistence if any live rebind fails. Keep a
			# rollback failure visible; never label a partially applied edit saved.
			try:
				api.SetKeyBindings(self.original)
				rebind(self.original)
			finally:
				if old is None: path.unlink()
				else: atomic_write(path, old)
			raise
		self.original = dict(self.working)

