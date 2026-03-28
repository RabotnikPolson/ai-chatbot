from unittest.mock import patch, MagicMock
from providers.ollama import OllamaProvider
from workers.tasks import generate_reply
from db.models import User, Conversation, Message, MessageStatusEnum

def test_ollama_provider_mock():
    provider = OllamaProvider()

    with patch("providers.ollama.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "I am a fake model"}}
        mock_post.return_value = mock_response

        answer = provider.generate(messages=[{"role": "user", "content": "Hello"}])

        assert answer == "I am a fake model"
        mock_post.assert_called_once()


def test_worker_idempotency(db_session):
    user = User(email="worker@test.com", password_hash="123")
    db_session.add(user)
    db_session.commit()

    conv = Conversation(owner_user_id=user.id, title="Test")
    db_session.add(conv)
    db_session.commit()

    msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content="Already done",
        status=MessageStatusEnum.done
    )
    db_session.add(msg)
    db_session.commit()

    with patch("workers.tasks.SessionLocal", return_value=db_session), \
            patch("workers.tasks.redis_client"):

        result = generate_reply(msg.id)

    assert result == "Already done"


def test_worker_persists_latency_on_success(db_session):
    user = User(email="worker_latency@test.com", password_hash="123")
    db_session.add(user)
    db_session.commit()

    conv = Conversation(owner_user_id=user.id, title="Latency test")
    db_session.add(conv)
    db_session.commit()

    msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content="",
        status=MessageStatusEnum.queued,
    )
    db_session.add(msg)
    db_session.commit()

    with patch("workers.tasks.SessionLocal", return_value=db_session), \
            patch("workers.tasks.redis_client.get", return_value=None), \
            patch("workers.tasks.redis_client.setex"), \
            patch("workers.tasks.redis_client.publish"), \
            patch("workers.tasks.OllamaProvider.generate_stream", return_value=iter(["Hel", "lo"])):
        result = generate_reply(msg.id)

    updated = db_session.query(Message).filter(Message.id == msg.id).first()

    assert result == "Success"
    assert updated is not None
    assert updated.status == MessageStatusEnum.done
    assert updated.content == "Hello"
    assert updated.provider == "ollama"
    assert updated.latency_ms is not None
    assert updated.latency_ms >= 0
