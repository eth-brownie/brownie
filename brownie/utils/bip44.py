"""This submodule provides the PublicKey, PrivateKey, and Signature classes.
It also provides HDPublicKey and HDPrivateKey classes for working with HD
wallets."""

# https://github.com/michailbrynard/ethereum-bip44-python

# Copyright (c) 2017-2018, Michail Brynard
# Copyright (c) 2015-2017, 21 Inc.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of 21 Inc.


import math
import base58
import base64
import hashlib
import hmac
from mnemonic.mnemonic import Mnemonic
import random
from two1.bitcoin.utils import bytes_to_str
from two1.bitcoin.utils import address_to_key_hash
from two1.bitcoin.utils import rand_bytes
from two1.crypto.ecdsa_base import Point
from two1.crypto.ecdsa import ECPointAffine
from two1.crypto.ecdsa import secp256k1

bitcoin_curve = secp256k1()

from eth_utils import encode_hex

from Crypto.Hash import keccak
sha3_256 = lambda x: keccak.new(digest_bits=256, data=x)


def sha3(seed):
    return sha3_256(seed).digest()


def get_bytes(s):
    """Returns the byte representation of a hex- or byte-string."""
    if isinstance(s, bytes):
        b = s
    elif isinstance(s, str):
        b = bytes.fromhex(s)
    else:
        raise TypeError("s must be either 'bytes' or 'str'!")

    return b


class PrivateKeyBase(object):
    """ Base class for both PrivateKey and HDPrivateKey.

    As this class is a base class it should not be used directly.

    Args:
        k (int): The private key.

    Returns:
        PrivateKey: The object representing the private key.
    """

    @staticmethod
    def from_b58check(private_key):
        """ Decodes a Base58Check encoded private-key.

        Args:
            private_key (str): A Base58Check encoded private key.

        Returns:
            PrivateKey: A PrivateKey object
        """
        raise NotImplementedError

    def __init__(self, k):
        self.key = k
        self._public_key = None

    @property
    def public_key(self):
        """ Returns the public key associated with this private key.

        Returns:
            PublicKey:
                The PublicKey object that corresponds to this
                private key.
        """
        return self._public_key

    def raw_sign(self, message, do_hash=True):
        """ Signs message using this private key.

        Args:
            message (bytes): The message to be signed. If a string is
               provided it is assumed the encoding is 'ascii' and
               converted to bytes. If this is not the case, it is up
               to the caller to convert the string to bytes
               appropriately and pass in the bytes.
            do_hash (bool): True if the message should be hashed prior
               to signing, False if not. This should always be left as
               True except in special situations which require doing
               the hash outside (e.g. handling Bitcoin bugs).

        Returns:
            ECPointAffine:
                a raw point (r = pt.x, s = pt.y) which is
                the signature.
        """
        raise NotImplementedError

    def sign(self, message, do_hash=True):
        """ Signs message using this private key.

        Note:
            This differs from `raw_sign()` since it returns a
            Signature object.

        Args:
            message (bytes or str): The message to be signed. If a
               string is provided it is assumed the encoding is
               'ascii' and converted to bytes. If this is not the
               case, it is up to the caller to convert the string to
               bytes appropriately and pass in the bytes.
            do_hash (bool): True if the message should be hashed prior
               to signing, False if not. This should always be left as
               True except in special situations which require doing
               the hash outside (e.g. handling Bitcoin bugs).

        Returns:
            Signature: The signature corresponding to message.
        """
        raise NotImplementedError

    def sign_bitcoin(self, message, compressed=False):
        """ Signs a message using this private key such that it
        is compatible with bitcoind, bx, and other Bitcoin
        clients/nodes/utilities.

        Note:
            0x18 + b\"Bitcoin Signed Message:" + newline + len(message) is
            prepended to the message before signing.

        Args:
            message (bytes or str): Message to be signed.
            compressed (bool): True if the corresponding public key will be
              used in compressed format. False if the uncompressed version
              is used.

        Returns:
            bytes: A Base64-encoded byte string of the signed message.
            The first byte of the encoded message contains information
            about how to recover the public key. In bitcoind parlance,
            this is the magic number containing the recovery ID and
            whether or not the key was compressed or not. (This function
            always processes full, uncompressed public-keys, so the magic
            number will always be either 27 or 28).
        """
        raise NotImplementedError

    def to_b58check(self, testnet=False):
        """ Generates a Base58Check encoding of this private key.

        Returns:
            str: A Base58Check encoded string representing the key.
        """
        raise NotImplementedError

    def to_hex(self):
        """ Generates a hex encoding of the serialized key.

        Returns:
           str: A hex encoded string representing the key.
        """
        return bytes_to_str(bytes(self))

    def __bytes__(self):
        raise NotImplementedError

    def __int__(self):
        raise NotImplementedError


class PublicKeyBase(object):
    """ Base class for both PublicKey and HDPublicKey.

    As this class is a base class it should not be used directly.

    Args:
        x (int): The x component of the public key point.
        y (int): The y component of the public key point.

    Returns:
        PublicKey: The object representing the public key.

    """

    @staticmethod
    def from_bytes(key_bytes):
        """ Generates a public key object from a byte (or hex) string.

        Args:
            key_bytes (bytes or str): A byte stream.

        Returns:
            PublicKey: A PublicKey object.
        """
        raise NotImplementedError

    @staticmethod
    def from_private_key(private_key):
        """ Generates a public key object from a PrivateKey object.

        Args:
            private_key (PrivateKey): The private key object from
               which to derive this object.

        Returns:
            PublicKey: A PublicKey object.
        """
        return private_key.public_key

    def __init__(self):
        pass

    def hash160(self, compressed=True):
        """ Return the RIPEMD-160 hash of the SHA-256 hash of the
        public key.

        Args:
            compressed (bool): Whether or not the compressed key should
               be used.
        Returns:
            bytes: RIPEMD-160 byte string.
        """
        raise NotImplementedError

    def address(self, compressed=True, testnet=False):
        """ Address property that returns the Base58Check
        encoded version of the HASH160.

        Args:
            compressed (bool): Whether or not the compressed key should
               be used.
            testnet (bool): Whether or not the key is intended for testnet
               usage. False indicates mainnet usage.

        Returns:
            bytes: Base58Check encoded string
        """
        raise NotImplementedError

    def verify(self, message, signature, do_hash=True):
        """ Verifies that message was appropriately signed.

        Args:
            message (bytes): The message to be verified.
            signature (Signature): A signature object.
            do_hash (bool): True if the message should be hashed prior
              to signing, False if not. This should always be left as
              True except in special situations which require doing
              the hash outside (e.g. handling Bitcoin bugs).

        Returns:
            verified (bool): True if the signature is verified, False
            otherwise.
        """
        raise NotImplementedError

    def to_hex(self):
        """ Hex representation of the serialized byte stream.

        Returns:
            h (str): A hex-encoded string.
        """
        return bytes_to_str(bytes(self))

    def __bytes__(self):
        raise NotImplementedError

    def __int__(self):
        raise NotImplementedError

    @property
    def compressed_bytes(self):
        """ Byte string corresponding to a compressed representation
        of this public key.

        Returns:
            b (bytes): A 33-byte long byte string.
        """
        raise NotImplementedError


class PrivateKey(PrivateKeyBase):
    """ Encapsulation of a Bitcoin ECDSA private key.

    This class provides capability to generate private keys,
    obtain the corresponding public key, sign messages and
    serialize/deserialize into a variety of formats.

    Args:
        k (int): The private key.

    Returns:
        PrivateKey: The object representing the private key.
    """
    TESTNET_VERSION = 0xEF
    MAINNET_VERSION = 0x80

    @staticmethod
    def from_bytes(b):
        """ Generates PrivateKey from the underlying bytes.

        Args:
            b (bytes): A byte stream containing a 256-bit (32-byte) integer.

        Returns:
            tuple(PrivateKey, bytes): A PrivateKey object and the remainder
            of the bytes.
        """
        if len(b) < 32:
            raise ValueError('b must contain at least 32 bytes')

        return PrivateKey(int.from_bytes(b[:32], 'big'))

    @staticmethod
    def from_hex(h):
        """ Generates PrivateKey from a hex-encoded string.

        Args:
            h (str): A hex-encoded string containing a 256-bit
                 (32-byte) integer.

        Returns:
            PrivateKey: A PrivateKey object.
        """
        return PrivateKey.from_bytes(bytes.fromhex(h))

    @staticmethod
    def from_int(i):
        """ Initializes a private key from an integer.

        Args:
            i (int): Integer that is the private key.

        Returns:
            PrivateKey: The object representing the private key.
        """
        return PrivateKey(i)

    @staticmethod
    def from_b58check(private_key):
        """ Decodes a Base58Check encoded private-key.

        Args:
            private_key (str): A Base58Check encoded private key.

        Returns:
            PrivateKey: A PrivateKey object
        """
        b58dec = base58.b58decode_check(private_key)
        version = b58dec[0]
        assert version in [PrivateKey.TESTNET_VERSION,
                           PrivateKey.MAINNET_VERSION]

        return PrivateKey(int.from_bytes(b58dec[1:], 'big'))

    @staticmethod
    def from_random():
        """ Initializes a private key from a random integer.

        Returns:
            PrivateKey: The object representing the private key.
        """
        return PrivateKey(random.SystemRandom().randrange(1, bitcoin_curve.n))

    def __init__(self, k):
        self.key = k
        self._public_key = None

    @property
    def public_key(self):
        """ Returns the public key associated with this private key.

        Returns:
            PublicKey:
                The PublicKey object that corresponds to this
                private key.
        """
        if self._public_key is None:
            self._public_key = PublicKey.from_point(
                bitcoin_curve.public_key(self.key))
        return self._public_key

    def raw_sign(self, message, do_hash=True):
        """ Signs message using this private key.

        Args:
            message (bytes): The message to be signed. If a string is
                provided it is assumed the encoding is 'ascii' and
                converted to bytes. If this is not the case, it is up
                to the caller to convert the string to bytes
                appropriately and pass in the bytes.
            do_hash (bool): True if the message should be hashed prior
                to signing, False if not. This should always be left as
                True except in special situations which require doing
                the hash outside (e.g. handling Bitcoin bugs).

        Returns:
            ECPointAffine:
                a raw point (r = pt.x, s = pt.y) which is
                the signature.
        """
        if isinstance(message, str):
            msg = bytes(message, 'ascii')
        elif isinstance(message, bytes):
            msg = message
        else:
            raise TypeError("message must be either str or bytes!")

        sig_pt, rec_id = bitcoin_curve.sign(msg, self.key, do_hash)

        # Take care of large s:
        # Bitcoin deals with large s, by subtracting
        # s from the curve order. See:
        # https://bitcointalk.org/index.php?topic=285142.30;wap2
        if sig_pt.y >= (bitcoin_curve.n // 2):
            sig_pt = Point(sig_pt.x, bitcoin_curve.n - sig_pt.y)
            rec_id ^= 0x1

        return (sig_pt, rec_id)

    def sign(self, message, do_hash=True):
        """ Signs message using this private key.

        Note:
            This differs from `raw_sign()` since it returns a Signature object.

        Args:
            message (bytes or str): The message to be signed. If a
                string is provided it is assumed the encoding is
                'ascii' and converted to bytes. If this is not the
                case, it is up to the caller to convert the string to
                bytes appropriately and pass in the bytes.
            do_hash (bool): True if the message should be hashed prior
                to signing, False if not. This should always be left as
                True except in special situations which require doing
                the hash outside (e.g. handling Bitcoin bugs).

        Returns:
            Signature: The signature corresponding to message.
        """
        # Some BTC things want to have the recovery id to extract the public
        # key, so we should figure that out.
        sig_pt, rec_id = self.raw_sign(message, do_hash)

        return Signature(sig_pt.x, sig_pt.y, rec_id)

    def sign_bitcoin(self, message, compressed=False):
        """ Signs a message using this private key such that it
        is compatible with bitcoind, bx, and other Bitcoin
        clients/nodes/utilities.

        Note:
            0x18 + b\"Bitcoin Signed Message:" + newline + len(message) is
            prepended to the message before signing.

        Args:
            message (bytes or str): Message to be signed.
            compressed (bool): True if the corresponding public key will be
              used in compressed format. False if the uncompressed version
              is used.

        Returns:
            bytes: A Base64-encoded byte string of the signed message.
            The first byte of the encoded message contains information
            about how to recover the public key. In bitcoind parlance,
            this is the magic number containing the recovery ID and
            whether or not the key was compressed or not.
        """
        if isinstance(message, str):
            msg_in = bytes(message, 'ascii')
        elif isinstance(message, bytes):
            msg_in = message
        else:
            raise TypeError("message must be either str or bytes!")

        msg = b"\x18Bitcoin Signed Message:\n" + bytes([len(msg_in)]) + msg_in
        msg_hash = hashlib.sha256(msg).digest()

        sig = self.sign(msg_hash)
        comp_adder = 4 if compressed else 0
        magic = 27 + sig.recovery_id + comp_adder

        return base64.b64encode(bytes([magic]) + bytes(sig))

    def to_b58check(self, testnet=False):
        """ Generates a Base58Check encoding of this private key.

        Returns:
            str: A Base58Check encoded string representing the key.
        """
        version = self.TESTNET_VERSION if testnet else self.MAINNET_VERSION
        return base58.b58encode_check(bytes([version]) + bytes(self))

    def __bytes__(self):
        return self.key.to_bytes(32, 'big')

    def __int__(self):
        return self.key


class PublicKey(PublicKeyBase):
    """ Encapsulation of a Bitcoin ECDSA public key.

    This class provides a high-level API to using an ECDSA public
    key, specifically for Bitcoin (secp256k1) purposes.

    Args:
        x (int): The x component of the public key point.
        y (int): The y component of the public key point.

    Returns:
        PublicKey: The object representing the public key.
    """

    TESTNET_VERSION = 0x6F
    MAINNET_VERSION = 0x00

    @staticmethod
    def from_point(p):
        """ Generates a public key object from any object
        containing x, y coordinates.

        Args:
            p (Point): An object containing a two-dimensional, affine
               representation of a point on the secp256k1 curve.

        Returns:
            PublicKey: A PublicKey object.
        """
        return PublicKey(p.x, p.y)

    @staticmethod
    def from_int(i):
        """ Generates a public key object from an integer.

        Note:
            This assumes that the upper 32 bytes of the integer
            are the x component of the public key point and the
            lower 32 bytes are the y component.

        Args:
            i (Bignum): A 512-bit integer representing the public
               key point on the secp256k1 curve.

        Returns:
            PublicKey: A PublicKey object.
        """
        point = ECPointAffine.from_int(bitcoin_curve, i)
        return PublicKey.from_point(point)

    @staticmethod
    def from_base64(b64str, testnet=False):
        """ Generates a public key object from a Base64 encoded string.

        Args:
            b64str (str): A Base64-encoded string.
            testnet (bool) (Optional): If True, changes the version that
               is prepended to the key.

        Returns:
            PublicKey: A PublicKey object.
        """
        return PublicKey.from_bytes(base64.b64decode(b64str))

    @staticmethod
    def from_bytes(key_bytes):
        """ Generates a public key object from a byte (or hex) string.

        The byte stream must be of the SEC variety
        (http://www.secg.org/): beginning with a single byte telling
        what key representation follows. A full, uncompressed key
        is represented by: 0x04 followed by 64 bytes containing
        the x and y components of the point. For compressed keys
        with an even y component, 0x02 is followed by 32 bytes
        containing the x component. For compressed keys with an
        odd y component, 0x03 is followed by 32 bytes containing
        the x component.

        Args:
            key_bytes (bytes or str): A byte stream that conforms to the above.

        Returns:
            PublicKey: A PublicKey object.
        """
        b = get_bytes(key_bytes)
        key_bytes_len = len(b)

        key_type = b[0]
        if key_type == 0x04:
            # Uncompressed
            if key_bytes_len != 65:
                raise ValueError("key_bytes must be exactly 65 bytes long when uncompressed.")

            x = int.from_bytes(b[1:33], 'big')
            y = int.from_bytes(b[33:65], 'big')
        elif key_type == 0x02 or key_type == 0x03:
            if key_bytes_len != 33:
                raise ValueError("key_bytes must be exactly 33 bytes long when compressed.")

            x = int.from_bytes(b[1:33], 'big')
            ys = bitcoin_curve.y_from_x(x)

            # Pick the one that corresponds to key_type
            last_bit = key_type - 0x2
            for y in ys:
                if y & 0x1 == last_bit:
                    break
        else:
            return None

        return PublicKey(x, y)

    @staticmethod
    def from_hex(h):
        """ Generates a public key object from a hex-encoded string.

        See from_bytes() for requirements of the hex string.

        Args:
            h (str): A hex-encoded string.

        Returns:
            PublicKey: A PublicKey object.
        """
        return PublicKey.from_bytes(h)

    @staticmethod
    def from_signature(message, signature):
        """ Attempts to create PublicKey object by deriving it
        from the message and signature.

        Args:
            message (bytes): The message to be verified.
            signature (Signature): The signature for message.
               The recovery_id must not be None!

        Returns:
            PublicKey:
                A PublicKey object derived from the
                signature, it it exists. None otherwise.
        """
        if signature.recovery_id is None:
            raise ValueError("The signature must have a recovery_id.")

        msg = get_bytes(message)
        pub_keys = bitcoin_curve.recover_public_key(msg,
                                                    signature,
                                                    signature.recovery_id)

        for k, recid in pub_keys:
            if signature.recovery_id is not None and recid == signature.recovery_id:
                return PublicKey(k.x, k.y)

        return None

    @staticmethod
    def verify_bitcoin(message, signature, address):
        """ Verifies a message signed using PrivateKey.sign_bitcoin()
        or any of the bitcoin utils (e.g. bitcoin-cli, bx, etc.)

        Args:
            message(bytes): The message that the signature corresponds to.
            signature (bytes or str): A Base64 encoded signature
            address (str): Base58Check encoded address.

        Returns:
            bool: True if the signature verified properly, False otherwise.
        """
        magic_sig = base64.b64decode(signature)

        magic = magic_sig[0]
        sig = Signature.from_bytes(magic_sig[1:])
        sig.recovery_id = (magic - 27) & 0x3
        compressed = ((magic - 27) & 0x4) != 0

        # Build the message that was signed
        msg = b"\x18Bitcoin Signed Message:\n" + bytes([len(message)]) + message
        msg_hash = hashlib.sha256(msg).digest()

        derived_public_key = PublicKey.from_signature(msg_hash, sig)
        if derived_public_key is None:
            raise ValueError("Could not recover public key from the provided signature.")

        ver, h160 = address_to_key_hash(address)
        hash160 = derived_public_key.hash160(compressed)
        if hash160 != h160:
            return False

        return derived_public_key.verify(msg_hash, sig)

    def __init__(self, x, y):
        p = ECPointAffine(bitcoin_curve, x, y)
        if not bitcoin_curve.is_on_curve(p):
            raise ValueError("The provided (x, y) are not on the secp256k1 curve.")

        self.point = p

        # RIPEMD-160 of SHA-256
        r = hashlib.new('ripemd160')
        r.update(hashlib.sha256(bytes(self)).digest())
        self.ripe = r.digest()

        r = hashlib.new('ripemd160')
        r.update(hashlib.sha256(self.compressed_bytes).digest())
        self.ripe_compressed = r.digest()

        self.keccak = sha3(bytes(self)[1:])

    def hash160(self, compressed=True):
        """ Return the RIPEMD-160 hash of the SHA-256 hash of the
        public key.

        Args:
            compressed (bool): Whether or not the compressed key should
               be used.
        Returns:
            bytes: RIPEMD-160 byte string.
        """
        return self.ripe_compressed if compressed else self.ripe

    def address(self, compressed=True):
        """ Address property that returns the Base58Check
        encoded version of the HASH160.

        Args:
            compressed (bool): Whether or not the compressed key should
               be used.

        Returns:
            bytes: Base58Check encoded string
        """
        return encode_hex(self.keccak[12:])

    def verify(self, message, signature, do_hash=True):
        """ Verifies that message was appropriately signed.

        Args:
            message (bytes): The message to be verified.
            signature (Signature): A signature object.
            do_hash (bool): True if the message should be hashed prior
              to signing, False if not. This should always be left as
              True except in special situations which require doing
              the hash outside (e.g. handling Bitcoin bugs).

        Returns:
            verified (bool): True if the signature is verified, False
            otherwise.
        """
        msg = get_bytes(message)
        return bitcoin_curve.verify(msg, signature, self.point, do_hash)

    def to_base64(self):
        """ Hex representation of the serialized byte stream.

        Returns:
            b (str): A Base64-encoded string.
        """
        return base64.b64encode(bytes(self))

    def __int__(self):
        mask = 2 ** 256 - 1
        return ((self.point.x & mask) << bitcoin_curve.nlen) | (self.point.y & mask)

    def __bytes__(self):
        return bytes(self.point)

    @property
    def compressed_bytes(self):
        """ Byte string corresponding to a compressed representation
        of this public key.

        Returns:
            b (bytes): A 33-byte long byte string.
        """
        return self.point.compressed_bytes


class Signature(object):
    """ Encapsulation of a ECDSA signature for Bitcoin purposes.

    Args:
        r (Bignum): r component of the signature.
        s (Bignum): s component of the signature.
        recovery_id (int) (Optional): Must be between 0 and 3 specifying
           which of the public keys generated by the algorithm specified
           in http://www.secg.org/sec1-v2.pdf Section 4.1.6 (Public Key
           Recovery Operation) is the correct one for this signature.

    Returns:
        sig (Signature): A Signature object.
    """

    @staticmethod
    def from_der(der):
        """ Decodes a Signature that was DER-encoded.

        Args:
            der (bytes or str): The DER encoding to be decoded.

        Returns:
            Signature: The deserialized signature.
        """
        d = get_bytes(der)
        # d must conform to (from btcd):
        # [0 ] 0x30      - ASN.1 identifier for sequence
        # [1 ] <1-byte>  - total remaining length
        # [2 ] 0x02      - ASN.1 identifier to specify an integer follows
        # [3 ] <1-byte>  - length of R
        # [4.] <bytes>   - R
        # [..] 0x02      - ASN.1 identifier to specify an integer follows
        # [..] <1-byte>  - length of S
        # [..] <bytes>   - S

        # 6 bytes + R (min. 1 byte) + S (min. 1 byte)
        if len(d) < 8:
            raise ValueError("DER signature string is too short.")
        # 6 bytes + R (max. 33 bytes) + S (max. 33 bytes)
        if len(d) > 72:
            raise ValueError("DER signature string is too long.")
        if d[0] != 0x30:
            raise ValueError("DER signature does not start with 0x30.")
        if d[1] != len(d[2:]):
            raise ValueError("DER signature length incorrect.")

        total_length = d[1]

        if d[2] != 0x02:
            raise ValueError("DER signature no 1st int marker.")
        if d[3] <= 0 or d[3] > (total_length - 7):
            raise ValueError("DER signature incorrect R length.")

        # Grab R, check for errors
        rlen = d[3]
        s_magic_index = 4 + rlen
        rb = d[4:s_magic_index]

        if rb[0] & 0x80 != 0:
            raise ValueError("DER signature R is negative.")
        if len(rb) > 1 and rb[0] == 0 and rb[1] & 0x80 != 0x80:
            raise ValueError("DER signature R is excessively padded.")

        r = int.from_bytes(rb, 'big')

        # Grab S, check for errors
        if d[s_magic_index] != 0x02:
            raise ValueError("DER signature no 2nd int marker.")
        slen_index = s_magic_index + 1
        slen = d[slen_index]
        if slen <= 0 or slen > len(d) - (slen_index + 1):
            raise ValueError("DER signature incorrect S length.")

        sb = d[slen_index + 1:]

        if sb[0] & 0x80 != 0:
            raise ValueError("DER signature S is negative.")
        if len(sb) > 1 and sb[0] == 0 and sb[1] & 0x80 != 0x80:
            raise ValueError("DER signature S is excessively padded.")

        s = int.from_bytes(sb, 'big')

        if r < 1 or r >= bitcoin_curve.n:
            raise ValueError("DER signature R is not between 1 and N - 1.")
        if s < 1 or s >= bitcoin_curve.n:
            raise ValueError("DER signature S is not between 1 and N - 1.")

        return Signature(r, s)

    @staticmethod
    def from_base64(b64str):
        """ Generates a signature object from a Base64 encoded string.

        Args:
            b64str (str): A Base64-encoded string.

        Returns:
            Signature: A Signature object.
        """
        return Signature.from_bytes(base64.b64decode(b64str))

    @staticmethod
    def from_bytes(b):
        """ Extracts the r and s components from a byte string.

        Args:
            b (bytes): A 64-byte long string. The first 32 bytes are
               extracted as the r component and the second 32 bytes
               are extracted as the s component.

        Returns:
            Signature: A Signature object.

        Raises:
            ValueError: If signature is incorrect length
        """
        if len(b) != 64:
            raise ValueError("from_bytes: Signature length != 64.")
        r = int.from_bytes(b[0:32], 'big')
        s = int.from_bytes(b[32:64], 'big')
        return Signature(r, s)

    @staticmethod
    def from_hex(h):
        """ Extracts the r and s components from a hex-encoded string.

        Args:
            h (str): A 64-byte (128 character) long string. The first
               32 bytes are extracted as the r component and the
               second 32 bytes are extracted as the s component.

        Returns:
            Signature: A Signature object.
        """
        return Signature.from_bytes(bytes.fromhex(h))

    def __init__(self, r, s, recovery_id=None):
        self.r = r
        self.s = s
        self.recovery_id = recovery_id

    @property
    def x(self):
        """ Convenience property for any method that requires
            this object to provide a Point interface.
        """
        return self.r

    @property
    def y(self):
        """ Convenience property for any method that requires
            this object to provide a Point interface.
        """
        return self.s

    def _canonicalize(self):
        rv = []
        for x in [self.r, self.s]:
            # Compute minimum bytes to represent integer
            bl = math.ceil(x.bit_length() / 8)
            # Make sure it's at least one byte in length
            if bl == 0:
                bl += 1
            x_bytes = x.to_bytes(bl, 'big')

            # make sure there's no way it could be interpreted
            # as a negative integer
            if x_bytes[0] & 0x80:
                x_bytes = bytes([0]) + x_bytes

            rv.append(x_bytes)

        return rv

    def to_der(self):
        """ Encodes this signature using DER

        Returns:
            bytes: The DER encoding of (self.r, self.s).
        """
        # Output should be:
        # 0x30 <length> 0x02 <length r> r 0x02 <length s> s
        r, s = self._canonicalize()

        total_length = 6 + len(r) + len(s)
        der = bytes([0x30, total_length - 2, 0x02, len(r)]) + r + bytes([0x02, len(s)]) + s
        return der

    def to_hex(self):
        """ Hex representation of the serialized byte stream.

        Returns:
            str: A hex-encoded string.
        """
        return bytes_to_str(bytes(self))

    def to_base64(self):
        """ Hex representation of the serialized byte stream.

        Returns:
            str: A Base64-encoded string.
        """
        return base64.b64encode(bytes(self))

    def __bytes__(self):
        nbytes = math.ceil(bitcoin_curve.nlen / 8)
        return self.r.to_bytes(nbytes, 'big') + self.s.to_bytes(nbytes, 'big')


class HDKey(object):
    """ Base class for HDPrivateKey and HDPublicKey.

    Args:
        key (PrivateKey or PublicKey): The underlying simple private or
           public key that is used to sign/verify.
        chain_code (bytes): The chain code associated with the HD key.
        depth (int): How many levels below the master node this key is. By
           definition, depth = 0 for the master node.
        index (int): A value between 0 and 0xffffffff indicating the child
           number. Values >= 0x80000000 are considered hardened children.
        parent_fingerprint (bytes): The fingerprint of the parent node. This
           is 0x00000000 for the master node.

    Returns:
        HDKey: An HDKey object.
    """
    @staticmethod
    def from_b58check(key):
        """ Decodes a Base58Check encoded key.

        The encoding must conform to the description in:
        https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki#serialization-format

        Args:
            key (str): A Base58Check encoded key.

        Returns:
            HDPrivateKey or HDPublicKey:
                Either an HD private or
                public key object, depending on what was serialized.
        """
        return HDKey.from_bytes(base58.b58decode_check(key))

    @staticmethod
    def from_bytes(b):
        """ Generates either a HDPrivateKey or HDPublicKey from the underlying
        bytes.

        The serialization must conform to the description in:
        https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki#serialization-format

        Args:
            b (bytes): A byte stream conforming to the above.

        Returns:
            HDPrivateKey or HDPublicKey:
                Either an HD private or
                public key object, depending on what was serialized.
        """
        if len(b) < 78:
            raise ValueError("b must be at least 78 bytes long.")

        version = int.from_bytes(b[:4], 'big')
        depth = b[4]
        parent_fingerprint = b[5:9]
        index = int.from_bytes(b[9:13], 'big')
        chain_code = b[13:45]
        key_bytes = b[45:78]

        rv = None
        if version == HDPrivateKey.MAINNET_VERSION or version == HDPrivateKey.TESTNET_VERSION:
            if key_bytes[0] != 0:
                raise ValueError("First byte of private key must be 0x00!")

            private_key = int.from_bytes(key_bytes[1:], 'big')
            rv = HDPrivateKey(key=private_key,
                              chain_code=chain_code,
                              index=index,
                              depth=depth,
                              parent_fingerprint=parent_fingerprint)
        elif version == HDPublicKey.MAINNET_VERSION or version == HDPublicKey.TESTNET_VERSION:
            if key_bytes[0] != 0x02 and key_bytes[0] != 0x03:
                raise ValueError("First byte of public key must be 0x02 or 0x03!")

            public_key = PublicKey.from_bytes(key_bytes)
            rv = HDPublicKey(x=public_key.point.x,
                             y=public_key.point.y,
                             chain_code=chain_code,
                             index=index,
                             depth=depth,
                             parent_fingerprint=parent_fingerprint)
        else:
            raise ValueError("incorrect encoding.")

        return rv

    @staticmethod
    def from_hex(h):
        """ Generates either a HDPrivateKey or HDPublicKey from the underlying
        hex-encoded string.

        The serialization must conform to the description in:
        https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki#serialization-format

        Args:
            h (str): A hex-encoded string conforming to the above.

        Returns:
            HDPrivateKey or HDPublicKey:
                Either an HD private or
                public key object, depending on what was serialized.
        """
        return HDKey.from_bytes(bytes.fromhex(h))

    @staticmethod
    def from_path(root_key, path):
        p = HDKey.parse_path(path)

        if p[0] == "m":
            if root_key.master:
                p = p[1:]
            else:
                raise ValueError("root_key must be a master key if 'm' is the first element of the path.")

        keys = [root_key]
        for i in p:
            if isinstance(i, str):
                hardened = i[-1] == "'"
                index = int(i[:-1], 0) | 0x80000000 if hardened else int(i, 0)
            else:
                index = i
            k = keys[-1]
            klass = k.__class__
            keys.append(klass.from_parent(k, index))

        return keys

    @staticmethod
    def parse_path(path):
        if isinstance(path, str):
            # Remove trailing "/"
            p = path.rstrip("/").split("/")
        elif isinstance(path, bytes):
            p = path.decode('utf-8').rstrip("/").split("/")
        else:
            p = list(path)

        return p

    @staticmethod
    def path_from_indices(l):
        p = []
        for n in l:
            if n == "m":
                p.append(n)
            else:
                if n & 0x80000000:
                    _n = n & 0x7fffffff
                    p.append(str(_n) + "'")
                else:
                    p.append(str(n))

        return "/".join(p)

    def __init__(self, key, chain_code, index, depth, parent_fingerprint):
        if index < 0 or index > 0xffffffff:
            raise ValueError("index is out of range: 0 <= index <= 2**32 - 1")

        if not isinstance(chain_code, bytes):
            raise TypeError("chain_code must be bytes")

        self._key = key
        self.chain_code = chain_code
        self.depth = depth
        self.index = index

        self.parent_fingerprint = get_bytes(parent_fingerprint)

    @property
    def master(self):
        """ Whether or not this is a master node.

        Returns:
            bool: True if this is a master node, False otherwise.
        """
        return self.depth == 0

    @property
    def hardened(self):
        """ Whether or not this is a hardened node.

        Hardened nodes are those with indices >= 0x80000000.

        Returns:
            bool: True if this is hardened, False otherwise.
        """
        # A hardened key is a key with index >= 2 ** 31, so
        # we check that the MSB of a uint32 is set.
        return self.index & 0x80000000

    @property
    def identifier(self):
        """ Returns the identifier for the key.

        A key's identifier and fingerprint are defined as:
        https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki#key-identifiers

        Returns:
            bytes: A 20-byte RIPEMD-160 hash.
        """
        raise NotImplementedError

    @property
    def fingerprint(self):
        """ Returns the key's fingerprint, which is the first 4 bytes
        of its identifier.

        A key's identifier and fingerprint are defined as:
        https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki#key-identifiers

        Returns:
            bytes: The first 4 bytes of the RIPEMD-160 hash.
        """
        return self.identifier[:4]

    def to_b58check(self, testnet=False):
        """ Generates a Base58Check encoding of this key.

        Args:
            testnet (bool): True if the key is to be used with
                testnet, False otherwise.
        Returns:
            str: A Base58Check encoded string representing the key.
        """
        b = self.testnet_bytes if testnet else bytes(self)
        return base58.b58encode_check(b)

    def _serialize(self, testnet=False):
        version = self.TESTNET_VERSION if testnet else self.MAINNET_VERSION
        key_bytes = self._key.compressed_bytes if isinstance(self, HDPublicKey) else b'\x00' + bytes(self._key)
        return (version.to_bytes(length=4, byteorder='big') +
                bytes([self.depth]) +
                self.parent_fingerprint +
                self.index.to_bytes(length=4, byteorder='big') +
                self.chain_code +
                key_bytes)

    def __bytes__(self):
        return self._serialize()

    @property
    def testnet_bytes(self):
        """ Serialization of the key for testnet.

        Returns:
            bytes:
                A 78-byte serialization of the key, specifically for
                testnet (i.e. the first 2 bytes will be 0x0435).
        """
        return self._serialize(True)


class HDPrivateKey(HDKey, PrivateKeyBase):
    """ Implements an HD Private Key according to BIP-0032:
    https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki

    For the vast majority of use cases, the 3 static functions
    (HDPrivateKey.master_key_from_entropy,
    HDPrivateKey.master_key_from_seed and
    HDPrivateKey.from_parent) will be used rather than directly
    constructing an object.

    Args:
        key (PrivateKey or PublicKey): The underlying simple private or
           public key that is used to sign/verify.
        chain_code (bytes): The chain code associated with the HD key.
        depth (int): How many levels below the master node this key is. By
           definition, depth = 0 for the master node.
        index (int): A value between 0 and 0xffffffff indicating the child
           number. Values >= 0x80000000 are considered hardened children.
        parent_fingerprint (bytes): The fingerprint of the parent node. This
           is 0x00000000 for the master node.

    Returns:
        HDKey: An HDKey object.

    """
    MAINNET_VERSION = 0x0488ADE4
    TESTNET_VERSION = 0x04358394

    @staticmethod
    def master_key_from_mnemonic(mnemonic, passphrase=''):
        """ Generates a master key from a mnemonic.

        Args:
            mnemonic (str): The mnemonic sentence representing
               the seed from which to generate the master key.
            passphrase (str): Password if one was used.

        Returns:
            HDPrivateKey: the master private key.
        """
        return HDPrivateKey.master_key_from_seed(
            Mnemonic.to_seed(mnemonic, passphrase))

    @staticmethod
    def master_key_from_entropy(passphrase='', strength=128):
        """ Generates a master key from system entropy.

        Args:
            strength (int): Amount of entropy desired. This should be
               a multiple of 32 between 128 and 256.
            passphrase (str): An optional passphrase for the generated
               mnemonic string.

        Returns:
            HDPrivateKey, str:
                a tuple consisting of the master
                private key and a mnemonic string from which the seed
                can be recovered.
        """
        if strength % 32 != 0:
            raise ValueError("strength must be a multiple of 32")
        if strength < 128 or strength > 256:
            raise ValueError("strength should be >= 128 and <= 256")
        entropy = rand_bytes(strength // 8)
        m = Mnemonic(language='english')
        n = m.to_mnemonic(entropy)
        return HDPrivateKey.master_key_from_seed(
            Mnemonic.to_seed(n, passphrase)), n

    @staticmethod
    def master_key_from_seed(seed):
        """ Generates a master key from a provided seed.

        Args:
            seed (bytes or str): a string of bytes or a hex string

        Returns:
            HDPrivateKey: the master private key.
        """
        S = get_bytes(seed)
        I = hmac.new(b"Bitcoin seed", S, hashlib.sha512).digest()
        Il, Ir = I[:32], I[32:]
        parse_Il = int.from_bytes(Il, 'big')
        if parse_Il == 0 or parse_Il >= bitcoin_curve.n:
            raise ValueError("Bad seed, resulting in invalid key!")

        return HDPrivateKey(key=parse_Il, chain_code=Ir, index=0, depth=0)

    @staticmethod
    def from_parent(parent_key, i):
        """ Derives a child private key from a parent
        private key. It is not possible to derive a child
        private key from a public parent key.

        Args:
            parent_private_key (HDPrivateKey):
        """
        if not isinstance(parent_key, HDPrivateKey):
            raise TypeError("parent_key must be an HDPrivateKey object.")

        hmac_key = parent_key.chain_code
        if i & 0x80000000:
            hmac_data = b'\x00' + bytes(parent_key._key) + i.to_bytes(length=4, byteorder='big')
        else:
            hmac_data = parent_key.public_key.compressed_bytes + i.to_bytes(length=4, byteorder='big')

        I = hmac.new(hmac_key, hmac_data, hashlib.sha512).digest()
        Il, Ir = I[:32], I[32:]

        parse_Il = int.from_bytes(Il, 'big')
        if parse_Il >= bitcoin_curve.n:
            return None

        child_key = (parse_Il + parent_key._key.key) % bitcoin_curve.n

        if child_key == 0:
            # Incredibly unlucky choice
            return None

        child_depth = parent_key.depth + 1
        return HDPrivateKey(key=child_key,
                            chain_code=Ir,
                            index=i,
                            depth=child_depth,
                            parent_fingerprint=parent_key.fingerprint)

    def __init__(self, key, chain_code, index, depth,
                 parent_fingerprint=b'\x00\x00\x00\x00'):
        if index < 0 or index > 0xffffffff:
            raise ValueError("index is out of range: 0 <= index <= 2**32 - 1")

        private_key = PrivateKey(key)
        HDKey.__init__(self, private_key, chain_code, index, depth,
                       parent_fingerprint)
        self._public_key = None

    @property
    def public_key(self):
        """ Returns the public key associated with this private key.

        Returns:
            HDPublicKey:
                The HDPublicKey object that corresponds to this
                private key.
        """
        if self._public_key is None:
            self._public_key = HDPublicKey(x=self._key.public_key.point.x,
                                           y=self._key.public_key.point.y,
                                           chain_code=self.chain_code,
                                           index=self.index,
                                           depth=self.depth,
                                           parent_fingerprint=self.parent_fingerprint)

        return self._public_key

    def raw_sign(self, message, do_hash=True):
        """ Signs message using the underlying non-extended private key.

        Args:
            message (bytes): The message to be signed. If a string is
                provided it is assumed the encoding is 'ascii' and
                converted to bytes. If this is not the case, it is up
                to the caller to convert the string to bytes
                appropriately and pass in the bytes.
            do_hash (bool): True if the message should be hashed prior
                to signing, False if not. This should always be left as
                True except in special situations which require doing
                the hash outside (e.g. handling Bitcoin bugs).

        Returns:
            ECPointAffine:
                a raw point (r = pt.x, s = pt.y) which is
                the signature.
        """
        return self._key.raw_sign(message, do_hash)

    def sign(self, message, do_hash=True):
        """ Signs message using the underlying non-extended private key.

        Note:
            This differs from `raw_sign()` since it returns a Signature object.

        Args:
            message (bytes or str): The message to be signed. If a
                string is provided it is assumed the encoding is
                'ascii' and converted to bytes. If this is not the
                case, it is up to the caller to convert the string to
                bytes appropriately and pass in the bytes.
            do_hash (bool): True if the message should be hashed prior
                to signing, False if not. This should always be left as
                True except in special situations which require doing
                the hash outside (e.g. handling Bitcoin bugs).

        Returns:
            Signature: The signature corresponding to message.
        """
        return self._key.sign(message, do_hash)

    def sign_bitcoin(self, message, compressed=False):
        """ Signs a message using the underlying non-extended private
        key such that it is compatible with bitcoind, bx, and other
        Bitcoin clients/nodes/utilities.

        Note:
            0x18 + b\"Bitcoin Signed Message:" + newline + len(message) is
            prepended to the message before signing.

        Args:
            message (bytes or str): Message to be signed.
            compressed (bool):
                True if the corresponding public key will be
                used in compressed format. False if the uncompressed version
                is used.

        Returns:
            bytes: A Base64-encoded byte string of the signed message.
            The first byte of the encoded message contains information
            about how to recover the public key. In bitcoind parlance,
            this is the magic number containing the recovery ID and
            whether or not the key was compressed or not. (This function
            always processes full, uncompressed public-keys, so the
            magic number will always be either 27 or 28).
        """

        return self._key.sign_bitcoin(message, compressed)

    @property
    def identifier(self):
        """ Returns the identifier for the key.

        A key's identifier and fingerprint are defined as:
        https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki#key-identifiers

        In this case, it will return the RIPEMD-160 hash of the
        corresponding public key.

        Returns:
            bytes: A 20-byte RIPEMD-160 hash.
        """
        return self.public_key.hash160()

    def __int__(self):
        return int(self.key)


class HDPublicKey(HDKey, PublicKeyBase):
    """ Implements an HD Public Key according to BIP-0032:
    https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki

    For the vast majority of use cases, the static function
    HDPublicKey.from_parent() will be used rather than directly
    constructing an object.

    Args:
        x (int): x component of the point representing the public key.
        y (int): y component of the point representing the public key.
        chain_code (bytes): The chain code associated with the HD key.
        depth (int): How many levels below the master node this key is. By
           definition, depth = 0 for the master node.
        index (int): A value between 0 and 0xffffffff indicating the child
           number. Values >= 0x80000000 are considered hardened children.
        parent_fingerprint (bytes): The fingerprint of the parent node. This
           is 0x00000000 for the master node.

    Returns:
        HDPublicKey: An HDPublicKey object.

    """

    MAINNET_VERSION = 0x0488B21E
    TESTNET_VERSION = 0x043587CF

    @staticmethod
    def from_parent(parent_key, i):
        """
        """
        if isinstance(parent_key, HDPrivateKey):
            # Get child private key
            return HDPrivateKey.from_parent(parent_key, i).public_key
        elif isinstance(parent_key, HDPublicKey):
            if i & 0x80000000:
                raise ValueError("Can't generate a hardened child key from a parent public key.")
            else:
                I = hmac.new(parent_key.chain_code,
                             parent_key.compressed_bytes + i.to_bytes(length=4, byteorder='big'),
                             hashlib.sha512).digest()
                Il, Ir = I[:32], I[32:]
                parse_Il = int.from_bytes(Il, 'big')
                if parse_Il >= bitcoin_curve.n:
                    return None

                temp_priv_key = PrivateKey(parse_Il)
                Ki = temp_priv_key.public_key.point + parent_key._key.point
                if Ki.infinity:
                    return None

                child_depth = parent_key.depth + 1
                return HDPublicKey(x=Ki.x,
                                   y=Ki.y,
                                   chain_code=Ir,
                                   index=i,
                                   depth=child_depth,
                                   parent_fingerprint=parent_key.fingerprint)
        else:
            raise TypeError("parent_key must be either a HDPrivateKey or HDPublicKey object")

    def __init__(self, x, y, chain_code, index, depth,
                 parent_fingerprint=b'\x00\x00\x00\x00'):
        key = PublicKey(x, y)
        HDKey.__init__(self, key, chain_code, index, depth, parent_fingerprint)
        PublicKeyBase.__init__(self)

    @property
    def identifier(self):
        """ Returns the identifier for the key.

        A key's identifier and fingerprint are defined as:
        https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki#key-identifiers

        In this case, it will return the RIPEMD-160 hash of the
        non-extended public key.

        Returns:
            bytes: A 20-byte RIPEMD-160 hash.
        """
        return self.hash160()

    def hash160(self, compressed=True):
        """ Return the RIPEMD-160 hash of the SHA-256 hash of the
        non-extended public key.

        Note:
            This always returns the hash of the compressed version of
            the public key.

        Returns:
            bytes: RIPEMD-160 byte string.
        """
        return self._key.hash160(True)

    def address(self, compressed=True, testnet=False):
        """ Address property that returns the Base58Check
        encoded version of the HASH160.

        Args:
            compressed (bool): Whether or not the compressed key should
               be used.
            testnet (bool): Whether or not the key is intended for testnet
               usage. False indicates mainnet usage.

        Returns:
            bytes: Base58Check encoded string
        """
        return self._key.address(True)

    def verify(self, message, signature, do_hash=True):
        """ Verifies that message was appropriately signed.

        Args:
            message (bytes): The message to be verified.
            signature (Signature): A signature object.
            do_hash (bool): True if the message should be hashed prior
                to signing, False if not. This should always be left as
                True except in special situations which require doing
                the hash outside (e.g. handling Bitcoin bugs).

        Returns:
            verified (bool): True if the signature is verified, False
            otherwise.
        """
        return self._key.verify(message, signature, do_hash)

    @property
    def compressed_bytes(self):
        """ Byte string corresponding to a compressed representation
        of this public key.

        Returns:
            b (bytes): A 33-byte long byte string.
        """
        return self._key.compressed_bytes
