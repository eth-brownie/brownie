#!/usr/bin/python3
# VERSION 1.0 - October 6, 2017

import base64
from cryptography.fernet import Fernet,InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os


class FernetKey:
	
	def __init__(self,password):
		password=password.encode('utf-8')
		kdf=PBKDF2HMAC(algorithm=hashes.SHA256(),length=32,salt=password,iterations=100000,backend=default_backend())
		self._key=Fernet(base64.urlsafe_b64encode(kdf.derive(password)))
	
	def encrypt(self,message,as_bytes=True):
		if type(message) is not bytes: message=message.encode('utf-8')
		return self._key.encrypt(message) if as_bytes else self._key.encrypt(message).decode('utf-8')
	
	def decrypt(self,message):
		if type(message) is not bytes: message=message.encode('utf-8')
		return self._key.decrypt(message).decode('utf-8')