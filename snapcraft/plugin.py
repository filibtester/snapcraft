# -*- Mode:Python; indent-tabs-mode:t; tab-width:4 -*-

import importlib.machinery
import os
import snapcraft
import subprocess
import sys
import yaml


class Plugin:

	def __init__(self, pluginDir, name, partName, properties):
		self.valid = False
		self.code = None
		self.config = None
		self.partNames = []

		self.sourcedir = os.path.join(os.getcwd(), "parts", partName, "src")
		self.builddir = os.path.join(os.getcwd(), "parts", partName, "build")
		self.stagedir = os.path.join(os.getcwd(), "staging")
		self.snapdir = os.path.join(os.getcwd(), "snap")

		configPath = os.path.join(pluginDir, name + ".yaml")
		if not os.path.exists(configPath):
			print("Missing config for part %s" % (name), file=sys.stderr)
			return
		self.config = yaml.load(open(configPath, 'r')) or {}

		codePath = os.path.join(pluginDir, name + ".py")
		if os.path.exists(codePath):
			class Options(): pass
			options = Options()

			for opt in self.config.get('options', []):
				if opt in properties:
					setattr(options, opt, properties[opt])
				else:
					if self.config['options'][opt].get('required', False):
						print("Required field %s missing on part %s" % (opt, name), file=sys.stderr)
						return
					setattr(options, opt, None)

			loader = importlib.machinery.SourceFileLoader("snapcraft.plugins." + name, codePath)
			module = loader.load_module()
			for propName in dir(module):
				prop = getattr(module, propName)
				if issubclass(prop, snapcraft.BaseHandler):
					self.code = prop(partName, options)
					break

		self.partNames.append(partName)
		self.valid = True

	def isValid(self):
		return self.valid

	def names(self):
		return self.partNames

	def notifyStage(self, stage):
		print('\033[01m' + stage + " " + self.partNames[0] + '\033[0m')

	def init(self):
		if self.code and hasattr(self.code, 'init'):
			return getattr(self.code, 'init')()

	def pull(self):
		try: os.makedirs(self.sourcedir)
		except: pass
		if self.code and hasattr(self.code, 'pull'):
			self.notifyStage("Pulling")
			return getattr(self.code, 'pull')()

	def build(self):
		try: os.makedirs(self.builddir)
		except: pass
		subprocess.call(['cp', '-Trf', self.sourcedir, self.builddir])
		if self.code and hasattr(self.code, 'build'):
			self.notifyStage("Building")
			return getattr(self.code, 'build')()

	def test(self):
		if self.code and hasattr(self.code, 'test'):
			self.notifyStage("Testing")
			return getattr(self.code, 'test')()

	def stage(self):
		try: os.makedirs(self.stagedir)
		except: pass
		if self.code and hasattr(self.code, 'stage'):
			self.notifyStage("Staging")
			return getattr(self.code, 'stage')()

	def deploy(self):
		try: os.makedirs(self.snapdir)
		except: pass
		if self.code and hasattr(self.code, 'deploy'):
			self.notifyStage("Deploying")
			return getattr(self.code, 'deploy')()

	def env(self):
		if self.code and hasattr(self.code, 'env'):
			return getattr(self.code, 'env')()
		return []