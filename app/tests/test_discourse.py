from unittest import TestCase

from ..discourse import sso

class HmacSigningTests(TestCase):
    def test_packing_and_unpacking_work_with_valid_signature(self):
        signed = sso.pack_and_sign_payload({'hello': 'there'}, secret='foo')
        payload = sso.unpack_and_verify_payload(signed, secret='foo')
        self.assertEqual(payload['hello'], 'there')

    def test_invalid_signature_error_is_raised(self):
        signed = sso.pack_and_sign_payload({'hello': 'there'}, secret='foo')
        with self.assertRaises(sso.InvalidSignatureError):
            payload = sso.unpack_and_verify_payload(signed, secret='bar')
