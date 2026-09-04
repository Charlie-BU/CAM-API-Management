import os
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from google.auth.exceptions import TransportError

from database.enums import UserRole
from database.models import Base, User, UserAuthIdentity
from services.user import (
    GoogleAuthError,
    userGoogleLogin,
    userLinkGoogleIdentity,
    userModifyPassword,
    verifyGoogleCredential,
)


class GoogleAuthTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    @staticmethod
    def google_payload(subject="google-subject", email="user@example.com"):
        return {
            "iss": "https://accounts.google.com",
            "sub": subject,
            "email": email,
            "email_verified": True,
            "name": "Google User",
        }

    def test_google_login_creates_guest_user_and_reuses_identity(self):
        with patch(
            "services.user.verifyGoogleCredential",
            return_value=self.google_payload(),
        ):
            first = userGoogleLogin(self.session, "credential")
            second = userGoogleLogin(self.session, "credential")

        self.assertEqual(200, first["status"])
        self.assertEqual(200, second["status"])
        self.assertEqual(1, self.session.query(User).count())
        self.assertEqual(1, self.session.query(UserAuthIdentity).count())
        user = self.session.query(User).one()
        self.assertEqual(UserRole.GUEST, user.role)
        self.assertIsNone(user.password)
        self.assertFalse(user.toJson()["has_password"])
        self.assertEqual(["google"], user.toJson()["auth_providers"])

    def test_google_login_requires_link_when_email_exists(self):
        self.session.add(
            User(
                username="local-user",
                password=User.hashPassword("password"),
                nickname="Local User",
                email="user@example.com",
                role=UserRole.GUEST,
            )
        )
        self.session.commit()

        with patch(
            "services.user.verifyGoogleCredential",
            return_value=self.google_payload(),
        ):
            with self.assertRaises(GoogleAuthError) as context:
                userGoogleLogin(self.session, "credential")

        self.assertEqual(409, context.exception.http_status)
        self.assertEqual("ACCOUNT_LINK_REQUIRED", context.exception.code)
        self.assertEqual(0, self.session.query(UserAuthIdentity).count())

    def test_authenticated_user_can_link_matching_google_email(self):
        user = User(
            username="local-user",
            password=User.hashPassword("password"),
            nickname="Local User",
            email="user@example.com",
            role=UserRole.GUEST,
        )
        self.session.add(user)
        self.session.commit()

        with patch(
            "services.user.verifyGoogleCredential",
            return_value=self.google_payload(),
        ):
            response = userLinkGoogleIdentity(
                self.session,
                user.id,
                "credential",
            )

        self.assertEqual(200, response["status"])
        identity = self.session.query(UserAuthIdentity).one()
        self.assertEqual(user.id, identity.user_id)

    def test_google_only_user_cannot_modify_local_password(self):
        user = User(
            username="google-user",
            password=None,
            nickname="Google User",
            email="user@example.com",
            role=UserRole.GUEST,
        )
        self.session.add(user)
        self.session.commit()

        response = userModifyPassword(
            self.session,
            user.id,
            "old-password",
            "new-password",
        )

        self.assertEqual(-4, response["status"])

    def test_google_credential_verification_checks_issuer_and_domain(self):
        payload = self.google_payload()
        with (
            patch.dict(
                os.environ,
                {
                    "GOOGLE_CLIENT_ID": "test-client-id",
                    "GOOGLE_HOSTED_DOMAIN": "example.com",
                },
                clear=False,
            ),
            patch(
                "services.user.google_id_token.verify_oauth2_token",
                return_value={**payload, "hd": "example.com"},
            ) as verifier,
        ):
            response = verifyGoogleCredential("credential")

        self.assertEqual(payload["sub"], response["sub"])
        self.assertEqual("test-client-id", verifier.call_args.args[2])

    def test_google_credential_rejects_unverified_email(self):
        with (
            patch.dict(
                os.environ,
                {"GOOGLE_CLIENT_ID": "test-client-id"},
                clear=False,
            ),
            patch(
                "services.user.google_id_token.verify_oauth2_token",
                return_value={
                    **self.google_payload(),
                    "email_verified": False,
                },
            ),
        ):
            with self.assertRaises(GoogleAuthError) as context:
                verifyGoogleCredential("credential")

        self.assertEqual(401, context.exception.http_status)
        self.assertEqual("UNVERIFIED_GOOGLE_ACCOUNT", context.exception.code)

    def test_google_credential_maps_transport_failure_to_service_unavailable(self):
        with (
            patch.dict(
                os.environ,
                {"GOOGLE_CLIENT_ID": "test-client-id"},
                clear=False,
            ),
            patch(
                "services.user.google_id_token.verify_oauth2_token",
                side_effect=TransportError("network unavailable"),
            ),
        ):
            with self.assertRaises(GoogleAuthError) as context:
                verifyGoogleCredential("credential")

        self.assertEqual(503, context.exception.http_status)
        self.assertEqual("GOOGLE_AUTH_UNAVAILABLE", context.exception.code)


if __name__ == "__main__":
    unittest.main()
