import os
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Account, Base
from app.services.oauth.service import OAuthService


class OAuthPersistenceTests(unittest.TestCase):
    def test_tokens_are_encrypted_and_restored_from_database(self):
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        sessions = sessionmaker(bind=engine)
        db = sessions()
        tokens = {"access_token": "access-secret", "refresh_token": "refresh-secret", "expires_in": 3600}
        service = OAuthService()
        service.store_tokens("owner@example.com", "GMAIL", tokens, db=db)

        account = db.query(Account).one()
        self.assertNotIn("access-secret", account.access_token_encrypted)
        self.assertNotIn("refresh-secret", account.refresh_token_encrypted)

        restored_service = OAuthService()
        restored = restored_service.get_tokens("owner@example.com", "GMAIL", db=db)
        self.assertEqual("access-secret", restored["access_token"])
        self.assertEqual("refresh-secret", restored["refresh_token"])
        db.close()


if __name__ == "__main__":
    unittest.main()
